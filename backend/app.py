# HuggingFace **Gradio** Space entrypoint for the CellCheck API.
#
# Debug prints run FIRST (flush=True) so a silent startup crash on HF — Python 3.10
# there vs 3.14 in dev — reveals exactly which import failed before the process dies.
# main.app holds all /api/cellcheck/* routes; gr.mount_gradio_app() mounts a Gradio
# landing page onto it, and HF serves the resulting top-level `app` itself (so we do
# not start a server here except for a local `python app.py`, guarded by SPACE_ID).
import sys

print(f"Python: {sys.version}", flush=True)

try:
    from main import app as fastapi_app
    print("main.py imported OK", flush=True)
except Exception as e:
    print(f"IMPORT ERROR: {e}", flush=True)
    raise

try:
    import gradio as gr
    print(f"Gradio {gr.__version__} imported OK", flush=True)
except Exception as e:
    print(f"GRADIO IMPORT ERROR: {e}", flush=True)
    raise

import os

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

try:
    # ssr_mode=False disables Gradio's Node SSR server, which otherwise tries to bind
    # its own port and conflicts with HF's port management. We don't need SSR.
    with gr.Blocks(title="CellCheck API", analytics_enabled=False, ssr_mode=False) as demo:
        gr.Markdown(_LANDING)

    # Mount the Gradio UI onto the FastAPI app at "/". Returns the same app object
    # (now with Gradio's routes). /api/cellcheck/* and /docs are unaffected.
    app = gr.mount_gradio_app(fastapi_app, demo, path="/")
    print("app.py fully loaded (Gradio mounted); handing off to HF", flush=True)
except Exception as e:
    print(f"MOUNT ERROR: {e}", flush=True)
    raise


# Local dev only: serve the mounted app (Gradio landing + /api/cellcheck/* + /docs)
# with uvicorn. Guarded by SPACE_ID so it never runs on HF.
if __name__ == "__main__" and not os.environ.get("SPACE_ID"):
    import uvicorn
    host = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    port = int(os.getenv("GRADIO_SERVER_PORT") or os.getenv("PORT") or 7860)
    uvicorn.run(app, host=host, port=port)

# HF Spaces (sdk: gradio): HF runs `python app.py` but starts no server itself, so we
# serve the MOUNTED app with uvicorn — one process, one port (7860), serving the
# Gradio landing AND all /api/cellcheck/* + /docs routes. (demo.launch() would spin up
# Gradio's Node SSR server, which fights HF for the port; uvicorn on `app` avoids that,
# and ssr_mode=False above disables SSR entirely.) Runs only on HF (SPACE_ID is set).
if os.environ.get("SPACE_ID"):
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
