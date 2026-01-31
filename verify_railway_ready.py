"""
Script para verificar que el proyecto está listo para deployment en Railway
"""
import os
import sys
from pathlib import Path

print("=" * 70)
print("  VERIFICACIÓN PRE-DEPLOYMENT - RAILWAY")
print("=" * 70)

errors = []
warnings = []
success = []

# 1. Verificar archivos críticos
print("\n📁 1. ARCHIVOS CRÍTICOS")
print("-" * 70)

critical_files = {
    "Dockerfile": "Configuración de Docker",
    "Procfile": "Comando de inicio",
    "requirements.txt": "Dependencias Python",
    "start_services.sh": "Script de inicio de servicios",
    "railway.json": "Configuración de Railway",
    ".env.local.example": "Ejemplo de variables de entorno"
}

for file, desc in critical_files.items():
    if Path(file).exists():
        success.append(f"✅ {file} - {desc}")
    else:
        errors.append(f"❌ {file} - {desc} NO ENCONTRADO")

for item in success:
    print(f"  {item}")
for item in errors:
    print(f"  {item}")

# 2. Verificar estructura de directorios
print("\n📂 2. ESTRUCTURA DE DIRECTORIOS")
print("-" * 70)

required_dirs = {
    "data-engine": "Motor de IA y trading",
    "src": "Frontend Next.js",
    "config": "Archivos de configuración"
}

for dir_name, desc in required_dirs.items():
    if Path(dir_name).exists():
        print(f"  ✅ {dir_name}/ - {desc}")
    else:
        errors.append(f"❌ {dir_name}/ - {desc} NO ENCONTRADO")
        print(f"  ❌ {dir_name}/ - {desc} NO ENCONTRADO")

# 3. Verificar archivos Python críticos
print("\n🐍 3. MÓDULOS PYTHON CRÍTICOS")
print("-" * 70)

python_modules = [
    "data-engine/cosmos_worker.py",
    "data-engine/cosmos_engine.py",
    "data-engine/nexus_api.py",
    "data-engine/scanner.py",
    "data-engine/db.py",
    "data-engine/redis_engine.py",
    "data-engine/pusher_client.py"
]

for module in python_modules:
    if Path(module).exists():
        print(f"  ✅ {module}")
    else:
        errors.append(f"❌ {module} NO ENCONTRADO")
        print(f"  ❌ {module} NO ENCONTRADO")

# 4. Verificar dependencias en requirements.txt
print("\n📦 4. DEPENDENCIAS PYTHON")
print("-" * 70)

required_packages = [
    "ccxt",
    "pandas",
    "fastapi",
    "uvicorn",
    "supabase",
    "pusher",
    "redis",
    "scikit-learn",
    "openai"
]

if Path("requirements.txt").exists():
    with open("requirements.txt", "r") as f:
        requirements = f.read().lower()
    
    for package in required_packages:
        if package.lower() in requirements:
            print(f"  ✅ {package}")
        else:
            warnings.append(f"⚠️  {package} no encontrado en requirements.txt")
            print(f"  ⚠️  {package} no encontrado en requirements.txt")
else:
    errors.append("❌ requirements.txt no existe")

# 5. Verificar permisos de start_services.sh
print("\n🔐 5. PERMISOS DE SCRIPTS")
print("-" * 70)

if Path("start_services.sh").exists():
    import stat
    st = os.stat("start_services.sh")
    if st.st_mode & stat.S_IXUSR:
        print("  ✅ start_services.sh tiene permisos de ejecución")
    else:
        warnings.append("⚠️  start_services.sh no tiene permisos de ejecución")
        print("  ⚠️  start_services.sh no tiene permisos de ejecución")
        print("     Ejecuta: chmod +x start_services.sh")

# 6. Verificar .env.local.example
print("\n🔑 6. VARIABLES DE ENTORNO")
print("-" * 70)

required_env_vars = [
    "NEXT_PUBLIC_SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "BINANCE_API_KEY",
    "BINANCE_SECRET",
    "PUSHER_APP_ID",
    "PUSHER_KEY",
    "PUSHER_SECRET",
    "OPENAI_API_KEY"
]

if Path(".env.local.example").exists():
    with open(".env.local.example", "r") as f:
        env_example = f.read()
    
    for var in required_env_vars:
        if var in env_example:
            print(f"  ✅ {var}")
        else:
            warnings.append(f"⚠️  {var} no está en .env.local.example")
            print(f"  ⚠️  {var} no está en .env.local.example")
else:
    warnings.append("⚠️  .env.local.example no existe")
    print("  ⚠️  .env.local.example no existe")

# 7. Verificar configuración de Railway
print("\n🚂 7. CONFIGURACIÓN DE RAILWAY")
print("-" * 70)

if Path("railway.json").exists():
    import json
    try:
        with open("railway.json", "r") as f:
            railway_config = json.load(f)
        
        if "build" in railway_config:
            print("  ✅ Configuración de build presente")
        else:
            warnings.append("⚠️  Falta configuración de build")
        
        if "deploy" in railway_config:
            print("  ✅ Configuración de deploy presente")
        else:
            warnings.append("⚠️  Falta configuración de deploy")
            
    except json.JSONDecodeError:
        errors.append("❌ railway.json tiene errores de sintaxis")
        print("  ❌ railway.json tiene errores de sintaxis")

# 8. Verificar Dockerfile
print("\n🐳 8. DOCKERFILE")
print("-" * 70)

if Path("Dockerfile").exists():
    with open("Dockerfile", "r") as f:
        dockerfile = f.read()
    
    checks = {
        "FROM python": "Imagen base de Python",
        "COPY requirements.txt": "Copia de dependencias",
        "RUN pip install": "Instalación de dependencias",
        "COPY data-engine": "Copia del código",
        "CMD": "Comando de inicio"
    }
    
    for check, desc in checks.items():
        if check in dockerfile:
            print(f"  ✅ {desc}")
        else:
            warnings.append(f"⚠️  {desc} no encontrado en Dockerfile")
            print(f"  ⚠️  {desc} no encontrado en Dockerfile")

# RESUMEN
print("\n" + "=" * 70)
print("  RESUMEN")
print("=" * 70)

print(f"\n✅ Verificaciones exitosas: {len(success)}")
print(f"⚠️  Advertencias: {len(warnings)}")
print(f"❌ Errores críticos: {len(errors)}")

if errors:
    print("\n🔴 ERRORES CRÍTICOS QUE DEBEN CORREGIRSE:")
    for error in errors:
        print(f"  {error}")

if warnings:
    print("\n🟡 ADVERTENCIAS (Recomendado corregir):")
    for warning in warnings:
        print(f"  {warning}")

print("\n" + "=" * 70)

if errors:
    print("❌ NO LISTO PARA DEPLOYMENT")
    print("   Corrige los errores críticos antes de hacer deploy")
    sys.exit(1)
elif warnings:
    print("⚠️  LISTO CON ADVERTENCIAS")
    print("   Puedes hacer deploy, pero revisa las advertencias")
    sys.exit(0)
else:
    print("✅ LISTO PARA DEPLOYMENT EN RAILWAY")
    print("   Todos los checks pasaron exitosamente")
    sys.exit(0)
