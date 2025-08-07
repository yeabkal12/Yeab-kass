# app.py (The Real-Time Backend)

import asyncio
import json
import logging
from typing import Dict, List
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

# --- In-Memory Storage (for this example) ---
# In a real app, this would be your database.
active_games: Dict[str, Dict] = {}

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
app = FastAPI(title="Real-Time Game Lobby API")

# --- Add CORS middleware to allow connections from your frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logging.info("New client connected.")
    
    # Send the current list of active games to the newly connected client
    initial_data = {"event": "initial_game_list", "games": list(active_games.values())}
    await websocket.send_text(json.dumps(initial_data))

    try:
        while True:
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            action = data.get("action")

            if action == "create_game":
                game_id = str(uuid.uuid4())
                new_game = {
                    "id": game_id,
                    "stake": data["stake"],
                    "winCondition": data["winCondition"],
                    "prize": int(data["stake"] * 2 * 0.9), # Calculate prize on server
                    "creator": "Player" + str(len(manager.active_connections)) # Example username
                }
                active_games[game_id] = new_game
                logging.info(f"Game created: {new_game}")
                
                # Broadcast the new game to all clients
                await manager.broadcast(json.dumps({"event": "new_game", "game": new_game}))

            elif action == "join_game" or action == "cancel_game":
                game_id = data.get("gameId")
                if game_id in active_games:
                    del active_games[game_id]
                    logging.info(f"Game removed: {game_id}")
                    # Broadcast the removal to all clients
                    await manager.broadcast(json.dumps({"event": "remove_game", "gameId": game_id}))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("Client disconnected.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"status": "Lobby server is running"}

# To run this server: uvicorn app:app --host 0.0.0.0 --port 8000 --reload