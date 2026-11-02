################################################################################
# FILE: backend/ingestion_engine.py
# VERSION: 2.0.0 | SYSTEM: Trace Rich Library Engine
# IDENTITY: Root Ingestion Engine Bridge
################################################################################

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ingestion_engine import (
    parse_syllabus_markdown,
    save_syllabus_to_db,
    get_global_units,
    delete_unit,
    update_unit,
    clone_unit_to_user
)

__all__ = [
    "parse_syllabus_markdown",
    "save_syllabus_to_db",
    "get_global_units",
    "delete_unit",
    "update_unit",
    "clone_unit_to_user"
]