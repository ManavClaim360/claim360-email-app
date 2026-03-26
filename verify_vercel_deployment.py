#!/usr/bin/env python3
"""
Vercel Deployment Verification Script
Checks for common Vercel deployment issues before deployment
"""

import os
import sys
import json
import re
from pathlib import Path


def check_file_exists(path, description):
    """Check if a file exists."""
    exists = Path(path).exists()
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {path}")
    return exists


def check_file_contains(path, patterns, description):
    """Check if a file contains required patterns."""
    if not Path(path).exists():
        print(f"✗ {description}: File not found {path}")
        return False
    
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        found_all = True
        for pattern in patterns if isinstance(patterns, list) else [patterns]:
            if pattern not in content:
                print(f"  ✗ Missing in {description}: {pattern}")
                found_all = False
        
        if found_all:
            print(f"✓ {description}: All required patterns found")
        return found_all
    except Exception as e:
        print(f"✗ {description}: Error reading file: {e}")
        return False


def check_json_valid(path, description):
    """Check if JSON file is valid."""
    try:
        with open(path, 'r') as f:
            json.load(f)
        print(f"✓ {description}: Valid JSON")
        return True
    except Exception as e:
        print(f"✗ {description}: Invalid JSON - {e}")
        return False


def main():
    print("\n" + "="*60)
    print("Claim360 Vercel Deployment Verification")
    print("="*60 + "\n")
    
    issues = []
    
    # 1. Check essential configuration files
    print("📋 Configuration Files:")
    print("-" * 60)
    
    if not check_file_exists("vercel.json", "vercel.json"):
        issues.append("Missing vercel.json - required for Vercel deployment")
    else:
        check_json_valid("vercel.json", "vercel.json JSON syntax")
    
    if not check_file_exists(".vercelignore", ".vercelignore"):
        issues.append("Missing .vercelignore - recommended for Vercel deployment")
    
    check_file_exists("backend/main.py", "Backend entry point")
    check_file_exists("frontend/package.json", "Frontend package.json")
    
    # 2. Check backend requirements
    print("\n🔧 Backend Configuration:")
    print("-" * 60)
    
    if check_file_exists("backend/requirements.txt", "Backend requirements.txt"):
        with open("backend/requirements.txt", 'r') as f:
            reqs = f.read()
        
        # Check for problematic dependencies
        if "celery" in reqs or "redis" in reqs:
            issues.append("⚠️  Celery/Redis in requirements.txt - not available on Vercel (safely ignored if not used)")
        
        required_packages = ["fastapi", "uvicorn", "sqlalchemy", "asyncpg"]
        missing = [pkg for pkg in required_packages if pkg not in reqs]
        
        if missing:
            issues.append(f"Missing required packages: {', '.join(missing)}")
        else:
            print(f"✓ All required packages present")
    
    # 3. Check main.py exports FastAPI app
    print("\n🚀 API Export:")
    print("-" * 60)
    
    if check_file_contains("backend/main.py", 
                          ["app = FastAPI", "include_router"],
                          "FastAPI app export and routers"):
        print("  (FastAPI app will be correctly exported to Vercel)")
    else:
        issues.append("FastAPI app not properly exported - Vercel needs 'app = FastAPI(...)'")
    
    # 4. Check frontend build configuration
    print("\n⚙️  Frontend Configuration:")
    print("-" * 60)
    
    if check_file_exists("frontend/vite.config.js", "Vite config"):
        check_file_contains("frontend/vite.config.js", "outDir", "Vite output directory")
    
    if check_file_exists("frontend/package.json", "Frontend package.json"):
        with open("frontend/package.json", 'r') as f:
            pkg = json.load(f)
        
        if "build" in pkg.get("scripts", {}):
            print(f"✓ Frontend has build script: npm run build")
        else:
            issues.append("Frontend missing 'build' script in package.json")
        
        if "react" in pkg.get("dependencies", {}):
            print(f"✓ React dependency found")
        else:
            issues.append("React not in frontend dependencies")
    
    # 5. Check API client configuration
    print("\n🔌 API Client:")
    print("-" * 60)
    
    if check_file_exists("frontend/src/utils/api.js", "Frontend API client"):
        check_file_contains("frontend/src/utils/api.js", 
                           "VITE_API_URL",
                           "Frontend API URL configuration")
    
    # 6. Check environment configuration
    print("\n🔐 Environment Configuration:")
    print("-" * 60)
    
    if check_file_exists("backend/.env.example", "Backend .env example"):
        with open("backend/.env.example", 'r') as f:
            env_content = f.read()
        
        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
            "BASE_URL"
        ]
        
        missing_vars = [var for var in required_vars if var not in env_content]
        
        if not missing_vars:
            print(f"✓ All required environment variables documented")
        else:
            issues.append(f"Missing in .env.example: {', '.join(missing_vars)}")
    
    if check_file_exists("frontend/.env.example", "Frontend .env example"):
        check_file_contains("frontend/.env.example", 
                           "VITE_API_URL",
                           "Frontend API URL environment variable")
    
    # 7. Verify vercel.json routing
    print("\n🛣️  Vercel Routing:")
    print("-" * 60)
    
    with open("vercel.json", 'r') as f:
        vercel_config = json.load(f)
    
    has_api_route = any(
        route.get("src") == "/api/(.*)" 
        for route in vercel_config.get("routes", [])
    )
    
    if has_api_route:
        print("✓ API routing configured for /api/* endpoints")
    else:
        issues.append("Missing /api/* routing in vercel.json")
    
    has_spa_fallback = any(
        route.get("src") == "/(.*)" and route.get("dest") == "/index.html"
        for route in vercel_config.get("routes", [])
    )
    
    if has_spa_fallback:
        print("✓ SPA fallback routing configured")
    else:
        issues.append("Missing SPA fallback routing in vercel.json")
    
    # 8. Check for common issues
    print("\n⚠️  Common Issues Check:")
    print("-" * 60)
    
    # Check .env files are not committed
    if Path("backend/.env").exists():
        issues.append("backend/.env exists - should not be committed (add to .gitignore)")
    else:
        print("✓ backend/.env not committed (good)")
    
    # Check gitignore
    if Path(".gitignore").exists():
        with open(".gitignore", 'r') as f:
            gitignore = f.read()
        
        if ".env" in gitignore:
            print("✓ .env files in .gitignore")
        else:
            issues.append(".env files not in .gitignore")
    
    # Summary
    print("\n" + "="*60)
    if not issues:
        print("✅ All checks passed! Your app is Vercel-ready.")
        print("="*60 + "\n")
        return 0
    else:
        print(f"⚠️  Found {len(issues)} issue(s):")
        print("="*60)
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        print("\n" + "="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
