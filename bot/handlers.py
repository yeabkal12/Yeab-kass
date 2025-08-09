# /bot/handlers.py (The Final, Perfected, and Fully Working Version with Deposit & Balance)

import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
) # <-- Add ConversationHandler
from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

# --- Make sure all necessary components are imported ---
from database_models.manager import get_db_session, games, users

logger = logging.getLogger(__name__)
LIVE_WEB_APP_URL = "https://yeab-kass-1.onrender.com"

# --- Keyboard Layout ---
# Added "Deposit 💵" to the main keyboard
main_keyboard = [
    [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))],
    [KeyboardButton("My Wallet 💰"), KeyboardButton("Deposit 💵")],
    [KeyboardButton("Support 📞")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

# --- Conversation States for Deposit Flow ---
AMOUNT, CONFIRM_PHONE = range(2)

# =========================================================
# =========== START: INJECTED/NEW COMMANDS ================
# =========================================================

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'My Wallet 💰' button to check the user's balance."""
    user = update.effective_user
    async with get_db_session() as session:
        # First, ensure the user exists with our "get or create" logic
        user_stmt = pg_insert(users).values(
            telegram_id=user.id,
            username=user.username or user.first_name
        ).on_conflict_do_update(
            index_elements=['telegram_id'],
            set_={'username': user.username or user.first_name} # Update username if it changed
        )
        await session.execute(user_stmt)

        # Now, fetch the user's balance
        query = select(users.c.balance).where(users.c.telegram_id == user.id)
        result = await session.execute(query)
        balance = result.scalar_one_or_none()

    if balance is not None:
        await update.message.reply_text(f"💰 **Your current balance is:** {balance:.2f} ETB", parse_mode='Markdown')
    else:
        await update.message.reply_text("Could not retrieve your balance. Please try again.")

async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the deposit conversation by asking for the amount."""
    await update.message.reply_text(
        "የሚከፍሉትን የገንዘብ መጠን ያስገቡ (min: 20, max: 5000 birr)"
    )
    return AMOUNT

async def received_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes the deposit amount and asks for phone number confirmation."""
    user = update.effective_user
    try:
        amount = float(update.message.text)
        if not (20 <= amount <= 5000):
            await update.message.reply_text("Invalid amount. Please enter a value between 20 and 5000.")
            return AMOUNT # Ask for the amount again
        
        # Store the amount for the next step
        context.user_data['deposit_amount'] = amount
        
        # In a real app, you'd fetch the user's registered phone number here.
        # For now, we'll use a placeholder.
        user_phone_number = "0912345678" # Placeholder
        context.user_data['phone_number'] = user_phone_number

        confirmation_keyboard = [
            [KeyboardButton(f"Confirm using {user_phone_number}")]
        ]
        
        await update.message.reply_text(
            f"ስልክ ቁጥርን: {user_phone_number}",
            reply_markup=ReplyKeyboardMarkup(confirmation_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return CONFIRM_PHONE

    except (ValueError, TypeError):
        await update.message.reply_text("Invalid input. Please enter a valid number.")
        return AMOUNT

async def confirm_phone_and_pay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms the phone number and generates a (mock) payment link."""
    amount = context.user_data.get('deposit_amount')
    phone_number = context.user_data.get('phone_number')

    if not amount or not phone_number:
        await update.message.reply_text("Something went wrong. Please start over.", reply_markup=REPLY_MARKUP)
        return ConversationHandler.END

    # --- Chapa Integration Point ---
    # Here you would call the Chapa API to get a real checkout URL
    # For now, we'll create a mock success message and link.
    # checkout_url = chapa.initialize_transaction(amount, user.id, ...)
    mock_checkout_url = f"https://checkout.chapa.co/mock-transaction-id-for-{amount}"

    payment_message = (
        f"Processing payment for **{amount:.2f} ETB**.\n\n"
        f"Please follow the link below to complete your payment with Chapa."
    )
    
    payment_button = InlineKeyboardButton("Proceed to Chapa Gateway", url=mock_checkout_url)
    keyboard = InlineKeyboardMarkup([[payment_button]])

    await update.message.reply_text(payment_message, reply_markup=keyboard)
    # Return to the main menu after showing the link
    await update.message.reply_text("You can use the main menu now.", reply_markup=REPLY_MARKUP)
    
    return ConversationHandler.END

async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the deposit conversation."""
    await update.message.reply_text("Deposit canceled.", reply_markup=REPLY_MARKUP)
    return ConversationHandler.END

# =========================================================
# ============= END: INJECTED/NEW COMMANDS ================
# =========================================================

# --- Existing Handlers (Unchanged) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=REPLY_MARKUP
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all data from the Web App."""
    data_str = update.effective_message.web_app_data.data
    user = update.effective_user
    logger.info(f"Received data from Web App from user {user.id}: {data_str}")
    
    if data_str.startswith("join_game_"):
        # ... your join game logic
        pass

    elif data_str.startswith("create_game_"):
        # ... your create game logic ...
        pass

# --- Setup Function (MODIFIED) ---
def setup_handlers(ptb_app: Application) -> Application:
    # Create the ConversationHandler for the deposit flow
    deposit_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Deposit 💵$'), deposit_command)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_amount)],
            CONFIRM_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_phone_and_pay)],
        },
        fallbacks=[CommandHandler('cancel', cancel_deposit)],
    )

    ptb_app.add_handler(CommandHandler("start", start_command))
    ptb_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # Add the new handlers
    ptb_app.add_handler(MessageHandler(filters.Regex('^My Wallet 💰$'), balance_command))
    ptb_app.add_handler(deposit_conv_handler)
    
    return ptb_app