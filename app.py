# app.py (Complete Backend Code - No Changes Needed)

import logging
import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from telegram.ext import Application
from telegram.error import RetryAfter

# --- Mock or Import Your Actual Project Components ---
try:
    from bot.handlers import setup_handlers
    from database_models.manager import get_db_session, games, users
    from sqlalchemy import select
    DATABASE_ENABLED = True
except ImportError:
    DATABASE_ENABLED = False
    logging.warning("Database or bot handler modules not found. Running in a limited mock mode.")
# ---

# --- 1. Setup & Configuration ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


# --- 2. Global Application Instances ---
bot_app: Application | None = None


# --- 3. Lifespan Management for Startup/Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles critical startup and shutdown events for the FastAPI application."""
    logger.info("Application startup...")
    global bot_app
    if bot_app:
        await bot_app.initialize()
        if WEBHOOK_URL:
            webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
            try:
                await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
                logger.info(f"Successfully set webhook to: {webhook_full_url}")
            except RetryAfter:
                logger.warning("Could not set webhook due to flood control. Another worker likely succeeded.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while setting webhook: {e}")
        else:
            logger.error("FATAL: WEBHOOK_URL environment variable is not set!")

    yield

    logger.info("Application shutdown...")
    if bot_app:
        await bot_app.shutdown()


# --- 4. Main FastAPI Application Initialization ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)

# --- [FIX] INJECT CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initialize Telegram Bot ---
if TELEGRAM_BOT_TOKEN and DATABASE_ENABLED:
    ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app = setup_handlers(ptb_application)
    logger.info("Telegram bot application created and handlers have been attached.")
else:
    logger.warning("Telegram Bot is disabled (TELEGRAM_BOT_TOKEN not set or modules missing).")


# --- 5. API Endpoints ---
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    if not bot_app:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.get("/api/games")
async def get_open_games():
    if not DATABASE_ENABLED:
        logger.info("Serving mock data because database is not enabled.")
        return {"games": [
            {"id": 1, "creator_name": "Player 1 (Mock)", "creator_avatar": "https://i.pravatar.cc/40?u=1", "stake": 50, "prize": 90.0},
            {"id": 2, "creator_name": "Player 2 (Mock)", "creator_avatar": "https://i.pravatar.cc/40?u=2", "stake": 100, "prize": 180.0},
        ]}

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
    except Exception as e:
        logger.error(f"Failed to fetch open games from database: {e}")
        return {"games": []}

    return {"games": live_games}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# --- 6. Mount Static Files ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")