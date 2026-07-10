"""HuggingFace Gradio Space entrypoint — simplest form.

HF's Gradio SDK manages the server itself (it kills a manually-started uvicorn), so we
do NOT run uvicorn or call demo.launch(). We expose a top-level `demo` (gr.Blocks) for
HF to auto-launch, and mount the FastAPI app onto it with gr.mount_gradio_app() so the
/api/cellcheck/* routes ride on the same ASGI app (`app`).

Local dev: `uvicorn app:app` (full app) or `uvicorn main:app` (API only).
"""
import os

# Gradio SSR starts a Node server that fights HF for the port -> [Errno 98].
# Must be set BEFORE `import gradio` (gradio reads it at import time).
os.environ["GRADIO_SSR_MODE"] = "False"

import gradio as gr

from main import app as fastapi_app

with gr.Blocks(title="CellCheck API", analytics_enabled=False) as demo:
    gr.Markdown(
        "# 🧬 CellCheck API\n\n"
        "FastAPI backend for **CellCheck** — this Gradio page is just the landing page.\n\n"
        "- Health check: `/api/cellcheck/health`\n"
        "- Interactive API docs: `/docs`\n"
    )

# Mount the FastAPI routes onto the Gradio app. `app` is the combined ASGI app.
# No uvicorn / demo.launch() here — HF launches `demo` and serves the mounted routes.
app = gr.mount_gradio_app(fastapi_app, demo, path="/")
