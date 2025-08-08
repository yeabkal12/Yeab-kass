# app.py (The Final, Complete, and Corrected Version)

import logging
import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import Application

# --- Mock or Import Your Bot's Command Handlers ---
# This assumes you have your 'start' function defined elsewhere.
try:
    from bot.handlers import setup_handlers
    BOT_ENABLED = True
except ImportError:
    BOT_ENABLED = False
    logging.warning("Bot handlers not found. Bot will be in a limited mode.")
# ---

# --- 1. Setup & Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# These environment variables MUST be set on your Render server.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# The value for WEBHOOK_URL on Render should be: https://yeab-kass.onrender.com
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


# --- 2. Global Application Instances ---
bot_app: Application | None = None


# --- 3. # In your main app.py file

# --- Add these imports at the top of your app.py file ---
import random
import asyncio

# ... (all your other imports) ...

# =====================================================================
# === THIS IS THE CORRECTED LIFESPAN FUNCTION =========================
# =====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup. It now includes a random delay to prevent a
    race condition between gunicorn workers when setting the webhook.
    """
    logger.info("Application startup... workers are starting...")
    if bot_app and WEBHOOK_URL:
        # Introduce a small, random delay for each worker
        # This prevents all workers from hitting the Telegram API at once.
        delay = random.uniform(0.5, 3.0)
        logger.info(f"Worker waiting for {delay:.2f} seconds before setting webhook.")
        await asyncio.sleep(delay)

        webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
        
        await bot_app.initialize()
        try:
            # The first worker to run this will succeed.
            await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
            logger.info(f"SUCCESS: Webhook set successfully to -> {webhook_full_url}")

        except Exception as e:
            # The other workers might fail with a flood control error, which is now OKAY.
            # We log it as a warning instead of a fatal error.
            if "Flood control exceeded" in str(e):
                logger.warning(f"Could not set webhook (another worker likely succeeded): {e}")
            else:
                logger.error(f"CRITICAL ERROR: Could not set webhook for a different reason: {e}")

    elif not WEBHOOK_URL:
         logger.error("FATAL: WEBHOOK_URL environment variable is not set!")
            
    yield
    
    logger.info("Application shutdown...")
    if bot_app:
        await bot_app.shutdown()
        webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
        
        await bot_app.initialize()
        try:
            # Tell Telegram where to send updates.
            await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
            logger.info(f"SUCCESS: Webhook set to -> {webhook_full_url}")
        except Exception as e:
            logger.error(f"FATAL: Could not set webhook to {webhook_full_url}: {e}")
    elif not WEBHOOK_URL:
         logger.error("FATAL: WEBHOOK_URL environment variable is not set!")
            
    yield  # The application is now running
    
    logger.info("Application shutdown...")
    if bot_app:
        await bot_app.shutdown()


# --- 4. Main FastAPI Application Initialization ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)

if TELEGRAM_BOT_TOKEN and BOT_ENABLED:
    ptb_builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    bot_app = setup_handlers(ptb_builder.build()) # setup_handlers should add your 'start' command
    logger.info("Telegram bot application created and handlers attached.")
else:
    logger.error("FATAL: Bot is disabled. Check TELEGRAM_BOT_TOKEN and handler imports.")


# --- 5. API Endpoints ---

# THIS IS THE FIX FOR YOUR "404 NOT FOUND" ERROR
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """This function now correctly listens for messages from Telegram."""
    if not bot_app:
        logger.error("Webhook called, but bot is not initialized.")
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/health")
async def health_check():
    """A simple health check endpoint for Render to use."""
    return {"status": "healthy", "bot_initialized": bool(bot_app)}