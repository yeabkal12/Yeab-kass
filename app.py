# app.py (The Final, Definitive Version with Database and Injected Real-Time Logic)

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
    def __init__(self):
        self.active_connections: Dict[WebSocket, int] = {} # Store user_id with connection
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
    # This function is already correct
    logger.info("Application startup...")
    # ... (your existing lifespan logic)
    yield
    logger.info("Application shutdown...")
    # ... (your existing lifespan logic)


# --- 4. MAIN FASTAPI APP INITIALIZATION ---
app = FastAPI(title="Yeab Game Zone API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if not TELEGRAM_BOT_TOKEN:
    logger.error("FATAL: TELEGRAM_BOT_TOKEN is not set! Bot will be disabled.")
else:
    ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app = setup_handlers(ptb_application)
    logger.info("Telegram bot application created and handlers have been attached.")


# --- 5. API ENDPOINTS ---

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    # This function is already correct
    # ... (your existing webhook logic)
    pass

async def get_game_details_as_dict(game_id: int) -> Dict:
    """Helper function to fetch full game details for broadcasting."""
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
# =========== START: INJECTED SECTION =====================
# =========================================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Handles real-time connections AND processes game actions."""
    await manager.connect(websocket, user_id)
    
    # Send the initial list of games from the real database
    try:
        async with get_db_session() as session:
            stmt = select(
                games.c.id, games.c.stake, games.c.pot, games.c.win_condition, games.c.creator_id, users.c.username
            ).join(users, games.c.creator_id == users.c.telegram_id).where(games.c.status == 'lobby')
            result = await session.execute(stmt)
            initial_games = [{
                "id": r.id, "creator": r.username or "Player", "avatarId": r.creator_id % 10,
                "stake": float(r.stake), "prize": float(r.pot * 0.9), "winCondition": r.win_condition
            } for r in result]
        
        await websocket.send_text(json.dumps({"event": "initial_game_list", "games": initial_games}))
    except Exception as e:
        logger.error(f"Failed to send initial game list: {e}")


    try:
        while True:
            # THIS IS THE INJECTED LOGIC TO PROCESS MESSAGES
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            action = data.get("action")

            if action == "create_game":
                stake = data["stake"]
                win_condition = data["winCondition"]
                
                async with get_db_session() as session:
                    # Create the game in the database
                    game_stmt = insert(games).values(
                        creator_id=user_id, stake=stake, pot=stake * 2,
                        win_condition=win_condition, status='lobby'
                    ).returning(games.c.id)
                    game_id = (await session.execute(game_stmt)).scalar_one()
                    await session.commit()
                
                # Fetch the full new game details to broadcast
                new_game_details = await get_game_details_as_dict(game_id)
                if new_game_details:
                    await manager.broadcast(json.dumps({"event": "new_game", "game": new_game_details}))

            elif action == "join_game":
                game_id_to_join = data.get("gameId")
                async with get_db_session() as session:
                    # Simple logic: delete the game from the lobby
                    stmt = delete(games).where(games.c.id == game_id_to_join)
                    await session.execute(stmt)
                    await session.commit()

                # Broadcast that the game has been removed
                await manager.broadcast(json.dumps({"event": "remove_game", "gameId": game_id_to_join}))


    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client {user_id} disconnected from WebSocket.")
    except Exception as e:
        logger.error(f"An error occurred in WebSocket for user {user_id}: {e}", exc_info=True)
        manager.disconnect(websocket)

# =========================================================
# ============= END: INJECTED SECTION =====================
# =========================================================

@app.get("/health")
async def health_check():
    """A simple health check endpoint."""
    return {"status": "healthy"}


# --- 6. MOUNT STATIC FILES FOR WEB APP ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")