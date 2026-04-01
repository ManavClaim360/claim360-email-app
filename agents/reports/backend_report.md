# Backend & Database Audit Report

**Date:** 2026-04-01
**Auditor:** Backend & Database Engineer Agent
**Scope:** `backend/` — API routes, services, models, core modules

---

## Executive Summary

The Claim360 backend had **multiple critical security vulnerabilities** that would expose production deployments to immediate risk, plus several high-severity bugs, missing database indexes, and performance anti-patterns. All critical and high issues have been fixed in-place.

**Most severe finding:** Passwords were stored and compared in **plain text** (`core/auth.py` lines 15-22). This has been remediated with bcrypt hashing via passlib, with a backward-compatible migration path for existing plain-text passwords.

| Severity | Found | Fixed | Remaining |
|----------|-------|-------|-----------|
| Critical | 3     | 3     | 0         |
| High     | 5     | 5     | 0         |
| Medium   | 7     | 7     | 0         |
| Low      | 3     | 0     | 3         |

---

## Security Findings

### CRITICAL

#### 1. Plain-Text Password Storage (`core/auth.py:15-22`)
- **Before:** `verify_password()` did direct string comparison; `get_password_hash()` returned the raw password.
- **Fix:** Replaced with bcrypt via `passlib.context.CryptContext`. Added backward-compatible migration: legacy plain-text passwords are detected (no `$2` prefix), accepted once, and auto-rehashed to bcrypt on next successful login (`api/auth.py` login endpoint).
- **Files changed:** `backend/core/auth.py:15-40`, `backend/api/auth.py:140-145`

#### 2. Missing `security = HTTPBearer()` Declaration (`core/auth.py`)
- **Before:** `get_current_user` referenced `security` in its `Depends()` but the variable was never defined — **every authenticated endpoint would crash at import time**.
- **Fix:** Added `security = HTTPBearer()` at module level.
- **File changed:** `backend/core/auth.py:17`

#### 3. Null-Pointer Dereference in Login (`api/auth.py:134`)
- **Before:** `verify_password(data.password, user.hashed_password)` was called without first checking if `user` was `None`. If a nonexistent email was used, the server returned an unhandled `AttributeError` (500) instead of 401.
- **Fix:** Added explicit `if not user: raise HTTPException(401)` before the password check.
- **File changed:** `backend/api/auth.py:131-132`

### HIGH

#### 4. CORS Wildcard in Production (`main.py:56`)
- **Before:** When `FRONTEND_URL` was not set on Render, CORS was set to `["*"]` with `allow_credentials=True`. This is a textbook credential-stealing vector.
- **Fix:** Changed the Render fallback to only allow localhost origins, matching the local-dev fallback.
- **File changed:** `backend/main.py:54-56`

#### 5. Internal Error Details Leaked to Clients (`main.py:78`)
- **Before:** Global exception handler returned `"error": str(exc)` — leaking stack traces, DB connection strings, and internal state.
- **Fix:** Changed to generic `{"detail": "Internal Server Error", "code": "INTERNAL_ERROR"}`.
- **File changed:** `backend/main.py:76`

#### 6. Login Error Leaks DB Details (`api/auth.py:176`)
- **Before:** Catch-all returned `f"Database error or server crash: {str(e)}"`.
- **Fix:** Changed to generic message; details still logged server-side.
- **File changed:** `backend/api/auth.py:176`

#### 7. OTP Code Returned in HTTP Response (`api/auth.py:214`)
- **Before:** When SMTP was not configured, the OTP code was returned directly in the JSON response: `"Code: {code}"`. Any network observer could intercept it.
- **Fix:** Removed the code from the response; it's still logged to the server console for dev use.
- **File changed:** `backend/api/auth.py:214`

#### 8. Weak Default SECRET_KEY with No Validation (`core/config.py:13`)
- **Before:** Default SECRET_KEY was `"change-me-in-production-use-strong-secret"` with no startup check.
- **Fix:** Added validation: in production environments (Render/Railway/Fly), the app now **crashes on startup** if SECRET_KEY is the default or shorter than 32 characters. In local dev, it warns.
- **File changed:** `backend/core/config.py:67-80`

### MEDIUM

#### 9. No Server-Side MIME Validation on Uploads (`api/templates.py:189-191`)
- **Before:** MIME type was guessed from the file extension only (`mimetypes.guess_type`), allowing an attacker to upload an executable with a `.pdf` extension.
- **Fix:** Added content-based MIME detection via `python-magic` with extension-based fallback if the library is not installed.
- **File changed:** `backend/api/templates.py:192-202`

#### 10. Path Traversal in Upload Filename (`api/templates.py:181-183`)
- **Before:** `file.filename` was used directly (only the extension was extracted for the stored name, but `original_filename` was saved to DB as-is). An attacker could craft filenames like `../../../etc/passwd` which would be stored and potentially served.
- **Fix:** Applied `os.path.basename()` and stripped null bytes, forward and backslashes.
- **File changed:** `backend/api/templates.py:180-183`

#### 11. SSE Stream Used Request-Scoped DB Session (`api/campaigns.py:219`)
- **Before:** The SSE generator captured the `db` session from `Depends(get_db)`. Once the initial HTTP response was sent, the request lifecycle ended and the session was closed — but the generator kept using it.
- **Fix:** Generator now creates its own `AsyncSessionLocal()` session that lives for the stream duration.
- **File changed:** `backend/api/campaigns.py:220-260`

#### 12. Variable Substitution Kept Raw Placeholder (`services/email_service.py:53`)
- **Before:** Missing variables returned `{{variable}}` in the final email body — leaking template internals to recipients.
- **Fix:** Missing variables now default to empty string `""`.
- **File changed:** `backend/services/email_service.py:51-53`

#### 13. Missing Database Indexes (multiple hot columns)
- `OAuthToken.user_id` — used in every auth-related query
- `EmailLog.campaign_id` — used in campaign log listing & progress stream
- `EmailLog.user_id` — used in admin stats
- `Contact.campaign_id` — used in campaign send loop
- `Signature.user_id` — used on every email send for signature lookup
- `OTP(email, purpose, expires_at)` — composite index for cleanup queries
- **File changed:** `backend/models/user.py` (6 index additions)

#### 14. N+1 Query in Admin User List (`api/tracking.py:58-69`)
- **Before:** For each user, two separate `COUNT()` queries were executed — O(2N) queries total.
- **Fix:** Replaced with a single query using correlated scalar subqueries.
- **File changed:** `backend/api/tracking.py:58-88`

#### 15. No Pagination on Heavy Admin Endpoints
- **Before:** `/api/admin/users`, `/api/admin/campaigns`, and `/api/campaigns/{id}/logs` returned all rows with no limit.
- **Fix:** Added `page` and `page_size` query parameters to all three endpoints.
- **Files changed:** `backend/api/tracking.py:58,172`, `backend/api/campaigns.py:134`

---

## Performance Findings

### Tracking Pixel Endpoint (`/api/track/{tracking_id}/pixel.gif`)
- **Status: OK.** `EmailLog.tracking_id` already had `unique=True, index=True` in the model. The `record_open` function does a single indexed lookup + one insert. Response is a pre-decoded 43-byte GIF with aggressive no-cache headers. Expected latency < 10ms under normal DB load.

### Campaign Send Loop
- **Status: OK.** Uses `asyncio.sleep(settings.SEND_DELAY_SECONDS)` (not blocking `time.sleep`). Per-email exceptions are caught and logged as `failed` without crashing the loop.

### Gmail Token Refresh
- **Improved.** Now logs refresh success/failure explicitly and updates the DB record with the new token after refresh. On failure, sets `is_valid = False` with a clear log message.

---

## Changes Made (Summary)

| File | Lines | Change |
|------|-------|--------|
| `backend/core/auth.py` | 1-55 | Replaced plain-text auth with bcrypt; added `security = HTTPBearer()`; fixed `datetime.utcnow()` deprecation |
| `backend/core/config.py` | 10-95 | Added `APP_VERSION`; SECRET_KEY validation (crash in prod if insecure); Google OAuth var validation; improved config logging |
| `backend/main.py` | 54-78, 135-142 | Removed CORS `["*"]` fallback; stopped leaking errors in global handler; added version/config summary at startup |
| `backend/models/user.py` | 1, 43, 123, 161-162, 198, 234 | Added `Index` import; added indexes on `OAuthToken.user_id`, `Contact.campaign_id`, `EmailLog.campaign_id`, `EmailLog.user_id`, `Signature.user_id`; added composite index on OTP |
| `backend/api/auth.py` | 128-145, 176, 214 | Fixed null user crash; auto-rehash legacy passwords; stopped leaking errors and OTP codes |
| `backend/api/templates.py` | 170-207 | Added path traversal protection (`os.path.basename`); added content-based MIME detection |
| `backend/api/tracking.py` | 1, 57-88, 171-182 | Fixed N+1 query with subqueries; added pagination to users and campaigns endpoints |
| `backend/api/campaigns.py` | 1, 134-160, 206-260 | Added pagination to logs; fixed SSE session lifecycle |
| `backend/services/email_service.py` | 50-53 | Missing variables default to `""` |
| `backend/services/gmail_service.py` | 147-158 | Improved token refresh logging and DB persistence |

---

## Remaining Recommendations (Low Priority)

### 1. Rate Limiting on Auth Endpoints
The `/api/auth/login`, `/api/auth/send-otp`, and `/api/auth/reset-password` endpoints have no rate limiting. An attacker could brute-force OTP codes (6 digits = 1M combinations) or passwords. **Recommendation:** Add `slowapi` or a Redis-backed rate limiter (e.g., 5 attempts/minute per IP).

### 2. OTP Cleanup Cron Job
Used OTP records are never deleted. Over time the `otps` table will grow unboundedly. **Recommendation:** Add a periodic task to delete expired OTPs (the new composite index makes this query efficient).

### 3. Encrypt OAuth Tokens at Rest
`OAuthToken.access_token` and `OAuthToken.refresh_token` are stored in plain text in the database. If the DB is compromised, all connected Gmail accounts are exposed. **Recommendation:** Encrypt these columns with a symmetric key (e.g., Fernet) derived from a secret not stored in the DB.

### 4. Add `python-magic` to Dependencies
The server-side MIME detection falls back to extension-based if `python-magic` is not installed. **Recommendation:** Add `python-magic` (or `python-magic-bin` for easier deployment) to `requirements.txt`.

### 5. Database Migration
The new indexes added to models will only apply to **new** databases created via `create_all()`. Existing production databases need an Alembic migration to add the indexes. **Recommendation:** Generate and apply: `alembic revision --autogenerate -m "add missing indexes"`.
