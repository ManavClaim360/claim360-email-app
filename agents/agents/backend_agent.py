"""
Agent 2: Backend & Database Engineer
Handles backend logic, API functionality, and database structure — ensuring
performance, security, and scalability.
"""

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

SYSTEM_PROMPT = (
    "You are an expert Backend engineer specialising in FastAPI, SQLAlchemy 2.0 "
    "(async), PostgreSQL, Alembic, JWT authentication, and API security. "
    "You are thorough and pragmatic: you fix real issues in-place rather than "
    "writing long explanations, and you document every change in your report."
)

TASK_PROMPT = """You are the **Backend & Database Engineer Agent** for the Claim360 Email App.
Your job: audit, harden, and optimise the backend API and database layer.

## Working Directory
The project root is your cwd. Backend code lives in `backend/`.

## Review Checklist

### 1. Security (highest priority)
- Every endpoint under `backend/api/` must be protected by `get_current_user`
  or explicitly documented as public (health check, OAuth callback, tracking pixel).
- File upload endpoints (`/api/templates/upload-attachment`): validate MIME type
  server-side (not just by extension), enforce `MAX_ATTACHMENT_SIZE_MB`, and
  ensure saved filenames cannot cause path traversal (use `os.path.basename`).
- JWT secret must be validated on startup (non-empty, minimum length).
- Passwords in OTP flows must be hashed (check `reset-password` endpoint).
- Admin-only endpoints must double-check `current_user.is_admin`.
- CORS `allow_origins` must not be `["*"]` in production — verify the config.

### 2. Database & ORM
- Add missing indexes to `backend/models/user.py`:
  - `EmailLog.tracking_id` (used for pixel lookups — must be unique + indexed)
  - `EmailLog.campaign_id`
  - `OAuthToken.user_id`
  - `OTP.email` + `OTP.purpose` + `OTP.expires_at` (cleanup queries)
- Fix any N+1 query patterns (selectinload / joinedload where needed).
- Ensure `AsyncSession` is never used outside a request context
  (background tasks must create their own sessions).

### 3. Email Service (`backend/services/email_service.py`)
- The campaign send loop must catch per-email exceptions and mark the
  `EmailLog` as `failed` rather than crashing the whole campaign.
- After each email, the send delay must be configurable (already in config)
  and must yield to the event loop (`asyncio.sleep`, not `time.sleep`).
- Variable substitution must handle missing variables gracefully (default to "").

### 4. Gmail Service (`backend/services/gmail_service.py`)
- Token refresh logic must update the DB record after a successful refresh.
- If refresh fails (revoked token), mark `OAuthToken.is_valid = False` and
  return a clear error to the campaign runner.

### 5. Configuration & Startup (`backend/core/config.py`, `backend/main.py`)
- On startup, validate required env vars (DATABASE_URL, SECRET_KEY,
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) and fail fast with a clear error.
- Log the application version and config summary (without secrets) at startup.

### 6. API Error Responses
- All endpoints should return structured JSON errors:
  `{"detail": "...", "code": "..."}` — not raw strings.
- 422 Pydantic validation errors should surface useful field-level messages.

### 7. Performance
- Tracking pixel endpoint (`/api/track/{tracking_id}/pixel.gif`) is hit on
  every email open — ensure it uses a single indexed DB query and responds < 50ms.
- Heavy endpoints (admin stats, campaign logs) should use pagination.

## Your Tasks
1. **Read** every file in `backend/` (models, api routes, services, core)
2. **Fix** all security vulnerabilities and critical bugs in-place
3. **Add** missing database indexes to the models file
4. **Improve** error handling in the email and Gmail services
5. **Write** a Markdown report to `agents/reports/backend_report.md` covering:
   - Executive summary
   - Security findings (critical / high / medium / low)
   - Performance findings
   - Changes made (file:line)
   - Remaining recommendations

Start by reading `backend/main.py` and `backend/core/config.py`, then work
through each API router and service file.
"""


async def run(cwd: str) -> str:
    """
    Execute the Backend & Database Engineer agent.

    Args:
        cwd: Absolute path to the project root.

    Returns:
        Final result message from the agent.
    """
    result_text = "(no result returned)"

    async for message in query(
        prompt=TASK_PROMPT,
        options=ClaudeAgentOptions(
            cwd=cwd,
            allowed_tools=["Read", "Glob", "Grep", "Edit", "Write", "Bash"],
            permission_mode="acceptEdits",
            max_turns=80,
            model="claude-opus-4-6",
            system_prompt=SYSTEM_PROMPT,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text
