import asyncio
import json
import websockets
from datetime import datetime, timezone
from db import insert_signal, log_error

# Thresholds
MIN_LIQ_USD = 50000 # Minimum single liquidation event size to trigger logic
CASCADE_THRESHOLD = 3 # Number of large liquidations in 1 min to trigger "Cascade"

liquidation_cache = {}

async def process_liquidation(data):
    try:
        # data structure: { "e": "forceOrder", "o": { ... } }
        order = data.get('o', {})
        symbol = order.get('s')
        side = order.get('S') # SELL = Long Liquidation, BUY = Short Liquidation
        qty = float(order.get('q', 0))
        price = float(order.get('p', 0))
        amount_usd = qty * price
        
        # Only track significant liquidations
        if amount_usd < MIN_LIQ_USD:
            return

        # "SELL" order means a LONG was liquidated. We want to BUY the dip.
        # "BUY" order means a SHORT was liquidated. We want to SELL the top.
        trade_signal = "BUY" if side == "SELL" else "SELL"
        signal_type = "LIQ_BUY_REBOUND" if side == "SELL" else "LIQ_SELL_REBOUND"
        
        print(f"   🌊 [LIQUIDATION] {symbol} {side} ${amount_usd:,.0f} @ {price}")
        
        # Simple Logic: Insert Signal immediately for huge single orders (> $100k)
        if amount_usd > 100000:
            confidence = 95 # High confidence for massive nukes
            
            insert_signal(
                symbol=symbol,
                price=price,
                rsi=50, # Placeholder, scanner might enrich later
                signal_type=signal_type,
                confidence=confidence,
                stop_loss=0, # Engine will calculate ATR SL
                take_profit=0,
                atr_value=0
            )
            print(f"      >>> SIGNAL FIRED: {signal_type} {symbol} (Whale Liq)")

    except Exception as e:
        print(f"Error processing luquidation: {e}")

async def liquidation_scanner():
    url = "wss://fstream.binance.com/ws/!forceOrder@arr"
    print(f"--- LIQUIDATION HUNTER V110 ACTIVATED ---")
    print(f"--- Listening for cascades > ${MIN_LIQ_USD:,.0f} ---")
    
    async for websocket in websockets.connect(url):
        try:
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                await process_liquidation(data)
        except websockets.ConnectionClosed:
            print("WebSocket closed, reconnecting...")
            continue
        except Exception as e:
            print(f"WebSocket Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(liquidation_scanner())
