import os
from dotenv import load_dotenv
from db import insert_signal

# Load env from parent directory
load_dotenv(dotenv_path='../.env.local')

print("Injecting PREMIUM SaaS Signal...")

# Premium Long Signal
insert_signal(
    symbol="ETH/USD",
    price=2250.00,
    rsi=25.5,
    signal_type="STRONG BUY (Oversold)",
    confidence=98,
    stop_loss=2205.00,  # 2% below
    take_profit=2340.00 # 4% above
)

# Premium Short Signal
insert_signal(
    symbol="SOL/USD",
    price=105.50,
    rsi=78.2,
    signal_type="STRONG SELL (Overbought)",
    confidence=92,
    stop_loss=107.60,
    take_profit=101.30
)

print("Done! Check the dashboard for the new cards.")
