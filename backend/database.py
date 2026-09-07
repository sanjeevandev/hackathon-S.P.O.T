"""Legacy Database API Compatibility Bridge.

Delegates commands to backend.db ORM layer while maintaining backward compatibility with legacy endpoints.
"""

from typing import Dict, Any, List, Optional
from backend.db.engine import SessionLocal
from backend.db.init_db import init_database
from backend.db.repositories.inspection_repository import InspectionRepository
from backend.db.repositories.batch_repository import BatchRepository
from backend.db.models.inspection import Inspection


def init_db():
    """Initialize ORM database schema and seed profiles/models."""
    init_database()


def log_grading_session(data: Dict[str, Any]) -> str:
    """Legacy helper function mapping data dicts into normalized inspection records."""
    init_database()
    db = SessionLocal()
    try:
        batch_repo = BatchRepository(db)
        batch_id = data.get("batch_id", "BATCH-UNKNOWN")
        batch = batch_repo.get_or_create(
            batch_id=batch_id,
            procurement_center_id=data.get("center_id"),
            declared_weight_kg=data.get("total_weight_kg"),
            weight_source="USER_SUPPLIED" if data.get("total_weight_kg") else "UNAVAILABLE"
        )
        db.commit()
        return batch.id
    finally:
        db.close()


def update_session_status(batch_id: str, status: str = "DISPUTED") -> bool:
    """Updates inspection review status in database."""
    init_database()
    db = SessionLocal()
    try:
        inspection = db.query(Inspection).filter(Inspection.batch_id == batch_id).first()
        if inspection:
            inspection.review_status = status
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_all_grading_sessions() -> List[Dict[str, Any]]:
    """Retrieves all inspection records in legacy dictionary format."""
    init_database()
    db = SessionLocal()
    try:
        inspections = db.query(Inspection).order_by(Inspection.created_at.desc()).all()
        results = []
        for insp in inspections:
            gr = insp.grading_result
            results.append({
                "batch_id": insp.batch_id,
                "center_id": insp.batch.procurement_center_id if insp.batch else "UNKNOWN",
                "timestamp": insp.created_at.isoformat() if insp.created_at else "",
                "status": insp.review_status,
                "overall_grade": gr.grade if gr else "Grade-C",
                "confidence_score": insp.inspection_confidence,
                "quality_score": gr.quality_score if gr else 0.0,
                "grade_a_percentage": gr.grade_a_percent if gr else 0.0,
                "grade_urs_percentage": gr.urs_percent if gr else 0.0,
                "rejected_percentage": round(100.0 - ((gr.grade_a_percent if gr else 0) + (gr.urs_percent if gr else 0)), 1),
            })
        return results
    finally:
        db.close()


def get_session_by_batch_id(batch_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a specific inspection record by batch ID."""
    init_database()
    db = SessionLocal()
    try:
        insp = db.query(Inspection).filter(Inspection.batch_id == batch_id).first()
        if not insp:
            return None
        gr = insp.grading_result
        return {
            "batch_id": insp.batch_id,
            "center_id": insp.batch.procurement_center_id if insp.batch else "UNKNOWN",
            "timestamp": insp.created_at.isoformat() if insp.created_at else "",
            "status": insp.review_status,
            "overall_grade": gr.grade if gr else "Grade-C",
            "confidence_score": insp.inspection_confidence,
            "quality_score": gr.quality_score if gr else 0.0,
            "grade_a_percentage": gr.grade_a_percent if gr else 0.0,
            "grade_urs_percentage": gr.urs_percent if gr else 0.0,
        }
    finally:
        db.close()
