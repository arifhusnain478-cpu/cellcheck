---
title: CellCheck API
emoji: 🧬
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
---

# CellCheck API

Backend for **CellCheck** — an AI-native cell line authentication tool. A FastAPI
service hosted on a free HuggingFace **Gradio** Space: `app.py` mounts the FastAPI
app inside a Gradio Blocks landing page via `gr.mount_gradio_app()`, so every
`/api/cellcheck/*` route works unchanged (Gradio is just the hosting container).
A `Dockerfile` is kept as a backup for Docker-based hosting but is unused here.

It cross-references live authoritative sources and uses an LLM only to *phrase*
grounded explanations of decisions made deterministically in code (never to invent
facts).

## Endpoints

Base path: `/api/cellcheck`

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness + upstream status |
| `POST` | `/quick` | Quick Check — identity + ICLAC traffic-light verdict, retractions |
| `POST` | `/str-analysis` | STR Test Reader — CLASTR match %, loci breakdown, interpretation |
| `POST` | `/methods-section` | Methods Generator — publication-ready methods paragraph + RRID |

Interactive docs at `/docs`.

## Data sources

Cellosaurus (identity/RRID) · ICLAC Register of Misidentified Cell Lines · CLASTR
(STR similarity) · Crossref (related/retracted papers).

## Configuration (set these as Space secrets)

No secrets are baked into the image — everything is read from the environment:

| Variable | Required | Notes |
| --- | --- | --- |
| `LLM_PROVIDER` | yes | `anthropic` (default) or `groq` |
| `ANTHROPIC_API_KEY` | if provider = anthropic | |
| `ANTHROPIC_MODEL` | no | default `claude-sonnet-4-5` |
| `GROQ_API_KEY` | if provider = groq | |
| `GROQ_MODEL` | no | default `llama-3.3-70b-versatile` |
| `CROSSREF_MAILTO` | no | contact email for Crossref's polite pool |
| `DEMO_MODE` | no | `true` pins LLM prose to `data/demo_cache.json` for byte-stable demos; default `false` |

CORS currently allows all origins (dev). Lock it to the Vercel frontend domain
once that URL is known.

## Run locally

```bash
pip install -r requirements.txt

uvicorn main:app --reload   # API only, http://localhost:8000 (no gradio needed)
python app.py               # full Space (Gradio landing + API), http://localhost:7860
```
