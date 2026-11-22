# 🚀 Trace Multi-Service Architecture & Local Deployment Guide

This guide describes how to run and deploy the **Trace Learning System** locally, and explains the complete separation between:
1. **Frontend Student & Clinical App** (React 18 + Vite SPA)
2. **Superuser / Admin Console & Telemetry Engine** (Isolated Dedicated Console)
3. **Backend Intelligence & Data Services** (Python FastAPI Backend on port 8001 / Node Express Orchestrator on port 3000)

---

## 🏛️ System Architecture Breakdown

```
+-----------------------------------------------------------------------------------+
|                              CLIENT EXPERIENCES                                   |
|                                                                                   |
|  [Student/Teacher/Parent App]                 [Admin Superuser Console]           |
|  - Dynamic Study Trail & Quizzes              - Real-Time Python/FastAPI Logs     |
|  - Socratic AI Mentorship                     - 5-Level Syllabus Ingestion        |
|  - Timetable & Vault Bookmarks                - Relational DB Schema & Users      |
+-----------------------------------------------------------------------------------+
                                         |
                    (API Proxy & Orchestration)
                                         v
+-----------------------------------------------------------------------------------+
|                         BACKEND SERVICE ARCHITECTURE                              |
|                                                                                   |
|  [Node / Express Server (Port 3000)]                                              |
|  - Gemini AI Key Rotation & Fallback                                              |
|  - In-Memory System Log Store & Audit Interceptor                                 |
|  - Static Asset Delivery                                                          |
|                                                                                   |
|  [Python / FastAPI Modular Backend (Port 8001)]                                   |
|  - SQLAlchemy 2.0 ORM Engine                                                      |
|  - Neon.tech PostgreSQL Cloud DB / SQLite Fallback                                |
|  - Request Telemetry & Error Logging Middleware                                   |
|  - Socratic Mentorship & Evaluation Routes                                        |
+-----------------------------------------------------------------------------------+
```

---

## 💻 Local Machine Quickstart (Two Methods)

You can run the entire system on your local machine using **Docker Compose** or directly with **Python & Node.js**.

---

### Method A: Docker Compose (One-Click All-in-One)

1. **Clone the repository** (or download the source):
   ```bash
   cd trace-learning-system
   ```

2. **Configure your environment secrets** in `.env`:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY
   ```

3. **Start all services**:
   ```bash
   docker-compose up --build
   ```

4. **Access your apps**:
   - **Frontend App & Student Portal**: [http://localhost:3000](http://localhost:3000)
   - **Isolated Admin Dashboard**: [http://localhost:3000/?view=admin](http://localhost:3000/?view=admin)
   - **FastAPI Backend (Direct)**: [http://localhost:8001](http://localhost:8001)
   - **Interactive API Swagger Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

### Method B: Manual Local Setup (Shell / Terminal)

#### 1. Start the Python FastAPI Backend (Port 8001)
Open **Terminal 1**:
```bash
cd backend

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run the Modular Backend
python run_modular.py
# (Or using uvicorn directly: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload)
```
*The Python backend will start on `http://127.0.0.1:8001` with real-time request logging enabled.*

#### 2. Start the Frontend & Node Orchestrator (Port 3000)
Open **Terminal 2**:
```bash
# In the project root directory
npm install

# Set your Gemini API key (optional for AI generation)
export GEMINI_API_KEY="your-gemini-api-key"

# Start the dev server
npm run dev
```
*The dev server will boot on `http://localhost:3000`.*

---

## 🛡️ Testing & Verifying The Isolation

1. **Standalone Admin Mode**:
   Access `http://localhost:3000/?view=admin` to launch directly into the Superuser Console without having to switch user accounts in the main app.
2. **Integrated App Mode**:
   Access `http://localhost:3000` to interact with the Student, Teacher, or Parent views. You can open the drawer to toggle between roles or click the Admin Console shortcut.
3. **Automated Mock Test Suite**:
   Run the Python mock app test against your running backend:
   ```bash
   cd backend
   python mock_app_test.py
   ```


---

## 📧 Email Verification for Public Signups

The public signup flows (`/signup` web portal, Android in-app enrollment, `/api/auth/signup`) require a 6-digit email verification code. Configure generic SMTP in `.env` (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, optionally `SMTP_USE_TLS`/`SMTP_USE_SSL`) and set `OTP_PEPPER_SECRET`. Then verify delivery on the deployed machine with:

```bash
cd backend && python scripts/test_smtp.py you@your-domain.com
```

Codes are hashed at rest, expire after 10 minutes, are single-use, and are rate-limited. See **[docs/email-verification.md](docs/email-verification.md)** for the provider matrix, local Mailpit setup, the `ENABLE_DEV_OTP_BYPASS` development escape hatch (default OFF), and troubleshooting.
