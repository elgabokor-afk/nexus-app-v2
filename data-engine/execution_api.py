
import os
import ccxt
import json
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from supabase import create_client, Client
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pusher import Pusher

from fastapi.middleware.cors import CORSMiddleware

# Load Env
load_dotenv()

app = FastAPI()

# V5000: CORS Security (MoE Router Protection)
origins = [
    "http://localhost:3000",
    "https://nexus-ui.up.railway.app",
    "https://www.nexuscryptosignals.com",
    "https://nexuscryptosignals.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Config & Security
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") # Must be Fernet Base64
PUSHER_APP_ID = os.getenv("PUSHER_APP_ID")
PUSHER_KEY = os.getenv("NEXT_PUBLIC_PUSHER_KEY")
PUSHER_SECRET = os.getenv("PUSHER_SECRET")
PUSHER_CLUSTER = os.getenv("NEXT_PUBLIC_PUSHER_CLUSTER")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase Credentials Missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not ENCRYPTION_KEY:
    print("WARNING: ENCRYPTION_KEY missing. One-Click Trade will fail.")

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

# 2. Key Manager
class KeyManager:
    def __init__(self, master_key):
        if not master_key: return
        self.fernet = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)

    def decrypt(self, token: str) -> str:
        return self.fernet.decrypt(token.encode()).decode()

key_manager = KeyManager(ENCRYPTION_KEY) if ENCRYPTION_KEY else None

# 3. Models
class TradeRequest(BaseModel):
    user_id: str
    symbol: str # BTC/USDT
    side: str # buy/sell
    amount_usd: float
    leverage: int = 1
    stop_loss: float = 0
    take_profit: float = 0

@app.get("/")
def health_check():
    return {"status": "active", "service": "Nexus Live Execution API"}

@app.post("/execute-trade")
def execute_trade(req: TradeRequest, x_secret_auth: str = Header(None)):
    """
    Executes a real trade on behalf of the user.
    """
    print(f"Received Execution Request: {req.symbol} {req.side} ${req.amount_usd}")
    
    if not key_manager:
        raise HTTPException(status_code=500, detail="Encryption System Not Configured")

    # A. Fetch Encrypted Keys from DB
    res = supabase.table("user_exchanges").select("*").eq("user_id", req.user_id).eq("is_active", "true").limit(1).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="No active Exchange Keys found for user.")
    
    exchange_data = res.data[0]
    
    try:
        # B. Decrypt
        api_key = key_manager.decrypt(exchange_data['api_key_enc'])
        secret = key_manager.decrypt(exchange_data['secret_key_enc'])
        
        # C. Initialize Exchange (Ephemeral)
        # Using the user's specific keys
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'options': {'defaultType': 'swap'} # Futures
        })
        
        # D. Pre-Check Permissions (Redundant but Safe)
        # We assume they were checked on insert, but one last check?
        # Checking permissions adds latency. We rely on "Fail Fast" if withdrawals attempted?
        # But we are trading here.
        
        # E. Execution Logic (Reused from binance_engine logic basically)
        # 1. Load Markets
        exchange.load_markets()
        market = exchange.market(req.symbol)
        
        # 2. Set Leverage
        try:
             exchange.set_leverage(req.leverage, req.symbol)
        except: pass
        
        # 3. Calc Amount
        price = exchange.fetch_ticker(req.symbol)['last']
        amount_coins = req.amount_usd / price
        amount_precision = exchange.amount_to_precision(req.symbol, amount_coins)
        
        # 4. Execute Market Order
        order = exchange.create_market_order(req.symbol, req.side, amount_precision)
        
        entry_price = float(order.get('average') or order.get('price') or price)
        
        # 5. OCO (TP/SL)
        sl_id, tp_id = None, None
        exit_side = 'sell' if req.side == 'buy' else 'buy'
        
        if req.stop_loss > 0:
            sl_price = exchange.price_to_precision(req.symbol, req.stop_loss)
            sl_order = exchange.create_order(req.symbol, 'STOP_MARKET', exit_side, amount_precision, params={'stopPrice': sl_price, 'reduceOnly': True})
            sl_id = sl_order['id']
            
        if req.take_profit > 0:
            tp_price = exchange.price_to_precision(req.symbol, req.take_profit)
            tp_order = exchange.create_order(req.symbol, 'TAKE_PROFIT_MARKET', exit_side, amount_precision, params={'stopPrice': tp_price, 'reduceOnly': True})
            tp_id = tp_order['id']
            
        print(f"SUCCESS: Order {order['id']} Filled @ {entry_price}")
        
        # F. Log to Live Trades
        supabase.table("live_trades").insert({
            "user_id": req.user_id,
            "symbol": req.symbol,
            "side": req.side,
            "entry_price": entry_price,
            "size": amount_coins,
            "status": "OPEN",
            "entry_order_id": str(order['id']),
            "sl_order_id": str(sl_id) if sl_id else None,
            "tp_order_id": str(tp_id) if tp_id else None
        }).execute()
        
        # G. Notify Pusher
        if pusher_client:
            pusher_client.trigger('private-execution-' + req.user_id, 'order-filled', {
                'symbol': req.symbol,
                'price': entry_price,
                'side': req.side,
                'status': 'FILLED'
            })
            
        return {"status": "success", "order": order}

    except Exception as e:
        print(f"Execution Failed: {e}")
        # Notify Failure
        if pusher_client:
             pusher_client.trigger('private-execution-' + req.user_id, 'order-failed', {'error': str(e)})
        raise HTTPException(status_code=400, detail=str(e))
