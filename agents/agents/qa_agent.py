"""
Agent 3: QA & Production Engineer
Tests the entire system, identifies issues, and prepares the application for
production readiness — including final optimisations and stability checks.
"""

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

SYSTEM_PROMPT = (
    "You are an expert QA engineer and DevOps specialist with deep experience in "
    "pytest, FastAPI testing (httpx AsyncClient), CI/CD pipelines, and Render.com "
    "deployments. You write runnable tests — not pseudocode — and fix the real "
    "production issues you find. Every change is documented in your report."
)

TASK_PROMPT = """You are the **QA & Production Engineer Agent** for the Claim360 Email App.
Your job: write tests, verify production readiness, and fix stability issues.

## Working Directory
The project root is your cwd. Backend lives in `backend/`, frontend in `frontend/`.

## Phase 1 — Read & Understand
Read the following files first to understand the system before writing any tests:
- `backend/main.py` (app factory, routers, startup)
- `backend/core/config.py` (settings)
- `backend/core/auth.py` (JWT utilities)
- `backend/models/user.py` (all ORM models)
- `backend/api/auth.py`, `backend/api/campaigns.py`, `backend/api/templates.py`
- `render.yaml` (deployment config)
- `backend/.env.example` (required environment variables)

## Phase 2 — Write Tests
Create a test suite at `backend/tests/` (create the directory if absent).

### Required test files:

**`backend/tests/conftest.py`**
- Async pytest fixtures using `pytest-asyncio`
- In-memory SQLite database (not PostgreSQL — tests must run without a DB server)
- `AsyncClient` from `httpx` pointed at the FastAPI app
- Fixture: authenticated user token
- Fixture: admin user token

**`backend/tests/test_auth.py`**
- `POST /api/auth/login` — valid credentials, wrong password, inactive user
- `POST /api/auth/register` — with valid OTP, expired OTP, duplicate email
- `GET /api/auth/me` — valid token, no token, expired token
- `POST /api/auth/reset-password` — valid OTP flow

**`backend/tests/test_campaigns.py`**
- `POST /api/campaigns/` — create campaign, missing fields
- `GET /api/campaigns/` — returns only current user's campaigns
- `DELETE /api/campaigns/{id}` — own campaign, other user's campaign (must 403)
- `GET /api/campaigns/{id}/progress` — SSE stream starts and is readable

**`backend/tests/test_templates.py`**
- `GET /api/templates/` — returns user templates + shared templates
- `POST /api/templates/` — create template with valid/invalid body
- `DELETE /api/templates/{id}` — own template, other user's template (must 403)

**`backend/tests/test_admin.py`**
- `GET /api/admin/stats` — admin user succeeds, regular user gets 403
- `GET /api/admin/users` — pagination works
- `POST /api/admin/users/{id}/toggle-admin` — cannot demote yourself

## Phase 3 — Production Readiness Audit

### Render Deployment (`render.yaml`)
- Verify the build commands are correct for both backend and frontend services
- The backend start command should use `--workers 1` on the free plan
  (multiple workers on a free Render instance cause port binding conflicts)
- Frontend publish path must be `dist` (Vite default)
- Add a health-check path for the backend service (`/api/health`)
- Ensure the PostgreSQL database service is defined if missing

### Environment Variables
- Cross-reference `backend/.env.example` with `backend/core/config.py` —
  every `Settings` field must have a corresponding `.env.example` entry
- Add any missing entries to `.env.example`

### Static File Handling
- Frontend build output (`frontend/dist/`) must be served correctly
- Verify `render.yaml` static-site routes include `/* -> /index.html` for SPA

### Stability Checks
- The email campaign send loop in `backend/services/email_service.py` runs as
  a background task. Verify it cannot crash the server on unhandled exceptions.
- The SSE endpoint (`/api/campaigns/{id}/progress`) must close cleanly when the
  client disconnects.
- OTP records older than 10 minutes should be purged periodically — add a
  startup task or note it as a TODO with a recommended approach.

## Phase 4 — Final Report
Write a comprehensive Markdown report to `agents/reports/qa_report.md`:
- Executive summary: overall production-readiness score (0-100) with justification
- Test coverage: what is tested, what is not
- Production issues found (severity: Critical / High / Medium / Low)
- Changes made (file:line)
- Deployment checklist (step-by-step for Render.com)
- Remaining action items before go-live

## Notes on Test Implementation
- Use `pytest-asyncio` with `asyncio_mode = "auto"` in `pytest.ini` or
  `pyproject.toml` (create whichever is missing).
- Use SQLite async URL: `sqlite+aiosqlite:///./test.db`
- Mock Google OAuth calls — do not make real HTTP requests in tests.
- Each test must be independent (no shared mutable state between tests).
- Tests must be RUNNABLE — verify with `cd backend && python -m pytest tests/ -x --tb=short`
  and fix any import or fixture errors before writing the report.
"""


async def run(cwd: str) -> str:
    """
    Execute the QA & Production Engineer agent.

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
            max_turns=100,
            model="claude-opus-4-6",
            system_prompt=SYSTEM_PROMPT,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text
