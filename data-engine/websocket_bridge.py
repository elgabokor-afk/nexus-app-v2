
import os
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from redis_engine import redis_engine
from dotenv import load_dotenv

app = FastAPI(title="Nexus WebSocket Bridge")

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async contract(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"   [WS] New Connection. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"   [WS] Disconnected. Active: {len(self.active_connections)}")

    async broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be dead
                pass

manager = ConnectionManager()

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.contract(websocket)
    try:
        while True:
            # Keep connection alive, can handle client messages if needed
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def redis_listener():
    """Listens to Redis and broadcasts to all WS clients."""
    print("   [WS BRIDGE] Redis Listener Started...")
    # Channels to listen to
    channels = ["live_signals", "live_analytics", "live_prices"]
    
    # We use a non-blocking loop for redis subscription in asgi
    # In a real production app, we might use aioredis, but redis-py pubsub.listen() is fine in a thread/task
    loop = asyncio.get_event_loop()
    
    # Run the listener in a separate thread to not block the event loop if needed, 
    # but since this is an async task we should use a non-blocking approach if possible.
    # redis-py's pubsub.get_message() is non-blocking.
    
    pubsub = redis_engine.client.pubsub()
    pubsub.subscribe(channels)
    
    while True:
        message = pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            payload = {
                "channel": message['channel'],
                "data": json.loads(message['data'])
            }
            await manager.broadcast(payload)
        await asyncio.sleep(0.01) # Low latency check

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 for Railway/Vercel connectivity
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
