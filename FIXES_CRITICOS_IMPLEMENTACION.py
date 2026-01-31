# ============================================================================
# COSMOS AI - CORRECCIONES CRÍTICAS PARA PRODUCCIÓN
# Fecha: 31 de Enero, 2026
# Auditor: Kiro AI System Architect
# ============================================================================

# ============================================================================
# FIX 1: RESOLVER SCOPE DE WHALE_MONITOR
# Archivo: data-engine/cosmos_worker.py
# Líneas: 40-66
# ============================================================================

# ANTES (INCORRECTO):
"""
try:
    from whales_monitor import WhaleMonitor
    whale_monitor = WhaleMonitor()  # ❌ Scope local
except ImportError as e:
    logger.warning(f"Engine import error: {e}")
"""

# DESPUÉS (CORRECTO):
"""
# GLOBAL SCOPE (Línea 40)
whale_monitor = None
redis_engine = None
scanner_engine = None
macro_brain = None
quant_engine = None
live_trader = None

try:
    from cosmos_engine import brain
except ImportError as e:
    logger.warning(f"Cosmos Brain missing: {e}")

try:
    from redis_engine import redis_engine
except ImportError as e:
    logger.warning(f"Redis Engine missing: {e}")

try:
    from macro_feed import macro_brain
except ImportError as e:
    logger.warning(f"Macro Feed missing: {e}")

try:
    from cosmos_quant import quant_engine
except ImportError as e:
    logger.warning(f"Quant Engine missing: {e}")
    
try:
    from binance_engine import live_trader
    from dex_scanner import DEXScanner
    from whales_monitor import WhaleMonitor  # ✅ Import correcto
    from nexus_indexer import NexusIndexer
    from evm_indexer import EVMIndexer
    from cosmos_validator import validator as academic_validator
    from db import insert_signal, insert_analytics
    
    dex_scanner = DEXScanner()
    whale_monitor = WhaleMonitor()  # ✅ Asignación global
    nexus_indexer = NexusIndexer()
    evm_indexer_eth = EVMIndexer(chain="ethereum")
    evm_indexer_base = EVMIndexer(chain="base")
    
    logger.info("✅ All engines initialized successfully")
except ImportError as e:
    logger.warning(f"Engine import error: {e}")

# En main_loop() (línea 396, 518):
if whale_monitor:  # ✅ Check antes de usar
    whale_alerts = whale_monitor.scan_all_gatekeepers()
else:
    whale_alerts = []
    logger.debug("Whale monitor unavailable, skipping whale sentiment")
"""

# ============================================================================
# FIX 2: ENDURECER VALIDACIÓN ACADÉMICA
# Archivo: data-engine/cosmos_engine.py
# Método: decide_trade()
# Líneas: 280-295
# ============================================================================

# ANTES (DEMASIADO PERMISIVO):
"""
validation_result = validator.validate_signal_logic(thesis_context)

if not validation_result['approved']:
    if prob < 0.65:  # ❌ Bypass fácil
        return False, prob, f"REJECTED by PhD: {validation_result['reason']}"
    else:
        print(f"[PhD BYPASS] Academic support missing, but AI Confidence sufficient.")
"""

# DESPUÉS (ENDURECIDO):
"""
# Pesos por universidad (basado en ranking QS 2026)
UNIVERSITY_WEIGHTS = {
    'MIT': 1.15,
    'Harvard': 1.12,
    'Oxford': 1.10,
    'Stanford': 1.08,
    'Cambridge': 1.07,
    'Unknown': 1.0
}

validation_result = validator.validate_signal_logic(
    thesis_context,
    symbol=symbol,
    direction=signal_type,
    technical_context=features
)

if not validation_result['approved']:
    # Penalizar confianza en lugar de bypass total
    penalty = 0.30 if prob > 0.80 else 0.20
    original_prob = prob
    prob *= (1 - penalty)
    
    print(f"   [PhD PENALTY] {symbol}: No academic support found.")
    print(f"   [PhD PENALTY] Confidence reduced by {penalty*100:.0f}%: {original_prob*100:.1f}% -> {prob*100:.1f}%")
    
    # Si después de penalización sigue siendo bajo, rechazar
    if prob < min_conf:
        return False, prob, f"REJECTED: Confidence {prob*100:.1f}% < {min_conf*100:.1f}% after PhD penalty. Reason: {validation_result['reason']}"
    
    # Permitir pero con advertencia
    print(f"   [PhD WARNING] Trade allowed but flagged as HIGH RISK")

# Boost si hay validación académica
if validation_result['approved']:
    university = validation_result.get('university', 'Unknown')
    weight = UNIVERSITY_WEIGHTS.get(university, 1.0)
    boost = 0.10 * weight
    original_prob = prob
    prob += boost
    
    print(f"   [PhD VALIDATED] {symbol}: +{boost*100:.1f}% boost from {university}")
    print(f"   [PhD VALIDATED] Confidence: {original_prob*100:.1f}% -> {prob*100:.1f}%")
    print(f"   [PhD VALIDATED] Citation: {validation_result['citations'][0] if validation_result['citations'] else 'N/A'}")
    print(f"   [PhD VALIDATED] P-Value: {validation_result.get('p_value', 1.0):.4f}")

# Guardar metadata para DB
self.last_p_value = validation_result.get('p_value', 1.0)
self.last_thesis_id = validation_result.get('thesis_id', None)
self.last_university = university
"""

# ============================================================================
# FIX 3: IMPLEMENTAR CIRCUIT BREAKER
# Archivo: data-engine/circuit_breaker.py (NUEVO)
# ============================================================================

"""
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('.env.local')

class CircuitBreaker:
    '''
    Circuit Breaker para protección de capital.
    Implementa 3 niveles de protección:
    1. Daily Loss Limit (5% del capital)
    2. Consecutive Losses (5 trades seguidos)
    3. Drawdown Limit (10% desde peak)
    '''
    
    def __init__(self, config_path='circuit_breaker_config.json'):
        self.config_path = config_path
        self.load_config()
        
        # Estado del circuit breaker
        self.daily_pnl = 0
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.is_tripped = False
        self.trip_reason = None
        
        # Peak tracking para drawdown
        self.peak_capital = self.initial_capital
        self.current_capital = self.initial_capital
        
        # Reset diario
        self.last_reset_date = datetime.now().date()
    
    def load_config(self):
        '''Carga configuración desde archivo o usa defaults'''
        default_config = {
            'initial_capital': 10000,
            'max_daily_loss_pct': 5.0,
            'max_consecutive_losses': 5,
            'max_drawdown_pct': 10.0,
            'cooldown_minutes': 60,
            'auto_reset_daily': True
        }
        
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                default_config.update(config)
        
        self.initial_capital = default_config['initial_capital']
        self.max_daily_loss_pct = default_config['max_daily_loss_pct']
        self.max_consecutive_losses = default_config['max_consecutive_losses']
        self.max_drawdown_pct = default_config['max_drawdown_pct']
        self.cooldown_minutes = default_config['cooldown_minutes']
        self.auto_reset_daily = default_config['auto_reset_daily']
    
    def check_daily_reset(self):
        '''Reset automático a medianoche'''
        if not self.auto_reset_daily:
            return
        
        today = datetime.now().date()
        if today > self.last_reset_date:
            print(f"   [CIRCUIT BREAKER] Daily reset triggered")
            self.daily_pnl = 0
            self.last_reset_date = today
    
    def check_trade(self, proposed_risk_usd=None):
        '''
        Verifica si un trade puede ejecutarse.
        
        Args:
            proposed_risk_usd: Riesgo del trade propuesto (opcional)
        
        Returns:
            (bool, str): (puede_ejecutar, razón)
        '''
        self.check_daily_reset()
        
        # 1. Check si ya está tripped
        if self.is_tripped:
            # Verificar si cooldown ha pasado
            if self.last_loss_time:
                elapsed = (datetime.now() - self.last_loss_time).total_seconds() / 60
                if elapsed >= self.cooldown_minutes:
                    print(f"   [CIRCUIT BREAKER] Cooldown period ended. Resetting...")
                    self.reset()
                else:
                    remaining = self.cooldown_minutes - elapsed
                    return False, f"Circuit breaker active. Cooldown: {remaining:.1f} min remaining"
            
            return False, f"Circuit breaker tripped: {self.trip_reason}"
        
        # 2. Daily Loss Limit
        loss_pct = abs(self.daily_pnl / self.current_capital) * 100
        if self.daily_pnl < 0 and loss_pct >= self.max_daily_loss_pct:
            self.trip(f"Daily loss limit exceeded: {loss_pct:.2f}% >= {self.max_daily_loss_pct}%")
            return False, self.trip_reason
        
        # 3. Consecutive Losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.trip(f"Consecutive losses limit: {self.consecutive_losses} trades")
            return False, self.trip_reason
        
        # 4. Drawdown Limit
        drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        if drawdown_pct >= self.max_drawdown_pct:
            self.trip(f"Maximum drawdown exceeded: {drawdown_pct:.2f}% >= {self.max_drawdown_pct}%")
            return False, self.trip_reason
        
        # 5. Proposed Risk Check (opcional)
        if proposed_risk_usd:
            if proposed_risk_usd > (self.current_capital * 0.02):  # Max 2% risk per trade
                return False, f"Proposed risk ${proposed_risk_usd:.2f} exceeds 2% of capital"
        
        return True, "OK"
    
    def record_trade(self, pnl_usd):
        '''
        Registra el resultado de un trade.
        
        Args:
            pnl_usd: PnL del trade en USD (positivo = ganancia, negativo = pérdida)
        '''
        self.daily_pnl += pnl_usd
        self.current_capital += pnl_usd
        
        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        # Track consecutive losses
        if pnl_usd < 0:
            self.consecutive_losses += 1
            self.last_loss_time = datetime.now()
            print(f"   [CIRCUIT BREAKER] Loss recorded. Consecutive: {self.consecutive_losses}")
        else:
            self.consecutive_losses = 0
            print(f"   [CIRCUIT BREAKER] Win recorded. Consecutive losses reset.")
        
        # Log estado
        loss_pct = abs(self.daily_pnl / self.current_capital) * 100 if self.daily_pnl < 0 else 0
        drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        
        print(f"   [CIRCUIT BREAKER] Daily PnL: ${self.daily_pnl:.2f} ({loss_pct:.2f}% loss)")
        print(f"   [CIRCUIT BREAKER] Drawdown: {drawdown_pct:.2f}% (Max: {self.max_drawdown_pct}%)")
    
    def trip(self, reason):
        '''Activa el circuit breaker'''
        self.is_tripped = True
        self.trip_reason = reason
        print(f"\n{'='*60}")
        print(f"🚨 CIRCUIT BREAKER TRIPPED 🚨")
        print(f"Reason: {reason}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Enviar alerta a Telegram
        try:
            from telegram_utils import TelegramAlerts
            tg = TelegramAlerts()
            tg.send_alert(f"⚠️ TRADING HALTED\\n\\nReason: {reason}\\nTime: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"   [CIRCUIT BREAKER] Failed to send Telegram alert: {e}")
    
    def reset(self):
        '''Reset manual del circuit breaker'''
        self.consecutive_losses = 0
        self.is_tripped = False
        self.trip_reason = None
        print(f"   [CIRCUIT BREAKER] Manual reset completed")
    
    def get_status(self):
        '''Retorna estado actual del circuit breaker'''
        loss_pct = abs(self.daily_pnl / self.current_capital) * 100 if self.daily_pnl < 0 else 0
        drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        
        return {
            'is_tripped': self.is_tripped,
            'trip_reason': self.trip_reason,
            'daily_pnl': self.daily_pnl,
            'daily_loss_pct': loss_pct,
            'consecutive_losses': self.consecutive_losses,
            'current_capital': self.current_capital,
            'peak_capital': self.peak_capital,
            'drawdown_pct': drawdown_pct,
            'limits': {
                'max_daily_loss_pct': self.max_daily_loss_pct,
                'max_consecutive_losses': self.max_consecutive_losses,
                'max_drawdown_pct': self.max_drawdown_pct
            }
        }

# Singleton instance
circuit_breaker = CircuitBreaker()

if __name__ == "__main__":
    # Test
    print("Testing Circuit Breaker...")
    
    cb = CircuitBreaker()
    
    # Simular trades
    print("\\n1. Trade 1: -$100")
    cb.record_trade(-100)
    can_trade, reason = cb.check_trade()
    print(f"Can trade: {can_trade} ({reason})")
    
    print("\\n2. Trade 2: -$150")
    cb.record_trade(-150)
    can_trade, reason = cb.check_trade()
    print(f"Can trade: {can_trade} ({reason})")
    
    print("\\n3. Trade 3: +$200")
    cb.record_trade(200)
    can_trade, reason = cb.check_trade()
    print(f"Can trade: {can_trade} ({reason})")
    
    print("\\nStatus:")
    import json
    print(json.dumps(cb.get_status(), indent=2))
"""

# ============================================================================
# FIX 4: INTEGRAR CIRCUIT BREAKER EN COSMOS_WORKER
# Archivo: data-engine/cosmos_worker.py
# Método: main_loop()
# ============================================================================

"""
# Al inicio del archivo (después de imports)
from circuit_breaker import circuit_breaker

def main_loop():
    logger.info("--- COSMOS AI WORKER STARTED [RAILWAY MODE] ---")
    
    # ... código existente ...
    
    while True:
        try:
            # ✅ CHECK CIRCUIT BREAKER ANTES DE ESCANEAR
            can_trade, reason = circuit_breaker.check_trade()
            if not can_trade:
                logger.warning(f"[CIRCUIT BREAKER] Trading paused: {reason}")
                time.sleep(60)  # Wait 1 minute before checking again
                continue
            
            # ... resto del código de escaneo ...
            
            for sig in generated_signals:
                # ✅ CHECK CIRCUIT BREAKER ANTES DE CADA SEÑAL
                can_trade, reason = circuit_breaker.check_trade()
                if not can_trade:
                    logger.warning(f"[CIRCUIT BREAKER] Signal {sig['symbol']} blocked: {reason}")
                    break  # Stop processing signals
                
                sig_id = save_signal_to_db(sig)
                
                if sig_id:
                    # ... código de broadcast ...
                    logger.info(f"Published Signal: {sig['symbol']}")
            
            # ... resto del loop ...
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as e:
            logger.error(f"Critical Worker Error: {e}")
            traceback.print_exc()
            time.sleep(10)
"""

# ============================================================================
# FIX 5: ACTUALIZAR PAPER_TRADER PARA REPORTAR AL CIRCUIT BREAKER
# Archivo: data-engine/paper_trader.py
# ============================================================================

"""
from circuit_breaker import circuit_breaker

class PaperTrader:
    def close_position(self, position_id, exit_price, reason="MANUAL"):
        # ... código existente para cerrar posición ...
        
        # Calcular PnL
        pnl = self.calculate_pnl(position)
        
        # ✅ REPORTAR AL CIRCUIT BREAKER
        circuit_breaker.record_trade(pnl)
        
        logger.info(f"Position {position_id} closed. PnL: ${pnl:.2f}")
        
        # Check si circuit breaker se activó
        status = circuit_breaker.get_status()
        if status['is_tripped']:
            logger.critical(f"🚨 Circuit Breaker activated after this trade!")
        
        return pnl
"""

# ============================================================================
# FIX 6: IMPLEMENTAR VPIN CORRECTO
# Archivo: data-engine/cosmos_validator.py
# Método: calculate_vpin()
# ============================================================================

"""
def calculate_vpin_accurate(self, trades_df, bucket_size=50, window=50):
    '''
    Implementación correcta de VPIN según Easley et al. (2012)
    
    Args:
        trades_df: DataFrame con columnas ['timestamp', 'side', 'volume', 'price']
        bucket_size: Volumen por bucket (default: 50 unidades)
        window: Número de buckets para calcular VPIN (default: 50)
    
    Returns:
        float: VPIN score (0 a 1, >0.6 indica toxicidad)
    '''
    if trades_df.empty or len(trades_df) < window:
        return 0
    
    # 1. Crear buckets de volumen sincronizados
    buckets = []
    current_bucket = {'buy': 0, 'sell': 0, 'timestamp': None}
    cumulative_vol = 0
    
    for _, trade in trades_df.iterrows():
        if current_bucket['timestamp'] is None:
            current_bucket['timestamp'] = trade['timestamp']
        
        side = 'buy' if trade['side'] in ['buy', 'BUY', 1] else 'sell'
        current_bucket[side] += trade['volume']
        cumulative_vol += trade['volume']
        
        # Cuando el bucket alcanza el tamaño objetivo
        if cumulative_vol >= bucket_size:
            buckets.append(current_bucket.copy())
            current_bucket = {'buy': 0, 'sell': 0, 'timestamp': trade['timestamp']}
            cumulative_vol = 0
    
    # 2. Calcular VPIN sobre los últimos N buckets
    if len(buckets) < window:
        return 0
    
    recent_buckets = buckets[-window:]
    
    # VPIN = Average(|V_buy - V_sell| / (V_buy + V_sell))
    vpin_sum = 0
    valid_buckets = 0
    
    for bucket in recent_buckets:
        total_vol = bucket['buy'] + bucket['sell']
        if total_vol > 0:
            imbalance = abs(bucket['buy'] - bucket['sell'])
            vpin_sum += (imbalance / total_vol)
            valid_buckets += 1
    
    if valid_buckets == 0:
        return 0
    
    vpin = vpin_sum / valid_buckets
    
    # Log si VPIN es alto
    if vpin > 0.6:
        print(f"   [VPIN ALERT] High toxicity detected: {vpin:.3f} (Threshold: 0.6)")
    
    return vpin
"""

# ============================================================================
# CONFIGURACIÓN RECOMENDADA
# Archivo: circuit_breaker_config.json (NUEVO)
# ============================================================================

CIRCUIT_BREAKER_CONFIG = {
    "initial_capital": 10000,
    "max_daily_loss_pct": 5.0,
    "max_consecutive_losses": 5,
    "max_drawdown_pct": 10.0,
    "cooldown_minutes": 60,
    "auto_reset_daily": True
}

# ============================================================================
# ÍNDICES DE BASE DE DATOS RECOMENDADOS
# Ejecutar en Supabase SQL Editor
# ============================================================================

SQL_INDEXES = """
-- Optimización de consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_paper_positions_symbol 
ON paper_positions(symbol);

CREATE INDEX IF NOT EXISTS idx_paper_positions_status_closed 
ON paper_positions(status, closed_at DESC) 
WHERE status = 'CLOSED';

CREATE INDEX IF NOT EXISTS idx_signals_symbol_created 
ON signals(symbol, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_signals_confidence 
ON signals(ai_confidence DESC) 
WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_academic_papers_university 
ON academic_papers(university, published_date DESC);

-- Índice para búsqueda vectorial (si no existe)
CREATE INDEX IF NOT EXISTS idx_academic_chunks_embedding 
ON academic_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Estadísticas para el optimizador
ANALYZE paper_positions;
ANALYZE signals;
ANALYZE academic_papers;
ANALYZE academic_chunks;
"""

print("✅ Todos los fixes críticos documentados")
print("📋 Próximos pasos:")
print("   1. Aplicar Fix 1 (whale_monitor scope)")
print("   2. Aplicar Fix 2 (PhD validation)")
print("   3. Crear circuit_breaker.py")
print("   4. Integrar circuit breaker en cosmos_worker.py")
print("   5. Ejecutar SQL indexes en Supabase")
print("   6. Testear en ambiente de staging")
print("   7. Deploy a producción")
