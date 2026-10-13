# ==============================================================================
# MULTI-APP DISPATCHER & INGRESS TARGET IDENTIFIER
# Architecture: Trace (FastAPI:7860) | DebateHub (Express:3000) | Orbit (AI Gateway)
# ==============================================================================

from typing import Tuple
from fastapi import Request

DEBATEHUB_EXCLUSIVE_PREFIXES = (
    "/DebateHub",
    "/debatehub",
    "/api/debatehub",
    "/api/members",
    "/api/debates",
    "/api/transactions",
    "/api/agendas",
    "/api/announcements",
    "/api/events",
    "/api/mentorship",
    "/api/notifications",
    "/api/live/stream",
    "/api/db",
    "/api/system",
    "/api/auth/me",
    "/api/auth/logout",
    "/api/auth/google",
)

def identify_target_app(request: Request) -> Tuple[str, str]:
    """
    Deterministically identifies which app ecosystem should process the request.
    Returns (target_app, reason):
      - 'DebateHub': Great Lakes University Debate Club operations (Express:3000)
      - 'Orbit': Project Orbit Socratic AI reasoning gateway (FastAPI/Gemini)
      - 'Trace': Edu-AI Trace adaptive clinical learning engine (FastAPI:7860)
    """
    # 1. Explicit Header: X-App-Target or X-Client-App
    header_val = (
        request.headers.get("x-app-target")
        or request.headers.get("x-client-app")
        or request.headers.get("x-target-app")
        or ""
    ).strip().lower()

    if header_val in ("debatehub", "debate-hub", "gluk", "debate"):
        return "DebateHub", "header:x-app-target=DebateHub"
    if header_val in ("trace", "edu-ai", "eduai"):
        return "Trace", "header:x-app-target=Trace"
    if header_val in ("orbit", "neural-link"):
        return "Orbit", "header:x-app-target=Orbit"

    # 2. Query parameter: ?app=debatehub | ?app=trace | ?app=orbit
    query_app = request.query_params.get("app", "").strip().lower()
    if query_app in ("debatehub", "gluk"):
        return "DebateHub", "query:app=debatehub"
    if query_app == "trace":
        return "Trace", "query:app=trace"
    if query_app == "orbit":
        return "Orbit", "query:app=orbit"

    path = request.url.path

    # 3. Path prefix match
    if path.startswith(("/DebateHub", "/debatehub", "/api/debatehub")):
        return "DebateHub", f"path:{path}"
    if path.startswith(("/orbit", "/api/v1/orbit")):
        return "Orbit", f"path:{path}"
    if path.startswith(("/app", "/student", "/learn", "/admin", "/curriculum", "/ingest", "/delete-unit", "/update-unit")):
        return "Trace", f"path:{path}"

    # 4. DebateHub-exclusive entity paths
    for prefix in DEBATEHUB_EXCLUSIVE_PREFIXES:
        if path == prefix or path.startswith(f"{prefix}/"):
            return "DebateHub", f"entity-route:{prefix}"

    # 5. Referer URL check
    referer = request.headers.get("referer", "").lower()
    if "/debatehub" in referer:
        return "DebateHub", "referer:DebateHub"
    if "/orbit" in referer and not path.startswith("/api/auth"):
        return "Orbit", "referer:Orbit"

    # 6. Default to Trace
    return "Trace", "default-route"
