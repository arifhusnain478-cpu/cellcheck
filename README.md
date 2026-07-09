# CellCheck

**AI-native cell line authentication.** 15–20% of cell lines in biomedical research are misidentified
or contaminated, yet researchers rarely authenticate because it's expensive, slow, and confusing.
CellCheck makes it fast and legible.

Built for **Built with Claude: Life Sciences**.

## Modes

1. **Quick Check** — search a cell line by name / catalog # / RRID → verdict (safe / caution / danger),
   true identity, retracted papers, and next steps.
2. **STR Test Reader** — upload STR profile results → plain-language match interpretation.
3. **Methods Section Generator** — fill a short form → publication-ready methods paragraph with the
   correct RRID.

## Stack

- **Backend:** FastAPI (Python), httpx, Anthropic Claude API
- **Frontend:** React + Vite, Tailwind CSS v4, shadcn/ui, lucide-react, axios
- **Data sources:** Cellosaurus (identity + RRID), ICLAC register (misidentified lines),
  CLASTR (STR matching), Semantic Scholar (retracted papers)
- **Deploy:** HuggingFace Spaces (backend, Docker) + Vercel (frontend) — free tier

## Quickstart

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env        # then add your ANTHROPIC_API_KEY
uvicorn main:app --reload      # http://localhost:8000
```
Health check: `GET http://localhost:8000/api/cellcheck/health` → `{"status":"ok"}`
Interactive docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```
Add shadcn components with: `npx shadcn@latest add button card tabs`

### Docker (both)
```bash
docker-compose up --build
```

## Environment

Copy `.env.example` → `backend/.env` and fill in:

| Var | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | Claude API key |
| `ANTHROPIC_MODEL` | Model id (default `claude-sonnet-4-5`) |
| `PORT` | Backend port (default 8000; HF Spaces uses 7860) |
| `VITE_API_URL` | Backend base URL for the frontend |

## Structure

```
cellcheck/
├── backend/   FastAPI app, API routers, service clients, Pydantic models, prompts
├── frontend/  Vite + React + Tailwind v4 + shadcn
├── docs/      PRD, API contract, demo script
└── tests/     Test cell lines and fixtures
```

## Status

In progress — building the vertical slices for Quick Check → STR Reader → Methods Generator.
The Cellosaurus identity client is implemented; the rest of the service methods and routes are
still `# TODO` stubs / mocks.

Deferred or scoped-down features are tracked in [docs/BACKLOG.md](docs/BACKLOG.md) (with effort
estimates to add them back).

