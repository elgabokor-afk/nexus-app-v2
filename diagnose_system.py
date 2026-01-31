#!/usr/bin/env python3
"""
COSMOS AI - Diagnóstico Completo del Sistema
Verifica: DB, Pusher, Worker, Señales
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("  COSMOS AI - DIAGNÓSTICO COMPLETO")
print("=" * 70)
print()

# 1. Verificar Variables de Entorno
print("📋 1. VARIABLES DE ENTORNO")
print("-" * 70)

required_vars = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "PUSHER_APP_ID",
    "PUSHER_KEY",
    "PUSHER_SECRET",
    "PUSHER_CLUSTER"
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"  ✅ {var}: {masked}")
    else:
        print(f"  ❌ {var}: FALTA")
        missing_vars.append(var)

if missing_vars:
    print(f"\n⚠️  FALTAN {len(missing_vars)} variables críticas")
    print("   Verifica tu archivo .env.local")
else:
    print("\n✅ Todas las variables configuradas")

print()

# 2. Verificar Conexión a Supabase
print("📋 2. CONEXIÓN A SUPABASE")
print("-" * 70)

try:
    from supabase import create_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if url and key:
        client = create_client(url, key)
        
        # Test query
        response = client.table("signals").select("id").limit(1).execute()
        print(f"  ✅ Conexión exitosa")
        print(f"  ✅ Tabla 'signals' accesible")
        
        # Contar señales
        count_response = client.table("signals").select("id", count="exact").execute()
        total = count_response.count if hasattr(count_response, 'count') else 0
        print(f"  📊 Total señales en DB: {total}")
        
        # Última señal
        last_signal = client.table("signals").select("*").order("created_at", desc=True).limit(1).execute()
        if last_signal.data:
            sig = last_signal.data[0]
            print(f"  📊 Última señal: {sig.get('symbol')} - {sig.get('created_at')}")
        else:
            print(f"  ⚠️  No hay señales en la base de datos")
            
    else:
        print(f"  ❌ Variables de Supabase no configuradas")
        
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# 3. Verificar Pusher
print("📋 3. PUSHER (Realtime)")
print("-" * 70)

try:
    import pusher
    
    app_id = os.getenv("PUSHER_APP_ID")
    key = os.getenv("PUSHER_KEY")
    secret = os.getenv("PUSHER_SECRET")
    cluster = os.getenv("PUSHER_CLUSTER")
    
    if all([app_id, key, secret, cluster]):
        pusher_client = pusher.Pusher(
            app_id=app_id,
            key=key,
            secret=secret,
            cluster=cluster,
            ssl=True
        )
        
        # Test trigger
        test_data = {"test": "diagnostic", "timestamp": "now"}
        pusher_client.trigger("public-signals", "test-event", test_data)
        
        print(f"  ✅ Pusher configurado")
        print(f"  ✅ Cluster: {cluster}")
        print(f"  ✅ Test event enviado a 'public-signals'")
        print(f"  📡 Verifica en: https://dashboard.pusher.com/")
    else:
        print(f"  ❌ Variables de Pusher no configuradas")
        
except ImportError:
    print(f"  ❌ Librería 'pusher' no instalada")
    print(f"     Ejecuta: pip install pusher")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# 4. Verificar Worker Status
print("📋 4. WORKER STATUS")
print("-" * 70)

try:
    # Verificar si el worker está corriendo
    import psutil
    
    worker_running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'cosmos_worker.py' in ' '.join(cmdline):
                worker_running = True
                print(f"  ✅ Worker corriendo (PID: {proc.info['pid']})")
                break
        except:
            pass
    
    if not worker_running:
        print(f"  ⚠️  Worker NO está corriendo")
        print(f"     Inicia con: python data-engine/cosmos_worker.py")
        
except ImportError:
    print(f"  ⚠️  No se puede verificar (psutil no instalado)")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

print()

# 5. Verificar Última Actividad
print("📋 5. ÚLTIMA ACTIVIDAD")
print("-" * 70)

try:
    if url and key:
        # Últimas señales (últimas 24h)
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        recent = client.table("signals")\
            .select("symbol, created_at, ai_confidence")\
            .gte("created_at", yesterday)\
            .order("created_at", desc=True)\
            .limit(5)\
            .execute()
        
        if recent.data:
            print(f"  📊 Señales últimas 24h: {len(recent.data)}")
            for sig in recent.data:
                print(f"     - {sig['symbol']}: {sig.get('ai_confidence', 0):.2f} @ {sig['created_at']}")
        else:
            print(f"  ⚠️  No hay señales en las últimas 24 horas")
            print(f"     El worker puede no estar generando señales")
            
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# 6. Recomendaciones
print("=" * 70)
print("📋 RECOMENDACIONES")
print("=" * 70)

if missing_vars:
    print("\n🔴 CRÍTICO:")
    print("  1. Configura las variables faltantes en .env.local")
    print(f"     Faltan: {', '.join(missing_vars)}")

print("\n🟡 VERIFICACIONES:")
print("  1. ¿El worker está corriendo?")
print("     → python data-engine/cosmos_worker.py")
print()
print("  2. ¿El frontend está desplegado?")
print("     → Verifica en Railway/Vercel/Google Cloud")
print()
print("  3. ¿Pusher está recibiendo eventos?")
print("     → https://dashboard.pusher.com/ → Debug Console")
print()
print("  4. ¿El frontend está suscrito al canal correcto?")
print("     → Verifica src/hooks/usePusher.ts")

print()
print("=" * 70)
print("  FIN DEL DIAGNÓSTICO")
print("=" * 70)
