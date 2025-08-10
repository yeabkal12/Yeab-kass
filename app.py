import asyncio
import json
import uuid
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from database_models.manager import AsyncSessionLocal, Game

# The FastAPI app object is created here and will be imported by the root app.py
app = FastAPI(title="Yeab Game Zone WebSocket API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    async def disconnect(self, user_id: int):
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

async def handle_disconnect(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(Game).where(Game.creator_id == user_id, Game.status == 'waiting')
        result = await session.execute(stmt)
        games_to_remove = result.scalars().all()
        for game in games_to_remove:
            await session.delete(game)
            await session.commit()
            await manager.broadcast({"event": "remove_game", "gameId": game.id})

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(Game).where(Game.status == 'waiting').order_by(Game.id.desc())
            result = await session.execute(stmt)
            games = result.scalars().all()
            game_list = [
                {
                    "id": game.id, "creatorName": "Anonymous", "stake": float(game.stake),
                    "win_condition": game.win_condition, "prize": float(game.stake) * 2 * 0.9
                } for game in games
            ]
            await manager.send_personal_message({"event": "initial_game_list", "games": game_list}, user_id)

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event = message.get("event")
            if event == "create_game":
                payload = message.get("payload", {})
                stake, win_condition = payload.get("stake"), payload.get("winCondition")
                if stake is None or win_condition is None: continue
                new_game = Game(id=str(uuid.uuid4()), creator_id=user_id, stake=stake, win_condition=win_condition, status='waiting')
                async with AsyncSessionLocal() as session:
                    session.add(new_game)
                    await session.commit()
                game_data = {
                    "id": new_game.id, "creatorName": "Anonymous", "stake": float(new_game.stake),
                    "win_condition": new_game.win_condition, "prize": float(new_game.stake) * 2 * 0.9
                }
                await manager.broadcast({"event": "new_game", "game": game_data})
    except WebSocketDisconnect:
        await handle_disconnect(user_id)
    finally:
        await manager.disconnect(user_id)

@app.get("/")
def read_root():
    return {"status": "Yeab Game Zone API is running"}