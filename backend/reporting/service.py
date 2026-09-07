"""Reporting service orchestrator connecting ORM persistence to canonical presentation contracts."""

import json
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from backend.db.models.inspection import Inspection
from backend.db.models.report import Report
from backend.db.repositories.inspection_repository import InspectionRepository
from backend.db.repositories.audit_repository import AuditRepository
from backend.contracts.schemas import (
    CanonicalInspectionResult,
    BatchStatistics,
    Coverage,
    OnionResult,
    EvidenceRegion,
    GradingPresentation,
    ModelInformation,
    GradingProfileInformation,
)
from backend.reporting.explanation_engine import ExplanationEngine
from backend.reporting.report_contract import InspectionReport


class ReportingService:
    """Service providing canonical result assembly, structured report generation, and audit logging."""

    @classmethod
    def get_canonical_result(cls, inspection_id: str, db: Session) -> CanonicalInspectionResult:
        repo = InspectionRepository(db)
        insp = repo.get_by_id(inspection_id)
        if not insp:
            raise ValueError(f"Inspection ID '{inspection_id}' not found in database")

        # 1. Image Quality Summary
        first_img = insp.images[0] if insp.images else None
        qg_metrics = json.loads(first_img.quality_metrics_json) if first_img and first_img.quality_metrics_json else {}
        qg_status = first_img.quality_status if first_img else "PASS"

        # 2. Extract Onions & Evidence Regions
        onions_list: List[OnionResult] = []
        healthy_c = damaged_c = rotten_c = sprouted_c = undersized_c = 0

        if first_img and first_img.detections:
            for det in first_img.detections:
                bbox = json.loads(det.bbox_json) if det.bbox_json else [0, 0, 0, 0]
                dp = det.defect_prediction

                dmg_prob = dp.damage_probability if dp else 0.0
                rot_prob = dp.rot_probability if dp else 0.0
                spr_prob = dp.sprout_probability if dp else 0.0

                # Determine individual onion status
                if rot_prob > 0.4:
                    f_status = "ROTTEN"
                    rotten_c += 1
                elif dmg_prob > 0.4:
                    f_status = "DAMAGED"
                    damaged_c += 1
                elif spr_prob > 0.4:
                    f_status = "SPROUTED"
                    sprouted_c += 1
                else:
                    f_status = "HEALTHY"
                    healthy_c += 1

                evidence_regs = []
                if rot_prob > 0.3:
                    evidence_regs.append(EvidenceRegion(defect_type="ROT", coordinates=[0, 0, 100, 100], confidence=rot_prob))
                if dmg_prob > 0.3:
                    evidence_regs.append(EvidenceRegion(defect_type="DAMAGE", coordinates=[0, 0, 100, 100], confidence=dmg_prob))
                if spr_prob > 0.3:
                    evidence_regs.append(EvidenceRegion(defect_type="SPROUTING", coordinates=[0, 0, 100, 100], confidence=spr_prob))

                onions_list.append(OnionResult(
                    onion_id=det.external_onion_id,
                    bounding_box=bbox,
                    mask_reference=det.mask_reference,
                    detection_confidence=det.detection_confidence,
                    defect_probabilities={"damage": dmg_prob, "rot": rot_prob, "sprouting": spr_prob},
                    size_estimate={"estimated_diameter_mm": det.estimated_diameter_mm, "status": det.size_status, "confidence": det.size_confidence},
                    evidence_regions=evidence_regs,
                    final_status=f_status
                ))

        total_analyzed = len(onions_list)
        total_visible = total_analyzed

        batch_stats = BatchStatistics(
            total_visible_onions=total_visible,
            total_analyzed_onions=total_analyzed,
            healthy_count=healthy_c,
            damaged_count=damaged_c,
            rotten_count=rotten_c,
            sprouted_count=sprouted_c,
            undersized_count=undersized_c,
            healthy_percentage=round((healthy_c / total_analyzed * 100.0), 1) if total_analyzed > 0 else 0.0,
            damaged_percentage=round((damaged_c / total_analyzed * 100.0), 1) if total_analyzed > 0 else 0.0,
            rotten_percentage=round((rotten_c / total_analyzed * 100.0), 1) if total_analyzed > 0 else 0.0,
            sprouted_percentage=round((sprouted_c / total_analyzed * 100.0), 1) if total_analyzed > 0 else 0.0,
            undersized_percentage=round((undersized_c / total_analyzed * 100.0), 1) if total_analyzed > 0 else 0.0,
        )

        coverage = Coverage(
            captured_sample_images_count=len(insp.images),
            total_visible_onions=total_visible,
            total_analyzed_onions=total_analyzed,
            sampling_status="SAMPLE_ONLY"
        )

        # Determine report-level inspection status
        if qg_status == "RETAKE_REQUIRED":
            overall_status = "RETAKE_REQUIRED"
        elif insp.status == "FAILED":
            overall_status = "FAILED"
        elif insp.review_status == "REVIEW_REQUIRED":
            overall_status = "REVIEW_REQUIRED"
        else:
            overall_status = "COMPLETE"

        # Map GradingPresentation (suppressing grade if RETAKE_REQUIRED or MODEL_UNAVAILABLE)
        gr = insp.grading_result
        if gr and overall_status not in ["RETAKE_REQUIRED", "MODEL_UNAVAILABLE", "FAILED"]:
            grading_pres = GradingPresentation(
                quality_score=gr.quality_score,
                prototype_grade=gr.grade,
                grade_a_percent=gr.grade_a_percent,
                urs_percent=gr.urs_percent,
                review_status=gr.review_status,
                review_reason=json.loads(gr.review_reason_json) if gr.review_reason_json else [],
                inspection_confidence=gr.inspection_confidence,
                grading_profile_id=gr.grading_profile_id,
                grading_profile_version=gr.grading_profile.version if gr.grading_profile else "1.1.0-dev"
            )
        else:
            grading_pres = None

        # Explanation Engine
        review_reasons_list = json.loads(gr.review_reason_json) if gr and gr.review_reason_json else []
        explanation = ExplanationEngine.generate(
            status=overall_status,
            batch_stats=batch_stats,
            grading=grading_pres,
            review_status=insp.review_status,
            review_reasons=review_reasons_list
        )

        # Model & Profile Information
        model_info = ModelInformation(
            model_id=insp.model_version.model_id if insp.model_version else "DevelopmentMockVisionModel",
            model_name=insp.model_version.model_name if insp.model_version else "Dev Mock Pipeline",
            model_version=insp.model_version.model_version if insp.model_version else "0.1.0-mock",
            source=insp.model_version.source if insp.model_version else "development_mock"
        )

        prof_record = gr.grading_profile if gr and gr.grading_profile else None
        profile_info = GradingProfileInformation(
            profile_id=prof_record.profile_id if prof_record else "prototype-procurement-v1",
            profile_name=prof_record.profile_name if prof_record else "Experimental Procurement Profile",
            version=prof_record.version if prof_record else "1.1.0-dev",
            status=prof_record.status if prof_record else "EXPERIMENTAL",
            official_status=prof_record.official_status if prof_record else "NOT_OFFICIAL",
            disclaimer=prof_record.disclaimer if prof_record else "Prototype grading profile. Not an official government certification or statutory grading standard."
        )

        # Report reference if exists
        existing_report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
        rpt_ref = existing_report.report_reference if existing_report else None

        return CanonicalInspectionResult(
            inspection_id=insp.id,
            batch_id=insp.batch_id,
            status=overall_status,
            sampling_status="SAMPLE_ONLY",
            image_quality={"quality_status": qg_status, "metrics": qg_metrics},
            coverage=coverage,
            onions=onions_list,
            batch_statistics=batch_stats,
            grading=grading_pres,
            explanation=explanation,
            confidence=insp.inspection_confidence,
            review={"review_status": insp.review_status, "review_reason": insp.review_reason or ""},
            model=model_info,
            grading_profile=profile_info,
            report_reference=rpt_ref
        )

    @classmethod
    def get_or_create_report(cls, inspection_id: str, db: Session) -> InspectionReport:
        canonical_result = cls.get_canonical_result(inspection_id, db)
        existing_report = db.query(Report).filter(Report.inspection_id == inspection_id).first()

        if existing_report:
            version = int(existing_report.report_type.split("_V")[-1]) if "_V" in existing_report.report_type else 1
            return InspectionReport.from_canonical_result(
                report_id=existing_report.id,
                result=canonical_result,
                report_version=version
            )

        return cls.generate_and_persist_report(inspection_id, db, force_increment=False)

    @classmethod
    def generate_and_persist_report(cls, inspection_id: str, db: Session, force_increment: bool = True) -> InspectionReport:
        canonical_result = cls.get_canonical_result(inspection_id, db)

        existing_report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
        if existing_report:
            current_ver = int(existing_report.report_type.split("_V")[-1]) if "_V" in existing_report.report_type else 1
            version = current_ver + 1 if force_increment else current_ver
            report_id = existing_report.id
            existing_report.report_type = f"INSPECTION_CERTIFICATE_V{version}"
        else:
            version = 1
            report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"
            new_report_record = Report(
                id=report_id,
                inspection_id=inspection_id,
                report_reference=f"/reports/{report_id}.json",
                report_type="INSPECTION_CERTIFICATE_V1"
            )
            db.add(new_report_record)

        report_contract = InspectionReport.from_canonical_result(
            report_id=report_id,
            result=canonical_result,
            report_version=version
        )

        # Append audit event
        audit_repo = AuditRepository(db)
        audit_repo.log_event(
            entity_type="REPORT",
            entity_id=report_id,
            event_type="REPORT_GENERATED" if version == 1 else "REPORT_REGENERATED",
            actor_id="SYSTEM",
            payload={
                "inspection_id": inspection_id,
                "batch_id": canonical_result.batch_id,
                "report_version": version
            }
        )

        db.commit()
        return report_contract
