
import os
import time
from dotenv import load_dotenv
from db import insert_signal
from datetime import datetime

load_dotenv()

print("/// SEEDING LIVE TEST SIGNALS (ETH & SOL) ///")

# 1. ETH Signal
print("Injecting ETH Signal...")
insert_signal(
    symbol="ETH/USD",
    price=2250.50,
    rsi=25.5,
    signal_type="STRONG BUY (Oversold Test)",
    confidence=95,
    stop_loss=2200.00,
    take_profit=2350.00
)

time.sleep(1)

# 2. SOL Signal
print("Injecting SOL Signal...")
insert_signal(
    symbol="SOL/USD",
    price=98.75,
    rsi=75.2,
    signal_type="STRONG SELL (Overbought Test)",
    confidence=88,
    stop_loss=102.00,
    take_profit=92.50
)

print("Done! Check Dashboard.")
