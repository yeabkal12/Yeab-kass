# app.py (The Final, Definitive Version with Database and Real-Time Logic)

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
from sqlalchemy import select

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
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
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
        except Exception as e:
            logger.warning(f"Webhook setup failed (another worker may have succeeded): {e}")
    yield
    logger.info("Application shutdown...")
    if bot_app:
        await bot_app.shutdown()

# --- 4. MAIN FASTAPI APP INITIALIZATION ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not TELEGRAM_BOT_TOKEN:
    logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set! Bot will be disabled.")
else:
    ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app = setup_handlers(ptb_application)
    logger.info("Telegram bot application created and handlers have been attached.")

# --- 5. API ENDPOINTS ---

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Main webhook to receive updates from Telegram."""
    if not bot_app: return Response(status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}", exc_info=True)
        return Response(status_code=500)

@app.get("/api/games")
async def get_open_games():
    """Endpoint for the web app to fetch the initial list of open games."""
    live_games = []
    try:
        async with get_db_session() as session:
            stmt = select(
                games.c.id, games.c.stake, games.c.pot, games.c.win_condition, users.c.username
            ).join(users, games.c.creator_id == users.c.telegram_id)\
             .where(games.c.status == 'lobby').order_by(games.c.created_at.desc())
            
            result = await session.execute(stmt)
            for row in result.fetchall():
                live_games.append({
                    "id": row.id,
                    "creator": row.username or "Player",
                    "avatarId": games.c.creator_id % 10, # Consistent avatar logic
                    "stake": float(row.stake),
                    "prize": float(row.pot * 0.9),
                    "winCondition": row.win_condition
                })
    except Exception as e:
        logger.error(f"Failed to fetch open games from database: {e}")
        return {"games": []}
    return {"games": live_games}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles real-time connections for live lobby updates."""
    await manager.connect(websocket)
    
    # Send the initial list of games upon connection
    initial_games = await get_open_games()
    await websocket.send_text(json.dumps({"event": "initial_game_list", "games": initial_games["games"]}))

    try:
        while True:
            # We don't need to process incoming messages for this lobby version,
            # as game creation is handled by the bot via web_app_data.
            # We just keep the connection alive to broadcast updates.
            await websocket.receive_text() 
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from WebSocket.")
    except Exception as e:
        logger.error(f"An error occurred in WebSocket: {e}", exc_info=True)
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """A simple health check endpoint."""
    return {"status": "healthy"}


# --- 6. MOUNT STATIC FILES FOR WEB APP ---
# This MUST be the last thing in the file.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")