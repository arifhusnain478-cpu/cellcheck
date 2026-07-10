# Deploying the CellCheck backend to Koyeb

The backend is a Dockerized FastAPI app (`backend/Dockerfile` → `uvicorn main:app`
on port **8000**). Koyeb's free tier builds it straight from GitHub — no credit card,
Docker-native.

> Koyeb has **no repo-level manifest** it auto-reads (unlike Vercel's `vercel.json`);
> services are configured in the dashboard, CLI, or API. Hence this doc rather than a
> `koyeb.yaml`. The dashboard steps below are the reliable path; a CLI equivalent is
> at the end.

## Key facts for the config

| Setting | Value |
| --- | --- |
| Repo | `github.com/arifhusnain478-cpu/cellcheck` |
| Branch | `main` (auto-deploys on push) |
| Builder | **Dockerfile** |
| Work directory | **`backend`** ← the Docker build context; the app lives in a subfolder |
| Dockerfile path | `Dockerfile` (relative to the work directory) |
| Exposed port | **8000** (HTTP) |
| Health check | HTTP, path `/api/cellcheck/health` |
| Instance | Free |

The **work directory = `backend`** is the important part: the repo root holds both
`backend/` and `frontend/`, and the Dockerfile's `COPY . .` expects the backend folder
as its build context.

## Deploy via the dashboard (GitHub integration)

1. Sign in at <https://app.koyeb.com> and connect your GitHub account.
2. **Create Web Service → GitHub** → pick the `cellcheck` repo, branch `main`.
3. Builder: choose **Dockerfile**.
4. Set **Work directory** to `backend` (and Dockerfile path `Dockerfile`).
5. **Exposed port**: `8000`, protocol HTTP. Set the **health check** to HTTP path
   `/api/cellcheck/health`.
6. **Environment variables** (Settings → Environment) — add these; mark keys as
   *Secret*:
   - `LLM_PROVIDER` = `groq` (or `anthropic`)
   - `GROQ_API_KEY` = `…` (or `ANTHROPIC_API_KEY` if using anthropic)
   - optional: `GROQ_MODEL`, `ANTHROPIC_MODEL`, `CROSSREF_MAILTO`, `DEMO_MODE=false`
7. **Instance**: Free. Pick a region. **Deploy**.

Koyeb builds the image and gives you a public URL like
`https://<service>-<org>.koyeb.app`. Every push to `main` re-deploys automatically.

## Verify

```bash
curl https://<your-service>.koyeb.app/api/cellcheck/health      # -> {"status":"ok", ...}
```
Also open `/docs` (Swagger). If health returns JSON, the API is live.

## After it's live

1. Point the frontend at it: set `frontend/.env.production`
   → `VITE_API_URL=https://<your-service>.koyeb.app` and redeploy Vercel.
2. Lock down CORS in `backend/main.py`: replace `allow_origins=["*"]` with the
   Vercel frontend domain.

## CLI equivalent (optional)

With the [Koyeb CLI](https://www.koyeb.com/docs/build-and-deploy/cli/installation)
(`koyeb login` first). Flag names can drift between versions — confirm with
`koyeb service create --help`:

```bash
koyeb service create cellcheck-api \
  --app cellcheck \
  --git github.com/arifhusnain478-cpu/cellcheck \
  --git-branch main \
  --git-workdir backend \
  --git-docker-dockerfile Dockerfile \
  --ports 8000:http \
  --routes /:8000 \
  --instance-type free \
  --regions fra \
  --env LLM_PROVIDER=groq \
  --env GROQ_API_KEY=@GROQ_API_KEY   # reference a Koyeb secret
```
