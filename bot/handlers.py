# /bot/handlers.py (Final, Perfected Version with Your Live URL)

import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

# --- 1. CRITICAL FIX: Use the live URL of your new Static Site ---
# This is the address of the frontend website you just successfully deployed.
LIVE_WEB_APP_URL = "https://yeab-kass-1.onrender.com"


# --- 2. Create the Keyboard Layout ---
# The "Play" button is now a special Web App button that points to your live site.
main_keyboard = [
    [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))],
    [KeyboardButton("My Wallet 💰"), KeyboardButton("Support 📞")]
]
REPLY_MARKUP = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)


# --- 3. Define Callback Functions ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main menu keyboard with the Web App button."""
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=REPLY_MARKUP
    )

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles data sent back from the Web App (e.g., when a user clicks 'Join' or 'Create').
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
        # TODO: Add your full game joining logic here (check balance, deduct stake, start game).

    # --- Logic for Creating a Game ---
    elif data_str.startswith("create_game_"):
        parts = data_str.split('_')
        stake = int(parts[3])
        win = int(parts[5])
        
        await update.message.reply_text(
            f"Creating your game with a {stake} ETB stake, needing {win} token(s) to win...",
            reply_markup=REPLY_MARKUP
        )
        # TODO: Add your database logic here to create the new game lobby.
        # After saving to the DB, you can send a confirmation.


# --- 4. Define the Setup Function ---
def setup_handlers(ptb_app: Application) -> Application:
    """Attaches all handlers to the application."""
    # Add the handler for the /start command
    ptb_app.add_handler(CommandHandler("start", start_command))
    
    # Add the special handler that listens for data coming from our Web App
    ptb_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # TODO: You can add handlers for the other text buttons ("My Wallet", etc.) here later.
    
    return ptb_app