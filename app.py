# app.py (Final, Complete, and Perfected Version)

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware # <-- The security permission slip
from telegram import Update
from telegram.ext import Application
from telegram.error import RetryAfter

from bot.handlers import setup_handlers
from database_models.manager import get_db_session, games, users
from sqlalchemy import select

# --- 1. SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- 2. LIFESPAN LOGIC (FOR STARTUP & SHUTDOWN) ---
bot_app: Application | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_app
    logger.info("Application startup...")
    
    if TELEGRAM_BOT_TOKEN:
        ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        bot_app = setup_handlers(ptb_application)
        logger.info("Telegram bot application created and handlers have been attached.")
        
        await bot_app.initialize()
        
        if WEBHOOK_URL:
            webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
            try:
                await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
                logger.info(f"Successfully set webhook to: {webhook_full_url}")
            except RetryAfter:
                logger.warning("Webhook already set or flood control. Continuing.")
            except Exception as e:
                logger.error(f"Failed to set webhook: {e}")
        else:
            logger.error("FATAL: WEBHOOK_URL is not set!")
    else:
        logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set! Bot will be disabled.")

    yield
    
    logger.info("Application shutdown...")
    if bot_app:
        await bot_app.shutdown()

# --- 3. FASTAPI APP INITIALIZATION ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)

# --- CRITICAL FIX: Add CORS Middleware ---
# This tells your backend that it is safe to accept requests from your frontend website.
# Without this, the browser will block the connection, causing the "Failed to load" error.
origins = [
    "https://yeab-kass-1.onrender.com", # Your Frontend URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"], # We only need GET for the games list
    allow_headers=["*"],
)


# --- 4. API ENDPOINTS ---

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Main webhook to receive updates from Telegram."""
    if not bot_app:
        return Response(status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=200)
    except Exception:
        logger.error("Error processing Telegram update", exc_info=True)
        return Response(status_code=500)

@app.get("/api/games")
async def get_open_games():
    """Endpoint for the web app to fetch open game lobbies."""
    live_games = []
    try:
        async with get_db_session() as session:
            stmt = select(games.c.id, games.c.stake, games.c.pot, users.c.username).\
                   join(users, games.c.creator_id == users.c.telegram_id).\
                   where(games.c.status == 'lobby').order_by(games.c.created_at.desc())
            result = await session.execute(stmt)
            for row in result.fetchall():
                live_games.append({
                    "id": row.id,
                    "creator_name": row.username or "Player",
                    "creator_avatar": f"https://i.pravatar.cc/40?u={row.id}",
                    "stake": float(row.stake),
                    "prize": float(row.pot * 0.9),
                })
    except Exception:
        logger.error("Database error fetching open games", exc_info=True)
        return {"games": []}
    return {"games": live_games}

@app.get("/health")
async def health_check():
    """A simple health check endpoint for Render."""
    return {"status": "healthy"}

# NOTE: The app.mount("/", ...) line has been permanently removed as it is no longer needed.