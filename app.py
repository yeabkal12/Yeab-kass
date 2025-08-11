# app.py - The Final, Production-Ready Version

import asyncio
import json
import os
import logging
import uvicorn
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from telegram import Update
from telegram.ext import Application
from telegram.error import RetryAfter

# Import your project modules
from bot.handlers import setup_handlers # THE KEY CHANGE IS HERE
from database_models.manager import Base, engine, AsyncSessionLocal, Game

# --- Environment Variable Validation ---
logger = logging.getLogger(__name__)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

if not TELEGRAM_BOT_TOKEN: raise ValueError("FATAL: TELEGRAM_BOT_TOKEN is not set.")
if not WEBHOOK_URL: raise ValueError("FATAL: WEBHOOK_URL is not set.")
if not DATABASE_URL: raise ValueError("FATAL: DATABASE_URL is not set.")

PORT = int(os.getenv("PORT", "8000"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- Database Initialization ---
async def initialize_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables checked/initialized.")

# --- FastAPI Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    await initialize_database()
    
    # Setup Telegram Bot
    bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # THE KEY CHANGE IS HERE: All handlers are now set up in a separate function
    setup_handlers(bot_app)
    
    # Resilient Webhook Setup
    try:
        full_webhook_url = f"{WEBHOOK_URL}/api/telegram/webhook"
        current_webhook_info = await bot_app.bot.get_webhook_info()
        if current_webhook_info.url != full_webhook_url:
            await bot_app.bot.delete_webhook(drop_pending_updates=True)
            await bot_app.bot.set_webhook(url=full_webhook_url)
            logger.info(f"Webhook successfully set to {full_webhook_url}")
        else:
            logger.info("Webhook is already set correctly. Skipping.")
    except RetryAfter as e:
        logger.warning(f"Flood control exceeded while setting webhook. Details: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during webhook setup: {e}", exc_info=True)

    app.state.bot_app = bot_app
    
    yield # Application runs
    
    logger.info("Application shutting down...")
    try:
        await app.state.bot_app.bot.delete_webhook()
    except Exception as e:
        logger.error(f"Error deleting webhook on shutdown: {e}")

# --- Main Application Instance ---
app = FastAPI(title="Yeab Game Zone", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Connection Manager (No changes needed) ---
class ConnectionManager:
    def __init__(self): self.active_connections: dict[int, WebSocket] = {}
    async def connect(self, ws: WebSocket, user_id: int): await ws.accept(); self.active_connections[user_id] = ws
    def disconnect(self, user_id: int):
        if user_id in self.active_connections: del self.active_connections[user_id]
    async def broadcast(self, msg: dict): await asyncio.gather(*[c.send_text(json.dumps(msg)) for c in self.active_connections.values()], return_exceptions=True)
    async def send_personal_message(self, msg: dict, user_id: int):
        if user_id in self.active_connections: await self.active_connections[user_id].send_text(json.dumps(msg))
manager = ConnectionManager()

# --- Webhook Endpoint ---
@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Handles updates from Telegram by putting them into the bot's processing queue.
    """
    bot_app = request.app.state.bot_app
    update_data = await request.json()
    
    # THE KEY CHANGE IS HERE: Use the queue for better performance and reliability
    await bot_app.update_queue.put(Update.de_json(update_data, bot_app.bot))
    
    return {"status": "ok"}

# --- WebSocket Endpoint (No changes needed) ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Game).where(Game.status == 'waiting').order_by(Game.id.desc())
            games = (await session.execute(stmt)).scalars().all()
            game_list = [{"id": g.id, "creatorName": "Anonymous", "stake": float(g.stake), "win_condition": g.win_condition, "prize": float(g.stake) * 2 * 0.9} for g in games]
            await manager.send_personal_message({"event": "initial_game_list", "games": game_list}, user_id)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event = message.get("event")
            if event == "create_game":
                payload = message.get("payload", {})
                stake, wc = payload.get("stake"), payload.get("winCondition")
                new_game = Game(id=str(uuid.uuid4()), creator_id=user_id, stake=stake, win_condition=wc, status='waiting')
                async with AsyncSessionLocal() as session:
                    session.add(new_game)
                    await session.commit()
                game_data = {"id": new_game.id, "creatorName": "Anonymous", "stake": float(stake), "win_condition": wc, "prize": float(stake) * 2 * 0.9}
                await manager.broadcast({"event": "new_game", "game": game_data})
    except WebSocketDisconnect:
        logger.info(f"Client {user_id} disconnected.")
        async with AsyncSessionLocal() as session:
            stmt = select(Game).where(Game.creator_id == user_id, Game.status == 'waiting')
            games_to_remove = (await session.execute(stmt)).scalars().all()
            for game in games_to_remove:
                await session.delete(game)
                await session.commit()
                await manager.broadcast({"event": "remove_game", "gameId": game.id})
    finally:
        manager.disconnect(user_id)

# --- Root Endpoint (No changes needed) ---
@app.get("/")
def read_root():
    return {"status": "Yeab Game Zone API is running"}