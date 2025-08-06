# /bot/handlers.py (The Final, Perfected, and Fully Working Version)

import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert # <-- CRITICAL IMPORT for "Get or Create"

# --- Make sure all necessary components are imported ---
from database_models.manager import get_db_session, games, users

logger = logging.getLogger(__name__)
LIVE_WEB_APP_URL = "https://yeab-kass-1.onrender.com"

# --- Keyboard Layout (Unchanged) ---
main_keyboard = [
    [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))],
    [KeyboardButton("My Wallet 💰"), KeyboardButton("Support 📞")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

# --- Command Handlers (Unchanged) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=REPLY_MARKUP
    )

# --- Web App Data Handler (THE FINAL, PERFECTED VERSION) ---
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all data from the Web App, including the CRITICAL "get or create" user logic.
    """
    data_str = update.effective_message.web_app_data.data
    user = update.effective_user
    logger.info(f"Received data from Web App from user {user.id}: {data_str}")
    
    # --- Logic for Joining a Game (Unchanged) ---
    if data_str.startswith("join_game_"):
        game_id = data_str.split('_')[-1]
        await update.message.reply_text(f"Joining game #{game_id}...")
        # TODO: Full game joining logic.

    # --- FINAL, WORKING LOGIC for Creating a Game ---
    elif data_str.startswith("create_game_"):
        try:
            parts = data_str.split('_')
            stake = int(parts[3])
            win_condition = int(parts[5])
            
            async with get_db_session() as session:
                # --- THIS IS THE FINAL, CRITICAL FIX ---
                # "Get or Create" User: We attempt to create a new user.
                # If the user already exists (based on telegram_id), the DB will do nothing.
                # This guarantees the user exists before we create a game for them.
                user_stmt = pg_insert(users).values(
                    telegram_id=user.id,
                    username=user.username or user.first_name
                ).on_conflict_do_nothing(index_elements=['telegram_id'])
                await session.execute(user_stmt)
                # ----------------------------------------
                
                # Now that we know the user exists, we can create the game.
                game_stmt = insert(games).values(
                    creator_id=user.id,
                    stake=stake,
                    pot=stake * 2,
                    win_condition=win_condition,
                    status='lobby'
                ).returning(games.c.id)
                
                result = await session.execute(game_stmt)
                game_id = result.scalar_one()

            if not game_id:
                await context.bot.send_message(user.id, "Sorry, there was a database error. Please try again.")
                return

            # --- Send the final "Game Lobby Created!" success message ---
            lobby_message = (
                f"📣 **Game Lobby Created!**\n\n"
                f"Your game is now visible to all players in the lobby.\n\n"
                f"💰 **Stake:** {stake} ETB\n"
                f"🏆 **Win Condition:** {win_condition} token(s) home"
            )
            await context.bot.send_message(
                chat_id=user.id, text=lobby_message, parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Failed to create game for user {user.id}: {e}", exc_info=True)
            await context.bot.send_message(user.id, "An error occurred while creating your game. Please try again.")

# --- Setup Function (Unchanged) ---
def setup_handlers(ptb_app: Application) -> Application:
    ptb_app.add_handler(CommandHandler("start", start_command))
    ptb_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    return ptb_app