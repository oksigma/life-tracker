# 0006. App password (single-user login)

- **Status:** In progress (approved by request, 2026-11-19)
- **Area:** cross-cutting
- **Created:** 2026-11-19
- **Related:** ADR `0004-hosting-vercel-atlas.md`

## Summary
Once deployed, the app is on a public URL. A single password keeps my photos and entries private.
I enter it once per device; the device stays signed in for 90 days.

## Requirements
### Must have
- Password set with the `APP_PASSWORD` environment variable. **If it is empty, there is no login** (local development).
- `/login` page: password field, "Sign in". Wrong password → "Wrong password". After signing in, go back to the page I came from.
- When signed in, a session cookie: `HttpOnly`, `Secure` (configurable for local http), `SameSite=Lax`, 90 days.
  It holds only an expiry and an HMAC signature (key from `SESSION_SECRET` + `APP_PASSWORD`, so changing the
  password signs every device out). No database table.
- Every `/api` route needs the cookie, except `/api/health` and `/api/auth/*`. Without it: `401`. Photos too.
- Any `401` in the app sends me to `/login`.
- "Sign out" on the home page (only shown when a password is set).
- Too many wrong passwords (10 in 15 minutes) → `429` "Too many attempts, try again later". Password compared in constant time.

### Out of scope
- Multiple users, password reset, passkeys, 2FA.

## API (under `/api/auth`)
| Method | Path | Notes |
|---|---|---|
| GET | `/status` | `{ required: bool, signed_in: bool }` |
| POST | `/login` | `{ password }` → `204` + cookie; `401` wrong; `429` too many attempts |
| POST | `/logout` | `204`, clears the cookie |

## Acceptance criteria
- [ ] With `APP_PASSWORD` set, opening the app on a new device shows the login page; the right password opens the page I wanted. _(needs a manual check)_
- [x] Wrong password → 401 and no cookie; 10 wrong attempts → 429. _(tests)_
- [x] Without the cookie, every data route (incl. photos) returns 401; health and auth routes still work. _(tests)_
- [x] With no `APP_PASSWORD`, everything works without signing in. _(tests)_
- [x] A tampered or expired cookie is rejected; changing the password signs everyone out. _(tests)_
- [ ] Sign out returns me to the login page. _(needs a manual check)_

## Implementation checklist
- [x] Backend: settings, session tokens, auth middleware, routes + pytest tests
- [x] Frontend: `/login` page, 401 redirect, sign-out button
- [x] `.env.example`, deployment docs
