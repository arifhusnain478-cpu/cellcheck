# Deploying CellCheck to Vercel (frontend + backend, one domain, free)

The whole app runs on a single Vercel project — zero cost, no card:

- **Frontend** — the Vite/React app in `frontend/`, built to static files.
- **Backend** — a single Python **serverless function** at `api/index.py` (Vercel's
  FastAPI detection finds it there) that builds the full FastAPI app from the existing
  routers in `backend/` (imported by file path; `backend/**` is bundled into the
  function via `vercel.json` → `includeFiles`). A rewrite sends every `/api/*` here.

Because both are served from the same origin, `src/api/client.js` uses a **relative**
base URL (`/api/cellcheck`) and there is no CORS to configure.

## Layout

```
vercel.json                     # build + function + rewrites (project root)
requirements.txt                # Python deps for the serverless function
api/index.py                    # the full FastAPI app: /api/cellcheck/{quick,
                                #   str-analysis,methods-section,health}
backend/                        # unchanged; api/index.py imports its routers/services
frontend/                       # Vite app -> built to frontend/dist
```

## Deploy

1. In Vercel, **Import** the `cellcheck` GitHub repo.
2. **Root Directory: the repo root** (NOT `frontend/`). This is the #1 gotcha — Vercel
   must see the root `api/` directory and `vercel.json`. If a previous project set the
   Root Directory to `frontend`, change it in **Settings → General → Root Directory**.
3. Framework preset: **Other** (our `vercel.json` defines the build). It sets:
   - install `cd frontend && npm install`, build `cd frontend && npm run build`
   - output `frontend/dist`
   - `functions.api/cellcheck/*.py` → `includeFiles: backend/**`, `maxDuration: 60`
4. **Environment Variables** (Settings → Environment Variables) — the functions read
   these from the environment (there is no `.env` in prod):
   - `LLM_PROVIDER` = `groq` (or `anthropic`)
   - `GROQ_API_KEY` = `…`  (or `ANTHROPIC_API_KEY` if using anthropic)
   - optional: `GROQ_MODEL`, `ANTHROPIC_MODEL`, `CROSSREF_MAILTO`, `DEMO_MODE`
5. **Deploy.**

## Verify

```bash
curl https://<your-app>.vercel.app/api/cellcheck/health     # -> {"status":"ok", ...}
```
Then open the site and run a Quick Check (e.g. `MDA-MB-435`).

## Notes

- **Cold starts / duration:** each function cold-starts (a few seconds); LLM + CLASTR
  calls can take several seconds, so `maxDuration` is set to 60s (the Hobby max). If a
  request still times out, the cause is a slow upstream (Cellosaurus/CLASTR), not the code.
- **In-memory cache** (`utils/cache`) does not persist across invocations — fine; the
  byte-stable demo cache (`backend/data/demo_cache.json`, `DEMO_MODE=true`) is file-based
  and still works.
- **The `backend/Dockerfile`** is now a fallback for container hosting; Vercel doesn't use it.

## Local dev is unchanged

```bash
# terminal 1 — API
cd backend && uvicorn main:app --reload            # http://localhost:8000

# terminal 2 — frontend (Vite proxies /api -> :8000, see vite.config.js)
cd frontend && npm run dev                         # http://localhost:5173
```
