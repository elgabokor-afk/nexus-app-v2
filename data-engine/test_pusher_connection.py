import os
import pusher
from dotenv import load_dotenv

# Load Env
load_dotenv(dotenv_path='.env.local')

APP_ID = os.getenv("PUSHER_APP_ID")
KEY = os.getenv("NEXT_PUBLIC_PUSHER_KEY")
SECRET = os.getenv("PUSHER_SECRET")
CLUSTER = os.getenv("NEXT_PUBLIC_PUSHER_CLUSTER")

print(f"--- PUSHER DIAGNOSTIC ---")
print(f"APP_ID: {APP_ID}")
print(f"KEY: {KEY[:5]}...")
print(f"CLUSTER: {CLUSTER}")

if not all([APP_ID, KEY, SECRET, CLUSTER]):
    print("!!! CRITICAL: MISSING CREDENTIALS !!!")
    exit(1)

try:
    client = pusher.Pusher(
        app_id=APP_ID,
        key=KEY,
        secret=SECRET,
        cluster=CLUSTER,
        ssl=True
    )
    print("Client Initialized. Attempting Trigger...")
    
    # Trigger Test Event
    client.trigger('public-signals', 'test-event', {'message': 'Hello from Backend Diagnostic'})
    print(">>> SUCCESS: Event Sent to 'public-signals' channel.")
    
except Exception as e:
    print(f"!!! TRIGGER FAILED: {e}")
