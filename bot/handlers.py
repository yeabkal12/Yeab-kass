# bot/handlers.py

import os
import uuid
import logging
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.future import select

# Import database session and models
from database_models.manager import AsyncSessionLocal, User, Transaction

# --- Environment Variables ---
WEB_APP_URL = os.getenv("WEB_APP_URL") # The URL where your frontend is hosted
CHAPA_API_KEY = os.getenv("CHAPA_API_KEY")
CHAPA_API_URL = "https://api.chapa.co/v1/transaction/initialize"

# --- Conversation States ---
DEPOSIT_AMOUNT = range(1)

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
async def get_or_create_user(user_id: int, username: str) -> User:
    """Gets a user from the DB or creates a new one if they don't exist."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            logger.info(f"Creating new user for ID: {user_id}, Username: {username}")
            user = User(telegram_id=user_id, username=username, balance=0.00)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

def build_main_menu() -> InlineKeyboardMarkup:
    """Builds the main menu keyboard."""
    buttons = [
        [InlineKeyboardButton("🚀 Open Game Zone", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton("💰 My Wallet", callback_data="wallet"),
            InlineKeyboardButton("📥 Deposit", callback_data="deposit"),
        ],
        [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")], # Withdrawal can be implemented here
    ]
    return InlineKeyboardMarkup(buttons)

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    await get_or_create_user(user.id, user.username)
    
    welcome_text = (
        f"👋 Welcome to **Yeab Game Zone**, {user.first_name}!\n\n"
        "Ready to play Ludo? Open the Game Zone to find or create a match."
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=build_main_menu(),
        parse_mode='Markdown'
    )

# --- Callback Query (Button Click) Handlers ---
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all button clicks from the main menu."""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    user_id = query.from_user.id

    if action == "wallet":
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
            balance = user.balance if user else 0.00
        
        wallet_text = f"💰 **Your Wallet**\n\n**Current Balance:** `{balance:.2f} ETB`"
        await query.edit_message_text(
            wallet_text,
            reply_markup=build_main_menu(),
            parse_mode='Markdown'
        )

    elif action == "deposit":
        await query.edit_message_text(
            text="Please enter the amount you want to deposit (in ETB).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="cancel_conv")]])
        )
        return DEPOSIT_AMOUNT

    elif action == "withdraw":
         await query.edit_message_text(
            text="Withdrawal feature is coming soon!",
            reply_markup=build_main_menu()
        )
         
    # This handler can be expanded for other buttons like "Help", "History", etc.
    return ConversationHandler.END


# --- Conversation Handlers (for Deposit) ---
async def deposit_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the amount entered by the user for deposit."""
    user = update.effective_user
    try:
        amount = float(update.message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a positive number. Or type /cancel.")
        return DEPOSIT_AMOUNT

    # Chapa expects amount in the smallest currency unit, but for ETB it's just the amount.
    tx_ref = f"YGZ-DEP-{user.id}-{uuid.uuid4()}"
    deposit_fee = amount * 0.02 # 2% deposit fee
    amount_after_fee = amount - deposit_fee

    headers = {
        "Authorization": f"Bearer {CHAPA_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # User info can be pre-filled for Chapa
    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": "user@email.com", # Placeholder
        "first_name": user.first_name,
        "last_name": user.last_name or "Player",
        "tx_ref": tx_ref,
        "callback_url": f"{WEB_APP_URL}/payment-webhook", # IMPORTANT: You need a webhook endpoint
        "return_url": "https://t.me/YourBotUsername", # URL to return to after payment
        "customization[title]": "Yeab Game Zone Deposit",
        "customization[description]": f"Deposit of {amount} ETB",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CHAPA_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        checkout_url = data["data"]["checkout_url"]
        
        # Store transaction record
        async with AsyncSessionLocal() as session:
            new_tx = Transaction(tx_ref=tx_ref, user_id=user.id, amount=amount)
            session.add(new_tx)
            await session.commit()
            
        text = (
            f"✅ Deposit initiated!\n\n"
            f"**Amount:** `{amount:.2f} ETB`\n"
            f"**Fee (2%):** `{deposit_fee:.2f} ETB`\n"
            f"**You will receive:** `{amount_after_fee:.2f} ETB`\n\n"
            "Click the button below to complete your payment."
        )
        
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Pay with Chapa", url=checkout_url)]])
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    except httpx.HTTPStatusError as e:
        logger.error(f"Chapa API Error: {e.response.text}")
        await update.message.reply_text("Sorry, we couldn't connect to the payment gateway. Please try again later.")
    except Exception as e:
        logger.error(f"An error occurred during deposit: {e}")
        await update.message.reply_text("An unexpected error occurred. Please contact support.")

    # End the conversation
    return ConversationHandler.END


async def cancel_conversation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation (e.g., deposit)."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Action canceled. What would you like to do next?",
        reply_markup=build_main_menu()
    )
    return ConversationHandler.END