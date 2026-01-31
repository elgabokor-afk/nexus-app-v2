import os
from dotenv import load_dotenv
from db import insert_signal
import random

# Load env from parent directory
load_dotenv(dotenv_path='../.env.local')

# Sample Data
samples = [
    {"symbol": "BTC/USD", "price": 42150.50, "rsi": 28.5, "signal": "STRONG BUY (Oversold)", "conf": 95},
    {"symbol": "ETH/USD", "price": 2250.75, "rsi": 72.1, "signal": "STRONG SELL (Overbought)", "conf": 88},
    {"symbol": "SOL/USD", "price": 95.20, "rsi": 45.0, "signal": "NEUTRAL", "conf": 0},
    {"symbol": "USDT/USD", "price": 1.00, "rsi": 50.1, "signal": "NEUTRAL", "conf": 0},
]

print("Seeding Supabase with sample signals...")

for s in samples:
    insert_signal(
        symbol=s["symbol"],
        price=s["price"],
        rsi=s["rsi"],
        signal_type=s["signal"],
        confidence=s["conf"]
    )

print("Done! Check your dashboard.")
