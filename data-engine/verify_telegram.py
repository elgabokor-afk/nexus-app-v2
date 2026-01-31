import requests
import sys

# User provided credentials
TOKEN = "8119493028:AAGw4Zb0OLT8DstzJJy7ThxN4mMvhuN9unw"
CHAT_ID = "-1003537646096"

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
