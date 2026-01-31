"""
Script de diagnóstico para Railway - Verifica que todo esté configurado
"""
import os
import sys

print("=" * 70)
print("  RAILWAY DIAGNOSTIC")
print("=" * 70)

# 1. Python version
print(f"\n🐍 Python: {sys.version}")

# 2. Working directory
print(f"\n📁 Working Directory: {os.getcwd()}")
print(f"   Files: {os.listdir('.')}")

# 3. Environment variables
print("\n🔑 Environment Variables:")
env_vars = [
    "PORT",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "BINANCE_API_KEY",
    "PUSHER_APP_ID",
    "OPENAI_API_KEY",
    "PYTHONUNBUFFERED"
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive data
        if len(value) > 20:
            masked = value[:10] + "..." + value[-5:]
        else:
            masked = value
        print(f"   ✅ {var}: {masked}")
    else:
        print(f"   ❌ {var}: NOT SET")

# 4. Check data-engine directory
print("\n📂 Data Engine Directory:")
if os.path.exists("data-engine"):
    files = os.listdir("data-engine")
    print(f"   ✅ Exists ({len(files)} files)")
    critical_files = [
        "cosmos_worker.py",
        "nexus_api.py",
        "db.py",
        "scanner.py"
    ]
    for f in critical_files:
        path = os.path.join("data-engine", f)
        if os.path.exists(path):
            print(f"   ✅ {f}")
        else:
            print(f"   ❌ {f} MISSING")
else:
    print("   ❌ data-engine directory NOT FOUND")

# 5. Check dependencies
print("\n📦 Dependencies:")
try:
    import ccxt
    print("   ✅ ccxt")
except ImportError:
    print("   ❌ ccxt")

try:
    import fastapi
    print("   ✅ fastapi")
except ImportError:
    print("   ❌ fastapi")

try:
    import supabase
    print("   ✅ supabase")
except ImportError:
    print("   ❌ supabase")

try:
    import pusher
    print("   ✅ pusher")
except ImportError:
    print("   ❌ pusher")

# 6. Test Supabase connection
print("\n🔗 Testing Supabase Connection:")
try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if url and key:
        client = create_client(url, key)
        result = client.table("signals").select("id").limit(1).execute()
        print("   ✅ Supabase connection successful")
    else:
        print("   ❌ Supabase credentials missing")
except Exception as e:
    print(f"   ❌ Supabase connection failed: {e}")

print("\n" + "=" * 70)
print("  DIAGNOSTIC COMPLETE")
print("=" * 70)
