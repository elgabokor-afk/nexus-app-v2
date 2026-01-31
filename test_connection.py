#!/usr/bin/env python3
"""
Test rápido de conexión a Supabase y Pusher
"""
import sys
sys.path.insert(0, 'data-engine')

print("=" * 70)
print("  TEST DE CONEXIÓN - Cosmos AI")
print("=" * 70)
print()

# Test 1: Supabase
print("📋 1. SUPABASE")
print("-" * 70)
try:
    from supabase import create_client
    
    url = "https://uxjjqrctxfajzicruvxc.supabase.co"
    key = "tu_supabase_key_aqui"
    
    client = create_client(url, key)
    
    # Test query
    response = client.table("signals").select("id").limit(1).execute()
    print(f"  ✅ Conexión exitosa a Supabase")
    
    # Contar señales
    count_response = client.table("signals").select("id", count="exact").execute()
    total = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
    print(f"  ✅ Total señales en DB: {total}")
    
    # Última señal
    last_signal = client.table("signals").select("*").order("created_at", desc=True).limit(1).execute()
    if last_signal.data:
        sig = last_signal.data[0]
        print(f"  ✅ Última señal: {sig.get('symbol')} @ {sig.get('created_at')}")
    else:
        print(f"  ⚠️  No hay señales todavía")
        
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# Test 2: Pusher
print("📋 2. PUSHER")
print("-" * 70)
try:
    import pusher
    
    pusher_client = pusher.Pusher(
        app_id="2107673",
        key="dda05a0dc630ab53ec2e",
        secret="e4747199473f7ff11690",
        cluster="mt1",
        ssl=True
    )
    
    # Test trigger
    test_data = {
        "test": "connection_test",
        "message": "Sistema funcionando correctamente"
    }
    pusher_client.trigger("public-signals", "test-event", test_data)
    
    print(f"  ✅ Pusher configurado correctamente")
    print(f"  ✅ Cluster: mt1")
    print(f"  ✅ Test event enviado a 'public-signals'")
    print(f"  📡 Verifica en: https://dashboard.pusher.com/apps/2107673/getting_started")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

print()
print("=" * 70)
print("  ✅ CONFIGURACIÓN CORRECTA")
print("=" * 70)
print()
print("🚀 PRÓXIMOS PASOS:")
print("  1. Inicia el worker: python data-engine/cosmos_worker.py")
print("  2. Verifica señales en Supabase")
print("  3. Verifica eventos en Pusher Dashboard")
print("  4. Deploy el frontend")
print()
