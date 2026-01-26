
import os
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis_engine import redis_engine
from dotenv import load_dotenv

load_dotenv()

# V1100: Extended Channels for HA Dashboard (Updated V1400)
CHANNELS = ["live_signals", "live_analytics", "live_prices", "live_positions", "live_logs", "ai_rankings"]

async def redis_listener():
    """Listens to Redis and broadcasts to all WS clients."""
    print("   [WS BRIDGE] Redis Listener Started...")
    
    if not redis_engine.client:
        print("   [WS BRIDGE] Error: Redis client not connected. Bridge will not function.")
        return

    pubsub = redis_engine.client.pubsub()
    pubsub.subscribe(CHANNELS)
    
    while True:
        message = pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            payload = {
                "channel": message['channel'],
                "data": json.loads(message['data'])
            }
            await manager.broadcast(payload)
        await asyncio.sleep(0.01) # Low latency check

# V1201: Modern Lifespan Handler (Fixes DeprecationWarning)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Redis Listener
    asyncio.create_task(redis_listener())
    yield
    # Shutdown logic (if any) goes here

app = FastAPI(title="Nexus WebSocket Bridge", lifespan=lifespan)

# V1102: Enable CORS for Vercel Connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def contract(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"   [WS] New Connection. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"   [WS] Disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# V1800: AI Chat Endpoint
from pydantic import BaseModel
from cosmos_agent import cosmos_agent

class ChatRequest(BaseModel):
    message: str
    signalContext: dict

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    V1800: Direct interface to Cosmos AI Agent.
    """
    response = cosmos_agent.analyze_signal(request.message, request.signalContext)
    return response

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.contract(websocket)
    try:
        while True:
            # Keep connection alive, can handle client messages if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 for Railway/Vercel connectivity
    port = int(os.getenv("PORT", 8000))
    print(f"   [BRIDGE] Starting on Port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
