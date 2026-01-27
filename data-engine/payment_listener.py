import os
import time
import requests
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PAYMENT LISTENER] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase Setup
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials missing. Exiting.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Constants
# TRC20 USDT Contract Address
USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
# Target Wallet to Monitor (The Service Provider)
TARGET_WALLET = "TC3zTgbRdAXKvy9sikUTeKdAr1bmsqR5p7"
# TronScan API (Public)
TRONSCAN_API = "https://apilist.tronscan.org/api/token_trc20/transfers"

CHECK_INTERVAL = 30 # Seconds

def fetch_recent_transactions():
    """Fetches key parameters for recent USDT transfers to our wallet."""
    try:
        params = {
            "limit": 20,
            "start": 0,
            "contract_address": USDT_CONTRACT,
            "toAddress": TARGET_WALLET
        }
        headers = {
            "User-Agent": "NexusWorker/1.0"
        }
        
        response = requests.get(TRONSCAN_API, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('token_transfers', [])
        else:
            logger.warning(f"TronScan API Error: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Failed to fetch transactions: {e}")
        return []

def process_transaction(tx):
    """
    Verifies a transaction and logs it.
    tx object structure from TronScan: column names typically include 'transaction_id', 'quant', 'from_address'...
    """
    try:
        tx_hash = tx.get('transaction_id')
        sender = tx.get('from_address')
        amount_raw = float(tx.get('quant', 0)) # USDT has 6 decimals
        amount_usdt = amount_raw / 1_000_000
        
        # 1. Check if already processed
        res = supabase.table("payment_logs").select("id").eq("tx_hash", tx_hash).execute()
        if res.data:
            return # Already handled
            
        logger.info(f"New Transaction Detected: {amount_usdt} USDT from {sender} (TX: {tx_hash})")
        
        # 2. Log to Database
        log_data = {
            "tx_hash": tx_hash,
            "sender_address": sender,
            "amount": amount_usdt,
            "currency": "USDT",
            "status": "UNCLAIMED", # Waiting for user to claim via TXID
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table("payment_logs").insert(log_data).execute()
        logger.info(f"   >>> Logged payment: {tx_hash}")
        
    except Exception as e:
        logger.error(f"Error processing transaction {tx.get('transaction_id')}: {e}")

def main_loop():
    logger.info(f"--- PAYMENT LISTENER STARTED [{TARGET_WALLET}] ---")
    
    while True:
        try:
            transactions = fetch_recent_transactions()
            
            if transactions:
                # Process latest first
                for tx in transactions:
                    process_transaction(tx)
            
            logger.info("Heartbeat: Scan complete.")
            
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
