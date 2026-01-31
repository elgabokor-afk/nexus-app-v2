#!/usr/bin/env python3
"""
NEXUS AI - Configuration Verification Script
==============================================
Verifies all environment variables and system configuration
for production deployment on Railway.

Usage: python verify_config.py
"""

import os
import sys
from typing import Dict, List, Tuple

def check_env_var(name: str, required: bool = True) -> Tuple[bool, str]:
    """Check if environment variable exists and is not empty."""
    value = os.getenv(name)
    if value:
        # Mask secrets for security
        if any(secret in name.upper() for secret in ['KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
            masked = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}" if len(value) > 8 else "****"
            return True, f"✓ {name} = {masked}"
        return True, f"✓ {name} = {value}"
    elif required:
        return False, f"✗ {name} is MISSING (required)"
    else:
        return True, f"⚠ {name} is optional (not set)"

def verify_backend_config() -> Dict[str, List[str]]:
    """Verify backend configuration."""
    results = {"passed": [], "failed": [], "warnings": []}
    
    # Core configuration
    core_vars = [
        ("PORT", False),
        ("PYTHONUNBUFFERED", False),
    ]
    
    # Database
    db_vars = [
        ("NEXT_PUBLIC_SUPABASE_URL", True),
        ("SUPABASE_SERVICE_ROLE_KEY", True),
    ]
    
    # Real-time services
    realtime_vars = [
        ("REDIS_URL", True),
        ("PUSHER_APP_ID", True),
        ("PUSHER_SECRET", True),
        ("NEXT_PUBLIC_PUSHER_KEY", True),
        ("NEXT_PUBLIC_PUSHER_CLUSTER", True),
    ]
    
    # AI Services
    ai_vars = [
        ("OPENAI_API_KEY", True),
    ]
    
    # Trading (optional in dev, required in production)
    trading_vars = [
        ("BINANCE_API_KEY", False),
        ("BINANCE_SECRET", False),
        ("TRADING_MODE", False),
    ]
    
    # Market Data APIs
    market_vars = [
        ("CMC_PRO_API_KEY", False),
        ("HELIUS_API_KEY", False),
    ]
    
    all_vars = core_vars + db_vars + realtime_vars + ai_vars + trading_vars + market_vars
    
    for var_name, required in all_vars:
        passed, message = check_env_var(var_name, required)
        if passed and "✓" in message:
            results["passed"].append(message)
        elif passed and "⚠" in message:
            results["warnings"].append(message)
        else:
            results["failed"].append(message)
    
    return results

def verify_frontend_config() -> Dict[str, List[str]]:
    """Verify frontend configuration."""
    results = {"passed": [], "failed": [], "warnings": []}
    
    frontend_vars = [
        ("NEXT_PUBLIC_SUPABASE_URL", True),
        ("NEXT_PUBLIC_SUPABASE_ANON_KEY", True),
        ("NEXT_PUBLIC_PUSHER_KEY", True),
        ("NEXT_PUBLIC_PUSHER_CLUSTER", True),
        ("NEXT_PUBLIC_API_URL", True),
    ]
    
    for var_name, required in frontend_vars:
        passed, message = check_env_var(var_name, required)
        if passed and "✓" in message:
            results["passed"].append(message)
        elif passed and "⚠" in message:
            results["warnings"].append(message)
        else:
            results["failed"].append(message)
    
    return results

def print_results(service_name: str, results: Dict[str, List[str]]):
    """Print verification results."""
    print(f"\n{'='*60}")
    print(f"  {service_name} Configuration")
    print(f"{'='*60}\n")
    
    if results["passed"]:
        print("✅ PASSED:")
        for msg in results["passed"]:
            print(f"  {msg}")
    
    if results["warnings"]:
        print("\n⚠️  WARNINGS:")
        for msg in results["warnings"]:
            print(f"  {msg}")
    
    if results["failed"]:
        print("\n❌ FAILED:")
        for msg in results["failed"]:
            print(f"  {msg}")
    
    total = len(results["passed"]) + len(results["failed"]) + len(results["warnings"])
    passed = len(results["passed"])
    print(f"\n📊 Score: {passed}/{total} required variables configured")

def main():
    """Main verification function."""
    print("\n" + "="*60)
    print("   NEXUS AI - Configuration Verification")
    print("="*60)
    
    # Detect environment
    is_backend = os.path.exists("data-engine")
    is_frontend = os.path.exists("src/app")
    
    if is_backend:
        backend_results = verify_backend_config()
        print_results("BACKEND", backend_results)
        
        if backend_results["failed"]:
            print("\n❌ Backend configuration is INCOMPLETE")
            sys.exit(1)
        else:
            print("\n✅ Backend configuration is COMPLETE")
    
    if is_frontend:
        frontend_results = verify_frontend_config()
        print_results("FRONTEND", frontend_results)
        
        if frontend_results["failed"]:
            print("\n❌ Frontend configuration is INCOMPLETE")
            sys.exit(1)
        else:
            print("\n✅ Frontend configuration is COMPLETE")
    
    if not is_backend and not is_frontend:
        print("\n⚠️  Could not detect project type")
        print("   Run this script from the project root directory")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("   All required environment variables are configured!")
    print("="*60 + "\n")
    sys.exit(0)

if __name__ == "__main__":
    main()
