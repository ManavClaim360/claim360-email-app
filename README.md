# ✉ Claim360 Email WebApp

A production-grade, team-based bulk email platform with:
- **Desktop client** (.exe) — PyQt6 with hamburger menu navigation
- **Backend API** — Python FastAPI
- **Database** — PostgreSQL (all tracking, logs, templates, users)
- **Gmail integration** — OAuth 2.0 per-user authentication
- **Email tracking** — open tracking via pixel, live campaign status
- **Admin panel** — user management, platform-wide stats, shared templates

---

## 🗂 Project Structure

```
claim360/
├── backend/                  # FastAPI backend
│   ├── main.py               # App entrypoint, router registration, DB init
│   ├── core/
│   │   ├── config.py         # Settings from .env
│   │   ├── database.py       # SQLAlchemy async engine + session
│   │   └── auth.py           # JWT auth, password hashing, current_user
│   ├── models/
│   │   └── user.py           # All SQLAlchemy ORM models
│   ├── api/
│   │   ├── auth.py           # /api/auth — login, register, OAuth
│   │   ├── templates.py      # /api/templates — CRUD + attachments
│   │   ├── campaigns.py      # /api/campaigns — create, send, SSE stream
│   │   ├── data.py           # /api/data — Excel parse, sample download, dummy gen
│   │   └── tracking.py       # /api/track — pixel endpoint + /api/admin
│   ├── services/
│   │   ├── gmail_service.py  # Google OAuth flow, token refresh, MIME builder
│   │   └── email_service.py  # Campaign send loop, variable substitution, tracking
│   ├── requirements.txt
│   └── .env.example
│
├── desktop/                  # PyQt6 desktop client
│   ├── main.py               # Full UI — all 7 pages, login dialog, nav
│   ├── api_client.py         # Typed wrapper for all backend REST calls
│   ├── claim360.spec        # PyInstaller spec for .exe build
│   ├── requirements.txt
│   └── .env.example
│
├── scripts/
│   └── init_db.py            # Create tables + seed admin user
│

```

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | Backend and desktop |
| PostgreSQL | 14+ | Local or cloud (Neon, Supabase, Railway) |
| Redis | 6+ | Optional — for Celery; not required for basic sending |


---

### Step 1 — Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g. "Claim360")
3. Enable the **Gmail API**:  
   APIs & Services → Library → search "Gmail API" → Enable
4. Create OAuth 2.0 credentials:  
   APIs & Services → Credentials → Create → OAuth Client ID → Web application
5. Add authorized redirect URIs:
   - `http://localhost:8000/api/auth/oauth/callback` (local dev)
   - `https://your-backend-domain.com/api/auth/oauth/callback` (production)
6. Copy your **Client ID** and **Client Secret**

---

### Step 2 — Backend Setup

```bash
cd claim360/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — fill in DATABASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, etc.
```

Edit `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/claim360
DATABASE_URL_SYNC=postgresql://postgres:yourpassword@localhost:5432/claim360
GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/oauth/callback
SECRET_KEY=your-random-secret-string
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=StrongPassword123
BASE_URL=http://localhost:8000
```

```bash
# Create PostgreSQL database
createdb claim360

# Initialize tables + admin user
cd ..
python scripts/init_db.py

# Start the API server
cd backend
uvicorn main:app --reload --port 8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) to verify the API is running.

---

### Step 3 — Desktop Client Setup

```bash
cd claim360/desktop

# Create virtual environment (separate from backend)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit MAILBLAST_API_URL if backend is not on localhost:8000

# Run the desktop app
python main.py
```

---

### Step 4 — First Login

1. Launch the desktop app
2. Click **Register** to create your account  
   *(or use the admin credentials set in .env)*
3. Go to **Configuration** → Connect Gmail → authorize in browser
4. You're ready!

---

## 📋 Feature Walkthrough

### ⚙ Configuration (Page 1)
- Set backend API URL and test connectivity
- Connect Gmail via OAuth — opens browser, stores tokens securely
- View connection status; disconnect at any time

### 📊 Data & Variables (Page 2)
- **Custom Variables tab**: Define variables like `name`, `company`, `position`  
  These become `{{name}}`, `{{company}}` in templates
- **Excel Upload tab**: Upload `.xlsx` or `.csv`, preview data, validate email column
- **Dummy Data tab**: Generate fake contacts for testing

### 📝 Templates (Page 3)
- Rich text editor with HTML support
- Variable hints — type `{{` to start a merge field
- Upload and attach files to templates
- Mark templates as **Shared** (admin-created, visible to all users)

### 👁 Preview (Page 4)
- Select template + recipient to preview merged email
- Shows subject, body, attachments
- Dynamic variable replacement

### ✉ Send Email (Page 5)
- Name your campaign, select template
- Contacts from Data page auto-loaded
- 3-second delay between emails (configurable in backend .env)
- Live status table: Pending → Sending → Sent / Failed
- Runs in background thread — UI stays responsive

### 📈 Tracking & Logs (Page 6)
- Select any campaign to view per-email status
- Stats cards: Total / Sent / Opened / Failed
- Open tracking via invisible 1×1 GIF pixel injected into email HTML
- Timestamps for sent and opened events

### 🛡 Admin Panel (Page 7 — Admin only)
- **Overview**: Platform-wide stats
- **Users**: Toggle admin rights, activate/deactivate accounts
- **All Campaigns**: View every campaign across all users

---

## 🏗 Database Schema

| Table | Purpose |
|-------|---------|
| `users` | Accounts, admin flag, active status |
| `oauth_tokens` | Gmail access/refresh tokens per user |
| `templates` | Email templates with HTML body |
| `attachments` | Uploaded files (stored on disk/tmp) |
| `template_attachments` | Many-to-many: templates ↔ attachments |
| `custom_variables` | Variable definitions per campaign |
| `contacts` | Recipients per campaign with variable values |
| `campaigns` | Campaign metadata, counters, status |
| `email_logs` | Per-email send record with tracking ID |
| `tracking_data` | Open/click events from pixel endpoint |

---

## ☁ Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# From project root
vercel

# Set environment variables (or use Vercel dashboard)
vercel env add DATABASE_URL
vercel env add DATABASE_URL_SYNC
vercel env add SECRET_KEY
vercel env add GOOGLE_CLIENT_ID
vercel env add GOOGLE_CLIENT_SECRET
vercel env add GOOGLE_REDIRECT_URI   # https://your-app.vercel.app/api/auth/oauth/callback
vercel env add ADMIN_EMAIL
vercel env add ADMIN_PASSWORD
vercel env add BASE_URL              # https://your-app.vercel.app

# Deploy to production
vercel --prod
```

> **Note**: Vercel is stateless. For file attachments in production, replace local file storage with **AWS S3**, **Cloudflare R2**, or **Supabase Storage**. Update `upload_attachment()` in `api/templates.py` and the path references in `email_service.py`.

> **Note**: For the email send queue on Vercel (serverless), the background task approach works for small batches. For large campaigns (1000+ emails), run a separate Celery worker on a VPS or use a queue service.

---

## 🔨 Build Desktop .exe

```bash
cd claim360/desktop

# Ensure venv is active and PyInstaller is installed
pip install pyinstaller

# Build single-file .exe
pyinstaller claim360.spec

# Output: dist/Claim360.exe (Windows)
#         dist/Claim360     (macOS/Linux)
```

Distribute `Claim360.exe` to team members. They only need to set `MAILBLAST_API_URL` pointing to your backend deployment.

---

## 🔒 Security Notes

- JWT tokens expire after 7 days (configurable)
- Gmail refresh tokens are stored in PostgreSQL — encrypt at rest in production
- All API endpoints require authentication except `/health` and `/api/track/*`
- Admin endpoints require `is_admin=True` on the user record
- CORS is open (`*`) by default — restrict to your desktop app origin in production

---

## 📦 Key Dependencies

**Backend**
- `fastapi` + `uvicorn` — async web framework
- `sqlalchemy` (async) + `asyncpg` — ORM + PostgreSQL driver
- `google-auth` + `google-api-python-client` — Gmail API
- `python-jose` + `passlib` — JWT + password hashing
- `openpyxl` — Excel generation
- `faker` — dummy data

**Desktop**
- `PyQt6` — cross-platform GUI
- `requests` — HTTP client for API calls
- `openpyxl` — local Excel parsing
- `PyInstaller` — .exe packaging
