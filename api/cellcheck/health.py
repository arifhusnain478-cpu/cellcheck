"""Vercel serverless function -> GET /api/cellcheck/health.

Static liveness response — mirrors backend/main.py's /health. No backend import
needed (nothing to compute).
"""
from fastapi import FastAPI

app = FastAPI(title="CellCheck API")


@app.get("/api/cellcheck/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "upstream_services": {
            "cellosaurus": "ok",
            "iclac": "ok",
            "clastr": "ok",
            "crossref": "ok",
            "llm": "ok",
        },
    }
