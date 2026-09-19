"""Inspection repository for transactional persistence of inspection runs."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.db.models.inspection import Inspection
from backend.db.models.inspection_image import InspectionImage
from backend.db.models.onion_detection import OnionDetectionModel
from backend.db.models.defect_prediction import DefectPrediction
from backend.db.models.grading_result import GradingResultModel
from backend.db.models.model_version import ModelVersion
from backend.db.models.grading_profile import GradingProfileModel
from backend.db.repositories.batch_repository import BatchRepository
from backend.db.repositories.audit_repository import AuditRepository
from backend.pipeline.schemas import PipelineResult
from backend.grading.schemas import GradingResult


class InspectionRepository:
    """Data access repository for inspection orchestration and atomic transaction persistence."""

    def __init__(self, db: Session):
        self.db = db
        self.batch_repo = BatchRepository(db)
        self.audit_repo = AuditRepository(db)

    def get_by_id(self, inspection_id: str) -> Optional[Inspection]:
        return self.db.query(Inspection).filter(Inspection.id == inspection_id).first()

    def list_inspections(
        self,
        batch_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Inspection]:
        query = self.db.query(Inspection)
        if batch_id:
            query = query.filter(Inspection.batch_id == batch_id)
        if status:
            query = query.filter(Inspection.status == status)
        return query.order_by(Inspection.created_at.desc()).limit(limit).all()

    def save_inspection_result(
        self,
        batch_id: str,
        pipeline_result: PipelineResult,
        grading_result: Optional[GradingResult] = None,
        center_id: Optional[str] = None,
        declared_weight_kg: Optional[float] = None,
        weight_source: str = "UNAVAILABLE",
        actor_id: str = "SYSTEM"
    ) -> Inspection:
        """Saves a complete inspection run transactionally.

        Atomically persists Batch, Inspection, Image, Detections, Defect Predictions, Grading Result, and Audit Event.
        Rolls back cleanly on any transaction failure.
        """
        try:
            # 1. Ensure Batch exists
            batch = self.batch_repo.get_or_create(
                batch_id=batch_id,
                procurement_center_id=center_id,
                declared_weight_kg=declared_weight_kg,
                weight_source=weight_source
            )

            # 2. Get active ModelVersion & GradingProfile reference
            model_ver = self.db.query(ModelVersion).filter(ModelVersion.source == pipeline_result.vision_result.source).first() if pipeline_result.vision_result else None
            model_ver_id = model_ver.id if model_ver else "MOD-0.1.0-MOCK"

            insp_id = f"INSP-{pipeline_result.request_id}" if pipeline_result.request_id else f"INSP-{uuid.uuid4().hex[:8].upper()}"

            # 3. Create Inspection record
            inspection = Inspection(
                id=insp_id,
                batch_id=batch.id,
                inspector_id=actor_id if actor_id != "SYSTEM" else None,
                model_version_id=model_ver_id,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                status="COMPLETED" if pipeline_result.status == "SUCCESS" else "FAILED",
                inspection_confidence=pipeline_result.vision_result.overall_confidence if pipeline_result.vision_result else 0.0,
                review_status=grading_result.review_status if grading_result else "NOT_REVIEWED",
                review_reason=" ".join(grading_result.review_reason) if grading_result and grading_result.review_reason else None
            )
            self.db.add(inspection)
            self.db.flush()

            # 4. Save InspectionImage
            metrics = pipeline_result.quality_gate.metrics if pipeline_result.quality_gate else None
            img_id = f"IMG-{uuid.uuid4().hex[:8].upper()}"
            img_record = InspectionImage(
                id=img_id,
                inspection_id=inspection.id,
                image_reference=f"/storage/images/{inspection.id}.jpg",
                original_filename="sample_capture.jpg",
                mime_type="image/jpeg",
                width=metrics.width if metrics else 1920,
                height=metrics.height if metrics else 1080,
                quality_status=pipeline_result.quality_gate.status if pipeline_result.quality_gate else "PASS",
                quality_metrics_json=json.dumps(metrics.model_dump()) if metrics else None
            )
            self.db.add(img_record)
            self.db.flush()

            # 5. Save Detections & Defect Predictions if vision result exists
            if pipeline_result.vision_result and pipeline_result.vision_result.onions:
                for onion in pipeline_result.vision_result.onions:
                    det_id = f"DET-{uuid.uuid4().hex[:8].upper()}"
                    size_mm = onion.size_estimate.estimated_diameter_mm if onion.size_estimate and onion.size_estimate.status == "AVAILABLE" else None
                    det_record = OnionDetectionModel(
                        id=det_id,
                        inspection_image_id=img_record.id,
                        external_onion_id=onion.onion_id,
                        bbox_json=json.dumps(onion.bbox),
                        detection_confidence=onion.detection_confidence,
                        size_status=onion.size_estimate.status if onion.size_estimate else "UNAVAILABLE",
                        estimated_diameter_mm=size_mm,
                        size_confidence=onion.size_estimate.confidence if onion.size_estimate else 0.0
                    )
                    self.db.add(det_record)
                    self.db.flush()

                    # Save Defect Prediction
                    dp = onion.defect_probabilities
                    def_record = DefectPrediction(
                        id=f"DEF-{uuid.uuid4().hex[:8].upper()}",
                        onion_detection_id=det_record.id,
                        damage_probability=dp.damage,
                        rot_probability=dp.rot,
                        sprout_probability=dp.sprouting
                    )
                    self.db.add(def_record)

            # 6. Save GradingResult if present
            if grading_result:
                profile_record = self.db.query(GradingProfileModel).filter(GradingProfileModel.profile_id == grading_result.profile_id).first()
                profile_id_pk = profile_record.id if profile_record else "prototype-procurement-v1"

                res_record = GradingResultModel(
                    id=f"RES-{uuid.uuid4().hex[:8].upper()}",
                    inspection_id=inspection.id,
                    grading_profile_id=profile_id_pk,
                    quality_score=grading_result.quality_score,
                    grade=grading_result.final_prototype_grade,
                    grade_a_percent=grading_result.grade_a_percentage,
                    urs_percent=grading_result.grade_urs_percentage,
                    healthy_percent=grading_result.grade_a_percentage,
                    damaged_percent=0.0,
                    rotten_percent=0.0,
                    sprouted_percent=0.0,
                    undersized_percent=0.0,
                    review_status=grading_result.review_status,
                    review_reason_json=json.dumps(grading_result.review_reason) if grading_result.review_reason else None,
                    inspection_confidence=grading_result.inspection_confidence if hasattr(grading_result, "inspection_confidence") else 0.90,
                    sampling_status=grading_result.sampling_status,
                    explanation=grading_result.explanation,
                    rules_triggered_json=json.dumps(grading_result.rules_triggered)
                )
                self.db.add(res_record)

            # 7. Append-only Audit Trail event
            self.audit_repo.log_event(
                entity_type="INSPECTION",
                entity_id=inspection.id,
                event_type="INSPECTION_COMPLETED",
                actor_id=actor_id,
                payload={
                    "batch_id": batch_id,
                    "status": inspection.status,
                    "confidence": inspection.inspection_confidence,
                    "grade": grading_result.final_prototype_grade if grading_result else None
                }
            )

            self.db.commit()
            self.db.refresh(inspection)
            return inspection

        except Exception as e:
            self.db.rollback()
            raise e
