# /bot/handlers.py (The Final Version with Real-Time Broadcasting Injected)

import logging
import json # <--- INJECTED: Necessary for creating JSON messages
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    ConversationHandler
)
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

# --- Make sure all necessary components are imported ---
from database_models.manager import get_db_session, games, users
# <--- INJECTED: Import the necessary functions from your main server file
# NOTE: You may need to adjust the path depending on your project structure.
# This assumes app.py is in the parent directory of the 'bot' folder.
from app import get_game_details_as_dict

logger = logging.getLogger(__name__)
LIVE_WEB_APP_URL = "https://yeab-kass-1.onrender.com"

# --- Conversation States ---
AMOUNT, CONFIRM_PHONE = range(2)
WITHDRAW_AMOUNT, WITHDRAW_PHONE = range(2, 4)


# --- Helper Function to Create Keyboard ---
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Creates and returns the main keyboard markup."""
    main_keyboard = [
        [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))],
        [KeyboardButton("My Wallet 💰"), KeyboardButton("Deposit 💵")],
        [KeyboardButton("Withdraw 📤"), KeyboardButton("Support 📞")]
    ]
    return ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)


# --- Core Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=get_main_keyboard()
    )

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function is already correct
    # ... (your existing register logic) ...
    pass


# --- Wallet Command Handlers ---
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function is already correct
    # ... (your existing balance logic) ...
    pass

# ... (All your deposit and withdrawal conversation handlers are correct) ...
async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def received_amount(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def confirm_phone_and_pay(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Deposit canceled.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def received_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def received_withdraw_phone(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def cancel_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Withdrawal canceled.", reply_markup=get_main_keyboard())
    return ConversationHandler.END


# =========================================================
# =========== START: INJECTED SECTION =====================
# =========================================================

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    [MODIFIED] Handles data from the Web App and now BROADCASTS updates
    to the real-time lobby.
    """
    data_str = update.effective_message.web_app_data.data
    user = update.effective_user
    logger.info(f"Received Web App data from user {user.id}: {data_str}")

    # 1. Access the Connection Manager from the bot's context (the "bridge")
    manager = context.bot_data.get("connection_manager")
    if not manager:
        logger.error("Connection manager not found in bot_data!")
        return
    
    if data_str.startswith("create_game_"):
        try:
            parts = data_str.split('_')
            stake = int(parts[3])
            win_condition = int(parts[5])
            game_id = None
            
            async with get_db_session() as session:
                # Ensure the user is in the database
                user_stmt = pg_insert(users).values(
                    telegram_id=user.id, username=user.username or user.first_name
                ).on_conflict_do_nothing(index_elements=['telegram_id'])
                await session.execute(user_stmt)
                
                # Insert the new game and get its ID
                game_stmt = insert(games).values(
                    creator_id=user.id, stake=stake, pot=stake * 2,
                    win_condition=win_condition, status='lobby'
                ).returning(games.c.id)
                
                result = await session.execute(game_stmt)
                game_id = result.scalar_one()
                await session.commit()

            # If game creation was successful, fetch its details and broadcast
            if game_id:
                # 2. Fetch the full details of the newly created game
                new_game_details = await get_game_details_as_dict(game_id)
                
                # 3. CRUCIAL FIX: Broadcast the new game event to all lobby users
                if new_game_details:
                    await manager.broadcast(json.dumps({"event": "new_game", "game": new_game_details}))
                    logger.info(f"Broadcasted new game creation: ID {game_id}")

            # Send a confirmation message back to the creator
            await context.bot.send_message(user.id, "Your game is now live in the lobby!")

        except Exception as e:
            logger.error(f"Failed to create game for user {user.id}: {e}", exc_info=True)
            await context.bot.send_message(user.id, "An error occurred while creating your game.")

# =========================================================
# ============= END: INJECTED SECTION =====================
# =========================================================


# --- Setup Function ---
def setup_handlers(ptb_app: Application) -> Application:
    """Creates and registers all handlers for the bot."""
    
    # This function is already correct and doesn't need changes.
    # ... (your existing ConversationHandler and registration logic) ...
    deposit_conv_handler = ConversationHandler(...)
    withdraw_conv_handler = ConversationHandler(...)

    ptb_app.add_handler(CommandHandler("start", start_command))
    ptb_app.add_handler(CommandHandler("register", register_command))
    
    ptb_app.add_handler(MessageHandler(filters.Regex('^My Wallet 💰$'), balance_command))
    ptb_app.add_handler(deposit_conv_handler)
    ptb_app.add_handler(withdraw_conv_handler)
    
    ptb_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    return ptb_app