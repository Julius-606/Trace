
# 🛠️ Local Backend Testing Environment

This guide helps you run and test the Trace Learning Backend on your local machine.

## 1. Prerequisites
- **Python 3.14+** (Already installed in your project folder)
- **.env file**: Put all local secrets in one `backend/.env` file. Copy `backend/.env.example` and set `TRACE_DATABASE_URL`, `ORBIT_DATABASE_URL`, and `DEBATEHUB_NEON_DATABASE_URL` independently.

## 2. Starting the Server
You can now easily switch between the new **Modular** version and the **Legacy** version.

### Option A: Run Modular Version (Recommended)
```bash
python run_modular.py
```

### Option B: Run Legacy Version (Old Flat Structure)
```bash
python run_legacy.py
```

The server will start at `http://127.0.0.1:8000`.

## 3. Developer Keys
- **Internal API Key**: Found in `local.properties` (Root directory) and `.env`. 
  - Value: `64923e4d8f1a2c5b9e0f3d7a6c5b9eX0f3d7a6c5b9e0f3d7a`
- **Gemini API Keys**: Found in `backend/.env`. These are used for AI features.

## 3. Running Mock Tests
While the server is running, open **another terminal** and run the mock test script. This script mimics all the calls the mobile app makes (Login, Dashboard, AI Chat, Quiz, etc.).

```bash
# In a second terminal
cd backend
.venv\Scripts\activate
python mock_app_test.py
```

## 4. Troubleshooting
- **PostgreSQL / Neon SSL Error (`SSL error: unexpected eof while reading`)**:
  - The Neon free-tier serverless pooler automatically scales down to zero when idle. If a connection closes unexpectedly, the backend now includes **automatic fallback to SQLite** (`edu_ai_vault.db`) so your server never crashes.
  - To test Trace with local SQLite directly without touching remote Neon, set `TRACE_DATABASE_URL=sqlite:///./edu_ai_vault.db` in `backend/.env`.
  - Orbit uses its own local fallback database when `ORBIT_DATABASE_URL=sqlite:///./orbit_vault.db`.
  - If connecting to Neon, make sure your connection string uses endpoint pooler mode with `?sslmode=require`.

- **Hugging Face Container Health Check (`500 on /?logs=container`)**:
  - Resolved! The root route now responds immediately to Hugging Face container telemetry probes without failing on database timeouts.

- **Unauthorized (403)**: Ensure `INTERNAL_API_KEY` in `main.py` matches the one in `mock_app_test.py` (default is `DEVELOPMENT_KEY`).
- **AI Errors**: Check the server terminal for logs. I've enabled automatic key rotation, so it should handle rate limits (429) automatically.

---
**Note:** You can now modify `ai_engine.py` or `main.py` and immediately test the changes by rerunning `mock_app_test.py` without pushing to production!


 