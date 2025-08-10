# app.py - The final, robust version with resilient startup

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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from telegram.error import RetryAfter # IMPORT THE SPECIFIC ERROR

# --- Import Your Project Modules ---
from bot.handlers import (
    start_command, main_menu_handler, deposit_amount_handler, cancel_conversation_handler,
    DEPOSIT_AMOUNT
)
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
    bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    deposit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(main_menu_handler, pattern='^deposit$')],
        states={DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_handler)]},
        fallbacks=[CallbackQueryHandler(cancel_conversation_handler, pattern='^cancel_conv$')]
    )
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(deposit_conv)
    bot_app.add_handler(CallbackQueryHandler(main_menu_handler))

    # ==============================================================================
    # --- THIS IS THE KEY FIX: Resilient Webhook Setup ---
    # ==============================================================================
    try:
        full_webhook_url = f"{WEBHOOK_URL}/api/telegram/webhook"
        
        # 1. First, CHECK the current webhook
        current_webhook_info = await bot_app.bot.get_webhook_info()
        
        # 2. Only SET the webhook if it's not already correct
        if current_webhook_info.url != full_webhook_url:
            await bot_app.bot.delete_webhook(drop_pending_updates=True)
            await bot_app.bot.set_webhook(url=full_webhook_url)
            logger.info(f"Webhook successfully set to {full_webhook_url}")
        else:
            logger.info("Webhook is already set correctly. Skipping.")

    # 3. CATCH the flood control error and prevent the crash
    except RetryAfter as e:
        logger.warning(f"Flood control exceeded while setting webhook. Will retry on next startup. Details: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during webhook setup: {e}")
        # Depending on the severity, you might want to raise this to stop the app
        # For now, we'll log it and continue.

    app.state.bot_app = bot_app
    
    yield # Application runs here
    
    logger.info("Application shutting down...")
    # It's good practice to try cleaning up, but don't crash if it fails
    try:
        await app.state.bot_app.bot.delete_webhook()
    except Exception as e:
        logger.error(f"Error deleting webhook on shutdown: {e}")

# (The rest of your app.py remains exactly the same)
# ...
# --- Main Application Instance ---
app = FastAPI(title="Yeab Game Zone", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    async def broadcast(self, message: dict):
        message_str = json.dumps(message)
        tasks = [conn.send_text(message_str) for conn in self.active_connections.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

manager = ConnectionManager()

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    bot_app = request.app.state.bot_app
    update_data = await request.json()
    update = Update.de_json(update_data, bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

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

@app.get("/")
def read_root():
    return {"status": "Yeab Game Zone API is running"}