# app.py
import asyncio
import json
import uuid
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# --- In-Memory Storage ---
# In a production environment, you would replace this with a proper database (e.g., Redis, PostgreSQL).
active_games: Dict[str, Dict[str, Any]] = {}

app = FastAPI()

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket connection."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Sends a message to all active connections."""
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def create_game_object(stake: int, win_condition: int) -> Dict[str, Any]:
    """Creates a new game dictionary with a unique ID."""
    game_id = str(uuid.uuid4())
    # You would also include creator info, etc., from the Telegram WebApp data.
    return {
        "id": game_id,
        "stake": stake,
        "win_condition": win_condition,
        "players": 1, # The creator is the first player
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main WebSocket endpoint for handling game logic."""
    await manager.connect(websocket)
    print("New client connected.")

    # 1. Send the initial list of games to the newly connected client
    initial_data = {
        "event": "initial_game_list",
        "games": list(active_games.values())
    }
    await websocket.send_text(json.dumps(initial_data))

    try:
        while True:
            # 2. Listen for incoming messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            event = message.get("event")

            if event == "create_game":
                payload = message.get("payload", {})
                stake = payload.get("stake")
                win_condition = payload.get("winCondition")

                if stake is not None and win_condition is not None:
                    # Create and store the new game
                    new_game = create_game_object(stake, win_condition)
                    active_games[new_game["id"]] = new_game
                    print(f"New game created: {new_game}")

                    # Broadcast the new game to all clients
                    broadcast_message = {
                        "event": "new_game",
                        "game": new_game
                    }
                    await manager.broadcast(json.dumps(broadcast_message))

            # --- You would add other events here ---
            # e.g., "join_game", "player_move", "game_over", etc.

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected.")
    except Exception as e:
        print(f"An error occurred: {e}")
        manager.disconnect(websocket)


# A simple root endpoint to confirm the server is running
@app.get("/")
def read_root():
    return {"status": "Ludo Game Server is running"}