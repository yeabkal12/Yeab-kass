# bot/handlers.py - The Final, Production-Ready Version with Race Condition Fix

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
# We ONLY check for variables that are needed immediately at import time.
# WEB_APP_URL will be checked later, inside the functions that use it.
CHAPA_API_KEY = os.getenv("CHAPA_API_KEY")
if not CHAPA_API_KEY: raise ValueError("FATAL: CHAPA_API_KEY is not set.")

CHAPA_API_URL = "https://api.chapa.co/v1/transaction/initialize"

# --- Conversation States & Logging ---
DEPOSIT_AMOUNT = range(1)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
async def get_or_create_user(user_id: int, username: str) -> User:
    # This robust version handles race conditions correctly
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user: return user
        try:
            logger.info(f"Creating new user for ID: {user_id}")
            new_user = User(telegram_id=user_id, username=username, balance=0.00)
            session.add(new_user)
            await session.commit()
            return new_user
        except IntegrityError:
            await session.rollback()
            result = await session.execute(stmt)
            return result.scalar_one()

def build_main_menu() -> InlineKeyboardMarkup:
    """Builds the main menu keyboard, checking for WEB_APP_URL just-in-time."""
    
    # --- THIS IS THE CRITICAL FIX ---
    # We get the WEB_APP_URL here, inside the function, not at the top of the file.
    WEB_APP_URL = os.getenv("WEB_APP_URL")
    
    # Base buttons that are always available
    buttons = [
        [
            InlineKeyboardButton("💰 My Wallet", callback_data="wallet"),
            InlineKeyboardButton("📥 Deposit", callback_data="deposit"),
        ],
        [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
    ]
    
    # Only add the "Open Game Zone" button if the URL is actually available
    if WEB_APP_URL:
        buttons.insert(0, [InlineKeyboardButton("🚀 Open Game Zone", web_app=WebAppInfo(url=WEB_APP_URL))])
    else:
        # If the URL is missing, we log a critical error but DO NOT crash.
        logger.critical("FATAL: WEB_APP_URL is not set! The 'Open Game Zone' button will be hidden.")

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
        if amount <= 10: raise ValueError("Amount must be > 10")
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid amount. Please enter a number greater than 10.")
        return DEPOSIT_AMOUNT

    tx_ref = f"YGZ-DEP-{user.id}-{uuid.uuid4()}"
    
    # Get the WEB_APP_URL again, just in time
    WEB_APP_URL = os.getenv("WEB_APP_URL")

    # Save the pending transaction first
    try:
        async with AsyncSessionLocal() as session:
            new_tx = Transaction(tx_ref=tx_ref, user_id=user.id, amount=amount, type='deposit', status='pending')
            session.add(new_tx)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save pending transaction to DB: {e}")
        await update.message.reply_text("A database error occurred. Please try again.")
        return ConversationHandler.END

    # Then, contact Chapa
    headers = {"Authorization": f"Bearer {CHAPA_API_KEY}"}
    payload = {
        "amount": str(amount), "currency": "ETB", "email": f"{user.id}@telegram.user",
        "first_name": user.first_name, "last_name": user.last_name or "Ludo", "tx_ref": tx_ref,
        "callback_url": f"{WEB_APP_URL}/api/payment/webhook",
        "return_url": f"https://t.me/{context.bot.username}",
        "customization[title]": "Yeab Game Zone Deposit", "customization[description]": f"Deposit of {amount} ETB"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(CHAPA_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        
        checkout_url = data["data"]["checkout_url"]
        deposit_fee = amount * 0.02
        amount_after_fee = amount - deposit_fee
        text = (f"✅ Deposit initiated!\n\n**Amount:** `{amount:.2f} ETB`\n**You will receive:** `{amount_after_fee:.2f} ETB`\n\nClick below to complete your payment.")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Pay with Chapa", url=checkout_url)]])
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    except httpx.HTTPStatusError as e:
        logger.error(f"Chapa API Error: {e.response.text}")
        await update.message.reply_text("Sorry, we couldn't connect to the payment gateway.")
    except Exception as e:
        logger.error(f"An error occurred during Chapa request: {e}")
        await update.message.reply_text("An unexpected error occurred.")

    return ConversationHandler.END

async def cancel_conversation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Action canceled.", reply_markup=build_main_menu())
    else:
        await update.message.reply_text("Action canceled.", reply_markup=build_main_menu())
    return ConversationHandler.END

def setup_handlers(application: Application):
    """Registers all the bot handlers with the Application instance."""
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_handler, pattern='^deposit$')],
        states={DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_handler)]},
        fallbacks=[CommandHandler('cancel', cancel_conversation_handler), CallbackQueryHandler(cancel_conversation_handler, pattern='^cancel_conv$')]
    )
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(main_menu_handler))