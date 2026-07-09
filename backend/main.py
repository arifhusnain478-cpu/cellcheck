"""CellCheck API — FastAPI entrypoint.

Run locally from this directory:
    uvicorn main:app --reload
"""
import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import methods_generator, quick_check, str_reader

load_dotenv()

app = FastAPI(title="CellCheck API", version="0.1.0")

# Permissive CORS for local dev + the Vercel frontend. Tighten before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/cellcheck/health")
def health():
    # TODO: replace static upstream statuses with real reachability checks.
    return {
        "status": "ok",
        "version": app.version,
        "upstream_services": {
            "cellosaurus": "ok",
            "iclac": "ok",
            "semantic_scholar": "ok",
            "claude": "ok",
        },
    }


app.include_router(quick_check.router, prefix="/api/cellcheck", tags=["quick-check"])
app.include_router(str_reader.router, prefix="/api/cellcheck", tags=["str-reader"])
app.include_router(methods_generator.router, prefix="/api/cellcheck", tags=["methods"])


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
