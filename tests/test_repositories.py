"""Unit tests for database repositories."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.engine import Base
from backend.db.repositories.batch_repository import BatchRepository
from backend.db.repositories.inspection_repository import InspectionRepository
from backend.db.models.model_version import ModelVersion
from backend.db.models.grading_profile import GradingProfileModel
from backend.pipeline.schemas import PipelineResult, QualityGateResult, QualityGateMetrics
from backend.ai.schemas import VisionResult, OnionDetection, DefectProbabilities
from backend.grading.schemas import GradingResult, LotPercentages, WeightDistribution


@pytest.fixture
def repo_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed mock model version and default profile
    session.add(ModelVersion(
        id="MOD-0.1.0-MOCK", model_id="DevelopmentMockVisionModel",
        model_name="Dev Mock", model_version="0.1.0-mock", source="development_mock"
    ))
    session.add(GradingProfileModel(
        id="prototype-procurement-v1", profile_id="prototype-procurement-v1",
        profile_name="Prototype Profile", version="1.1.0-dev", rules_json="{}"
    ))
    session.commit()

    yield session
    session.close()


def test_batch_repository_get_or_create(repo_db):
    """Verify BatchRepository get_or_create logic."""
    batch_repo = BatchRepository(repo_db)
    b1 = batch_repo.get_or_create("TEST-BATCH-101", declared_weight_kg=50.0, weight_source="SCALE_MEASURED")
    assert b1.id == "TEST-BATCH-101"
    assert b1.declared_weight_kg == 50.0

    b2 = batch_repo.get_or_create("TEST-BATCH-101")
    assert b2.id == "TEST-BATCH-101"


def test_inspection_repository_save_and_transaction_safety(repo_db):
    """Verify InspectionRepository atomically saves inspection, images, detections, defect predictions, and grading result."""
    insp_repo = InspectionRepository(repo_db)

    metrics = QualityGateMetrics(blur_score=150.0, brightness=120.0, contrast=50.0, width=1920, height=1080)
    qg_res = QualityGateResult(status="PASS", passed=True, reasons=[], metrics=metrics, recommendations=[])

    onions = [
        OnionDetection(
            onion_id="O1", bbox=[10, 10, 50, 50], detection_confidence=0.95,
            defect_probabilities=DefectProbabilities(damage=0.0, rot=0.0, sprouting=0.0)
        )
    ]
    vr = VisionResult(
        request_id="REQ-1", model_name="TestModel", model_version="1.0",
        source="development_mock", processing_time_ms=10.0, onions=onions, overall_confidence=0.95, status="SUCCESS"
    )
    from backend.pipeline.schemas import PipelineTimings
    timings = PipelineTimings(quality_gate_time_ms=5.0, vision_time_ms=10.0, total_pipeline_time_ms=15.0)
    pipeline_res = PipelineResult(status="SUCCESS", request_id="REQ-TEST-1", quality_gate=qg_res, vision_result=vr, timings=timings)

    pct = LotPercentages(healthy_pct=100.0, damaged_pct=0.0, rotten_pct=0.0, sprouted_pct=0.0, undersized_pct=0.0)
    w_dist = WeightDistribution(is_weight_estimated=False, weight_source="UNAVAILABLE", grade_a_weight_percentage=100.0, grade_urs_weight_percentage=0.0, rejected_weight_percentage=0.0)
    grading_res = GradingResult(
        batch_id="TEST-BATCH-202", profile_id="prototype-procurement-v1", profile_version="1.1.0-dev",
        grade_a_percentage=100.0, grade_urs_percentage=0.0, rejected_percentage=0.0,
        quality_score=100.0, final_prototype_grade="Grade-A", review_status="ACCEPTED",
        explanation="Pass test", rules_triggered=[]
    )

    insp = insp_repo.save_inspection_result(
        batch_id="TEST-BATCH-202",
        pipeline_result=pipeline_res,
        grading_result=grading_res
    )

    assert insp.id == "INSP-REQ-TEST-1"
    assert insp.batch_id == "TEST-BATCH-202"
    assert len(insp.images) == 1
    assert len(insp.images[0].detections) == 1
    assert insp.grading_result.grade == "Grade-A"
    assert insp.grading_result.sampling_status == "SAMPLE_ONLY"
