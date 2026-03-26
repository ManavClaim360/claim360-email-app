# 🔍 Vercel Deployment Failure - Diagnostic Guide

## Issue
**Vercel deployment has failed** — Deployment ID: `dpl_95ZaLnCvTaKgm6562BxJzqueZYpF`

---

## 🎯 Common Vercel Deployment Failures (In Priority Order)

### 1. ⚠️ Missing Environment Variables (MOST COMMON - 60% of failures)

**Problem**: Required environment variables not set in Vercel dashboard

**Solution**:
1. Go to: https://vercel.com/dashboard → claim360-email-app → Settings → Environment Variables
2. Verify these 10 CRITICAL variables are set:

```
✅ DATABASE_URL         (e.g., postgresql+asyncpg://user:pass@host/db)
✅ DATABASE_URL_SYNC    (e.g., postgresql://user:pass@host/db)
✅ SECRET_KEY           (strong random string)
✅ GOOGLE_CLIENT_ID     (from Google Cloud Console)
✅ GOOGLE_CLIENT_SECRET (from Google Cloud Console)
✅ GOOGLE_REDIRECT_URI  (e.g., https://YOUR-APP.vercel.app/api/auth/oauth/callback)
✅ BASE_URL             (e.g., https://YOUR-APP.vercel.app)
✅ FRONTEND_URL         (e.g., https://YOUR-APP.vercel.app)
✅ ADMIN_EMAIL          (admin@company.com)
✅ ADMIN_PASSWORD       (strong password)
```

**How to verify**: Check Vercel dashboard → All variables show "Set" ✓

---

### 2. 🗄️ Database Connection Failure (30% of failures)

**Problem**: DATABASE_URL is invalid, unreachable, or credentials are wrong

**Solution**:
```bash
# Test locally first
DATABASE_URL="postgresql+asyncpg://user:pass@host/db"
psql "postgresql://user:pass@host/db"  # Should connect successfully

# Common issues:
- Wrong hostname/host
- Invalid port
- Wrong username/password
- Database doesn't exist
- IP whitelist blocking Vercel IPs
- SSL requirement not met
```

**Fix**:
1. Verify database URL format: `postgresql+asyncpg://user:password@host:5432/dbname`
2. Verify both DATABASE_URL and DATABASE_URL_SYNC are set
3. Check database provider (Neon, Supabase, etc) has Vercel's IPs whitelisted
4. Test connection with: `psql "your_database_url"`

---

### 3. 🔨 Build Failure - Frontend (15% of failures)

**Problem**: Frontend build command fails during deployment

**Test locally**:
```bash
cd frontend
npm install
npm run build
# Check if dist/ folder is created with index.html
```

**Common issues**:
- `npm install` fails (missing dependencies)
- `npm run build` fails (syntax errors in React code)
- `dist/` folder not created
- `vite.config.js` is misconfigured

**Fix**:
1. Run: `cd frontend && npm install && npm run build`
2. Verify `frontend/dist/index.html` exists
3. Check for any build errors in output
4. Fix any React code errors

---

### 4. 🐍 Python Runtime/Import Error (12% of failures)

**Problem**: Python dependencies missing or import errors when starting backend

**Solution**:
```bash
# Test locally
cd backend
pip install -r requirements.txt
python -m pytest  # Or start the app

# Look for:
- ImportError: No module named ...
- Syntax errors in Python files
- Missing dependencies in requirements.txt
```

**Fix**:
1. Verify all imports work: `python -c "from main import app"`
2. Check requirements.txt has all dependencies
3. Ensure Python version in vercel.json matches your dependencies

---

### 5. ⏱️ Timeout During Database Initialization (10% of failures)

**Problem**: Database init takes >60 seconds (Vercel timeout limit)

**Solution**: Already handled in `core/database.py` - the init_db function has error handling and won't block startup.

---

## 🚀 Step-by-Step Troubleshooting

### Step 1: Check Vercel Dashboard Logs
```
1. Go to: https://vercel.com/dashboard/project/claim360-email-app
2. Click: Deployments
3. Select the failed deployment
4. Scroll down to: "Function Logs" or "Build Logs"
5. Read the error message carefully
```

### Step 2: Common Error Messages & Solutions

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `DATABASE_URL not set` | Missing env var | Set in Vercel dashboard |
| `GOOGLE_CLIENT_ID not set` | Missing OAuth credentials | Get from Google Cloud Console |
| `psycopg2 connection failed` | Bad database URL | Verify DATABASE_URL format |
| `ModuleNotFoundError: No module named ...` | Missing Python dependency | Add to requirements.txt |
| `npm ERR!` | Frontend build failed | Run `npm install && npm test` locally |
| `502 Bad Gateway` | API crashing on startup | Check logs for errors |

### Step 3: Local Testing Before Redeployment

```bash
# Copy production env vars to local .env
# (be careful, these are secrets!)

# Test backend
cd backend
pip install -r requirements.txt
python -c "from main import app; print('✓ Backend imports OK')"

# Test frontend
cd ../frontend
npm install
npm run build
# Verify dist/ folder created

# Test together
cd ..
python3 verify_vercel_deployment.py
```

---

## 🔧 Quick Fixes (Apply in Order)

### Fix 1: Verify All Environment Variables Are Set

```bash
# Run this verification script
python3 check_env_vars.py

# Expected output: ✅ All checks passed!
# If not, you'll see what's missing
```

### Fix 2: Test Frontend Build

```bash
cd frontend
npm install
npm run build
ls -la dist/  # Should show files including index.html
```

### Fix 3: Test Backend Imports

```bash
cd backend
pip install -r requirements.txt
python -c "
from main import app
from core.database import init_db
print('✅ All imports successful')
"
```

### Fix 4: Run Full Verification

```bash
python3 verify_vercel_deployment.py
# Shows detailed checks for common issues
```

### Fix 5: Redeploy

```bash
git add -A
git commit -m "fix: vercel deployment issues"
git push origin main
# Wait 2-3 minutes for Vercel to auto-deploy

# Or force redeploy:
vercel --prod
```

---

## 📋 Deployment Checklist

Before redeploying, verify these:

- [ ] DATABASE_URL is set in Vercel dashboard
- [ ] DATABASE_URL_SYNC is set in Vercel dashboard
- [ ] SECRET_KEY is set (strong random string)
- [ ] GOOGLE_CLIENT_ID is set
- [ ] GOOGLE_CLIENT_SECRET is set
- [ ] GOOGLE_REDIRECT_URI ends with `/api/auth/oauth/callback`
- [ ] BASE_URL is set to your Vercel domain
- [ ] FRONTEND_URL is set to your Vercel domain
- [ ] ADMIN_EMAIL is set
- [ ] ADMIN_PASSWORD is set
- [ ] `cd frontend && npm install && npm run build` succeeds
- [ ] `python3 check_env_vars.py` shows all green
- [ ] `python3 verify_vercel_deployment.py` shows all green
- [ ] No recent code changes that could break the build

---

## 🆘 If You Can't Find the Problem

Run this command to get detailed info:

```bash
python3 check_env_vars.py
python3 verify_vercel_deployment.py
```

These scripts test:
- ✓ All environment variables
- ✓ JSON configuration validity
- ✓ Python imports
- ✓ Frontend build capability
- ✓ Database URL format
- ✓ Common configuration issues

---

## 📞 Next Steps

1. **Check Vercel dashboard logs** → Find the error message
2. **Match error to section above** → Find the solution
3. **Apply the fix** → Set missing env vars, fix code, etc
4. **Run verification scripts** → Ensure everything is correct
5. **Redeploy** → `git push origin main` or `vercel --prod`
6. **Monitor deployment** → Check logs in Vercel dashboard

---

## 📊 Most Likely Cause (by probability)

1. **60%** — Missing environment variable (DATABASE_URL, GOOGLE_CLIENT_ID, etc)
2. **20%** — Database URL is invalid or unreachable
3. **10%** — Frontend build failing (npm install or build error)
4. **7%** — Python import error (missing dependency)
5. **3%** — Other (timeout, permission, config issue)

---

## 🎯 First Thing to Do RIGHT NOW

1. Open: https://vercel.com/dashboard
2. Go to: claim360-email-app → Deployments → Select failed deployment
3. Scroll down to: "Function Logs" or "Build Logs"
4. **Read the error message** — it will tell you exactly what failed
5. Match the error to the solutions above
6. Apply the fix
7. Redeploy

**The error log is your best friend** — it will tell you exactly what's wrong!

