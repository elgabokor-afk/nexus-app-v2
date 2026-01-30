"""
COSMOS AI - Structured Logging Configuration
Implementa logging estructurado con JSON para mejor observabilidad
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    print("Warning: structlog not installed. Install with: pip install structlog")
    STRUCTLOG_AVAILABLE = False

# Configuración de directorios de logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Niveles de log por servicio
LOG_LEVELS = {
    "cosmos_engine": "INFO",
    "cosmos_worker": "INFO",
    "cosmos_oracle": "INFO",
    "cosmos_validator": "INFO",
    "binance_engine": "WARNING",
    "redis_engine": "WARNING",
    "circuit_breaker": "INFO",
    "default": "INFO"
}

def get_log_level(service_name):
    """Obtiene el nivel de log para un servicio específico"""
    return LOG_LEVELS.get(service_name, LOG_LEVELS["default"])

if STRUCTLOG_AVAILABLE:
    # Configuración de structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name):
    """
    Crea un logger estructurado para un servicio.
    
    Args:
        name: Nombre del servicio (ej: "cosmos_engine")
    
    Returns:
        Logger configurado con JSON output
    """
    if STRUCTLOG_AVAILABLE:
        logger = structlog.get_logger(name)
        return logger
    else:
        # Fallback a logging estándar
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, get_log_level(name)))
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Handler para archivo
        file_handler = logging.FileHandler(LOG_DIR / f"{name}.log")
        file_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger

# Helpers para logging estructurado
class StructuredLogger:
    """
    Wrapper para logging estructurado con contexto.
    Permite añadir contexto persistente a todos los logs.
    """
    
    def __init__(self, name, **context):
        self.logger = get_logger(name)
        self.context = context
    
    def _log(self, level, message, **kwargs):
        """Log interno con contexto"""
        full_context = {**self.context, **kwargs}
        
        if STRUCTLOG_AVAILABLE:
            getattr(self.logger, level)(message, **full_context)
        else:
            # Fallback: convertir contexto a string
            context_str = " | ".join(f"{k}={v}" for k, v in full_context.items())
            full_message = f"{message} | {context_str}" if context_str else message
            getattr(self.logger, level)(full_message)
    
    def debug(self, message, **kwargs):
        self._log("debug", message, **kwargs)
    
    def info(self, message, **kwargs):
        self._log("info", message, **kwargs)
    
    def warning(self, message, **kwargs):
        self._log("warning", message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log("error", message, **kwargs)
    
    def critical(self, message, **kwargs):
        self._log("critical", message, **kwargs)
    
    def bind(self, **kwargs):
        """Añade contexto persistente al logger"""
        self.context.update(kwargs)
        return self

# Ejemplos de uso
if __name__ == "__main__":
    # Ejemplo 1: Logger básico
    logger = get_logger("test_service")
    
    if STRUCTLOG_AVAILABLE:
        logger.info("signal_generated", 
                   symbol="BTC/USDT", 
                   confidence=0.87, 
                   thesis_id=123,
                   p_value=0.023)
        
        logger.warning("circuit_breaker_triggered",
                      reason="consecutive_losses",
                      count=5,
                      capital=9500)
        
        logger.error("api_error",
                    service="binance",
                    error_code=451,
                    message="Geo-block detected")
    else:
        logger.info("signal_generated | symbol=BTC/USDT | confidence=0.87")
        logger.warning("circuit_breaker_triggered | reason=consecutive_losses")
        logger.error("api_error | service=binance | error_code=451")
    
    # Ejemplo 2: Logger con contexto
    worker_logger = StructuredLogger("cosmos_worker", 
                                    worker_id="w1", 
                                    version="v3.0")
    
    worker_logger.info("worker_started", uptime_seconds=0)
    worker_logger.info("signal_processed", symbol="ETH/USDT", confidence=0.92)
    
    # Añadir más contexto
    worker_logger.bind(session_id="abc123")
    worker_logger.info("trade_executed", symbol="SOL/USDT", pnl=150.50)
    
    print("\n✅ Logging test completed. Check logs/ directory for output.")
