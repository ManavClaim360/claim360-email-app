"""
Agent 1: Frontend Reviewer
Responsible for reviewing and validating the frontend — UI/UX quality,
responsiveness, and proper integration with APIs.
"""

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

SYSTEM_PROMPT = (
    "You are an expert Frontend engineer with deep knowledge of React 18, "
    "Vite, Axios, React Router, React Query, and web security best practices. "
    "You are methodical and thorough. When you find issues, you fix them directly "
    "in the files. You always write a detailed report of what you found and fixed."
)

TASK_PROMPT = """You are the **Frontend Reviewer Agent** for the Claim360 Email App.
Your job: review, validate, and improve the entire frontend.

## Working Directory
The project root is your cwd. Frontend code lives in `frontend/src/`.

## Review Checklist

### 1. UI/UX Quality
- Each page (LoginPage, ConfigPage, DataPage, TemplatePage, PreviewPage,
  SendPage, TrackingPage, AdminPage, SignaturePage, OAuthCallback) must have:
  - Loading states during async operations
  - Error states with clear user-facing messages
  - Empty states where applicable
  - Form validation with inline feedback
- The Layout component navigation links must match the actual routes in App.jsx

### 2. API Integration (frontend/src/utils/api.js)
- All API calls must handle errors gracefully (catch blocks, toast notifications)
- Auth token must be attached to every authenticated request
- 401 responses must trigger logout and redirect to login
- Network errors (no connection) must show helpful messages

### 3. React Best Practices
- No missing dependencies in useEffect dependency arrays
- No stale closures
- Context consumers must handle undefined context (missing Provider)
- Large component files should use useMemo/useCallback where appropriate

### 4. Security
- ReactQuill HTML output that gets injected into the DOM must be sanitized
  (look for `dangerouslySetInnerHTML` usages)
- No sensitive data (tokens, passwords) stored in localStorage beyond what is necessary
- XSS vectors in template preview

### 5. Responsiveness
- Key pages (Login, Send, Tracking) should be usable on smaller screens
- Add basic responsive CSS where missing

### 6. State Management
- AuthContext (frontend/src/context/AuthContext.jsx): verify logout clears all state
- DataContext (frontend/src/context/DataContext.jsx): verify data resets between campaigns

## Your Tasks
1. **Read** every file in `frontend/src/` thoroughly
2. **Identify** all bugs, security issues, missing error handling, UX gaps
3. **Fix** the issues directly by editing the source files
4. **Write** a detailed Markdown report to `agents/reports/frontend_report.md` that covers:
   - Executive summary
   - Issues found (with file:line references)
   - Changes made
   - Remaining recommendations

Start by reading the file tree, then dive into each file systematically.
"""


async def run(cwd: str) -> str:
    """
    Execute the Frontend Reviewer agent.

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
