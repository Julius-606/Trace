################################################################################
# FILE: backend/app/core/scheduler.py
# VERSION: 1.0.0 | SYSTEM: Trace Rich Library Engine
# IDENTITY: Background Job Scheduler & Periodic Task Orchestrator
################################################################################

import asyncio
import logging
import threading
from typing import Optional
from app.workers.cron_jobs import (
    run_diagram_enrichment_job,
    run_multi_perspective_job,
    run_quality_audit_job
)

logger = logging.getLogger("Trace-Scheduler")


class ContentJobScheduler:
    """
    Periodic job scheduler supporting APScheduler with automatic fallback
    to an asynchronous event-loop worker thread.
    """

    def __init__(self):
        self.is_running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Starts background periodic execution of enrichment and audit crons."""
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()

        # Try APScheduler if installed
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            scheduler = BackgroundScheduler()
            scheduler.add_job(run_diagram_enrichment_job, "interval", hours=4, id="diagram_enrichment")
            scheduler.add_job(run_multi_perspective_job, "interval", hours=6, id="multi_perspective")
            scheduler.add_job(run_quality_audit_job, "interval", hours=8, id="quality_audit")
            scheduler.start()
            logger.info("Trace Rich Library Scheduler active via APScheduler.")
            return
        except ImportError:
            logger.info("APScheduler not installed. Using native asynchronous daemon thread loop.")

        # Fallback to daemon worker loop
        def _worker_loop():
            # Initial run after 15 seconds warm-up
            time_wait = 15
            if self._stop_event.wait(timeout=time_wait):
                return

            try:
                run_diagram_enrichment_job()
                run_multi_perspective_job()
                run_quality_audit_job()
            except Exception as e:
                logger.warning(f"Initial cron run exception: {e}")

            # Recurring loop: every 2 hours
            interval_sec = 2 * 3600
            while not self._stop_event.is_set():
                if self._stop_event.wait(timeout=interval_sec):
                    break
                try:
                    run_diagram_enrichment_job()
                    run_multi_perspective_job()
                    run_quality_audit_job()
                except Exception as exc:
                    logger.error(f"Error in scheduler worker loop: {exc}")

        self._thread = threading.Thread(target=_worker_loop, daemon=True, name="TraceSchedulerThread")
        self._thread.start()
        logger.info("Trace Rich Library Scheduler daemon thread started.")

    def stop(self):
        """Stops the scheduler loop."""
        self.is_running = False
        self._stop_event.set()
        logger.info("Trace Rich Library Scheduler stopped.")


scheduler = ContentJobScheduler()
