# ==============================================================================
# Trace Modular Backend Dockerfile (Monolithic 24/7 Deployment)
#
# MODULE ARCHITECTURE:
# 1. Full-Stack Web App Module: Pre-compiled React SPA served directly by FastAPI
#    -> Accessible at /app, /student, /learn (assets mounted at /assets)
# 2. Public Homepage & Infrastructure Intro:
#    -> Accessible at /home, /welcome, and /
# 3. Superuser Admin Control Center & THE OVERSEER:
#    -> Accessible at /admin/login, /admin, /admin/overseer
# 4. Public Student Registration:
#    -> Accessible at /signup
# 5. Core REST API & Socratic AI Engine:
#    -> Accessible at /api/*, /docs, /health
# ==============================================================================

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for PostgreSQL driver
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# DebateHub is an independent Node/Express service running beside Trace.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from backend into container
COPY . .

RUN if [ -f DebateHub/package.json ]; then \
        cd DebateHub && npm install --include=dev && npm run build; \
    fi

# Hugging Face Spaces uses port 7860 by default; local runs use 8000 / 8001
ENV PORT=7860
EXPOSE 7860

# Launch Uvicorn server hosting the modular FastAPI application
# Serves Superuser Admin Login at root '/' and Public Registration at '/signup'
CMD ["bash", "run_monorepo.sh"]
