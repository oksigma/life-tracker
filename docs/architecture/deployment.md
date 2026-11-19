# Deploying LifeTracker (Vercel + MongoDB Atlas)

Decision: [ADR 0004](decisions/0004-hosting-vercel-atlas.md). Code: `github.com/oksigma/life-tracker`.

Two Vercel projects are deployed from the same repo, plus one free Atlas database:

| Part | Where | Root Directory |
|---|---|---|
| Frontend (Next.js) | Vercel project `life-tracker` | `life-tracker-app/frontend` |
| Backend (FastAPI) | Vercel project `life-tracker-api` | `life-tracker-app/backend` |
| Database | MongoDB Atlas, free M0 cluster | — |

Pick one region for everything (e.g. Sydney: Atlas `AWS / ap-southeast-2`, Vercel `syd1`).

## 1. MongoDB Atlas
1. Sign up at <https://www.mongodb.com/cloud/atlas/register> and create a **free M0** cluster in your region.
2. **Database Access** → add a database user with a generated password (role: read and write to any database).
3. **Network Access** → add `0.0.0.0/0` (allow from anywhere). Vercel has no fixed IP addresses; the user's password protects the database.
4. **Connect → Drivers** → copy the connection string, e.g.
   `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`
   Keep it private: it contains the password.

## 2. Backend project on Vercel
1. Sign in at <https://vercel.com> with GitHub (the oksigma account) → **Add New → Project** → import `oksigma/life-tracker`.
2. **Project name:** `life-tracker-api`. **Root Directory:** `life-tracker-app/backend`. Framework preset: FastAPI (or "Other").
3. **Environment Variables:**

   | Name | Value |
   |---|---|
   | `MONGODB_URL` | the Atlas connection string |
   | `MONGODB_DB` | `lifetracker` |
   | `APP_PASSWORD` | the password you'll type to open the app |
   | `SESSION_SECRET` | a long random string (`openssl rand -hex 32`) |
   | `TMDB_API_KEY` | your TMDB key (optional) |

4. Deploy, then open `https://<backend>.vercel.app/api/health` → `{"status":"ok"}`.
5. Settings → Functions → Function Region → your region.

## 3. Frontend project on Vercel
1. **Add New → Project** → import `oksigma/life-tracker` again.
2. **Project name:** `life-tracker`. **Root Directory:** `life-tracker-app/frontend`. Framework: Next.js.
3. **Environment Variables:** `BACKEND_URL` = `https://<backend>.vercel.app` (the backend's production URL, no trailing slash).
4. Deploy, open the site → you should see the login page.

Every push to `main` redeploys both projects. Changing an environment variable needs a redeploy (Deployments → ⋯ → Redeploy).

## 4. Copy your local data to Atlas (optional)
With the local Docker database running (`npm run db:up`), from `life-tracker-app/`:

```sh
docker exec lifetracker-mongo-1 mongodump --db lifetracker --archive \
  | docker exec -i lifetracker-mongo-1 mongorestore --archive --uri "PASTE_ATLAS_CONNECTION_STRING"
```

This copies movies, outfits, meals, saved foods and photos (GridFS). Run it once, before you start adding entries online.

## Limits to know
- **Photos over 4 MB** are shrunk in the browser before upload (Vercel's 4.5 MB request limit). Very large HEIC
  photos can't be shrunk in browsers that can't read HEIC (Chrome); Safari on iPhone is fine.
- **Atlas M0** holds 512 MB, roughly 1,000 photos.
- The first request after a quiet period is slower (cold start).

## Troubleshooting
- **Frontend pages load but show "Request failed (404)" or can't reach the server:** check `BACKEND_URL`, and redeploy the frontend after changing it.
- **Backend 500 errors:** Vercel → backend project → Logs. Usually a wrong `MONGODB_URL`, or Atlas Network Access missing `0.0.0.0/0`.
- **Login page keeps coming back:** the site must be served over https (it is on Vercel); `SESSION_COOKIE_SECURE` must stay `true`.
