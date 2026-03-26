# Vercel Deployment - Quick Checklist

## ✅ Code Fixes Applied
- [x] `backend/core/config.py` - Environment variable loading fixed
- [x] `backend/main.py` - Startup logging enhanced
- [x] Configuration now checks for .env file before loading
- [x] Removed localhost defaults for production variables
- [x] Missing critical variables will now show clear warnings

---

## 📋 Pre-Deployment Checklist

### Before you redeploy, complete these steps:

**1. Set Environment Variables in Vercel Dashboard**
- [ ] Go to: vercel.com → Your Project → Settings → Environment Variables
- [ ] Add these 10 CRITICAL variables (copy from your local `.backend/.env`):
  
   **Connection:**
   - [ ] `DATABASE_URL`
   - [ ] `DATABASE_URL_SYNC`
   
   **Security:**
   - [ ] `SECRET_KEY` (strong random string, NOT "change-me-in-production-use-strong-secret")
   
   **Google OAuth:**
   - [ ] `GOOGLE_CLIENT_ID`
   - [ ] `GOOGLE_CLIENT_SECRET`  
   - [ ] `GOOGLE_REDIRECT_URI` (set to `https://YOUR-VERCEL-URL.vercel.app/api/auth/google/callback`)
   
   **URLs:**
   - [ ] `BASE_URL` (set to `https://YOUR-VERCEL-URL.vercel.app`)
   - [ ] `FRONTEND_URL` (set to `https://YOUR-VERCEL-URL.vercel.app`)
   
   **Admin Account:**
   - [ ] `ADMIN_EMAIL` (your admin email)
   - [ ] `ADMIN_PASSWORD` (strong password)

**2. Verify Settings**
- [ ] All 10 variables show as "Set" in Vercel Dashboard
- [ ] No variable is blank or empty
- [ ] DATABASE_URL starts with `postgresql+asyncpg://`
- [ ] URL variables start with `https://` (not `http://` for production)
- [ ] SECRET_KEY is NOT the default text "change-me-..."

**3. Deploy**
```bash
# Option A: Push to GitHub (if connected)
git add -A
git commit -m "fix: vercel environment variable loading"
git push origin main

# Option B: Direct deploy to Vercel
vercel --prod
```

---

## 📊 After Deployment

**Monitor the Logs:**
1. Go to Vercel Dashboard → Deployments → Select your deployment
2. Scroll to "Function Logs" and wait for startup
3. You should see:
   ```
   ============================================================
   🚀 Starting up Claim360 API...
   ============================================================
   ✓ Configuration loaded successfully
   Environment: VERCEL
   ✓ Database initialized successfully.
   ============================================================
   ✓ Startup complete - API ready to serve requests
   ============================================================
   ```

**Test the App:**
```bash
# Replace YOUR-VERCEL-URL with your actual Vercel URL
curl https://YOUR-VERCEL-URL.vercel.app/api/health

# Should return:
# {"status":"ok","message":"API and Database are connected"}
```

**Manual Testing:**
- [ ] Load app in browser - should see login page
- [ ] Admin tab should be visible with orange styling
- [ ] Google OAuth button should redirect properly
- [ ] Admin login should work with credentials you set

---

## ⚠️ If Deployment Fails

**Check these in order:**

1. **Look at Function Logs for errors**
   - Vercel Dashboard → Deployments → Function Logs
   - Look for lines starting with ❌ or ERROR

2. **Common Issues:**
   - ❌ `Database connection failed` → DATABASE_URL is wrong or not set
   - ❌ `OAuth redirect mismatch` → GOOGLE_REDIRECT_URI doesn't match Google Console
   - ❌ `SECRET_KEY must be set` → SECRET_KEY is empty or using default
   - ❌ `CRITICAL: Missing variables: ...` → Some env vars not set in Vercel

3. **Fix:**
   - Return to Vercel Dashboard → Environment Variables
   - Update the variable that's failing
   - Redeploy with `vercel --prod`

---

## 📚 Reference Documents

- **Full Details**: [VERCEL_DEPLOYMENT_FIX.md](./VERCEL_DEPLOYMENT_FIX.md)
- **Environment Variables**: [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)
- **Configuration**: [backend/core/config.py](./backend/core/config.py)
- **Startup Logic**: [backend/main.py](./backend/main.py)

---

## 🎯 Summary

**What was broken:**
- Configuration was trying to load .env file on Vercel (where it doesn't exist)
- Would silently fall back to localhost URLs
- App would connect to wrong database or fail to start

**What was fixed:**
- Configuration now checks if .env exists before loading
- Production variables have no defaults - must come from environment
- Startup logs clearly show if configuration loaded successfully
- Missing variables trigger clear warnings

**What you need to do:**
1. ✅ Code is already fixed
2. ⏳ Set 10 environment variables in Vercel Dashboard  
3. ⏳ Deploy the fixed code
4. ⏳ Verify app starts successfully
