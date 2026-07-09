"""HuggingFace **Gradio** Space entrypoint for the CellCheck API.

HF Docker Spaces require a paid plan, but Gradio Spaces are free. This module wraps
the existing FastAPI app (``main.app`` — all ``/api/cellcheck/*`` routes) inside a
Gradio Blocks landing page via ``gr.mount_gradio_app()``. Gradio is *only* the
hosting container: the FastAPI routes are unchanged and fully functional, and the
Gradio page is mounted at ``/`` as the Space's landing page.

Route precedence: the FastAPI routes (``/openapi.json``, ``/docs``,
``/api/cellcheck/*``) are registered in main.py before the Gradio mount is added
here, so they always match first — the ``/`` mount only catches everything else.

On HF Spaces (``sdk: gradio``), HF auto-detects the top-level ``app`` (the FastAPI
app returned by ``mount_gradio_app``) and serves it with uvicorn itself — so this
file must NOT start its own server, or both bind port 7860 ([Errno 98] Address
already in use). The ``__main__`` block is therefore guarded to run only for a LOCAL
``python app.py``; you can also run ``uvicorn main:app`` for the API alone.
"""
import os

import gradio as gr
import uvicorn

from main import app  # existing FastAPI app with the /api/cellcheck/* routes

_LANDING = """
# 🧬 CellCheck API

Backend for **CellCheck** — an AI-native cell line authentication tool. This Space
hosts a FastAPI service; this Gradio page is just the container's landing page.

### Endpoints — base path `/api/cellcheck`
| Method | Path | Purpose |
| --- | --- | --- |
| `GET`  | `/api/cellcheck/health` | Liveness + upstream status |
| `POST` | `/api/cellcheck/quick` | Quick Check verdict + retractions |
| `POST` | `/api/cellcheck/str-analysis` | STR match %, loci, interpretation |
| `POST` | `/api/cellcheck/methods-section` | Methods paragraph + RRID |

**Interactive API docs:** [`/docs`](/docs)  ·  **OpenAPI:** [`/openapi.json`](/openapi.json)

Data sources: Cellosaurus · ICLAC · CLASTR · Crossref. The LLM only *phrases*
grounded explanations of decisions made deterministically in code.
"""

with gr.Blocks(title="CellCheck API", analytics_enabled=False) as demo:
    gr.Markdown(_LANDING)

# Mount the Gradio UI onto the existing FastAPI app at "/". Returns the same app
# object (now with Gradio's routes). /api/cellcheck/* and /docs are unaffected.
app = gr.mount_gradio_app(app, demo, path="/")


# On HF Spaces (sdk: gradio), HF auto-detects the top-level `app` (the FastAPI app
# returned by mount_gradio_app) and serves it with uvicorn itself. We must NOT start
# a server here too, or both bind port 7860 -> [Errno 98] Address already in use.
# HF sets SPACE_ID, so this block runs ONLY for a local `python app.py`.
if __name__ == "__main__" and not os.environ.get("SPACE_ID"):
    host = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    port = int(os.getenv("GRADIO_SERVER_PORT") or os.getenv("PORT") or 7860)
    uvicorn.run(app, host=host, port=port)
