# /bot/handlers.py (The Definitive, Corrected Version)

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
# ... all other imports ...

logger = logging.getLogger(__name__)
LIVE_WEB_APP_URL = "https://yeab-kass-1.onrender.com"

# --- Conversation States (These are simple integers and are safe at the top level) ---
AMOUNT, CONFIRM_PHONE = range(2)
WITHDRAW_AMOUNT, WITHDRAW_PHONE = range(2, 4)


# =========================================================
# =========== 1. CORE COMMAND HANDLERS ====================
# =========================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    
    # =========================================================
    # =========== THIS IS THE CRITICAL FIX ====================
    # =========================================================
    # We create the keyboard HERE, inside the command handler,
    # when the application is guaranteed to be running.
    main_keyboard = [
        [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))],
        [KeyboardButton("My Wallet 💰"), KeyboardButton("Deposit 💵")],
        [KeyboardButton("Withdraw 📤"), KeyboardButton("Support 📞")]
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=reply_markup # Use the locally created keyboard
    )

# --- All other command handlers (register, balance, deposit, etc.) remain the same ---
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function needs the keyboard too.
    main_keyboard = [
        [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))],
        # ... other buttons
    ]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    # ... rest of the function ...
    await update.message.reply_text(response_text, reply_markup=reply_markup)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ...
    pass

# ... (rest of your deposit and withdrawal functions)
# Make sure to create the reply_markup inside any function that cancels a conversation
# For example:
async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    main_keyboard = [[KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=LIVE_WEB_APP_URL))], [KeyboardButton("My Wallet 💰"), KeyboardButton("Deposit 💵")], [KeyboardButton("Withdraw 📤"), KeyboardButton("Support 📞")]]
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("Deposit canceled.", reply_markup=reply_markup)
    return ConversationHandler.END


# ... (your web_app_data handler remains the same) ...

# =========================================================
# =========== 4. SETUP FUNCTION ===========================
# =========================================================

def setup_handlers(ptb_app: Application) -> Application:
    # This function remains exactly the same.
    # ...
    return ptb_app```

### Your Action Plan

1.  **Open `bot/handlers.py`**.
2.  **Delete** the `main_keyboard` and `REPLY_MARKUP` definitions from the top of the file.
3.  **Copy and paste** the `main_keyboard` and `reply_markup` creation logic into the **beginning of every function** that sends a reply with that keyboard (`start_command`, `register_command`, `cancel_deposit`, `cancel_withdraw`, etc.).
4.  **Redeploy** your backend Web Service.

After this change, your server will no longer crash on startup. The `WebAppInfo` object will only be created when it's needed, inside a running application, and your bot will come back online and respond to commands.