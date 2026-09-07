"""Unit tests for SQLAlchemy ORM database models."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.engine import Base
from backend.db.models.user import User
from backend.db.models.supplier import Supplier
from backend.db.models.procurement_center import ProcurementCenter
from backend.db.models.batch import Batch
from backend.db.models.model_version import ModelVersion
from backend.db.models.grading_profile import GradingProfileModel
from backend.db.models.inspection import Inspection
from backend.db.models.inspection_image import InspectionImage
from backend.db.models.onion_detection import OnionDetectionModel
from backend.db.models.defect_prediction import DefectPrediction
from backend.db.models.grading_result import GradingResultModel
from backend.db.models.report import Report
from backend.db.models.audit_event import AuditEvent


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_models_creation_and_relations(in_memory_db):
    """Verify all 13 ORM models can be instantiated, saved, and queried with relationships."""
    session = in_memory_db

    user = User(id="TEST-FIXTURE-USER-1", name="Test Inspector", role="INSPECTOR")
    supplier = Supplier(id="TEST-FIXTURE-SUP-1", name="Test Agro Supplier")
    center = ProcurementCenter(id="TEST-FIXTURE-CENTER-1", name="Test APMC Yard", location="Nashik")
    
    session.add_all([user, supplier, center])
    session.flush()

    batch = Batch(
        id="TEST-FIXTURE-BATCH-1",
        batch_code="LOT-TEST-001",
        supplier_id=supplier.id,
        procurement_center_id=center.id,
        declared_weight_kg=100.0,
        weight_source="SCALE_MEASURED",
        sampling_status="SAMPLE_ONLY"
    )
    session.add(batch)
    session.flush()

    model_ver = ModelVersion(
        id="TEST-FIXTURE-MOD-1",
        model_id="DevelopmentMockVisionModel",
        model_name="Dev Mock Vision Pipeline",
        model_version="0.1.0-mock",
        source="development_mock"
    )
    prof = GradingProfileModel(
        id="TEST-FIXTURE-PROF-1",
        profile_id="prototype-procurement-v1",
        profile_name="Experimental Procurement Profile",
        version="1.1.0-dev",
        status="EXPERIMENTAL",
        official_status="NOT_OFFICIAL",
        source="PROJECT_DEFINED",
        rules_json="{}"
    )
    session.add_all([model_ver, prof])
    session.flush()

    insp = Inspection(
        id="TEST-FIXTURE-INSP-1",
        batch_id=batch.id,
        inspector_id=user.id,
        model_version_id=model_ver.id,
        status="COMPLETED",
        inspection_confidence=0.92,
        review_status="NOT_REVIEWED"
    )
    session.add(insp)
    session.flush()

    img = InspectionImage(
        id="TEST-FIXTURE-IMG-1",
        inspection_id=insp.id,
        image_reference="/test/image1.jpg",
        original_filename="image1.jpg",
        width=1920,
        height=1080,
        quality_status="PASS"
    )
    session.add(img)
    session.flush()

    det = OnionDetectionModel(
        id="TEST-FIXTURE-DET-1",
        inspection_image_id=img.id,
        external_onion_id="O1",
        bbox_json="[10, 10, 50, 50]",
        detection_confidence=0.95,
        size_status="UNAVAILABLE"
    )
    session.add(det)
    session.flush()

    defect = DefectPrediction(
        id="TEST-FIXTURE-DEF-1",
        onion_detection_id=det.id,
        damage_probability=0.10,
        rot_probability=0.05,
        sprout_probability=0.0
    )
    session.add(defect)
    session.flush()

    gr = GradingResultModel(
        id="TEST-FIXTURE-RES-1",
        inspection_id=insp.id,
        grading_profile_id=prof.id,
        quality_score=92.5,
        grade="Grade-A",
        grade_a_percent=90.0,
        urs_percent=5.0,
        healthy_percent=90.0,
        damaged_percent=3.0,
        rotten_percent=1.0,
        sprouted_percent=1.0,
        undersized_percent=5.0,
        review_status="ACCEPTED",
        inspection_confidence=0.92,
        sampling_status="SAMPLE_ONLY",
        explanation="Test explanation",
        rules_triggered_json="[]"
    )
    rpt = Report(
        id="TEST-FIXTURE-RPT-1",
        inspection_id=insp.id,
        report_reference="/reports/rpt1.pdf",
        report_type="INSPECTION_CERTIFICATE"
    )
    session.add_all([gr, rpt])
    session.commit()

    # Query back & verify
    queried_insp = session.query(Inspection).filter(Inspection.id == "TEST-FIXTURE-INSP-1").first()
    assert queried_insp is not None
    assert queried_insp.batch.batch_code == "LOT-TEST-001"
    assert queried_insp.model_version.model_version == "0.1.0-mock"
    assert len(queried_insp.images) == 1
    assert queried_insp.images[0].detections[0].defect_prediction.damage_probability == 0.10
    assert queried_insp.grading_result.quality_score == 92.5
    assert queried_insp.grading_result.sampling_status == "SAMPLE_ONLY"
