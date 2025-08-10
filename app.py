import asyncio
import json
import os
import uuid
from typing import Dict, List, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

# Import database session and models from your project structure
from database_models.manager import AsyncSessionLocal, Game, User

app = FastAPI(title="Yeab Game Zone API")

# --- CORS Middleware ---
# Allows your frontend to connect to this backend, essential for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Connection Management & Real-Time Presence ---
class ConnectionManager:
    """Manages active WebSocket connections and user presence."""
    def __init__(self):
        # Maps a user's telegram_id to their active WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accepts and stores a new WebSocket connection for a given user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"Client connected: {user_id}")

    async def disconnect(self, user_id: int):
        """Removes a user's WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"Client disconnected: {user_id}")

    async def broadcast(self, message: dict):
        """Sends a JSON message to all active connections."""
        message_str = json.dumps(message)
        # Create a list of tasks to send messages concurrently
        tasks = [
            connection.send_text(message_str)
            for connection in self.active_connections.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def send_personal_message(self, message: dict, user_id: int):
        """Sends a personal JSON message to a specific user."""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

manager = ConnectionManager()

# --- Core Disconnect Logic ---
async def handle_disconnect(user_id: int):
    """
    Handles cleaning up when a user disconnects.
    Specifically, removes any 'waiting' games created by that user.
    """
    async with AsyncSessionLocal() as session:
        # Find games created by this user that are still waiting for an opponent
        stmt = select(Game).where(Game.creator_id == user_id, Game.status == 'waiting')
        result = await session.execute(stmt)
        games_to_remove = result.scalars().all()

        if not games_to_remove:
            return

        for game in games_to_remove:
            print(f"Creator {user_id} disconnected, removing waiting game {game.id}")
            # Delete the game lobby from the database
            await session.delete(game)
            await session.commit()

            # Broadcast to all other users that this game has been removed
            await manager.broadcast({
                "event": "remove_game",
                "gameId": game.id
            })

# --- WebSocket Endpoint ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        # 1. Send the initial list of currently open games to the new user
        async with AsyncSessionLocal() as session:
            stmt = select(Game).where(Game.status == 'waiting').order_by(Game.id.desc())
            result = await session.execute(stmt)
            games = result.scalars().all()
            
            # Prepare the game list with all data the frontend needs, including prize
            game_list = [
                {
                    "id": game.id,
                    "creatorName": "Anonymous", # Or fetch from User model if available
                    "stake": float(game.stake),
                    "win_condition": game.win_condition,
                    "prize": float(game.stake) * 2 * 0.9  # Calculate 90% prize
                } for game in games
            ]
            await manager.send_personal_message({"event": "initial_game_list", "games": game_list}, user_id)

        # 2. Listen for incoming messages from the user
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event = message.get("event")

            if event == "create_game":
                payload = message.get("payload", {})
                stake = payload.get("stake")
                win_condition = payload.get("winCondition")

                if stake is None or win_condition is None:
                    continue
                
                # Create a new game object for the database
                new_game = Game(
                    id=str(uuid.uuid4()),
                    creator_id=user_id,
                    stake=stake,
                    win_condition=win_condition,
                    status='waiting'
                )
                async with AsyncSessionLocal() as session:
                    session.add(new_game)
                    await session.commit()
                
                # Prepare the game data to be broadcasted to all users
                game_data_for_broadcast = {
                    "id": new_game.id,
                    "creatorName": "Anonymous",
                    "stake": float(new_game.stake),
                    "win_condition": new_game.win_condition,
                    "prize": float(new_game.stake) * 2 * 0.9 # Calculate prize
                }
                
                await manager.broadcast({"event": "new_game", "game": game_data_for_broadcast})

            # ... You will add other events here like "join_game", "roll_dice", etc.

    except WebSocketDisconnect:
        # This block executes when the client's connection is lost
        await handle_disconnect(user_id)
    finally:
        # Always ensure the connection is removed from the manager
        await manager.disconnect(user_id)

# --- Root Endpoint ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm the server is running."""
    return {"status": "Yeab Game Zone API is running"}