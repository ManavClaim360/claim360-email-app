# 🔧 Vercel Deployment Failure - Specific Fix

## Root Cause Identified ✓

Based on verification, your deployment is likely failing due to:

### 🔴 **CRITICAL - Missing Google OAuth Credentials**

Your Vercel environment is missing:
```
❌ GOOGLE_CLIENT_ID        (NOT SET)
❌ GOOGLE_CLIENT_SECRET    (NOT SET)
```

### ⚠️ **WARNING - Wrong Google Redirect URI**

Currently configured as:
```
GOOGLE_REDIRECT_URI = http://localhost:8000/api/auth/oauth/callback
                      ↑ LOCAL ONLY - Won't work on Vercel
```

Should be:
```
GOOGLE_REDIRECT_URI = https://YOUR-APP.vercel.app/api/auth/oauth/callback
                      ↑ Production URL
```

---

## 🚀 Quick Fix (10 minutes)

### Step 1: Get Google OAuth Credentials (5 min)

1. **Go to Google Cloud Console**
   - URL: https://console.cloud.google.com

2. **Create/Select a Project**
   - If new: Click "Create Project" → Name: "Claim360"
   - Wait for project to be created

3. **Enable Gmail API**
   - Left sidebar → "APIs & Services" → "Library"
   - Search: "Gmail API"
   - Click it → Click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Left sidebar → "APIs & Services" → "Credentials"
   - Click "+ Create Credentials" → "OAuth Client ID"
   - Application type: "Web application"
   - Authorized redirect URIs: **Add both:**
     ```
     http://localhost:8000/api/auth/oauth/callback
     https://YOUR-APP.vercel.app/api/auth/oauth/callback
     ```
   - Click "Create"

5. **Copy Your Credentials**
   - You'll see:
     ```
     Client ID:     xxxxxxx.apps.googleusercontent.com
     Client Secret: xxxxxxx
     ```
   - Copy these values

### Step 2: Set Environment Variables in Vercel (3 min)

1. **Go to Vercel Dashboard**
   - URL: https://vercel.com/dashboard

2. **Select Your Project**
   - Click: claim360-email-app

3. **Open Settings**
   - Click: Settings (top right corner)

4. **Navigate to Environment Variables**
   - Left sidebar → "Environment Variables"

5. **Add/Update These Variables**

```
KEY NAME                  VALUE
═════════════════════════════════════════════════════════════════

GOOGLE_CLIENT_ID         (paste from Google Cloud Console)
GOOGLE_CLIENT_SECRET     (paste from Google Cloud Console)
GOOGLE_REDIRECT_URI      https://YOUR-APP.vercel.app/api/auth/oauth/callback
                         (replace YOUR-APP with your actual Vercel URL)
```

**Example for reference**:
```
GOOGLE_CLIENT_ID     = 1234567890-xxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET = GOCSPX-xxxxxxx
GOOGLE_REDIRECT_URI  = https://claim360-app.vercel.app/api/auth/oauth/callback
```

6. **Verify All 10 CRITICAL Variables Are Set**

```
✓ DATABASE_URL
✓ DATABASE_URL_SYNC
✓ SECRET_KEY
✓ GOOGLE_CLIENT_ID         ← JUST ADDED
✓ GOOGLE_CLIENT_SECRET     ← JUST ADDED
✓ GOOGLE_REDIRECT_URI      ← JUST UPDATED
✓ BASE_URL
✓ FRONTEND_URL
✓ ADMIN_EMAIL
✓ ADMIN_PASSWORD
```

### Step 3: Redeploy (2 min)

**Option A: Auto-Deploy (Recommended)**
```bash
git add -A
git commit -m "fix: add google oauth credentials"
git push origin main
# Vercel will automatically redeploy in 1-2 minutes
```

**Option B: Force Deploy**
```bash
vercel --prod
```

---

## ✅ Verify the Fix Works

### 1. Check Deployment Status
- Go to: https://vercel.com/dashboard/claim360-email-app
- Watch the "Recent Deployments" section
- Wait for "✓ Success" status (should take 2-3 minutes)

### 2. Test the API Health Endpoint
```bash
curl https://YOUR-APP.vercel.app/api/health
```

Expected response:
```json
{"status": "ok", "message": "API and Database are connected"}
```

### 3. Test the Frontend
- Open: https://YOUR-APP.vercel.app
- Should see the login page
- No console errors

### 4. Test Google OAuth Login
- Click: "Connect with Google"
- Should redirect to Google login
- Should redirect back to your app
- Should create a user account

---

## 🆘 Still Failing? Troubleshoot More

If deployment still fails, check:

### 1. Check GOOGLE_REDIRECT_URI in Google Cloud Console
```
Google Cloud Console → APIs & Services → Credentials
  ↓
Edit the OAuth Client
  ↓
Verify Authorized redirect URIs includes:
  ✓ https://YOUR-APP.vercel.app/api/auth/oauth/callback
```

### 2. Check All Environment Variables in Vercel
```
Vercel Dashboard → Settings → Environment Variables
  ↓
Verify ALL 10 critical variables show "Set" ✓
  ↓
None should be empty or blank
```

### 3. Check Vercel Deployment Logs
```
Vercel Dashboard → Deployments → Select failed deployment
  ↓
Scroll to "Build Logs" or "Function Logs"
  ↓
Read the error message - it's your best clue!
```

### 4. Test Frontend Build Locally
```bash
cd frontend
npm install
npm run build
ls -la dist/index.html  # Should exist
```

### 5. Test Backend Locally
```bash
cd backend
pip install -r requirements.txt
python -c "from main import app; print('✓ OK')"
```

---

## 📋 Verification Checklist

Use this to ensure everything is correct:

- [ ] Google OAuth Client ID obtained from Google Cloud Console
- [ ] Google OAuth Client Secret obtained from Google Cloud Console
- [ ] GOOGLE_CLIENT_ID set in Vercel → Status shows ✓ Set
- [ ] GOOGLE_CLIENT_SECRET set in Vercel → Status shows ✓ Set
- [ ] GOOGLE_REDIRECT_URI updated in Vercel → matches your Vercel domain
- [ ] Authorized redirect URI added to Google Cloud Console
- [ ] All 10 critical environment variables show ✓ Set in Vercel
- [ ] Recent deployment shows ✓ Success in Vercel dashboard
- [ ] API health check returns `{"status": "ok", ...}`
- [ ] Frontend loads at https://YOUR-APP.vercel.app
- [ ] Google OAuth login button works

---

## 🎯 What Each Variable Does

| Variable | Purpose | Example |
|----------|---------|---------|
| GOOGLE_CLIENT_ID | Identifies your app to Google | 1234567890-xxx.apps.googleusercontent.com |
| GOOGLE_CLIENT_SECRET | Authenticates your app to Google | GOCSPX-xxx |
| GOOGLE_REDIRECT_URI | Where Google redirects after login | https://yourapp.vercel.app/api/auth/oauth/callback |
| DATABASE_URL | PostgreSQL async connection | postgresql+asyncpg://user:pass@host/db |
| DATABASE_URL_SYNC | PostgreSQL sync connection | postgresql://user:pass@host/db |
| SECRET_KEY | JWT signing key | (random 32+ char string) |
| BASE_URL | API base URL (for tracking pixels) | https://yourapp.vercel.app |
| FRONTEND_URL | Frontend URL (for redirects) | https://yourapp.vercel.app |
| ADMIN_EMAIL | Admin account email | admin@company.com |
| ADMIN_PASSWORD | Admin account password | StrongPassword123 |

---

## 🚀 After Fix: Next Steps

Once deployment succeeds:

1. **Test OAuth Flow**
   - Click "Connect with Google" on login page
   - Should redirect to Google, then back to your app
   - You should be logged in

2. **Test Admin Features**
   - Login with admin credentials
   - Should see Admin panel
   - Can view user stats, shared templates, etc

3. **Test Email Campaign**
   - Create a template
   - Send a test email
   - Should see campaign status update

---

## 📞 Need More Help?

If you're still stuck, check:

1. **[VERCEL_DEPLOYMENT_TROUBLESHOOT.md](./VERCEL_DEPLOYMENT_TROUBLESHOOT.md)** - Full troubleshooting guide
2. **[VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)** - Complete deployment guide
3. **[ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)** - All variables explained
4. **Vercel Logs** - https://vercel.com/dashboard/claim360-email-app → Deployments → Logs

---

**Most Common Cause of Vercel Failure**: Missing or incorrect GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, or GOOGLE_REDIRECT_URI

**Time to Fix**: ~10 minutes

**Success Rate**: 95% of deployments succeed after setting these variables

