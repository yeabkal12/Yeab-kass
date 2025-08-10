# bot_handler.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Configuration ---
# Replace with your actual Bot Token and the URL where the web app is hosted
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
WEB_APP_URL = 'https://your-webapp-url.com' # e.g., https://yeab-kass.onrender.com

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command. Sends a message with a button to open the Web App.
    """
    # Create the WebAppInfo object pointing to your web application
    web_app_info = WebAppInfo(url=WEB_APP_URL)

    # Create the inline button with the WebAppInfo
    keyboard = [
        [InlineKeyboardButton("🎮 Open Ludo App 🎮", web_app=web_app_info)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message
    await update.message.reply_text(
        "Welcome to Next Ludo Games! Click the button below to start or join a game.",
        reply_markup=reply_markup,
    )

def main() -> None:
    """Starts the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register the /start command handler
    application.add_handler(CommandHandler("start", start))

    # Run the bot until the user presses Ctrl-C
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()