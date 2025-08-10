# app.py - The Final and Unified Version

import asyncio
import os
import logging
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# --- Correctly Import Your Project Modules ---
from bot.handlers import (
    start_command, main_menu_handler, deposit_amount_handler, cancel_conversation_handler,
    DEPOSIT_AMOUNT
)
from api.main import app as fastapi_app  # Import the FastAPI app object from api/main.py
from database_models.manager import Base, engine # Import Base and engine

# --- Environment Variables & Constants ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8000"))

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("FATAL ERROR: TELEGRAM_BOT_TOKEN environment variable is not set.")
if not WEBHOOK_URL:
    raise ValueError("FATAL ERROR: WEBHOOK_URL environment variable is not set.")

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Database Setup Function ---
async def initialize_database():
    """Creates all database tables defined in the models if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables checked/initialized successfully.")

# --- FastAPI Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    This is where we set up the database and the Telegram bot.
    """
    logger.info("Application starting up...")

    await initialize_database()

    # --- Telegram Bot Setup ---
    bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Register Handlers ---
    deposit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_handler, pattern='^deposit$')],
        states={
            DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_handler)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel_conversation_handler),
            CallbackQueryHandler(cancel_conversation_handler, pattern='^cancel_conv$')
        ],
        per_message=False
    )

    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(deposit_conv_handler)
    bot_app.add_handler(CallbackQueryHandler(main_menu_handler))

    # --- Webhook Setup ---
    await bot_app.bot.delete_webhook(drop_pending_updates=True)
    full_webhook_url = f"{WEBHOOK_URL}/api/telegram/webhook"
    await bot_app.bot.set_webhook(url=full_webhook_url)

    app.state.bot_app = bot_app
    logger.info(f"Telegram webhook has been set to {full_webhook_url}")

    yield  # Application runs here

    # --- Shutdown Logic ---
    logger.info("Application shutting down...")
    await app.state.bot_app.bot.delete_webhook()

# --- Main Application Instance ---
app = fastapi_app
app.router.lifespan_context = lifespan

# --- Webhook Endpoint ---
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Receives all updates from Telegram and processes them."""
    bot_app = request.app.state.bot_app
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, bot_app.bot)
        await bot_app.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")
    return {"status": "ok"}

# --- Local Development Runner ---
if __name__ == "__main__":
    logger.info("Starting server for local development...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)