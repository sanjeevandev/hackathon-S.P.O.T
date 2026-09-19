import uuid
from typing import Dict, Any, List, Optional
from backend.db.engine import SessionLocal
from backend.db.init_db import init_database
from backend.db.repositories.inspection_repository import InspectionRepository
from backend.db.repositories.batch_repository import BatchRepository
from backend.db.models.inspection import Inspection
from backend.db.models.grading_result import GradingResultModel


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
        
        # Check if inspection exists or create one
        insp = db.query(Inspection).filter(Inspection.batch_id == batch_id).first()
        if not insp:
            insp_id = f"INSP-{uuid.uuid4().hex[:8].upper()}"
            insp = Inspection(
                id=insp_id,
                batch_id=batch.id,
                status="COMPLETED",
                inspection_confidence=float(data.get("confidence_score", 0.0)),
                review_status="NOT_REVIEWED",
                sha256_hash=data.get("sha256_hash")
            )
            db.add(insp)
            db.flush()
            
            # Create grading result model
            gr_id = f"GR-{uuid.uuid4().hex[:8].upper()}"
            gr = GradingResultModel(
                id=gr_id,
                inspection_id=insp.id,
                grading_profile_id="AGMARK_COMMERCIAL_V1",
                quality_score=float(data.get("grade_a_percentage", 80.0)),
                grade=data.get("overall_grade", "Grade-A"),
                grade_a_percent=float(data.get("grade_a_percentage", 0.0)),
                urs_percent=float(data.get("grade_urs_percentage", 0.0)),
                healthy_percent=float(data.get("grade_a_percentage", 0.0)),
                damaged_percent=float(data.get("damaged_count", 0)),
                rotten_percent=float(data.get("rotten_count", 0)),
                sprouted_percent=float(data.get("sprouted_count", 0)),
                undersized_percent=float(data.get("undersized_count", 0)),
                review_status="ACCEPTED",
                inspection_confidence=float(data.get("confidence_score", 0.0)),
                explanation=data.get("farmer_recommendation", "Standard grading evaluation"),
                rules_triggered_json="[]"
            )
            db.add(gr)
        else:
            if data.get("sha256_hash"):
                insp.sha256_hash = data.get("sha256_hash")
            if data.get("confidence_score"):
                insp.inspection_confidence = float(data.get("confidence_score"))
                
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
                "overall_grade": gr.grade if gr else "Grade-A",
                "confidence_score": insp.inspection_confidence,
                "quality_score": gr.quality_score if gr else 0.0,
                "grade_a_percentage": gr.grade_a_percent if gr else 0.0,
                "grade_urs_percentage": gr.urs_percent if gr else 0.0,
                "rejected_percentage": round(100.0 - ((gr.grade_a_percent if gr else 0) + (gr.urs_percent if gr else 0)), 1),
                "sha256_hash": insp.sha256_hash,
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
            "overall_grade": gr.grade if gr else "Grade-A",
            "confidence_score": insp.inspection_confidence,
            "quality_score": gr.quality_score if gr else 0.0,
            "grade_a_percentage": gr.grade_a_percent if gr else 0.0,
            "grade_urs_percentage": gr.urs_percent if gr else 0.0,
            "sha256_hash": insp.sha256_hash,
        }
    finally:
        db.close()
