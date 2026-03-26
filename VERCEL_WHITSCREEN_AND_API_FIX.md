# 🔧 Vercel Deployment - White Screen & API Error Fix

## Issue
Both URLs show white screen, API returns: `FUNCTION_INVOCATION_FAILED`

## Root Cause
**Critical environment variables are NOT set in Vercel dashboard**:
```
❌ GOOGLE_CLIENT_ID        = NOT SET
❌ GOOGLE_CLIENT_SECRET    = NOT SET
```

And these are pointing to localhost (should be production):
```
⚠️  BASE_URL               = http://localhost:3000
⚠️  FRONTEND_URL           = http://localhost:3000
⚠️  GOOGLE_REDIRECT_URI    = http://localhost:8000/...
```

Without these, the API cannot start → frontend shows white screen.

---

## ⚡ Quick Fix (5 minutes)

### Step 1: Go to Vercel Dashboard
- https://vercel.com/dashboard/claim360-email-app
- Click **Settings** → **Environment Variables**

### Step 2: Update Environment Variables

Update these variables to your **production URL** (replace `YOUR-APP` with your actual Vercel subdomain):

```
KEY                      CURRENT VALUE              NEW VALUE
═══════════════════════════════════════════════════════════════════

BASE_URL                 http://localhost:3000      https://YOUR-APP.vercel.app

FRONTEND_URL             http://localhost:3000      https://YOUR-APP.vercel.app

GOOGLE_REDIRECT_URI      http://localhost:8000/...  https://YOUR-APP.vercel.app/api/auth/oauth/callback

GOOGLE_CLIENT_ID         (NOT SET)                  (Get from Google Cloud Console)*

GOOGLE_CLIENT_SECRET     (NOT SET)                  (Get from Google Cloud Console)*
```

*If you don't have Google OAuth credentials yet:
1. Go to: https://console.cloud.google.com
2. APIs & Services → Credentials
3. Create OAuth 2.0 Client (Web application)
4. Copy Client ID and Secret

### Step 3: Redeploy

After updating settings:
```bash
git add -A
git commit -m "fix: update vercel environment variables for production"
git push origin main
```

This triggers auto-redeploy. Or manually: `vercel --prod`

---

## 🌐 Consolidating to One URL

Vercel automatically creates multiple URLs:
- `https://claim360-email-app-manavclaim360s-projects.vercel.app/` (full path)
- `https://claim360-email-app.vercel.app/` (shorter)

**To keep only one**:

### Option A: Use the Shorter URL (Recommended)
1. Keep using: `https://claim360-email-app.vercel.app/`
2. All your environment variables should point to this (already done suggested above)
3. The longer URL will still work but you can ignore it

### Option B: Set a Custom Domain
1. In Vercel: Settings → Domains
2. Add your custom domain (e.g., claim360.yourdomain.com)
3. Both auto-generated URLs still work, but primary is your custom domain

### Option C: Remove the Longer URL
This is more complex - you can't really "remove" Vercel-auto-generated URLs, but you can:
1. Just not use the longer one
2. Make sure all services point to: `https://claim360-email-app.vercel.app/`

---

## ✅ Verification Checklist

After fixing environment variables and redeploying:

- [ ] Vercel dashboard shows ✓ Success deployment
- [ ] API health check works: `curl https://claim360-email-app.vercel.app/api/health`
  - Should return: `{"status": "ok", ...}`
- [ ] Frontend loads (no white screen): `https://claim360-email-app.vercel.app/`
  - Should show login page
- [ ] Open browser console (F12) - no errors
- [ ] Click "Connect with Google" - should redirect to Google (if using OAuth)

---

## 📋 Your Actual Vercel URL

To find your exact Vercel URL:
1. Go to: https://vercel.com/dashboard/claim360-email-app
2. Look for the URL shown at the top of the deployments
3. Usually format: `https://PROJECT-NAME.vercel.app/`

For you, it's: `https://claim360-email-app.vercel.app/`

---

## 🚀 Expected Result

After updating environment variables and redeploying:

✅ Frontend loads with login page (no white screen)
✅ API responds to requests
✅ Google OAuth works (if credentials set)
✅ You can log in and use the app

---

## ⏱️ Timeline

- **Fix environment variables**: 5 minutes
- **Redeploy**: Auto (2-3 minutes) or manual (`vercel --prod`)
- **Total**: 10 minutes

---

**Status**: 🔴 **AWAITING ACTION** - Update environment variables in Vercel dashboard

