#!/usr/bin/env python3
"""
Environment Variables Verification Script
Run this before deploying to Vercel to ensure all variables are correctly set
Usage: python3 check_env_vars.py
"""

import os
import sys
import re
from pathlib import Path

# Load environment from backend/.env manually
env_file = os.path.join(os.path.dirname(__file__), 'backend', '.env')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Get settings from environment variables
class Settings:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production-use-strong-secret')
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:password@localhost/claim360')
    DATABASE_URL_SYNC = os.getenv('DATABASE_URL_SYNC', 'postgresql://postgres:password@localhost/claim360')
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/auth/oauth/callback')
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@company.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    SEND_DELAY_SECONDS = os.getenv('SEND_DELAY_SECONDS', '3')
    MAX_ATTACHMENT_SIZE_MB = os.getenv('MAX_ATTACHMENT_SIZE_MB', '25')
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '10080')

settings = Settings()

def check_url_format(url, url_type):
    """Verify URL format"""
    if url_type == "database_async":
        return url.startswith("postgresql+asyncpg://")
    elif url_type == "database_sync":
        return url.startswith("postgresql://")
    elif url_type == "http":
        return url.startswith("http://") or url.startswith("https://")
    return True

def mask_secret(value, char_count=8):
    """Mask sensitive values"""
    if not value:
        return "NOT SET"
    if len(value) <= char_count:
        return "*" * len(value)
    return value[:3] + "*" * char_count + value[-3:]

def verify_variable(name, value, url_type=None, min_length=None, required=False):
    """Check a single variable"""
    if not value or value == "":
        status = "✗ MISSING" if required else "⚠ EMPTY"
        return (False if required else True, status, "NOT SET")
    
    # Check URL format if specified
    if url_type and not check_url_format(value, url_type):
        return (False, "✗ INVALID FORMAT", f"Expected format: {url_type}")
    
    # Check minimum length
    if min_length and len(value) < min_length:
        return (False, "✗ TOO SHORT", f"Min {min_length} characters")
    
    return (True, "✓", mask_secret(value))

print("\n" + "="*70)
print("🔍 ENVIRONMENT VARIABLES VERIFICATION")
print("="*70 + "\n")

all_ok = True

# ── CRITICAL VARIABLES ────────────────────────────────────────────────────
print("🔴 CRITICAL VARIABLES (Required for Vercel):")
print("-" * 70)

critical_checks = [
    ("SECRET_KEY", settings.SECRET_KEY, {"required": True, "min_length": 16, "mask": True}),
    ("DATABASE_URL", settings.DATABASE_URL, {"required": True, "url_type": "database_async"}),
    ("DATABASE_URL_SYNC", settings.DATABASE_URL_SYNC, {"required": True, "url_type": "database_sync"}),
    ("GOOGLE_CLIENT_ID", settings.GOOGLE_CLIENT_ID, {"required": True, "min_length": 20}),
    ("GOOGLE_CLIENT_SECRET", settings.GOOGLE_CLIENT_SECRET, {"required": True, "min_length": 20, "mask": True}),
    ("GOOGLE_REDIRECT_URI", settings.GOOGLE_REDIRECT_URI, {"required": True, "url_type": "http"}),
    ("BASE_URL", settings.BASE_URL, {"required": True, "url_type": "http"}),
    ("FRONTEND_URL", settings.FRONTEND_URL, {"required": True, "url_type": "http"}),
    ("ADMIN_EMAIL", settings.ADMIN_EMAIL, {"required": True, "pattern": r"^[^@]+@[^@]+\.[^@]+$"}),
    ("ADMIN_PASSWORD", settings.ADMIN_PASSWORD, {"required": True, "min_length": 8, "mask": True}),
]

for var_name, var_value, checks in critical_checks:
    ok, status, display_value = verify_variable(
        var_name, 
        var_value,
        url_type=checks.get("url_type"),
        min_length=checks.get("min_length"),
        required=checks.get("required", False)
    )
    
    if not ok:
        all_ok = False
    print(f"{status} {var_name:30} = {display_value}")

# ── VERCEL-SPECIFIC CHECKS ────────────────────────────────────────────────
print("\n🌐 VERCEL-SPECIFIC CHECKS:")
print("-" * 70)

vercel_checks = []

# Check GOOGLE_REDIRECT_URI matches BASE_URL pattern
if "localhost" in settings.GOOGLE_REDIRECT_URI:
    vercel_checks.append(("GOOGLE_REDIRECT_URI", "⚠ LOCALHOST", "Should be https://YOUR-APP.vercel.app for production", False))
else:
    vercel_checks.append(("GOOGLE_REDIRECT_URI", "✓", "Points to production domain", True))

# Check BASE_URL matches GOOGLE_REDIRECT_URI
base_domain = settings.BASE_URL.replace("https://", "").replace("http://", "").split("/")[0]
redirect_domain = settings.GOOGLE_REDIRECT_URI.replace("https://", "").replace("http://", "").split("/")[0]
if base_domain == redirect_domain:
    vercel_checks.append(("BASE_URL ↔ GOOGLE_REDIRECT_URI", "✓", "Domains match", True))
else:
    vercel_checks.append(("BASE_URL ↔ GOOGLE_REDIRECT_URI", "⚠ MISMATCH", f"{base_domain} ≠ {redirect_domain}", False))

# Check ADMIN credentials are different from defaults
if settings.ADMIN_PASSWORD == "admin123":
    vercel_checks.append(("ADMIN_PASSWORD", "⚠ WEAK", "Using default 'admin123' - change for security!", False))
else:
    vercel_checks.append(("ADMIN_PASSWORD", "✓", "Custom password set", True))

for check_name, status, message, is_ok in vercel_checks:
    print(f"{status} {check_name:30} - {message}")
    if not is_ok and "MISMATCH" in status:
        all_ok = False

# ── OPTIONAL VARIABLES ────────────────────────────────────────────────
print("\n🟡 OPTIONAL VARIABLES (Nice to have):")
print("-" * 70)

optional_checks = [
    ("SEND_DELAY_SECONDS", str(settings.SEND_DELAY_SECONDS), "Email throttle delay"),
    ("MAX_ATTACHMENT_SIZE_MB", str(settings.MAX_ATTACHMENT_SIZE_MB), "File upload limit"),
    ("ACCESS_TOKEN_EXPIRE_MINUTES", str(settings.ACCESS_TOKEN_EXPIRE_MINUTES), "Token expiry time"),
]

for var_name, var_value, description in optional_checks:
    status = "✓" if var_value else "⚠ EMPTY"
    print(f"{status} {var_name:30} = {var_value:15} ({description})")

# ── DATABASE CONNECTION TEST ────────────────────────────────────────────────
print("\n🧪 DATABASE CONNECTION TEST:")
print("-" * 70)

try:
    # Just verify the URL format, don't try to connect
    if settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
        print("✓ DATABASE_URL format is correct (async)")
    else:
        print("✗ DATABASE_URL format is incorrect")
        all_ok = False
    
    if settings.DATABASE_URL_SYNC.startswith("postgresql://"):
        print("✓ DATABASE_URL_SYNC format is correct (sync)")
    else:
        print("✗ DATABASE_URL_SYNC format is incorrect")
        all_ok = False
        
    # Only try actual connection if localhost (dev environment)
    if "localhost" not in settings.DATABASE_URL:
        print("⚠ Production database - skipping connection test")
    else:
        print("ℹ Local database - test with: psql $DATABASE_URL_SYNC")
except Exception as e:
    print(f"⚠ Could not verify database: {str(e)}")

# ── SUMMARY ────────────────────────────────────────────────────────────────
print("\n" + "="*70)
if all_ok:
    print("✅ ALL CHECKS PASSED - Ready for Vercel deployment!")
    print("\nNext steps:")
    print("1. Commit these changes: git add . && git commit -m 'chore: add env setup'")
    print("2. Set variables in Vercel dashboard:")
    print("   - Go to Settings → Environment Variables")
    print("   - Add all CRITICAL variables from above")
    print("3. Deploy: vercel --prod")
    print("="*70 + "\n")
else:
    print("⚠️  SOME CHECKS FAILED - Fix issues before deploying")
    print("\nFor help, see:")
    print("- ENVIRONMENT_VARIABLES.md (complete reference)")
    print("- VERCEL_DEPLOYMENT.md (deployment guide)")
    print("="*70 + "\n")
    sys.exit(1)
