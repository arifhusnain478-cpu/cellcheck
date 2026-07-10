"""Vercel serverless function -> POST /api/cellcheck/quick.

Thin wrapper around the EXISTING backend logic. It loads the FastAPI router from
backend/api/quick_check.py *by file path* (so this root-level `api/` functions
directory never name-clashes with the backend's own `api/` package) and mounts it.
No logic is rewritten here — everything lives in backend/services + backend/api.

`backend/**` is bundled into the function via vercel.json `includeFiles`, and added
to sys.path so the router's `from services...`/`from models...` imports resolve.
"""
import importlib.util
import pathlib
import sys

from fastapi import FastAPI

_BACKEND = pathlib.Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_spec = importlib.util.spec_from_file_location("cc_quick_check", _BACKEND / "api" / "quick_check.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

app = FastAPI(title="CellCheck API")
app.include_router(_mod.router, prefix="/api/cellcheck")
