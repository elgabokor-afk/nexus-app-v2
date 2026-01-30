import os
import sys
import json
import time

# Add data-engine to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from db import insert_signal, client

def verify_pipeline():
    print("/// N E X U S  P I P E L I N E  V E R I F I C A T I O N ///")
    
    test_signal = {
        "symbol": "BTC/USDT",
        "price": 45000.0,
        "rsi": 35.0,
        "signal_type": "STRONG BUY (TEST)",
        "confidence": 95,
        "stop_loss": 44000.0,
        "take_profit": 47000.0,
        "academic_thesis_id": 1, # Valid BigInt
        "nli_safety_score": 0.98
    }
    
    print(f"\n1. Sending test signal for {test_signal['symbol']}...")
    try:
        sig_id = insert_signal(
            symbol=test_signal['symbol'],
            price=test_signal['price'],
            rsi=test_signal['rsi'],
            signal_type=test_signal['signal_type'],
            confidence=test_signal['confidence'],
            stop_loss=test_signal['stop_loss'],
            take_profit=test_signal['take_profit'],
            academic_thesis_id=test_signal['academic_thesis_id'],
            nli_safety_score=test_signal['nli_safety_score']
        )
        
        if sig_id and sig_id != "queued_v9":
            print(f"   [SUCCESS] Signal saved to Supabase 'signals'. ID: {sig_id}")
        else:
            print(f"   [FAIL] Signal not saved or returned invalid ID: {sig_id}")
            return
            
        print("\n2. Pipeline Verification Complete.")
        print("   Check Redis 'trade_signal' channel for broadcast.")
        print("   Check Supabase Dashboard for the new Signal Card.")
        
    except Exception as e:
        print(f"   [CRITICAL ERROR] {e}")

if __name__ == "__main__":
    verify_pipeline()
