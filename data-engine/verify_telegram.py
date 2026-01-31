import requests
import sys

import os
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(parent_dir, '.env.local'))

# Parameters
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_test_alert():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    message = (
        "<b>🟢 NEXUS AI SYSTEM V2.5 ONLINE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📡 <b>Alert System:</b> CONNECTED\n"
        "🔐 <b>Auth Gate:</b> ACTIVE\n"
        "📊 <b>Dashboard:</b> READY\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Waiting for market signals...</i>\n\n"
        "🔗 <a href='https://nexus-app-v2.vercel.app/dashboard'>Open Terminal</a>"
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        print(f"Sending test message to {CHAT_ID}...")
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        print("✅ Success! Telegram message sent.")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Server response: {e.response.text}")

if __name__ == "__main__":
    send_test_alert()
