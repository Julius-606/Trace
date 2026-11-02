# Project Orbit Infrastructure Blueprint & Logic Transfer Plan

---

## Part 1: System Blueprint & Target Architecture

```
                                  +------------------------------------+
                                  |        FastAPI Monolith Root       |
                                  |         (backend/app/main.py)      |
                                  +-----------------+------------------+
                                                    |
          +-----------------------------------------+-----------------------------------------+
          |                                         |                                         |
          v                                         v                                         v
+------------------+                      +-------------------+                     +--------------------+
|   Trace Engine   |                      |   Adopted Logic   |                     |     DebateHub      |
| (Learning Domain)|                      |  (Orbit & Extras) |                     |  (Realtime Module) |
+------------------+                      +-------------------+                     +--------------------+
| - Ingestion      |                      | - Orbit Brain     |                     | - Static Node app  |
| - Syllabus Tree  |                      | - Governor        |                     | - Shared DB access |
| - Quizzes / PnL  |                      | - SSS & WhatsApp  |                     | - Realtime Sync    |
| - Pre-gen Library|                      | - Differential    |                     |                    |
| - Quality / Cron |                      |                   |                     |                    |
+------------------+                      +-------------------+                     +--------------------+
          |                                         |                                         |
          +-----------------------------------------+-----------------------------------------+
                                                    |
                                                    v
                                      +---------------------------+
                                      |   Database & Infrastructure|
                                      +---------------------------+
                                      | - Neon Postgres (Primary) |
                                      | - SQLite (Fallback Engine)|
                                      | - Async Celery / APScheduler|
                                      | - Alembic Migration Sync  |
                                      +---------------------------+
```

---

## Part 2: Step-by-Step AI Agent Instruction Prompt

Copy and pass the text block below directly to your code-executing AI agent.

```text
================================================================================
AI AGENT DIRECTIVE: LOGIC MIGRATION, PRE-GENERATION & CONTENT PIPELINE
================================================================================

PROJECT: Project Orbit Backend Upgrade (Modular Integration & Content Pre-Gen)
STATUS: Execution Phase

--------------------------------------------------------------------------------
OBJECTIVE:
1. Integrate modules located in `backend/Adopted/` into the primary backend infrastructure (`backend/app/`).
2. Establish an asynchronous background content processing pipeline ("Trace Rich Library Engine") that automatically pre-generates, enriches, and audits learning material (notes, quizzes, alternative explanations, and visual diagrams) immediately upon syllabus publication rather than synchronously at user request time.

--------------------------------------------------------------------------------
1. TASK BREAKDOWN & TARGET FILE MAPPINGS

Task 1.1: Core Brain & AI Services Integration
- Source File: `backend/Adopted/Orbit/backend/app/services/orbit_brain.py`
- Target Location: `backend/app/services/orbit_brain.py`
- Goal: Copy and merge Orbit Brain capabilities into the active services folder. Standardize imports to `app.db.session` and `app.core.config`.

Task 1.2: Governor & Specialized Services Migration
- Source Files: 
  - `backend/Adopted/Orbit/backend/app/services/governor.py`
  - `backend/Adopted/Orbit/backend/app/services/telegram_mod.py`
  - `backend/Adopted/Orbit/backend/app/services/psych_check.py`
- Target Location: `backend/app/services/`
- Goal: Ensure all helper services, moderation mechanisms, and governor controls are accessible within `backend/app/services/`.

Task 1.3: WhatsApp Notification (SSS) Integration
- Source File: `backend/Adopted/SSS/WA_notify.py`
- Target Location: `backend/app/services/wa_notify.py`
- Goal: Adapt script logic into a modular service class (`WhatsAppNotifier`) that reads configuration variables from `backend/app/core/config.py`.

Task 1.4: Database Schema and Content Models Expansion
- Source Models: 
  - `backend/Adopted/Orbit/backend/app/models/study.py`
  - `backend/app/models/database_models.py`
- Target Location: `backend/app/models/`
- Goal: 
  - Standardize all models under `backend/app/db/session.py` Base.
  - Expand models to support pre-generated content pools:
    * `GeneratedQuizBank`: Pre-built quiz questions tagged by node/topic.
    * `NodeEnrichment`: Alternative explanations, diagrams/Mermaid charts, and metadata.
    * `ContentAuditLog`: Verification status, accuracy score, and flags.

Task 1.5: Async Content Generation Engine & Event Triggers
- Location: `backend/app/services/content_pipeline.py`
- Goal: 
  - Implement async trigger upon admin syllabus creation (`post_syllabus_event`).
  - Automatically enqueue background workers to pre-generate comprehensive quiz pools, summary notes, and topic breakdowns for each node in the syllabus tree.

Task 1.6: Background Jobs & Cron Workers (Enrichment & Auditing)
- Location: `backend/app/workers/cron_jobs.py` & `backend/app/core/scheduler.py`
- Goal:
  - Implement periodic jobs (using APScheduler/Celery) to:
    1. Diagram Enrichment: Parse topic notes and generate appropriate inline visual diagrams (e.g., SVG/Mermaid markup).
    2. Multi-Perspective Generation: Generate alternative explanations tailored to different learning styles (intuitive, technical, visual).
    3. Quality Control / Fact Check: Run double-pass LLM verifications over generated content to detect hallucinations, factual errors, or formatting flaws, marking verified units with audit scores.

Task 1.7: Router Integration & Cached Serving
- Source Routers:
  - `backend/Adopted/Orbit/backend/app/routers/orbit_ai.py`
  - `backend/Adopted/Orbit/backend/app/routers/terminal_pilot.py`
  - `backend/Adopted/Orbit/backend/app/routers/med_scholar.py`
- Target Location: `backend/app/routers/` & `backend/app/api/v1/`
- Goal: 
  - Mount all routes inside `backend/app/main.py`.
  - Update learning & quiz endpoints to fetch instantly from the pre-generated DB library instead of triggering real-time LLM generation during user interactions. Fall back to on-demand generation only if the pool is empty.

Task 1.8: Ingestion Engine Alignment
- Source File: `backend/ingestion_engine.py` & `backend/app/ingestion_engine.py`
- Target Location: `backend/app/ingestion_engine.py`
- Goal: Standardize ingestion routines for markdown syllabus parsing, automatically kicking off `content_pipeline.py` upon successful upload.

--------------------------------------------------------------------------------
2. TECHNICAL RULES & GUIDELINES FOR EDITING

1. MAINTAIN HEADERS & VERSIONS:
   - Preserve headers at the top of python files.
   - Increment major/minor version numbers accordingly when modifying files.

2. ASYNC & FALLBACK HANDLING:
   - Retain dual-support for Neon PostgreSQL with SQLite fallback where applicable.
   - Ensure background tasks do not block the main FastAPI request thread. Use background tasks or async worker queues.

3. DELIMITER FORMATTING:
   - Deliver file outputs enclosed in standard file blocks:
     ```markdown:Title:filepath
     ...
     ```

--------------------------------------------------------------------------------
3. VERIFICATION PROTOCOL:

After performing integrations, verify functionality by evaluating:
1. Syllabus Trigger: Uploading a syllabus creates entries and immediately queues pre-generation jobs.
2. Library Retrieval: Requesting a quiz or topic note returns data instantaneously from pre-generated tables.
3. Cron Verification: Background cron tasks execute diagram generation and accuracy audit checks without failing.
4. Routing Integrity: `backend/app/main.py` imports and mounts all sub-routers smoothly.
================================================================================
```