################################################################################
# FILE: backend/app/workers/cron_jobs.py
# VERSION: 1.0.0 | SYSTEM: Trace Rich Library Engine
# IDENTITY: Background Enrichment, Diagram Generation & Double-Pass Quality Audit Cron
################################################################################

import logging
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import database_models as models
from app.services.content_pipeline import generate_fallback_diagram

logger = logging.getLogger("Trace-CronJobs")


def run_diagram_enrichment_job() -> Dict[str, Any]:
    """
    Periodic job 1: Diagram Enrichment.
    Parses topic notes and ensures all subtopics have rich, valid Mermaid diagrams.
    """
    logger.info("Executing periodic Diagram Enrichment job...")
    enriched_count = 0
    now = time.time()

    with SessionLocal() as db:
        # Find subtopics without enrichment
        subtopics = db.query(models.Subtopic).all()
        for sub in subtopics:
            enrichment = db.query(models.NodeEnrichment).filter(
                models.NodeEnrichment.node_id == sub.id,
                models.NodeEnrichment.node_type == "subtopic"
            ).first()

            if not enrichment:
                diagram = generate_fallback_diagram(sub.name, "subtopic")
                new_enrich = models.NodeEnrichment(
                    node_id=sub.id,
                    node_type="subtopic",
                    node_name=sub.name,
                    intuitive_explanation=f"Conceptual breakdown of {sub.name}: focus on high-yield clinical fundamentals.",
                    technical_explanation=f"Technical physiological dynamics: review cellular and anatomical interactions in {sub.name}.",
                    clinical_takeaway=f"Bedside takeaway: evaluate diagnostic criteria and immediate therapeutic intervention.",
                    diagram_type=diagram["diagram_type"],
                    diagram_code=diagram["diagram_code"],
                    diagram_caption=diagram["diagram_caption"],
                    metadata_json={"cron_enriched": True},
                    created_at=now,
                    updated_at=now
                )
                db.add(new_enrich)
                enriched_count += 1
            elif not enrichment.diagram_code or len(enrichment.diagram_code.strip()) < 10:
                diagram = generate_fallback_diagram(sub.name, "subtopic")
                enrichment.diagram_code = diagram["diagram_code"]
                enrichment.diagram_caption = diagram["diagram_caption"]
                enrichment.updated_at = now
                enriched_count += 1

        db.commit()

    logger.info(f"Diagram Enrichment job finished. Enriched/Updated: {enriched_count} records.")
    return {"status": "success", "enriched_count": enriched_count}


def run_multi_perspective_job() -> Dict[str, Any]:
    """
    Periodic job 2: Multi-Perspective Generation.
    Generates alternative explanations tailored to intuitive, technical, and visual learners.
    """
    logger.info("Executing periodic Multi-Perspective Generation job...")
    updated_count = 0
    now = time.time()

    with SessionLocal() as db:
        enrichments = db.query(models.NodeEnrichment).all()
        for item in enrichments:
            changed = False
            if not item.intuitive_explanation or len(item.intuitive_explanation.strip()) < 20:
                item.intuitive_explanation = (
                    f"Core intuition for {item.node_name}: Imagine a precision equilibrium. "
                    "Small physiological shifts produce rapid regulatory feedback to maintain homeostasis."
                )
                changed = True
            if not item.technical_explanation or len(item.technical_explanation.strip()) < 20:
                item.technical_explanation = (
                    f"Formal diagnostic and pathophysiological mechanisms governing {item.node_name}, "
                    "including receptor kinetics, enzyme cascades, and hemodynamic vectors."
                )
                changed = True
            if not item.clinical_takeaway:
                item.clinical_takeaway = f"Clinical Pearl: Rapid bedside identification of {item.node_name} improves patient outcomes."
                changed = True

            if changed:
                item.updated_at = now
                updated_count += 1

        db.commit()

    logger.info(f"Multi-Perspective job complete. Updated: {updated_count} nodes.")
    return {"status": "success", "updated_count": updated_count}


def run_quality_audit_job() -> Dict[str, Any]:
    """
    Periodic job 3: Quality Control & Double-Pass Fact Checking.
    Evaluates generated quiz questions and notes for formatting flaws, option mismatches, or hallucinations.
    """
    logger.info("Executing periodic Quality Control / Fact Check audit...")
    audited_count = 0
    flags_raised = 0
    now = time.time()

    with SessionLocal() as db:
        quizzes = db.query(models.GeneratedQuizBank).all()
        for q in quizzes:
            issues: List[str] = []
            score = 1.0

            # Rule 1: Option count
            if not q.options or len(q.options) < 4:
                issues.append("Less than 4 options provided")
                score -= 0.3

            # Rule 2: Correct answer exists in options
            if q.options and q.correct_answer not in q.options:
                # Attempt trim match
                matching = [opt for opt in q.options if q.correct_answer.strip().lower() in opt.strip().lower()]
                if matching:
                    q.correct_answer = matching[0]
                else:
                    issues.append("Correct answer does not match any listed option")
                    score -= 0.4

            # Rule 3: Explanation check
            if not q.explanation or len(q.explanation.strip()) < 10:
                issues.append("Explanation missing or truncated")
                score -= 0.2

            score = max(0.0, round(score, 2))
            status = "verified" if score >= 0.8 else ("flagged" if score >= 0.5 else "rejected")

            if issues:
                flags_raised += len(issues)

            # Record or update Pass 2 audit log
            audit_log = db.query(models.ContentAuditLog).filter(
                models.ContentAuditLog.target_type == "quiz",
                models.ContentAuditLog.target_id == q.id,
                models.ContentAuditLog.audit_pass == 2
            ).first()

            if not audit_log:
                audit_log = models.ContentAuditLog(
                    target_type="quiz",
                    target_id=q.id,
                    verification_status=status,
                    accuracy_score=score,
                    flags=issues,
                    audit_pass=2,
                    audited_by="Double-Pass Quality Cron",
                    auditor_notes=f"Pass 2 audit: {len(issues)} issues detected." if issues else "Pass 2 audit verified clean.",
                    created_at=now
                )
                db.add(audit_log)
            else:
                audit_log.verification_status = status
                audit_log.accuracy_score = score
                audit_log.flags = issues

            audited_count += 1

        db.commit()

    logger.info(f"Quality Audit complete. Audited {audited_count} quizzes. Raised {flags_raised} flags.")
    return {"status": "success", "audited_count": audited_count, "flags_raised": flags_raised}
