# app.py (The Final, Definitive, and Unified Version)

import logging
import os
import asyncio
import json
import uuid
import random
from typing import Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter
from sqlalchemy import select, insert, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

# --- Import all necessary components ---
from database_models.manager import get_db_session, games, users

# --- 1. SETUP & CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
STATIC_SITE_URL = os.getenv("STATIC_SITE_URL", "https://yeab-kass-1.onrender.com") # Default value for safety

# --- 2. GLOBAL INSTANCES & REAL-TIME MANAGER ---
bot_app: Application | None = None

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self): self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket): await websocket.accept(); self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections: self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections: await connection.send_text(message)

manager = ConnectionManager()

# =========================================================
# === LOGIC MOVED FROM bot/handlers.py TO FIX IMPORTS =====
# =========================================================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Creates and returns the main keyboard markup safely."""
    main_keyboard = [
        [KeyboardButton("Play Ludo Games 🎮", web_app=WebAppInfo(url=STATIC_SITE_URL))],
        [KeyboardButton("My Wallet 💰"), KeyboardButton("Deposit 💵")],
        [KeyboardButton("Withdraw 📤"), KeyboardButton("Support 📞")]
    ]
    return ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    await update.message.reply_text(
        "Welcome to Yeab Game Zone! Tap 'Play Ludo Games' to see the lobby.", 
        reply_markup=get_main_keyboard()
    )

async def get_game_details_as_dict(game_id: int) -> Dict:
    """Helper to fetch full game details for broadcasting."""
    async with get_db_session() as session:
        stmt = select(games.c.id, games.c.stake, games.c.pot, games.c.win_condition, games.c.creator_id, users.c.username).join(users, games.c.creator_id == users.c.telegram_id).where(games.c.id == game_id)
        row = (await session.execute(stmt)).first()
        if not row: return None
        return {"id": row.id, "creator": row.username or "Player", "avatarId": row.creator_id % 10, "stake": float(row.stake), "prize": float(row.pot * 0.9), "winCondition": row.win_condition}

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles data from the Web App and broadcasts updates."""
    data_str = update.effective_message.web_app_data.data
    user = update.effective_user
    logger.info(f"Received Web App data from user {user.id}: {data_str}")

    if data_str.startswith("create_game_"):
        try:
            parts = data_str.split('_')
            stake = int(parts[3])
            win_condition = int(parts[5])
            
            async with get_db_session() as session:
                user_stmt = pg_insert(users).values(telegram_id=user.id, username=user.username or user.first_name).on_conflict_do_nothing(index_elements=['telegram_id'])
                await session.execute(user_stmt)
                
                game_stmt = insert(games).values(creator_id=user.id, stake=stake, pot=stake * 2, win_condition=win_condition, status='lobby').returning(games.c.id)
                game_id = (await session.execute(game_stmt)).scalar_one()
                await session.commit()

            if game_id:
                new_game_details = await get_game_details_as_dict(game_id)
                if new_game_details:
                    await manager.broadcast(json.dumps({"event": "new_game", "game": new_game_details}))
                    logger.info(f"Broadcasted new game creation: ID {game_id}")
            await context.bot.send_message(user.id, "Your game is now live in the lobby!")
        except Exception as e:
            logger.error(f"Failed to create game for user {user.id}: {e}", exc_info=True)
            await context.bot.send_message(user.id, "An error occurred while creating your game.")

# =========================================================
# =========================================================

# --- 3. LIFESPAN MANAGER (HANDLES BOT STARTUP) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    if bot_app and WEBHOOK_URL:
        await bot_app.initialize()
        webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
        try:
            await asyncio.sleep(random.uniform(0.5, 2.0))
            await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
            logger.info(f"Successfully set webhook to: {webhook_full_url}")
        except RetryAfter:
            logger.warning("Could not set webhook (another worker likely succeeded).")
        except Exception as e:
            logger.error(f"An unexpected error occurred while setting webhook: {e}")
    yield
    logger.info("Application shutdown...")
    if bot_app: await bot_app.shutdown()

# --- 4. MAIN FASTAPI APP INITIALIZATION ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if not TELEGRAM_BOT_TOKEN:
    logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set! Bot will be disabled.")
else:
    ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    # --- Attach handlers directly here ---
    ptb_application.add_handler(CommandHandler("start", start_command))
    ptb_application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    # You can add your other handlers (balance, deposit, etc.) here as well
    bot_app = ptb_application
    logger.info("Telegram bot application created and handlers have been attached directly.")

# --- 5. API ENDPOINTS ---

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    if not bot_app: return Response(status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)
        return Response(status_code=500)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket)
    try:
        async with get_db_session() as session:
            stmt = select(games.c.id, games.c.stake, games.c.pot, games.c.win_condition, games.c.creator_id, users.c.username).join(users, games.c.creator_id == users.c.telegram_id).where(games.c.status == 'lobby')
            result = await session.execute(stmt)
            initial_games = [{"id": r.id, "creator": r.username or "Player", "avatarId": r.creator_id % 10, "stake": float(r.stake), "prize": float(r.pot * 0.9), "winCondition": r.win_condition} for r in result]
        await websocket.send_text(json.dumps({"event": "initial_game_list", "games": initial_games}))

        while True:
            data = await websocket.receive_json()
            if data.get("action") == "join_game":
                game_id_to_join = data.get("gameId")
                async with get_db_session() as session:
                    await session.execute(delete(games).where(games.c.id == game_id_to_join))
                    await session.commit()
                await manager.broadcast(json.dumps({"event": "remove_game", "gameId": game_id_to_join}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Error for user {user_id}: {e}", exc_info=True)
        manager.disconnect(websocket)

@app.get("/health")
async def health_check(): return {"status": "healthy"}

# --- 6. MOUNT STATIC FILES FOR WEB APP ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")