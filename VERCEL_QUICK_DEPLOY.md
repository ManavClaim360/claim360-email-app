# 🚀 Vercel Deployment - Quick Reference

## ⚡ Quick Deploy (5 minutes)

### Step 1: Set Environment Variables (2 min)
Go to Vercel Dashboard → Project Settings → Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://[USER]:[PASS]@[HOST]/[DB]
DATABASE_URL_SYNC=postgresql://[USER]:[PASS]@[HOST]/[DB]
SECRET_KEY=your-strong-random-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://YOUR-APP.vercel.app/api/auth/oauth/callback
BASE_URL=https://YOUR-APP.vercel.app
FRONTEND_URL=https://YOUR-APP.vercel.app
ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=StrongPassword123
```

### Step 2: Add OAuth Redirect URI to Google Cloud (1 min)
1. Google Cloud Console → APIs & Services → Credentials
2. Edit OAuth Client → Authorized redirect URIs
3. Add: `https://YOUR-APP.vercel.app/api/auth/oauth/callback`

### Step 3: Verify Before Deploy (1 min)
```bash
python3 verify_vercel_deployment.py
# Should show: ✅ All checks passed!
```

### Step 4: Deploy (1 min)
```bash
vercel --prod
# or use Vercel Dashboard
```

---

## ✅ Post-Deploy Verification

### Test API Health
```bash
curl https://YOUR-APP.vercel.app/api/health
```

**Expected Response**:
```json
{"status": "ok", "message": "API and Database are connected"}
```

### Test Frontend
Open `https://YOUR-APP.vercel.app` in browser
- Should load React app
- Should see login page
- No console errors

### Test OAuth
1. Click "Connect with Google"
2. Should redirect to Google login
3. Should redirect back and create user

---

## 🆘 Quick Troubleshooting

### "502 Bad Gateway" or API not responding
```bash
# Check deployment logs in Vercel dashboard
vercel logs --prod
```

**Common causes**:
- Environment variable not set → Fix in Vercel dashboard
- Database URL wrong → Verify DATABASE_URL
- Google OAuth credentials wrong → Verify credentials

### "Failed to authenticate" 
**Cause**: GOOGLE_REDIRECT_URI doesn't match  
**Fix**: Go to Google Cloud Console, update redirect URI to match your Vercel URL

### "CORS Error" in browser console
**Cause**: Frontend can't reach backend API  
**Fix**: Check `VITE_API_URL` environment variable (should be empty or your backend URL)

### Database "connection refused"
**Cause**: DATABASE_URL is wrong or database is down  
**Fix**: 
1. Test locally: `psql $DATABASE_URL_SYNC`
2. Verify database service is running
3. Check IP whitelist settings in database admin

---

## 📚 Full Documentation

- **Complete Guide**: VERCEL_DEPLOYMENT.md
- **Audit Report**: VERCEL_AUDIT_REPORT.md
- **What Was Fixed**: FIXES_SUMMARY.md
- **Verification Script**: verify_vercel_deployment.py

---

## 🎯 Important Notes

1. **Database URL Format**
   - Must use `postgresql+asyncpg://` for async operations
   - Must have full credentials and database name

2. **Google OAuth**
   - Redirect URI must exactly match (including https://)
   - Update both Vercel environment variable AND Google Console

3. **Environment Variables**
   - Set all required variables BEFORE deploying
   - Missing variables will cause deployment failures

4. **Cold Starts**
   - First request after deployment might be slow (up to 30s)
   - Subsequent requests are fast (<500ms)

---

## ✨ You're All Set!

Your Claim360 app is 100% Vercel-ready. Follow these 4 steps and you're live in minutes.

**Need help?** See VERCEL_DEPLOYMENT.md for detailed troubleshooting.
