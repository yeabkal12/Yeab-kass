# bot/handlers.py - The Final, Production-Ready Version

import os
import uuid
import logging
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

# Import database session and models
from database_models.manager import AsyncSessionLocal, User, Transaction

# --- Environment Variable Validation ---
WEB_APP_URL = os.getenv("WEB_APP_URL")
CHAPA_API_KEY = os.getenv("CHAPA_API_KEY")
CHAPA_API_URL = "https://api.chapa.co/v1/transaction/initialize"

if not WEB_APP_URL: raise ValueError("FATAL: WEB_APP_URL is not set.")
if not CHAPA_API_KEY: raise ValueError("FATAL: CHAPA_API_KEY is not set.")

# --- Conversation States & Logging ---
DEPOSIT_AMOUNT = range(1)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
async def get_or_create_user(user_id: int, username: str) -> User:
    """Gets a user from the DB or creates one, handling race conditions."""
    async with AsyncSessionLocal() as session:
        # First attempt to get the user
        stmt = select(User).where(User.telegram_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return user
        
        # If user doesn't exist, try to create them
        try:
            logger.info(f"Creating new user for ID: {user_id}, Username: {username}")
            new_user = User(telegram_id=user_id, username=username, balance=0.00)
            session.add(new_user)
            await session.commit()
            return new_user
        except IntegrityError:
            # THIS IS THE FIX for the race condition
            logger.warning(f"Race condition detected for user {user_id}. Rolling back and re-fetching.")
            await session.rollback()
            # The user must exist now, so we can fetch them
            result = await session.execute(stmt)
            user = result.scalar_one()
            return user

def build_main_menu() -> InlineKeyboardMarkup:
    """Builds the main menu keyboard."""
    buttons = [
        [InlineKeyboardButton("🚀 Open Game Zone", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton("💰 My Wallet", callback_data="wallet"),
            InlineKeyboardButton("📥 Deposit", callback_data="deposit"),
        ],
        [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
    ]
    return InlineKeyboardMarkup(buttons)

# --- Command & Callback Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await get_or_create_user(user.id, user.username)
    welcome_text = f"👋 Welcome to **Yeab Game Zone**, {user.first_name}!\n\nReady to play Ludo?"
    await update.message.reply_text(welcome_text, reply_markup=build_main_menu(), parse_mode='Markdown')

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data
    user_id = query.from_user.id

    if action == "wallet":
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
        balance = user.balance if user else 0.00
        wallet_text = f"💰 **Your Wallet**\n\n**Current Balance:** `{balance:.2f} ETB`"
        await query.edit_message_text(wallet_text, reply_markup=build_main_menu(), parse_mode='Markdown')
        return ConversationHandler.END

    elif action == "deposit":
        await query.edit_message_text(
            text="Please enter the amount you want to deposit (in ETB).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="cancel_conv")]])
        )
        return DEPOSIT_AMOUNT

    elif action == "withdraw":
        await query.edit_message_text(text="Withdrawal feature is coming soon!", reply_markup=build_main_menu())
        return ConversationHandler.END

# --- Conversation Handlers (for Deposit) ---
async def deposit_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    try:
        amount = float(update.message.text)
        if amount <= 10: raise ValueError("Amount must be greater than 10 ETB.")
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid amount. Please enter a number greater than 10. Or type /cancel.")
        return DEPOSIT_AMOUNT

    tx_ref = f"YGZ-DEP-{user.id}-{uuid.uuid4()}"
    deposit_fee = amount * 0.02
    amount_after_fee = amount - deposit_fee

    # --- THIS IS THE FIX for the "Ghost Transaction" ---
    # 1. First, save the transaction record to our database as 'pending'.
    try:
        async with AsyncSessionLocal() as session:
            new_tx = Transaction(tx_ref=tx_ref, user_id=user.id, amount=amount, type='deposit', status='pending')
            session.add(new_tx)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save pending transaction to DB: {e}")
        await update.message.reply_text("A database error occurred. Please try again later.")
        return ConversationHandler.END

    # 2. Only after saving, attempt to contact the payment gateway.
    headers = {"Authorization": f"Bearer {CHAPA_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "amount": str(amount), "currency": "ETB", "email": f"{user.id}@telegram.user",
        "first_name": user.first_name, "last_name": user.last_name or "Ludo", "tx_ref": tx_ref,
        "callback_url": f"{WEB_APP_URL}/api/payment/webhook", # You'll need to build this endpoint
        "return_url": f"https://t.me/{context.bot.username}",
        "customization[title]": "Yeab Game Zone Deposit", "customization[description]": f"Deposit of {amount} ETB"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CHAPA_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        checkout_url = data["data"]["checkout_url"]
        text = (
            f"✅ Deposit initiated!\n\n**Amount:** `{amount:.2f} ETB`\n**Fee (2%):** `{deposit_fee:.2f} ETB`\n"
            f"**You will receive:** `{amount_after_fee:.2f} ETB`\n\nClick the button below to complete your payment."
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Pay with Chapa", url=checkout_url)]])
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    except httpx.HTTPStatusError as e:
        logger.error(f"Chapa API Error: {e.response.text}")
        await update.message.reply_text("Sorry, we couldn't connect to the payment gateway. Please try again later.")
        # Optional: Update transaction status to 'failed' in DB
    except Exception as e:
        logger.error(f"An error occurred during Chapa request: {e}")
        await update.message.reply_text("An unexpected error occurred. Please contact support.")

    return ConversationHandler.END

async def cancel_conversation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("Action canceled. What would you like to do next?", reply_markup=build_main_menu())
    else:
        await update.message.reply_text("Action canceled.", reply_markup=build_main_menu())
    return ConversationHandler.END

def setup_handlers(application: Application):
    """Registers all the bot handlers with the Application instance."""
    deposit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_handler, pattern='^deposit$')],
        states={ DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_handler)] },
        fallbacks=[ CommandHandler('cancel', cancel_conversation_handler), CallbackQueryHandler(cancel_conversation_handler, pattern='^cancel_conv$') ],
        per_message=False
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(deposit_conv_handler)
    application.add_handler(CallbackQueryHandler(main_menu_handler))