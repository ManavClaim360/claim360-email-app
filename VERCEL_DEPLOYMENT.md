# Claim360 Vercel Deployment Checklist

This guide ensures your Claim360 app is 100% Vercel-ready.

## Pre-Deployment Setup

### 1. Environment Variables

Set these in your Vercel dashboard (Settings → Environment Variables):

```
# Backend Database
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
DATABASE_URL_SYNC=postgresql://user:password@host/dbname

# Authentication
SECRET_KEY=your-very-strong-secret-key-change-in-production
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=strong-password

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-app.vercel.app/api/auth/oauth/callback

# URLs (important for OAuth and tracking)
BASE_URL=https://your-app.vercel.app
FRONTEND_URL=https://your-app.vercel.app

# Optional: Additional settings
ACCESS_TOKEN_EXPIRE_MINUTES=10080
SEND_DELAY_SECONDS=3
```

⚠️ **Critical**: Update `GOOGLE_REDIRECT_URI` and `FRONTEND_URL` to match your actual Vercel deployment URL.

### 2. Database Requirements

- Use a cloud PostgreSQL database (Neon, Supabase, Railway, Amazon RDS)
- Ensure SSL is enabled on your database connection
- Test the connection locally before deploying:
  ```bash
  psql "your-database-url"
  ```

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Update authorized redirect URIs to include:
   - `https://your-app.vercel.app/api/auth/oauth/callback`
3. Copy Client ID and Client Secret to Vercel environment variables

## Deployment

### Using Vercel CLI

```bash
# Install Vercel CLI (if not already installed)
npm install -g vercel

# Deploy from the root directory
vercel --prod
```

### Using Vercel Dashboard

1. Connect your GitHub repository to Vercel
2. Import project → Select the `claim360-email-app` repo
3. Framework: `Other`
4. Root Directory: `.` (root)
5. Set environment variables in Settings
6. Deploy

## Verification Checklist

After deployment, verify these endpoints:

- [ ] **API Health**: `https://your-app.vercel.app/api/health` → should return `{"status": "ok"}`
- [ ] **API Root**: `https://your-app.vercel.app/` → should return API version info
- [ ] **Frontend**: `https://your-app.vercel.app/` → should load React app
- [ ] **API Docs**: `https://your-app.vercel.app/docs` → should show Swagger UI
- [ ] **Login Page**: `https://your-app.vercel.app/login` → should load without errors

### Test API Connectivity

```bash
curl https://your-app.vercel.app/api/health
```

Expected response:
```json
{"status": "ok", "message": "API and Database are connected"}
```

### Test OAuth Flow

1. Go to `https://your-app.vercel.app/login`
2. Click "Connect with Google"
3. Should redirect to Google and back to the app
4. Should create a user account

## Troubleshooting

### Database Connection Failed

**Symptom**: `[error] Database connection failed` in logs

**Solutions**:
1. Verify DATABASE_URL is correct in Vercel dashboard
2. Check if database service is running
3. Ensure Vercel IP whitelist includes all IPs (set to `0.0.0.0/0`)
4. Test locally: `psql $DATABASE_URL_SYNC`

### API Routes Not Working

**Symptom**: `404 Not Found` on `/api/*` routes

**Solutions**:
1. Check `vercel.json` routing configuration
2. Verify `backend/main.py` exports `app = FastAPI(...)`
3. Check Vercel build logs for Python errors

### Frontend Shows Blank Page

**Symptom**: White screen or 404 on main page

**Solutions**:
1. Check Vercel build logs for Node.js errors
2. Verify `frontend/package.json` has `build` script
3. Check `frontend/vite.config.js` output directory is `dist`

### OAuth Redirect URI Mismatch

**Symptom**: `redirect_uri_mismatch` error from Google

**Solutions**:
1. Check Google Cloud Console → OAuth Client IDs
2. Authorized redirect URIs must include: `https://your-app.vercel.app/api/auth/oauth/callback`
3. Update in Vercel environment: `GOOGLE_REDIRECT_URI=https://your-app.vercel.app/api/auth/oauth/callback`

### CORS Errors

**Symptom**: Browser console shows CORS errors

**Solutions**:
1. Backend has CORS middleware enabled (check `backend/main.py`)
2. Frontend uses correct API URL (check `VITE_API_URL` environment variable)
3. If deploying frontend separately, set `VITE_API_URL` to your backend URL

## Performance Optimization

### Reduce Cold Start Times

- Set `maxLambdaSize` in `vercel.json` to reasonable value (default: 50mb)
- Database initialization is optimized to not timeout
- Consider Vercel Pro for faster cold starts

### Caching

- Frontend assets are cached indefinitely (max-age=31536000)
- API responses should implement proper cache headers

## Maintenance

### Monitor Logs

Vercel Dashboard → Project → Deployments → View logs

### Scale Database

If experiencing database connection issues with multiple concurrent requests:
- Increase connection pool size in config
- Consider managed PostgreSQL service with auto-scaling

## Success Indicators

Your deployment is 100% Vercel-ready when:

✅ All API endpoints return correct responses  
✅ Frontend loads without errors  
✅ OAuth flow works end-to-end  
✅ Database queries execute successfully  
✅ No errors in Vercel build logs  
✅ Loading performance is acceptable (<3s first paint)  

---

For issues or questions, check the project README.md or refer to Vercel documentation at https://vercel.com/docs
