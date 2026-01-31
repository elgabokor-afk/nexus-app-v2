
from fastapi import FastAPI, Request, HTTPException
import uvicorn
import os
import json
import redis
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

app = FastAPI(title="Nexus Webhook Receiver")

# Redis Connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
r = redis.from_url(REDIS_URL, decode_responses=True)

@app.get("/health")
async def health_check():
    return {"status": "ACTIVE", "service": "NEXUS_WEBHOOK"}

@app.post("/helius")
async def receive_helius_webhook(request: Request):
    """
    Receives and processes Helius Enhanced Transaction Webhooks.
    """
    try:
        data = await request.json()
        
        # V5100: REAL-TIME INGESTION
        # Helius sends a list of transactions
        for tx in data:
            tx_type = tx.get('type')
            signature = tx.get('signature')
            
            # Focus on Swaps (Raydium, Jupiter, etc.)
            if tx_type == "SWAP":
                description = tx.get('description', 'Unknown Swap')
                
                # Broadcast to Redis for the Worker to consume
                payload = {
                    "source": "HELIUS_WEBHOOK",
                    "signature": signature,
                    "type": "SWAP",
                    "timestamp": tx.get('timestamp'),
                    "events": tx.get('events', {}),
                    "raw": tx # Pass full data for indexer parsing
                }
                
                r.publish("realtime_swaps", json.dumps(payload))
                print(f"   [WEBHOOK] Published Swap: {signature[:8]}...")

        return {"status": "SUCCESS", "processed": len(data)}

    except Exception as e:
        print(f"Webhook Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"/// N E X U S  W E B H O O K  (V5.1) ///")
    print(f"Listening on port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
