import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy import insert

# Assuming your database models are structured this way
from database_models.manager import get_db_session, games

logger = logging.getLogger(__name__)

# --- 1. Live URL for the Web App ---
# This should be the public address of your deployed frontend application.
LIVE_WEB_APP_URL = "https://yeab-kass-1.onrender.com"


# --- 2. Keyboard Layout ---
# The "Play" button launches the Web App.
main_keyboard = [
    [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))],
    [KeyboardButton("My Wallet 💰"), KeyboardButton("Support 📞")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)


# --- 3. Command and Message Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main menu keyboard with the Web App button."""
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=REPLY_MARKUP
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all data sent back from the Web App.
    This version saves created games to the database and confirms with the user.
    """
    data_str = update.effective_message.web_app_data.data
    user = update.effective_user
    logger.info(f"Received data from Web App from user {user.id}: {data_str}")
    
    # --- Logic for Joining a Game ---
    if data_str.startswith("join_game_"):
        game_id = data_str.split('_')[-1]
        await update.message.reply_text(
            f"Joining game #{game_id}...",
            reply_markup=REPLY_MARKUP
        )
        # TODO: Add your full game joining logic (check balance, deduct stake, start game).

    # --- Logic for Creating a Game ---
    elif data_str.startswith("create_game_"):
        try:
            parts = data_str.split('_')
            stake = int(parts[3])
            win_condition = int(parts[5])
            
            # --- Connect to the database and save the game ---
            game_id = None
            async with get_db_session() as session:
                # TODO: First, check if the user has enough balance in the DB before proceeding.
                
                # Insert the new game into the 'games' table
                stmt = insert(games).values(
                    creator_id=user.id,
                    stake=stake,
                    pot=stake * 2,  # Assuming a 2-player game
                    win_condition=win_condition,
                    status='lobby'
                ).returning(games.c.id)
                
                result = await session.execute(stmt)
                game_id = result.scalar_one()  # Get the new game's ID

            if not game_id:
                await context.bot.send_message(user.id, "Sorry, there was a database error. Please try again.")
                return

            # --- Send the final "Game Lobby Created!" message ---
            lobby_message = (
                f"📣 **Game Lobby Created!**\n\n"
                f"Your game is now visible to all players in the lobby.\n\n"
                f"💰 **Stake:** {stake} ETB\n"
                f"🏆 **Win Condition:** {win_condition} token(s) home"
            )
            
            # Send the lobby message as a new message to the user
            await context.bot.send_message(
                chat_id=user.id,
                text=lobby_message,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Failed to create game from web app data: {e}", exc_info=True)
            await context.bot.send_message(user.id, "An error occurred while creating your game. Please check the details and try again.")


# --- 4. Setup Function ---
def setup_handlers(ptb_app: Application) -> Application:
    """Attaches all handlers to the application."""
    # Add the handler for the /start command
    ptb_app.add_handler(CommandHandler("start", start_command))
    
    # Add the special handler that listens for data coming from our Web App
    ptb_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # TODO: Add handlers for "My Wallet 💰" and "Support 📞" here later.
    
    return ptb_app