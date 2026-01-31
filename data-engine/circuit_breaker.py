"""
COSMOS AI - Circuit Breaker
Protección contra pérdidas en cascada

Fix 3: Sistema de protección que detiene el trading automáticamente
cuando se detectan condiciones peligrosas.
"""

import json
import os
from datetime import datetime, date

class CircuitBreaker:
    def __init__(self, config_path="circuit_breaker_config.json"):
        self.config_path = config_path
        self.is_tripped = False
        self.trip_reason = None
        self.consecutive_losses = 0
        self.daily_pnl = 0
        self.last_loss_time = None
        self.last_reset_date = date.today()
        
        # Load config
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
        self.current_capital = self.initial_capital
        self.peak_capital = self.initial_capital
        self.max_daily_loss_pct = default_config['max_daily_loss_pct']
        self.max_consecutive_losses = default_config['max_consecutive_losses']
        self.max_drawdown_pct = default_config['max_drawdown_pct']
        self.cooldown_minutes = default_config['cooldown_minutes']
        self.auto_reset_daily = default_config['auto_reset_daily']
        
        print(f"   [CIRCUIT BREAKER] Initialized with capital: ${self.initial_capital}")
    
    def check_daily_reset(self):
        """Reset automático a medianoche"""
        if not self.auto_reset_daily:
            return
        
        today = date.today()
        if today > self.last_reset_date:
            print(f"   [CIRCUIT BREAKER] Daily reset triggered")
            self.daily_pnl = 0
            self.last_reset_date = today
    
    def check_trade(self, proposed_risk_usd=None):
        """
        Verifica si un trade puede ejecutarse.
        
        Args:
            proposed_risk_usd: Riesgo del trade propuesto (opcional)
        
        Returns:
            (bool, str): (puede_ejecutar, razón)
        """
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
        if self.current_capital > 0:
            loss_pct = abs(self.daily_pnl / self.current_capital) * 100
            if self.daily_pnl < 0 and loss_pct >= self.max_daily_loss_pct:
                self.trip(f"Daily loss limit exceeded: {loss_pct:.2f}% >= {self.max_daily_loss_pct}%")
                return False, self.trip_reason
        
        # 3. Consecutive Losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.trip(f"Consecutive losses limit: {self.consecutive_losses} trades")
            return False, self.trip_reason
        
        # 4. Drawdown Limit
        if self.peak_capital > 0:
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
        """
        Registra el resultado de un trade.
        
        Args:
            pnl_usd: PnL del trade en USD (positivo = ganancia, negativo = pérdida)
        """
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
        loss_pct = abs(self.daily_pnl / self.current_capital) * 100 if self.daily_pnl < 0 and self.current_capital > 0 else 0
        drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100 if self.peak_capital > 0 else 0
        
        print(f"   [CIRCUIT BREAKER] Daily PnL: ${self.daily_pnl:.2f} ({loss_pct:.2f}% loss)")
        print(f"   [CIRCUIT BREAKER] Drawdown: {drawdown_pct:.2f}% (Max: {self.max_drawdown_pct}%)")
    
    def trip(self, reason):
        """Activa el circuit breaker"""
        self.is_tripped = True
        self.trip_reason = reason
        print(f"\n{'='*60}")
        print(f"🚨 CIRCUIT BREAKER TRIPPED 🚨")
        print(f"Reason: {reason}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Enviar alerta a Telegram (opcional)
        try:
            from telegram_utils import TelegramAlerts
            tg = TelegramAlerts()
            tg.send_msg(f"⚠️ TRADING HALTED\n\nReason: {reason}\nTime: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"   [CIRCUIT BREAKER] Telegram alert unavailable: {e}")
    
    def reset(self):
        """Reset manual del circuit breaker"""
        self.consecutive_losses = 0
        self.is_tripped = False
        self.trip_reason = None
        print(f"   [CIRCUIT BREAKER] Manual reset completed")
    
    def get_status(self):
        """Retorna estado actual del circuit breaker"""
        loss_pct = abs(self.daily_pnl / self.current_capital) * 100 if self.daily_pnl < 0 and self.current_capital > 0 else 0
        drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100 if self.peak_capital > 0 else 0
        
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
    print("\n1. Trade 1: -$100")
    cb.record_trade(-100)
    can_trade, reason = cb.check_trade()
    print(f"Can trade: {can_trade} ({reason})")
    
    print("\n2. Trade 2: -$150")
    cb.record_trade(-150)
    can_trade, reason = cb.check_trade()
    print(f"Can trade: {can_trade} ({reason})")
    
    print("\n3. Trade 3: +$200")
    cb.record_trade(200)
    can_trade, reason = cb.check_trade()
    print(f"Can trade: {can_trade} ({reason})")
    
    print("\n4. Simular 5 pérdidas consecutivas:")
    for i in range(5):
        print(f"\n   Loss {i+1}: -$50")
        cb.record_trade(-50)
        can_trade, reason = cb.check_trade()
        print(f"   Can trade: {can_trade} ({reason})")
    
    print("\nStatus Final:")
    import json
    print(json.dumps(cb.get_status(), indent=2))
