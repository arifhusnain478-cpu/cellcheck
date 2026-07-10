"""Vercel serverless entrypoint — the full CellCheck FastAPI app.

Vercel's FastAPI detection looks for the app at a conventional location; `api/index.py`
is one. This builds the COMPLETE app by loading the existing backend routers *by file
path* — so this root-level `api/` directory never name-clashes with the backend's own
`api/` package — and mounts them all under /api/cellcheck. Nothing is rewritten; all
logic lives in backend/services + backend/api.

`backend/**` is bundled into the function via vercel.json `includeFiles`, and added to
sys.path so the routers' `from services...`/`from models...` imports resolve. A rewrite
sends every /api/* request here and FastAPI routes it to the right endpoint.
"""
import importlib.util
import pathlib
import sys

from fastapi import FastAPI

_BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load_router(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, _BACKEND / "api" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.router


app = FastAPI(title="CellCheck API")
app.include_router(_load_router("cc_quick_check", "quick_check.py"), prefix="/api/cellcheck")
app.include_router(_load_router("cc_str_reader", "str_reader.py"), prefix="/api/cellcheck")
app.include_router(_load_router("cc_methods_generator", "methods_generator.py"), prefix="/api/cellcheck")


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
