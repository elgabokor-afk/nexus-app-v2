from db import insert_signal
import time

print("Testing Supabase Connection...")
insert_signal(
    symbol="TEST/USDT",
    price=12345.67,
    rsi=25.5,
    signal_type="TEST_BUY",
    confidence=100
)
print("Test Complete.")
