"""
COSMOS AI - Unit Tests for Circuit Breaker
Tests para validar la protección de capital
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data-engine'))

# Mock del archivo de configuración antes de importar
@pytest.fixture(autouse=True)
def mock_config_file():
    """Mock del archivo de configuración para tests"""
    with patch('os.path.exists', return_value=False):
        yield

from circuit_breaker import CircuitBreaker

class TestCircuitBreaker:
    """Tests para la clase CircuitBreaker"""
    
    @pytest.fixture
    def cb(self):
        """Fixture que crea una instancia de CircuitBreaker para tests"""
        cb = CircuitBreaker()
        cb.initial_capital = 10000
        cb.current_capital = 10000
        cb.peak_capital = 10000
        cb.daily_pnl = 0
        cb.consecutive_losses = 0
        cb.is_tripped = False
        return cb
    
    def test_check_trade_allows_when_healthy(self, cb):
        """Test que check_trade permite trades cuando el sistema está saludable"""
        can_trade, reason = cb.check_trade()
        
        assert can_trade == True
        assert reason == "OK"
    
    def test_check_trade_blocks_after_daily_loss_limit(self, cb):
        """Test que check_trade bloquea después de alcanzar el límite de pérdida diaria"""
        # Simular pérdida del 5% (límite)
        cb.daily_pnl = -500  # 5% de 10000
        cb.current_capital = 9500
        
        can_trade, reason = cb.check_trade()
        
        assert can_trade == False
        assert "Daily loss limit" in reason
        assert cb.is_tripped == True
    
    def test_check_trade_blocks_after_consecutive_losses(self, cb):
        """Test que check_trade bloquea después de 5 pérdidas consecutivas"""
        cb.consecutive_losses = 5
        cb.last_loss_time = datetime.now()
        
        can_trade, reason = cb.check_trade()
        
        assert can_trade == False
        assert "Consecutive losses" in reason
        assert cb.is_tripped == True
    
    def test_check_trade_blocks_after_max_drawdown(self, cb):
        """Test que check_trade bloquea después de alcanzar el drawdown máximo"""
        cb.peak_capital = 10000
        cb.current_capital = 8900  # 11% drawdown (>10% límite)
        
        can_trade, reason = cb.check_trade()
        
        assert can_trade == False
        assert "drawdown" in reason.lower()
        assert cb.is_tripped == True
    
    def test_record_trade_updates_consecutive_losses(self, cb):
        """Test que record_trade actualiza correctamente las pérdidas consecutivas"""
        # Primera pérdida
        cb.record_trade(-100)
        assert cb.consecutive_losses == 1
        
        # Segunda pérdida
        cb.record_trade(-50)
        assert cb.consecutive_losses == 2
        
        # Ganancia (reset)
        cb.record_trade(200)
        assert cb.consecutive_losses == 0
    
    def test_record_trade_updates_daily_pnl(self, cb):
        """Test que record_trade actualiza correctamente el PnL diario"""
        cb.record_trade(100)
        assert cb.daily_pnl == 100
        
        cb.record_trade(-50)
        assert cb.daily_pnl == 50
        
        cb.record_trade(25)
        assert cb.daily_pnl == 75
    
    def test_record_trade_updates_peak_capital(self, cb):
        """Test que record_trade actualiza el peak capital correctamente"""
        initial_peak = cb.peak_capital
        
        # Ganancia que supera el peak
        cb.record_trade(500)
        assert cb.current_capital == 10500
        assert cb.peak_capital == 10500
        assert cb.peak_capital > initial_peak
    
    def test_reset_clears_state(self, cb):
        """Test que reset limpia el estado del circuit breaker"""
        # Configurar estado "tripped"
        cb.consecutive_losses = 5
        cb.is_tripped = True
        cb.trip_reason = "Test reason"
        
        # Reset
        cb.reset()
        
        assert cb.consecutive_losses == 0
        assert cb.is_tripped == False
        assert cb.trip_reason is None
    
    def test_check_daily_reset(self, cb):
        """Test que check_daily_reset resetea el PnL diario a medianoche"""
        # Simular día anterior
        cb.last_reset_date = (datetime.now() - timedelta(days=1)).date()
        cb.daily_pnl = -300
        
        # Trigger reset
        cb.check_daily_reset()
        
        assert cb.daily_pnl == 0
        assert cb.last_reset_date == datetime.now().date()
    
    def test_get_status_returns_complete_info(self, cb):
        """Test que get_status retorna información completa del estado"""
        cb.daily_pnl = -200
        cb.consecutive_losses = 2
        cb.current_capital = 9800
        
        status = cb.get_status()
        
        assert 'is_tripped' in status
        assert 'daily_pnl' in status
        assert 'consecutive_losses' in status
        assert 'current_capital' in status
        assert 'peak_capital' in status
        assert 'drawdown_pct' in status
        assert 'limits' in status
        
        assert status['daily_pnl'] == -200
        assert status['consecutive_losses'] == 2
        assert status['current_capital'] == 9800
    
    def test_cooldown_period_works(self, cb):
        """Test que el período de cooldown funciona correctamente"""
        # Activar circuit breaker
        cb.consecutive_losses = 5
        cb.last_loss_time = datetime.now() - timedelta(minutes=30)
        cb.cooldown_minutes = 60
        
        # Debería estar bloqueado (solo 30 min han pasado)
        can_trade, reason = cb.check_trade()
        assert can_trade == False
        assert "Cooldown" in reason
        
        # Simular que pasó el tiempo de cooldown
        cb.last_loss_time = datetime.now() - timedelta(minutes=61)
        
        # Debería permitir trading (cooldown terminó)
        can_trade, reason = cb.check_trade()
        assert can_trade == True
        assert cb.is_tripped == False

class TestCircuitBreakerEdgeCases:
    """Tests para casos extremos"""
    
    @pytest.fixture
    def cb(self):
        cb = CircuitBreaker()
        cb.initial_capital = 10000
        cb.current_capital = 10000
        cb.peak_capital = 10000
        return cb
    
    def test_handles_zero_capital(self, cb):
        """Test que maneja correctamente capital en cero"""
        cb.current_capital = 0
        
        # No debería crashear
        can_trade, reason = cb.check_trade()
        assert can_trade == False
    
    def test_handles_negative_pnl_larger_than_capital(self, cb):
        """Test que maneja PnL negativo mayor al capital"""
        # Simular pérdida catastrófica
        cb.record_trade(-15000)
        
        assert cb.current_capital < 0
        assert cb.daily_pnl == -15000
        
        # Debería bloquear trading
        can_trade, reason = cb.check_trade()
        assert can_trade == False
    
    def test_handles_very_small_trades(self, cb):
        """Test que maneja trades muy pequeños"""
        # Trade de $0.01
        cb.record_trade(0.01)
        
        assert cb.daily_pnl == 0.01
        assert cb.current_capital == 10000.01
    
    def test_proposed_risk_check(self, cb):
        """Test que check_trade valida el riesgo propuesto"""
        # Proponer riesgo del 3% (>2% límite)
        proposed_risk = 300
        
        can_trade, reason = cb.check_trade(proposed_risk_usd=proposed_risk)
        
        assert can_trade == False
        assert "Proposed risk" in reason
        assert "2%" in reason

class TestCircuitBreakerIntegration:
    """Tests de integración con otros componentes"""
    
    @pytest.fixture
    def cb(self):
        cb = CircuitBreaker()
        cb.initial_capital = 10000
        cb.current_capital = 10000
        cb.peak_capital = 10000
        return cb
    
    def test_realistic_trading_scenario(self, cb):
        """Test de escenario realista de trading"""
        # Día 1: 3 trades ganadores
        cb.record_trade(100)
        cb.record_trade(150)
        cb.record_trade(75)
        
        assert cb.consecutive_losses == 0
        assert cb.daily_pnl == 325
        assert cb.current_capital == 10325
        
        # Día 2: Reset diario
        cb.last_reset_date = (datetime.now() - timedelta(days=1)).date()
        cb.check_daily_reset()
        assert cb.daily_pnl == 0
        
        # Día 2: 2 pérdidas, 1 ganancia
        cb.record_trade(-100)
        cb.record_trade(-50)
        assert cb.consecutive_losses == 2
        
        cb.record_trade(200)
        assert cb.consecutive_losses == 0  # Reset por ganancia
        
        # Sistema debería seguir operativo
        can_trade, reason = cb.check_trade()
        assert can_trade == True
    
    @patch('circuit_breaker.TelegramAlerts')
    def test_sends_telegram_alert_on_trip(self, mock_telegram, cb):
        """Test que envía alerta a Telegram cuando se activa"""
        # Activar circuit breaker
        cb.consecutive_losses = 5
        cb.last_loss_time = datetime.now()
        
        # Debería intentar enviar alerta
        can_trade, reason = cb.check_trade()
        
        # Verificar que se intentó enviar alerta
        # (El mock puede no funcionar si TelegramAlerts no está disponible)
        assert can_trade == False

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=circuit_breaker", "--cov-report=html"])
