# CellCheck API — container image (deployed on Koyeb, free tier).
#
# Serves the FastAPI app (main:app) directly with uvicorn on port 8000. No Gradio.
# Build context must be this backend/ directory (see docs/DEPLOY_KOYEB.md).
FROM python:3.11-slim

# Unbuffered stdout/stderr so logs stream live to the platform log viewer;
# no .pyc clutter; no pip cache in the image layer.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install deps first so the layer is cached across code-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend (api/, models/, services/, prompts/, data/, main.py).
# .dockerignore keeps secrets (.env), dev tooling (scripts/, tests/) and caches out.
COPY . .

# All configuration/secrets come from the environment (set as Koyeb env vars/secrets):
#   LLM_PROVIDER, ANTHROPIC_API_KEY / ANTHROPIC_MODEL, GROQ_API_KEY / GROQ_MODEL,
#   CROSSREF_MAILTO (optional), DEMO_MODE (optional). No secrets are baked in.
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
