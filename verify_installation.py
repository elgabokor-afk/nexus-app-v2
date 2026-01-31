#!/usr/bin/env python3
"""
COSMOS AI - Verificador de Instalación
Verifica que todas las dependencias de Semana 2 estén instaladas
"""

import sys
import importlib
from typing import List, Tuple

def check_module(module_name: str, display_name: str = None) -> Tuple[bool, str]:
    """Verifica si un módulo está instalado"""
    if display_name is None:
        display_name = module_name
    
    try:
        importlib.import_module(module_name)
        return True, f"✅ {display_name}"
    except ImportError:
        return False, f"❌ {display_name} - FALTA"

def main():
    print("=" * 60)
    print("  COSMOS AI - Verificación de Dependencias Semana 2")
    print("=" * 60)
    print()
    
    # Lista de módulos a verificar
    modules = [
        # Core dependencies
        ("ccxt", "ccxt (Binance API)"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("sklearn", "scikit-learn"),
        ("xgboost", "xgboost"),
        ("openai", "openai"),
        
        # Semana 2 - Críticas
        ("ratelimit", "ratelimit (Fix 5 - Rate Limiting)"),
        ("structlog", "structlog (Fix 8 - Logging)"),
        ("pytest", "pytest (Fix 7 - Testing)"),
        
        # Semana 2 - Opcionales
        ("radon", "radon (Code Quality)"),
    ]
    
    print("📦 DEPENDENCIAS CRÍTICAS:")
    print("-" * 60)
    
    results = []
    for module_name, display_name in modules:
        success, message = check_module(module_name, display_name)
        results.append((success, message))
        print(f"  {message}")
    
    print()
    print("=" * 60)
    
    # Resumen
    total = len(results)
    installed = sum(1 for success, _ in results if success)
    missing = total - installed
    
    print(f"📊 RESUMEN:")
    print(f"  Total: {total}")
    print(f"  Instaladas: {installed} ✅")
    print(f"  Faltantes: {missing} ❌")
    print()
    
    if missing > 0:
        print("⚠️  ACCIÓN REQUERIDA:")
        print("  Ejecuta: python -m pip install ratelimit structlog pytest radon")
        print("  O ejecuta: INSTALL_DEPENDENCIES.bat")
        print()
        return 1
    else:
        print("✅ TODAS LAS DEPENDENCIAS INSTALADAS CORRECTAMENTE")
        print()
        print("🚀 PRÓXIMOS PASOS:")
        print("  1. Ejecutar tests: pytest tests/ -v")
        print("  2. Verificar logs: python data-engine/cosmos_worker.py")
        print()
        return 0

if __name__ == "__main__":
    sys.exit(main())
