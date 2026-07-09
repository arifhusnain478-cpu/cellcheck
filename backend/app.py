"""HuggingFace **Gradio** Space entrypoint for the CellCheck API.

HF Docker Spaces require a paid plan, but Gradio Spaces are free. This module wraps
the existing FastAPI app (``main.app`` — all ``/api/cellcheck/*`` routes) inside a
Gradio Blocks landing page via ``gr.mount_gradio_app()``. Gradio is *only* the
hosting container: the FastAPI routes are unchanged and fully functional, and the
Gradio page is mounted at ``/`` as the Space's landing page.

Route precedence: the FastAPI routes (``/openapi.json``, ``/docs``,
``/api/cellcheck/*``) are registered in main.py before the Gradio mount is added
here, so they always match first — the ``/`` mount only catches everything else.

HF runs ``python app.py``; the ``__main__`` block below starts uvicorn on port 7860
(the Gradio Space convention). Locally you can run either ``python app.py`` (full
Space, needs gradio) or ``uvicorn main:app`` (API only, no gradio needed).
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


if __name__ == "__main__":
    host = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    port = int(os.getenv("GRADIO_SERVER_PORT") or os.getenv("PORT") or 7860)
    uvicorn.run(app, host=host, port=port)
