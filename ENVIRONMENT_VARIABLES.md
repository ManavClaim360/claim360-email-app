# 🔐 Environment Variables Audit & Configuration Guide

## 📊 Variables Status Check

### ✅ VERIFIED WORKING VARIABLES (All Active)

| Variable | Type | Used In | Required | Default | Vercel Needed |
|----------|------|---------|----------|---------|---------------|
| `SECRET_KEY` | string | JWT token generation | ✅ YES | "change-me-in-production-use-strong-secret" | ✅ REQUIRED |
| `ALGORITHM` | string | JWT encoding | ❌ NO | "HS256" | ❌ NO |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | Token expiry | ❌ NO | 10080 (7 days) | ❌ NO |
| `DATABASE_URL` | string | Async DB connection | ✅ YES | postgresql+asyncpg://... | ✅ REQUIRED |
| `DATABASE_URL_SYNC` | string | Sync DB operations | ❌ RARELY | postgresql://... | ✅ REQUIRED |
| `GOOGLE_CLIENT_ID` | string | OAuth login | ✅ YES | "" (empty) | ✅ REQUIRED |
| `GOOGLE_CLIENT_SECRET` | string | OAuth login | ✅ YES | "" (empty) | ✅ REQUIRED |
| `GOOGLE_REDIRECT_URI` | string | OAuth callback | ✅ YES | "http://localhost:8000/api/auth/oauth/callback" | ✅ REQUIRED |
| `GOOGLE_SCOPES` | list | Gmail API permissions | ✅ YES (hardcoded) | 4 scopes | ❌ NO (hardcoded) |
| `UPLOAD_DIR` | string | File storage | ✅ YES | "uploads" | ❌ NO |
| `MAX_ATTACHMENT_SIZE_MB` | int | File upload limit | ✅ YES | 25 | ❌ NO |
| `SEND_DELAY_SECONDS` | int | Email throttling | ✅ YES | 3 | ❌ NO |
| `BASE_URL` | string | Tracking pixel URLs | ✅ YES | "http://localhost:8000" | ✅ REQUIRED |
| `FRONTEND_URL` | string | OAuth redirect after login | ✅ YES | "http://localhost:3000" | ✅ REQUIRED |
| `ADMIN_EMAIL` | string | Admin account creation | ✅ YES | "admin@company.com" | ✅ REQUIRED |
| `ADMIN_PASSWORD` | string | Admin account creation | ✅ YES | "admin123" | ✅ REQUIRED |
| `APP_NAME` | string | API title | ❌ NO | "Claim360 Email WebApp" | ❌ NO |
| `REDIS_URL` | string | Celery (not used) | ❌ NO | "redis://localhost:6379/0" | ❌ NO |
| `CELERY_BROKER_URL` | string | Celery (not used) | ❌ NO | "redis://localhost:6379/0" | ❌ NO |
| `CELERY_RESULT_BACKEND` | string | Celery (not used) | ❌ NO | "redis://localhost:6379/0" | ❌ NO |
| `SYSTEM_EMAIL` | string | Sending OTP emails | ❌ OPTIONAL | Defaults to console | ❌ NO (optional) |
| `SYSTEM_EMAIL_PASSWORD` | string | SMTP authentication | ❌ OPTIONAL | Defaults to console | ❌ NO (optional) |

---

## 🚀 REQUIRED VARIABLES FOR VERCEL (MUST SET)

### Critical: Set These in Vercel Dashboard

1. **SECRET_KEY** ✅
   - **What**: Random string for signing JWT tokens
   - **Where Set**: Vercel Dashboard → Environment Variables
   - **How to Generate**: 
     ```bash
     python3 -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - **Example**: `qF-2v8pKj9_L4mN3xV6wZ1aB7cD5eF3`
   - **Impact**: Without this, token signing fails and users can't log in
   - **Status**: ⚠️ **CRITICAL**

2. **DATABASE_URL** ✅
   - **What**: Async PostgreSQL connection string
   - **Format**: `postgresql+asyncpg://user:password@host:port/database`
   - **Where Get**: Your Neon, Supabase, Railway, or RDS database
   - **Example**: `postgresql+asyncpg://john:mypass@db.neon.tech/claim360?sslmode=require`
   - **Impact**: Without this, API cannot access database
   - **Status**: ⚠️ **CRITICAL**

3. **DATABASE_URL_SYNC** ✅
   - **What**: Synchronous PostgreSQL connection (rarely used, for migrations)
   - **Format**: `postgresql://user:password@host:port/database`
   - **Example**: `postgresql://john:mypass@db.neon.tech/claim360?sslmode=require`
   - **Note**: Can be same as DATABASE_URL (just change asyncpg to plain postgresql)
   - **Impact**: Migrations and schema operations
   - **Status**: ⚠️ **CRITICAL**

4. **GOOGLE_CLIENT_ID** ✅
   - **What**: Google OAuth client identifier
   - **Where Get**: [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
   - **Example**: `123456789.apps.googleusercontent.com`
   - **Impact**: Without this, OAuth login doesn't work
   - **Status**: ⚠️ **CRITICAL**

5. **GOOGLE_CLIENT_SECRET** ✅
   - **What**: Google OAuth client secret key
   - **Where Get**: Same as above
   - **Example**: `GOCSPX-_ABC123xyz...`
   - **⚠️ IMPORTANT**: Never expose this in code or version control
   - **Impact**: Without this, OAuth fails
   - **Status**: ⚠️ **CRITICAL**

6. **GOOGLE_REDIRECT_URI** ✅
   - **What**: Where Google redirects after OAuth approval
   - **Format**: `https://YOUR-APP.vercel.app/api/auth/oauth/callback`
   - **Example**: `https://claim360.vercel.app/api/auth/oauth/callback`
   - **⚠️ IMPORTANT**: Must match exactly in Google Cloud Console
   - **Impact**: OAuth callback will fail if mismatched
   - **Status**: ⚠️ **CRITICAL**

7. **BASE_URL** ✅
   - **What**: Your Vercel app's public URL (for tracking pixels)
   - **Format**: `https://YOUR-APP.vercel.app`
   - **Example**: `https://claim360.vercel.app`
   - **Impact**: Email tracking won't work if wrong
   - **Status**: ⚠️ **CRITICAL**

8. **FRONTEND_URL** ✅
   - **What**: Frontend URL for OAuth redirect after login
   - **Format**: `https://YOUR-APP.vercel.app`
   - **Example**: `https://claim360.vercel.app`
   - **Note**: Usually same as BASE_URL if frontend and backend are on same domain
   - **Impact**: OAuth redirect loop if wrong
   - **Status**: ⚠️ **CRITICAL**

9. **ADMIN_EMAIL** ✅
   - **What**: Email of the admin account created on first deploy
   - **Format**: `admin@yourcompany.com`
   - **Example**: `admin@claim360.com`
   - **Impact**: Admin account won't be created if missing
   - **Status**: ⚠️ **CRITICAL**

10. **ADMIN_PASSWORD** ✅
    - **What**: Password for the admin account
    - **Format**: `StrongPassword123` (min 8 chars, recommended 12+)
    - **⚠️ IMPORTANT**: Change this to a secure password!
    - **Impact**: Admin account won't be usable if wrong
    - **Status**: ⚠️ **CRITICAL**

---

## ✅ OPTIONAL VARIABLES (Nice-to-Have)

| Variable | Purpose | Default | Recommended |
|----------|---------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | 10080 (7 days) | Keep as is |
| `SEND_DELAY_SECONDS` | Delay between sending emails | 3 | 1-5 seconds |
| `MAX_ATTACHMENT_SIZE_MB` | File upload limit | 25 | 25-50 MB |
| `UPLOAD_DIR` | Where to store files | "uploads" | Keep as is |
| `SYSTEM_EMAIL` | For sending OTP codes | Console output | Gmail address |
| `SYSTEM_EMAIL_PASSWORD` | For SMTP | Not sent | Gmail app password |

---

## 🔍 VARIABLE TESTING GUIDE

### Test Locally Before Deploying

```bash
cd backend

# 1. Create .env file with all variables
cp .env.example .env
# Edit .env with your values

# 2. Test if variables load correctly
python3 -c "
from core.config import get_settings
settings = get_settings()
print(f'✓ DATABASE_URL: {settings.DATABASE_URL[:30]}...')
print(f'✓ SECRET_KEY loaded: {bool(settings.SECRET_KEY)}')
print(f'✓ GOOGLE_CLIENT_ID loaded: {bool(settings.GOOGLE_CLIENT_ID)}')
print(f'✓ ADMIN_EMAIL: {settings.ADMIN_EMAIL}')
print(f'✓ BASE_URL: {settings.BASE_URL}')
"

# 3. Initialize database with admin user
cd ..
python3 scripts/init_db.py
# Should output: ✅ Admin created: admin@company.com / password

# 4. Start backend and check health
cd backend
uvicorn main:app --reload --port 8000

# 5. Test API in another terminal
curl http://localhost:8000/api/health
# Should show: {"status": "ok", "message": "API and Database are connected"}
```

---

## 🎯 VERCEL DEPLOYMENT VARIABLES CHECKLIST

### Command Line Setup (Using Vercel CLI)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login and link project
vercel login
vercel link

# 3. Add environment variables (interactive)
vercel env add SECRET_KEY
vercel env add DATABASE_URL
vercel env add DATABASE_URL_SYNC
vercel env add GOOGLE_CLIENT_ID
vercel env add GOOGLE_CLIENT_SECRET
vercel env add GOOGLE_REDIRECT_URI
vercel env add BASE_URL
vercel env add FRONTEND_URL
vercel env add ADMIN_EMAIL
vercel env add ADMIN_PASSWORD

# 4. Verify they're set
vercel env list

# 5. Deploy
vercel --prod
```

### Using Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable:
   - Key: (e.g., `SECRET_KEY`)
   - Value: (e.g., `qF-2v8pKj9_L4mN3xV6wZ1aB7cD5eF3`)
   - Environments: Select **Production** (and Preview if needed)
   - Click **Add**
5. Redeploy or manually redeploy from Deployments tab

---

## ⚠️ COMMON VARIABLE MISTAKES

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `GOOGLE_REDIRECT_URI` doesn't match Google Cloud | OAuth: "redirect_uri_mismatch" error | Update in both Vercel AND Google Cloud Console |
| `SECRET_KEY` is default or weak | JWT errors, security risk | Generate strong key with `secrets.token_urlsafe(32)` |
| `DATABASE_URL` is wrong | "Connection refused" or "authentication failed" | Test locally: `psql $DATABASE_URL_SYNC` |
| `BASE_URL` is localhost | Email tracking doesn't work in production | Set to `https://YOUR-APP.vercel.app` |
| Missing `ADMIN_EMAIL/PASSWORD` | Admin account not created | Set before first deployment |
| `FRONTEND_URL` still points to localhost | OAuth redirects to wrong URL | Update to `https://YOUR-APP.vercel.app` |

---

## 🧪 VERIFICATION SCRIPT

Create `check_env_vars.py` to audit all variables:

```python
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, 'backend')
from core.config import get_settings

settings = get_settings()

print("\n" + "="*60)
print("ENVIRONMENT VARIABLES AUDIT")
print("="*60 + "\n")

critical_vars = [
    'SECRET_KEY', 'DATABASE_URL', 'GOOGLE_CLIENT_ID', 
    'GOOGLE_CLIENT_SECRET', 'GOOGLE_REDIRECT_URI',
    'BASE_URL', 'FRONTEND_URL', 'ADMIN_EMAIL', 'ADMIN_PASSWORD'
]

print("CRITICAL VARIABLES (Required for Vercel):")
print("-" * 60)
for var in critical_vars:
    value = getattr(settings, var, None)
    status = "✓" if value and value != "" else "✗ MISSING"
    if var in ['SECRET_KEY', 'GOOGLE_CLIENT_SECRET']:
        printed = "***" if value else "NOT SET"
    else:
        printed = str(value)[:40] + "..." if value else "NOT SET"
    print(f"{status} {var:25} = {printed}")

print("\n")
print("✓ Ready for Vercel!" if all(getattr(settings, v) for v in critical_vars) else "⚠️ Missing critical variables!")
```

Run with:
```bash
python3 check_env_vars.py
```

---

## 🚀 QUICK REFERENCE

### Minimum Viable Setup
```env
SECRET_KEY=your-strong-random-key
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
DATABASE_URL_SYNC=postgresql://user:pass@host/dbname
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REDIRECT_URI=https://your-app.vercel.app/api/auth/oauth/callback
BASE_URL=https://your-app.vercel.app
FRONTEND_URL=https://your-app.vercel.app
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=StrongPassword123
```

### After Setting All Variables
1. ✅ Deploy with `vercel --prod`
2. ✅ Check logs for errors
3. ✅ Test endpoints:
   - API Health: `curl https://your-app.vercel.app/api/health`
   - Admin Login: POST to `/api/auth/login` with admin credentials
   - OAuth: Click "Connect with Google"

---

## 📞 Troubleshooting

### "SettingError: could not parse obj as JSON" during startup
**Cause**: Environment variable format is wrong
**Fix**: Check database URL format, ensure no invalid characters

### "JWT Token Decode Error"
**Cause**: `SECRET_KEY` is wrong or wasn't used when token was created
**Fix**: Don't change `SECRET_KEY` after users have tokens. Generate new key only for new deploy.

### "Email already registered" when registering admin
**Cause**: Admin already exists from previous deployment
**Fix**: This is normal. Delete user from database or change `ADMIN_EMAIL` for next deployment

### Database shows "no such table: users"
**Cause**: `init_db()` didn't run properly
**Fix**: 
- Check `DATABASE_URL` is correct
- Manually run: `python3 scripts/init_db.py`
- Or redeploy (Vercel will run init_db on startup)

---

**Last Updated**: March 26, 2026  
**Status**: ✅ All variables verified and documented
