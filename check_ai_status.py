"""
Script de diagnóstico completo para verificar por qué no se generan señales
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(current_dir, '.env.local'))

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERROR: Variables de Supabase no configuradas")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 70)
print("  DIAGNÓSTICO COMPLETO - COSMOS AI")
print("=" * 70)

# 1. Verificar última señal
print("\n📊 1. ÚLTIMA ACTIVIDAD DE SEÑALES")
print("-" * 70)
try:
    signals = supabase.table("signals").select("*").order("created_at", desc=True).limit(5).execute()
    if signals.data:
        last_signal = signals.data[0]
        last_time = datetime.fromisoformat(last_signal['created_at'].replace('Z', '+00:00'))
        time_diff = datetime.now(timezone.utc) - last_time
        
        print(f"  Última señal: {last_signal['symbol']}")
        print(f"  Timestamp: {last_signal['created_at']}")
        print(f"  Hace: {time_diff.total_seconds() / 3600:.1f} horas")
        print(f"  Confianza: {last_signal.get('ai_confidence', 0)}%")
        print(f"  Tipo: {last_signal.get('direction', 'N/A')}")
        
        if time_diff.total_seconds() > 7200:  # 2 horas
            print(f"\n  ⚠️  ALERTA: No hay señales nuevas en {time_diff.total_seconds() / 3600:.1f} horas")
    else:
        print("  ❌ No hay señales en la base de datos")
except Exception as e:
    print(f"  ❌ Error al consultar señales: {e}")

# 2. Verificar Circuit Breaker
print("\n🔒 2. CIRCUIT BREAKER STATUS")
print("-" * 70)
try:
    # Verificar si existe el archivo de configuración
    circuit_config_path = os.path.join(current_dir, "circuit_breaker_config.json")
    if os.path.exists(circuit_config_path):
        import json
        with open(circuit_config_path, 'r') as f:
            config = json.load(f)
        print(f"  Estado: {config.get('enabled', False)}")
        print(f"  Pérdidas consecutivas: {config.get('consecutive_losses', 0)}")
        print(f"  Max pérdidas permitidas: {config.get('max_consecutive_losses', 3)}")
        
        if config.get('consecutive_losses', 0) >= config.get('max_consecutive_losses', 3):
            print("\n  🔴 CRÍTICO: Circuit Breaker ACTIVADO - Trading pausado")
    else:
        print("  ✅ Circuit Breaker no configurado (trading activo)")
except Exception as e:
    print(f"  ⚠️  Error al verificar Circuit Breaker: {e}")

# 3. Verificar parámetros del bot
print("\n⚙️  3. PARÁMETROS DEL BOT")
print("-" * 70)
try:
    params = supabase.table("bot_params").select("*").eq("active", True).limit(1).execute()
    if params.data:
        p = params.data[0]
        print(f"  Min Confidence: {p.get('min_confidence', 'N/A')}%")
        print(f"  Leverage: {p.get('leverage', 'N/A')}x")
        print(f"  Max Positions: {p.get('max_positions', 'N/A')}")
        print(f"  Risk per Trade: {p.get('risk_per_trade', 'N/A')}%")
        
        if p.get('min_confidence', 0) > 85:
            print(f"\n  ⚠️  ALERTA: Umbral de confianza muy alto ({p.get('min_confidence')}%)")
            print("     Esto puede estar bloqueando señales válidas")
    else:
        print("  ⚠️  No hay parámetros activos configurados")
except Exception as e:
    print(f"  ❌ Error al consultar parámetros: {e}")

# 4. Verificar wallet
print("\n💰 4. ESTADO DEL WALLET")
print("-" * 70)
try:
    wallet = supabase.table("bot_wallet").select("*").limit(1).execute()
    if wallet.data:
        w = wallet.data[0]
        print(f"  Balance: ${w.get('balance', 0):.2f}")
        print(f"  Equity: ${w.get('equity', 0):.2f}")
        print(f"  Total Trades: {w.get('total_trades', 0)}")
        
        if w.get('balance', 0) < 100:
            print("\n  ⚠️  ALERTA: Balance muy bajo")
    else:
        print("  ❌ No hay wallet configurado")
except Exception as e:
    print(f"  ❌ Error al consultar wallet: {e}")

# 5. Verificar posiciones abiertas
print("\n📈 5. POSICIONES ABIERTAS")
print("-" * 70)
try:
    positions = supabase.table("paper_positions").select("*").eq("status", "OPEN").execute()
    if positions.data:
        print(f"  Posiciones abiertas: {len(positions.data)}")
        for pos in positions.data[:3]:
            print(f"    - {pos.get('symbol')}: ${pos.get('pnl', 0):.2f} PnL")
    else:
        print("  ✅ No hay posiciones abiertas")
except Exception as e:
    print(f"  ❌ Error al consultar posiciones: {e}")

# 6. Verificar errores recientes
print("\n🚨 6. ERRORES RECIENTES")
print("-" * 70)
try:
    errors = supabase.table("error_logs").select("*").order("created_at", desc=True).limit(5).execute()
    if errors.data:
        for err in errors.data:
            timestamp = err.get('created_at', 'N/A')
            message = err.get('message', 'N/A')
            severity = err.get('severity', 'INFO')
            print(f"  [{severity}] {timestamp[:19]}: {message[:60]}")
    else:
        print("  ✅ No hay errores recientes")
except Exception as e:
    print(f"  ❌ Error al consultar logs: {e}")

# 7. Verificar Pusher
print("\n📡 7. CONFIGURACIÓN PUSHER (Realtime)")
print("-" * 70)
pusher_key = os.getenv("PUSHER_KEY")
pusher_cluster = os.getenv("PUSHER_CLUSTER")
pusher_app_id = os.getenv("PUSHER_APP_ID")

if pusher_key and pusher_cluster and pusher_app_id:
    print(f"  ✅ Pusher configurado")
    print(f"     App ID: {pusher_app_id}")
    print(f"     Cluster: {pusher_cluster}")
else:
    print("  ❌ Pusher NO configurado - Realtime no funcionará")

# 8. Verificar Binance
print("\n🔗 8. CONFIGURACIÓN BINANCE")
print("-" * 70)
binance_key = os.getenv("BINANCE_API_KEY")
trading_mode = os.getenv("TRADING_MODE", "PAPER")

if binance_key:
    print(f"  ✅ Binance API configurada")
    print(f"     Modo: {trading_mode}")
else:
    print("  ❌ Binance API NO configurada")

# RESUMEN Y RECOMENDACIONES
print("\n" + "=" * 70)
print("  RESUMEN Y RECOMENDACIONES")
print("=" * 70)

recommendations = []

# Verificar si hay señales recientes
try:
    signals = supabase.table("signals").select("created_at").order("created_at", desc=True).limit(1).execute()
    if signals.data:
        last_time = datetime.fromisoformat(signals.data[0]['created_at'].replace('Z', '+00:00'))
        time_diff = datetime.now(timezone.utc) - last_time
        if time_diff.total_seconds() > 7200:
            recommendations.append("🔴 CRÍTICO: Worker no está generando señales")
            recommendations.append("   → Ejecutar: python data-engine/cosmos_worker.py")
except:
    pass

# Verificar Circuit Breaker
try:
    if os.path.exists(circuit_config_path):
        with open(circuit_config_path, 'r') as f:
            config = json.load(f)
        if config.get('consecutive_losses', 0) >= config.get('max_consecutive_losses', 3):
            recommendations.append("🔴 CRÍTICO: Circuit Breaker activado")
            recommendations.append("   → Resetear: Editar circuit_breaker_config.json")
except:
    pass

# Verificar Pusher
if not (pusher_key and pusher_cluster):
    recommendations.append("🟡 ADVERTENCIA: Pusher no configurado")
    recommendations.append("   → Configurar variables PUSHER_* en .env.local")

if recommendations:
    for rec in recommendations:
        print(f"\n{rec}")
else:
    print("\n✅ Sistema operativo - Verificar logs del worker para más detalles")

print("\n" + "=" * 70)
print("  FIN DEL DIAGNÓSTICO")
print("=" * 70)
