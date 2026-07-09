# CellCheck API — container image for HuggingFace Spaces (Docker SDK).
# The Space's README.md frontmatter sets app_port: 7860 to match EXPOSE/CMD below.
FROM python:3.11-slim

# Unbuffered stdout/stderr so logs stream live to the HF Spaces log viewer;
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

# All configuration/secrets come from the environment (set as Space secrets):
#   LLM_PROVIDER, ANTHROPIC_API_KEY / ANTHROPIC_MODEL, GROQ_API_KEY / GROQ_MODEL,
#   CROSSREF_MAILTO (optional), DEMO_MODE (optional). No secrets are baked in.
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
