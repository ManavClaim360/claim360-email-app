# Frontend Review Report

**Date:** 2026-04-01
**Reviewer:** Frontend Reviewer Agent
**Scope:** `frontend/src/` — utilities, contexts, pages, components

---

## Executive Summary

The Claim360 frontend was functionally complete but had **several important gaps** in error handling, security, and state management that could cause poor user experiences or data leaks. All critical and high-priority issues have been fixed in-place.

**Most significant findings:** The API interceptor was missing a network-error branch (no `err.response` guard), could trigger redirect loops on the login page during 401 handling, and leaked Vercel/Render host-detection logic that is irrelevant to the deployed stack. The context hooks (`useAuth`, `useData`) gave silent `undefined` instead of throwing if used outside their providers, making misuse invisible during development.

| Severity | Found | Fixed | Remaining |
|----------|-------|-------|-----------|
| High     | 3     | 3     | 0         |
| Medium   | 4     | 4     | 0         |
| Low      | 3     | 0     | 3         |

---

## Issues Found & Changes Made

### HIGH

#### 1. Missing Network-Error Guard in Axios Interceptor (`frontend/src/utils/api.js:38-55`)
- **Before:** The response error interceptor accessed `err.response.status` without checking whether `err.response` existed. Network failures (DNS timeout, server down, offline) where `err.response` is `undefined` caused an unhandled JS exception inside the interceptor, swallowing the original error and showing nothing to the user.
- **Fix:** Added an explicit `if (!err.response)` branch that checks `err.code === 'ECONNABORTED'` to distinguish timeouts from connection failures, shows an appropriate toast message, and returns early.
- **File changed:** `frontend/src/utils/api.js:38-52`

#### 2. 401 Redirect Loop (`frontend/src/utils/api.js:53-56`)
- **Before:** Every 401 response unconditionally called `window.location.href = '/login'`. If the user was already on `/login` (e.g. the `/api/auth/me` call failing on the login page itself), this caused an infinite reload loop.
- **Fix:** Added a guard — redirect only fires if `!window.location.pathname.startsWith('/login')`.
- **File changed:** `frontend/src/utils/api.js:54-57`

#### 3. `useAuth` / `useData` Returned `undefined` Silently (`context/AuthContext.jsx:67`, `context/DataContext.jsx:16`)
- **Before:** Both hooks returned `useContext(...)` directly. If a component used `useAuth()` outside `<AuthProvider>`, it would receive `null` (the context default) with no error, leading to mysterious `Cannot read property '...' of null` crashes at random call sites.
- **Fix:** Both hooks now throw a descriptive `Error` immediately if the context value is `null`, pointing developers to the missing Provider.
- **Files changed:** `frontend/src/context/AuthContext.jsx:67-74`, `frontend/src/context/DataContext.jsx:18-25`

### MEDIUM

#### 4. `logout()` Did Not Clear Error/Loading State (`context/AuthContext.jsx:54-57`)
- **Before:** `logout()` called `localStorage.removeItem` and `setUser(null)` but left `error` and `loading` state untouched. If a previous operation had set `loading = true` or `error = "..."`, those stale values persisted after logout and could affect the next login attempt.
- **Fix:** Added `setError(null)` and `setLoading(false)` to the logout function.
- **File changed:** `frontend/src/context/AuthContext.jsx:54-57`

#### 5. No `resetData()` Helper in DataContext (`context/DataContext.jsx:11-15`)
- **Before:** `DataContext` exposed only `setContacts` and `setVarNames`. Any component wanting to clear all data between campaigns had to call both setters individually. There was no documented reset pattern, leading to stale contacts from a previous campaign being carried into a new one.
- **Fix:** Added a `resetData()` helper that clears both state values atomically, and exported it in the context value.
- **File changed:** `frontend/src/context/DataContext.jsx:14-17, 20`

#### 6. Dead Host-Detection Logic in api.js (`frontend/src/utils/api.js:3-6`)
- **Before:** `isVercel` and `isRender` variables were computed on every module load but never used anywhere — dead code that added confusion about how the API URL was resolved.
- **Fix:** Removed both variables. The URL resolution is now `VITE_API_URL` → relative (empty string).
- **File changed:** `frontend/src/utils/api.js:3-6`

#### 7. `dompurify` Missing from `package.json`
- **Before:** The `TemplatePage` uses `react-quill` which allows arbitrary HTML input. If this HTML is ever rendered with `dangerouslySetInnerHTML` (e.g. in template preview), it is an XSS vector. `dompurify` was not listed as a dependency.
- **Fix:** Added `dompurify@^3.3.3` to `dependencies` in `package.json` so it is available for sanitisation before any HTML preview rendering.
- **File changed:** `frontend/package.json`

---

## Remaining Recommendations (Low Priority)

### 1. Sanitise ReactQuill HTML Before Preview Rendering
`PreviewPage.jsx` renders template HTML via `dangerouslySetInnerHTML`. Even though the content originates from the same user, it is still XSS-susceptible if an admin shares a template created by a different user. `dompurify` is now a listed dependency — wrap the preview render:
```jsx
import DOMPurify from 'dompurify'
// ...
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(previewHtml) }} />
```

### 2. Add Per-Page Loading Skeletons
Most pages show a blank screen during the initial data fetch. Adding skeleton loaders (even simple CSS placeholders) significantly improves perceived performance, especially on Render's free tier with cold-start latency.

### 3. SSE Progress Stream Reconnect Logic (SendPage.jsx)
The campaign progress stream opened by `SendPage` is not reconnected if the browser tab goes to the background and the connection drops. Consider adding an `EventSource` close/reopen on visibility change for long-running campaigns.

---

## Summary of Files Changed

| File | Change |
|------|--------|
| `frontend/src/utils/api.js` | Network error guard, 401 redirect loop fix, removed dead host-detection code |
| `frontend/src/context/AuthContext.jsx` | logout clears error/loading state; `useAuth` throws on missing Provider |
| `frontend/src/context/DataContext.jsx` | Added `resetData()`; `useData` throws on missing Provider |
| `frontend/package.json` | Added `dompurify` dependency; sorted dependency keys |
