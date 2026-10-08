
################################################################################
# FILE: backend/app/api/v1/api.py
# VERSION: 1.2.0 | SYSTEM: Orbit Protocol
################################################################################

from fastapi import APIRouter
# We are importing the versioned routers to ensure data integrity
from app.api.v1 import forex, tasks

# THE FIX: We are finally inviting orbit_ai to the party so it stops giving 404s 🚀
from app.routers import med_scholar, orbit_ai, terminal_pilot

api_router = APIRouter()

# Mount the Forex Guardian 📈
api_router.include_router(forex.router, prefix="/forex", tags=["Risk Management"])

# Mount the Med-Scholar (The Dean) 🩺
api_router.include_router(med_scholar.router, tags=["Syllabus Vault"])

# Mount the Life Tasks 🌍
api_router.include_router(tasks.router, prefix="/tasks", tags=["Life Admin"])

# Mount the Brain! 🧠 (This is what you were missing)
api_router.include_router(orbit_ai.router, tags=["Orbit-AI"])

# Mount the Terminal Pilot! 🖥️
api_router.include_router(terminal_pilot.router, tags=["Terminal Pilot"])

# Vibe Check: All routes are now synchronized. WAGMI. 🚀

