# app.py (The Final, Unified Version with Database, Bot, and Real-Time)

import logging
import os
import asyncio
import json
import uuid
from typing import Dict, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from telegram.ext import Application
from telegram.error import RetryAfter
from sqlalchemy import select, insert, delete

# --- Import all necessary components ---
from bot.handlers import setup_handlers
from database_models.manager import get_db_session, games, users

# --- 1. SETUP & CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- 2. GLOBAL INSTANCES & REAL-TIME MANAGER ---
bot_app: Application | None = None

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: Dict[WebSocket, int] = {}
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[websocket] = user_id
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- 3. LIFESPAN MANAGER (HANDLES BOT STARTUP) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles critical startup and shutdown events for the application."""
    logger.info("Application startup...")
    if bot_app and WEBHOOK_URL:
        await bot_app.initialize()
        webhook_full_url = f"{WEBHOOK_URL}/api/telegram/webhook"
        try:
            await bot_app.bot.set_webhook(url=webhook_full_url, allowed_updates=Update.ALL_TYPES)
            logger.info(f"Successfully set webhook to: {webhook_full_url}")
        except RetryAfter:
            logger.warning("Could not set webhook due to flood control. Another worker likely succeeded.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while setting webhook: {e}")
    yield
    logger.info("Application shutdown...")
    if bot_app:
        await bot_app.shutdown()

# --- 4. MAIN FASTAPI APP INITIALIZATION ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if not TELEGRAM_BOT_TOKEN:
    logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set! Bot will be disabled.")
else:
    ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app = setup_handlers(ptb_application)
    logger.info("Telegram bot application created and handlers have been attached.")


# --- 5. API ENDPOINTS (BOT & HTTP) ---

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Main webhook to receive updates from Telegram."""
    if not bot_app: return Response(status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        # By passing the manager, handlers can now broadcast messages
        await bot_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)
        return Response(status_code=500)

async def get_game_details_as_dict(game_id: int) -> Dict:
    """Helper to fetch full game details for broadcasting."""
    async with get_db_session() as session:
        stmt = select(
            games.c.id, games.c.stake, games.c.pot, games.c.win_condition, games.c.creator_id, users.c.username
        ).join(users, games.c.creator_id == users.c.telegram_id).where(games.c.id == game_id)
        row = (await session.execute(stmt)).first()
        if not row: return None
        return {
            "id": row.id,
            "creator": row.username or "Player",
            "avatarId": row.creator_id % 10,
            "stake": float(row.stake),
            "prize": float(row.pot * 0.9),
            "winCondition": row.win_condition
        }

# =========================================================
# =========== INJECTED REAL-TIME ENDPOINT =================
# =========================================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Handles real-time connections for live lobby updates."""
    await manager.connect(websocket, user_id)
    try:
        # Send initial game list from the database
        async with get_db_session() as session:
            stmt = select(games.c.id, games.c.stake, games.c.pot, games.c.win_condition, games.c.creator_id, users.c.username).join(users, games.c.creator_id == users.c.telegram_id).where(games.c.status == 'lobby')
            result = await session.execute(stmt)
            initial_games = [
                {"id": r.id, "creator": r.username or "Player", "avatarId": r.creator_id % 10, "stake": float(r.stake), "prize": float(r.pot * 0.9), "winCondition": r.win_condition}
                for r in result
            ]
        await websocket.send_text(json.dumps({"event": "initial_game_list", "games": initial_games}))

        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            # This is now the primary way games are joined
            if action == "join_game":
                game_id_to_join = data.get("gameId")
                async with get_db_session() as session:
                    # Here you would add logic to check if the user can join,
                    # update the game status from 'lobby' to 'active', etc.
                    # For now, we'll just delete it from the lobby.
                    stmt = delete(games).where(games.c.id == game_id_to_join)
                    await session.execute(stmt)
                    await session.commit()
                
                # Announce to everyone that the game is now gone
                await manager.broadcast(json.dumps({"event": "remove_game", "gameId": game_id_to_join}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Error for user {user_id}: {e}", exc_info=True)
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- 6. MOUNT STATIC FILES ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")