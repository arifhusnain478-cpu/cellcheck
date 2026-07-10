"""Vercel serverless function -> POST /api/cellcheck/str-analysis.

Thin wrapper: loads the existing router from backend/api/str_reader.py by file path
and mounts it. All logic lives in backend/. See api/cellcheck/quick.py for details.
"""
import importlib.util
import pathlib
import sys

from fastapi import FastAPI

_BACKEND = pathlib.Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_spec = importlib.util.spec_from_file_location("cc_str_reader", _BACKEND / "api" / "str_reader.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

app = FastAPI(title="CellCheck API")
app.include_router(_mod.router, prefix="/api/cellcheck")
