#!/usr/bin/env python3
"""
Script de Validación - FASE 1 Fixes
Verifica que todos los fixes críticos estén implementados correctamente
"""

import os
import sys

def check_file_exists(filepath):
    """Verifica que un archivo exista"""
    if os.path.exists(filepath):
        print(f"✅ {filepath} - Existe")
        return True
    else:
        print(f"❌ {filepath} - NO ENCONTRADO")
        return False

def check_string_in_file(filepath, search_string, description):
    """Verifica que un string esté presente en un archivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_string in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - NO ENCONTRADO")
                return False
    except Exception as e:
        print(f"❌ Error leyendo {filepath}: {e}")
        return False

def main():
    print("="*60)
    print("🔍 VALIDACIÓN DE FIXES - FASE 1")
    print("="*60)
    print()
    
    all_checks_passed = True
    
    # Fix 1: whale_monitor scope
    print("📋 Fix 1: whale_monitor Scope")
    print("-" * 40)
    
    checks = [
        ("data-engine/cosmos_worker.py", "whale_monitor = None", "Declaración global de whale_monitor"),
        ("data-engine/cosmos_worker.py", "if whale_monitor:", "Check de whale_monitor antes de usar"),
    ]
    
    for filepath, search, desc in checks:
        if not check_string_in_file(filepath, search, desc):
            all_checks_passed = False
    
    print()
    
    # Fix 2: Validación Académica
    print("📋 Fix 2: Validación Académica Endurecida")
    print("-" * 40)
    
    checks = [
        ("data-engine/cosmos_engine.py", "UNIVERSITY_WEIGHTS", "Diccionario de pesos universitarios"),
        ("data-engine/cosmos_engine.py", "self.last_university", "Tracking de universidad"),
    ]
    
    for filepath, search, desc in checks:
        if not check_string_in_file(filepath, search, desc):
            all_checks_passed = False
    
    print()
    
    # Fix 3: Circuit Breaker
    print("📋 Fix 3: Circuit Breaker")
    print("-" * 40)
    
    files = [
        "data-engine/circuit_breaker.py",
        "circuit_breaker_config.json",
    ]
    
    for filepath in files:
        if not check_file_exists(filepath):
            all_checks_passed = False
    
    checks = [
        ("data-engine/cosmos_worker.py", "from circuit_breaker import circuit_breaker", "Import en cosmos_worker"),
        ("data-engine/cosmos_worker.py", "Fix 3: Circuit Breaker Check", "Check antes de guardar señales"),
        ("data-engine/paper_trader.py", "Fix 3: Registrar resultado", "Registro en paper_trader"),
        ("data-engine/circuit_breaker.py", "class CircuitBreaker:", "Clase CircuitBreaker"),
    ]
    
    for filepath, search, desc in checks:
        if not check_string_in_file(filepath, search, desc):
            all_checks_passed = False
    
    print()
    
    # Fix Adicional: Favicon
    print("📋 Fix Adicional: Favicon")
    print("-" * 40)
    
    checks = [
        ("src/app/layout.tsx", "Nexus Crypto Signals", "Título actualizado"),
        ("src/app/layout.tsx", "icons:", "Configuración de favicon"),
    ]
    
    for filepath, search, desc in checks:
        if not check_string_in_file(filepath, search, desc):
            all_checks_passed = False
    
    print()
    print("="*60)
    
    if all_checks_passed:
        print("✅ TODOS LOS CHECKS PASARON")
        print()
        print("Próximos pasos:")
        print("1. Ejecutar: cd data-engine && python circuit_breaker.py")
        print("2. Ejecutar: pytest tests/ -v")
        print("3. Probar cosmos_worker.py en modo test")
        print("4. Deploy a producción")
        return 0
    else:
        print("❌ ALGUNOS CHECKS FALLARON")
        print()
        print("Revisa los errores arriba y corrige los archivos faltantes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
