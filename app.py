# app.py (The Definitive Version with Real-Time Broadcasting)

import asyncio
import json
import logging
import random
import uuid
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- In-Memory Storage for Active Games ---
# In a real app, this would be a database like Redis or PostgreSQL.
active_games: Dict[str, Dict] = {}


# --- WebSocket Connection Manager ---
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

# --- FastAPI App Initialization ---
# The lifespan function is no longer needed if the webhook is set manually or is stable
app = FastAPI(title="Real-Time Game Lobby API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================
# === THIS IS THE CORE OF THE FIX ==============================
# ==============================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logging.info(f"Client connected. Total clients: {len(manager.active_connections)}")
    
    # Immediately send the current list of games to the new user
    initial_data = {"event": "initial_game_list", "games": list(active_games.values())}
    await websocket.send_text(json.dumps(initial_data))

    try:
        while True:
            # Wait for a message from a client
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            action = data.get("action")

            # --- Logic to Handle Game Creation ---
            if action == "create_game":
                # 1. Create a new game object with a unique ID
                game_id = str(uuid.uuid4())
                new_game = {
                    "id": game_id,
                    "stake": data["stake"],
                    "winCondition": data["winCondition"],
                    "prize": int(data["stake"] * 2 * 0.90), # Calculate prize on the server
                    "creator": f"Player_{random.randint(100, 999)}" # Example username
                }
                
                # 2. Store the new game in our "database"
                active_games[game_id] = new_game
                logging.info(f"Game created: {new_game}")
                
                # 3. CRUCIAL FIX: Broadcast the 'new_game' event to ALL connected clients
                await manager.broadcast(json.dumps({"event": "new_game", "game": new_game}))

            # --- Logic to Handle Joining/Canceling a Game ---
            elif action == "join_game" or action == "cancel_game":
                game_id = data.get("gameId")
                if game_id in active_games:
                    logging.info(f"Game removed: {game_id}")
                    # Remove the game from storage
                    del active_games[game_id]
                    
                    # CRUCIAL: Broadcast the 'remove_game' event to ALL clients
                    await manager.broadcast(json.dumps({"event": "remove_game", "gameId": game_id}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info(f"Client disconnected. Total clients: {len(manager.active_connections)}")
    except Exception as e:
        logging.error(f"An error occurred in WebSocket: {e}", exc_info=True)
        manager.disconnect(websocket)

# A simple health check endpoint
@app.get("/")
def read_root():
    return {"status": "Lobby server is running", "active_games": len(active_games)}