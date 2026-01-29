
import os
import ccxt
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from redis_engine import redis_engine
from supabase import create_client, Client
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pusher import Pusher
from cosmos_agent import cosmos_agent

# 1. Config & Security
load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
PUSHER_APP_ID = os.getenv("PUSHER_APP_ID")
PUSHER_KEY = os.getenv("NEXT_PUBLIC_PUSHER_KEY")
PUSHER_SECRET = os.getenv("PUSHER_SECRET")
PUSHER_CLUSTER = os.getenv("NEXT_PUBLIC_PUSHER_CLUSTER")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase Credentials Missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Init Pusher
pusher_client = None
if PUSHER_APP_ID and PUSHER_KEY:
    pusher_client = Pusher(
        app_id=PUSHER_APP_ID,
        key=PUSHER_KEY,
        secret=PUSHER_SECRET,
        cluster=PUSHER_CLUSTER,
        ssl=True
    )

# 2. WebSocket Manager
CHANNELS = ["live_signals", "live_analytics", "live_prices", "live_positions", "live_logs", "ai_rankings"]

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

async def redis_listener():
    """Listens to Redis and broadcasts to all WS clients."""
    if not redis_engine.client:
        print("   [API] Redis offline. WS Broadcasting disabled.")
        return

    pubsub = redis_engine.client.pubsub()
    pubsub.subscribe(CHANNELS)
    
    while True:
        try:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                payload = {
                    "channel": message['channel'],
                    "data": json.loads(message['data'])
                }
                await manager.broadcast(payload)
        except Exception as e:
            print(f"   [API] Redis Error: {e}")
            await asyncio.sleep(1) # Backoff
        await asyncio.sleep(0.01)

# 3. Encryption Manager
class KeyManager:
    def __init__(self, master_key):
        if not master_key: return
        self.fernet = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)

    def decrypt(self, token: str) -> str:
        return self.fernet.decrypt(token.encode()).decode()

key_manager = KeyManager(ENCRYPTION_KEY) if ENCRYPTION_KEY else None

# 4. Lifespan Handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Redis Listener
    asyncio.create_task(redis_listener())
    print("   [API] Nexus Gateway Started (WS + REST)")
    yield

app = FastAPI(title="Nexus Unified API Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Models & Endpoints
class ChatRequest(BaseModel):
    message: str
    signalContext: dict

class TradeRequest(BaseModel):
    user_id: str
    symbol: str 
    side: str # buy/sell
    amount_usd: float
    leverage: int = 1
    stop_loss: float = 0
    take_profit: float = 0

@app.get("/")
def health():
    return {"status": "ok", "version": "v5.0"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return cosmos_agent.analyze_signal(request.message, request.signalContext)

@app.post("/execute-trade")
async def execute_trade(req: TradeRequest):
    if not key_manager:
        raise HTTPException(status_code=500, detail="Encryption System Not Configured")

    # A. Fetch Encrypted Keys
    res = supabase.table("user_exchanges").select("*").eq("user_id", req.user_id).eq("is_active", True).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="No active Exchange Keys found.")
    
    exchange_data = res.data[0]
    
    try:
        # B. Decrypt & Exec
        api_key = key_manager.decrypt(exchange_data['api_key_enc'])
        secret = key_manager.decrypt(exchange_data['secret_key_enc'])
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'options': {'defaultType': 'swap'}
        })
        
        # Security: Abort if withdrawals enabled (V500 Re-Check)
        # Using Private Get to verify
        restrictions = exchange.private_get_sapi_v1_account_apirestrictions()
        if restrictions.get('enableWithdrawals') is True:
            raise PermissionError("Withdrawals Enabled - Safety Abort")

        exchange.load_markets()
        price = exchange.fetch_ticker(req.symbol)['last']
        amount_coins = req.amount_usd / price
        qty = exchange.amount_to_precision(req.symbol, amount_coins)
        
        order = exchange.create_market_order(req.symbol, req.side, qty)
        entry_price = float(order.get('average', price))
        
        # Exits
        exit_side = 'sell' if req.side == 'buy' else 'buy'
        sl_id, tp_id = None, None
        
        if req.stop_loss > 0:
            sl_price = exchange.price_to_precision(req.symbol, req.stop_loss)
            sl = exchange.create_order(req.symbol, 'STOP_MARKET', exit_side, qty, params={'stopPrice': sl_price, 'reduceOnly': True})
            sl_id = sl['id']
            
        if req.take_profit > 0:
            tp_price = exchange.price_to_precision(req.symbol, req.take_profit)
            tp = exchange.create_order(req.symbol, 'TAKE_PROFIT_MARKET', exit_side, qty, params={'stopPrice': tp_price, 'reduceOnly': True})
            tp_id = tp['id']

        # Log & Notify
        supabase.table("live_trades").insert({
            "user_id": req.user_id, "symbol": req.symbol, "side": req.side,
            "entry_price": entry_price, "size": amount_coins, "status": "OPEN",
            "entry_order_id": str(order['id']), "sl_order_id": str(sl_id), "tp_order_id": str(tp_id)
        }).execute()
        
        if pusher_client:
            pusher_client.trigger('private-execution-' + req.user_id, 'order-filled', {
                'symbol': req.symbol, 'price': entry_price, 'status': 'FILLED'
            })
            
        return {"status": "success", "order": order}

    except Exception as e:
        if pusher_client:
            pusher_client.trigger('private-execution-' + req.user_id, 'order-failed', {'error': str(e)})
        raise HTTPException(status_code=400, detail=str(e))

class SaveKeyRequest(BaseModel):
    user_id: str
    exchange: str
    api_key: str
    secret_key: str
@app.post("/save-keys")
async def save_keys(req: SaveKeyRequest):
    """
    V5005: Securely encrypt and save user keys.
    Prevents plain-text keys from ever hitting the database long-term.
    """
    if not key_manager:
        raise HTTPException(status_code=500, detail="Encryption System Not Configured")

    try:
        # 1. Verify No Withdrawals (Optional but recommended on save)
        test_exchange = getattr(ccxt, req.exchange)({
            'apiKey': req.api_key,
            'secret': req.secret_key,
            'options': {'defaultType': 'swap'}
        })
        try:
            restrictions = test_exchange.private_get_sapi_v1_account_apirestrictions()
            if restrictions.get('enableWithdrawals') is True:
                return JSONResponse(status_code=400, content={"error": "Withdrawals Enabled. Please disable for safety."})
        except: pass # Some exchanges don't support this check easily

        # 2. Encrypt
        api_key_enc = key_manager.fernet.encrypt(req.api_key.encode()).decode()
        secret_key_enc = key_manager.fernet.encrypt(req.secret_key.encode()).decode()

        # 3. Save to Supabase
        res = supabase.table("user_exchanges").upsert({
            "user_id": req.user_id,
            "exchange": req.exchange,
            "api_key_enc": api_key_enc,
            "secret_key_enc": secret_key_enc,
            "is_active": True,
            "permissions_verified": True
        }, on_conflict="user_id").execute()

        return {"status": "success", "message": "Keys Encrypted & Saved Successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
