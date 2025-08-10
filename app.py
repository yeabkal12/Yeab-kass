# app.py
import asyncio
import json
import uuid
from typing import List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# --- In-Memory Storage ---
# In a real production app, you would replace this with a database like Redis or PostgreSQL.
# The key is the game_id (a string), and the value is the game dictionary.
active_games: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="Yaba Games WebSocket Server")

# --- CORS Middleware ---
# Allows your frontend (even when testing locally) to connect to the server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class ConnectionManager:
    """Manages active WebSocket connections to broadcast messages."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts and stores a new WebSocket connection."""
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

def create_game_object(stake: int, win_condition: int, creator_name: str) -> Dict[str, Any]:
    """Creates a new game dictionary with a unique ID and calculates the prize."""
    game_id = str(uuid.uuid4())
    commission_rate = 0.10
    total_pot = stake * 2
    prize = total_pot - (total_pot * commission_rate)

    return {
        "id": game_id,
        "stake": stake,
        "win_condition": win_condition,
        "prize": round(prize, 2),
        "creatorName": creator_name or "Player***", # Use provided name or a default
        "players": [creator_name], # Start with the creator as the first player
        "status": "waiting",
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The main WebSocket endpoint for handling all real-time game logic."""
    await manager.connect(websocket)
    print("A new client connected.")

    # 1. Send the initial list of games to the newly connected client
    try:
        initial_data = {
            "event": "initial_game_list",
            # We send games in reverse order so newest appear first
            "games": list(reversed(list(active_games.values())))
        }
        await websocket.send_text(json.dumps(initial_data))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected before initialization.")
        return

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
                # You can get user info from the Telegram Web App initData
                creator_name = payload.get("creatorName", "Anonymous")

                if stake is not None and win_condition is not None:
                    # Create and store the new game
                    new_game = create_game_object(stake, win_condition, creator_name)
                    active_games[new_game["id"]] = new_game
                    print(f"New game created: {new_game['id']} with stake {stake}")

                    # Broadcast the new game to ALL connected clients
                    broadcast_message = {
                        "event": "new_game",
                        "game": new_game
                    }
                    await manager.broadcast(json.dumps(broadcast_message))

            # --- You would add other events here ---
            # For example: "join_game", "player_move", "game_over", etc.
            # elif event == "join_game":
            #   ... handle logic for a player joining a game ...


    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        manager.disconnect(websocket)


@app.get("/")
def read_root():
    """A simple root endpoint to confirm the server is running."""
    return {"status": "Yaba Games Server is running", "active_games": len(active_games)}