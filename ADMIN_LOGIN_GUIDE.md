# 🛡️ Admin Login Guide

## Quick Start - Admin Login

### Local Development

1. **Initialize database with admin user**:
   ```bash
   cd backend
   python3 ../scripts/init_db.py
   ```
   Output should show:
   ```
   ✅ Admin created: admin@company.com / admin123
   ```

2. **Start the backend**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

4. **Login as admin**:
   - Go to `http://localhost:3000/login`
   - Click the **Admin** tab
   - Enter admin credentials:
     - Email: `admin@company.com`
     - Password: `admin123`
   - Click **Sign In**
   - You should see the admin panel with more features

---

## Vercel Deployment - Admin Login

### Set Admin Credentials

Before deploying to Vercel, set these environment variables in the Vercel dashboard:

1. **Go to Vercel Dashboard**
   - Project → Settings → Environment Variables
   - Add/Update:
     - `ADMIN_EMAIL`: `admin@yourcompany.com` (change this!)
     - `ADMIN_PASSWORD`: `StrongPassword123` (change this!)

2. **Deploy**:
   ```bash
   vercel --prod
   ```

3. **Admin will auto-create**:
   - On first deployment, Vercel's startup event runs `init_db()`
   - Admin user is automatically created with your credentials

4. **Login to admin panel**:
   - Go to `https://YOUR-APP.vercel.app`
   - Click **Admin** tab
   - Login with your `ADMIN_EMAIL` and `ADMIN_PASSWORD`

---

## Admin Login API Endpoint

### For Developers

The dedicated admin login endpoint is:

```
POST /api/auth/admin/login
Content-Type: application/json

{
  "email": "admin@company.com",
  "password": "admin123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 1,
  "email": "admin@company.com",
  "full_name": "System Admin",
  "is_admin": true
}
```

**Errors**:
- `401 Unauthorized`: Invalid email or password
- `403 Forbidden`: User exists but is not an admin
- `403 Forbidden`: Account is deactivated

### Test with cURL

```bash
curl -X POST http://localhost:8000/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "admin123"
  }'
```

---

## Two Types of Login

### 1. **User Login** (Regular Users)
- **Endpoint**: `POST /api/auth/login`
- **Purpose**: Regular users and admin users can login here
- **Returns**: User data with `is_admin` flag
- **No restrictions**: Non-admin users can use this

### 2. **Admin Login** (Admin Only)
- **Endpoint**: `POST /api/auth/admin/login`
- **Purpose**: Explicit admin-only login
- **Returns**: User data with `is_admin` flag
- **Restriction**: Only works if user has `is_admin = true`
- **Logs**: Admin logins are logged to console/logs

---

## Admin Features After Login

Once logged in as admin, you can access:

1. **Admin Panel** (`/admin`)
   - View all users
   - Toggle admin rights
   - Activate/deactivate accounts
   - View platform-wide statistics

2. **Campaign Management**
   - View all campaigns across all users
   - View detailed tracking data
   - Export reports

3. **Template Management**
   - Create shared templates
   - Manage company-wide templates

---

## Troubleshooting Admin Login

### "Only admin users can access this endpoint"
**Cause**: User exists but has `is_admin = false`
**Fix**: 
- Delete the user and recreate with admin credentials
- Or manually update the database:
  ```sql
  UPDATE users SET is_admin = true WHERE email = 'admin@company.com';
  ```

### "Invalid email or password"
**Cause**: Email or password is wrong
**Fix**: Check environment variables:
```bash
echo "ADMIN_EMAIL: $ADMIN_EMAIL"
echo "ADMIN_PASSWORD: $ADMIN_PASSWORD"
```

### "Account deactivated"
**Cause**: Admin account was manually deactivated
**Fix**: Reactivate in database:
```sql
UPDATE users SET is_active = true WHERE is_admin = true;
```

### Admin account not being created
**Cause**: `init_db()` didn't run or ADMIN_EMAIL/ADMIN_PASSWORD not set
**Fix**: 
- Make sure environment variables are set before deployment
- Manually run: `python3 scripts/init_db.py`
- Check Vercel deployment logs

---

## Security Notes

1. **Change Default Credentials**
   - Default: `admin123` is weak
   - Always set `ADMIN_PASSWORD` to a strong password

2. **No Default Export**
   - Credentials are never exported in code
   - Always stored in environment variables

3. **Tokens Are Time-Limited**
   - Default: 7 days expiry (`ACCESS_TOKEN_EXPIRE_MINUTES=10080`)
   - Tokens are invalidated on password reset

4. **Session Management**
   - Token stored in localStorage on client
   - Not stored in cookies (safe from CSRF)

5. **Gmail Re-authentication**
   - Every login invalidates existing Gmail tokens
   - Forces fresh OAuth on next action

---

## Quick Reference

| Task | Steps |
|------|-------|
| **Local Admin Login** | 1. Run `python3 scripts/init_db.py` 2. Start backend 3. Go to login page 4. Click Admin tab 5. Enter credentials |
| **Vercel Admin Login** | 1. Set ADMIN_EMAIL and ADMIN_PASSWORD in Vercel 2. Deploy 3. Wait for init_db to run 4. Go to app login page 5. Click Admin tab 6. Login |
| **Reset Admin Password** | 1. Update ADMIN_PASSWORD in Vercel env 2. Delete admin user from database 3. Redeploy (init_db creates new admin) |
| **Make User Admin** | 1. Login as admin 2. Admin Panel → Users 3. Toggle admin for user |
| **Create Another Admin** | 1. Use Admin Panel → Users 2. Or manually update database |

---

**Last Updated**: March 26, 2026

For more information, see:
- [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md) - Complete variable reference
- [README.md](./README.md) - Project overview
- [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) - Deployment guide
