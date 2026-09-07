"""Database initialization and seeding module."""

import json
from datetime import datetime, timezone
from backend.db.engine import engine, Base, SessionLocal
from backend.db.models.user import User
from backend.db.models.procurement_center import ProcurementCenter
from backend.db.models.model_version import ModelVersion
from backend.db.models.grading_profile import GradingProfileModel
from backend.grading.profiles import list_grading_profiles


def init_database() -> None:
    """Creates all database tables and seeds default model versions and grading profiles."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Default Inspector User
        if not db.query(User).filter(User.id == "USR-1001").first():
            db.add(User(
                id="USR-1001",
                name="APMC Duty Inspector",
                role="INSPECTOR",
                is_active=True
            ))

        # 2. Seed Default Procurement Center
        if not db.query(ProcurementCenter).filter(ProcurementCenter.id == "APMC-NASHIK-CENTER-04").first():
            db.add(ProcurementCenter(
                id="APMC-NASHIK-CENTER-04",
                name="APMC Nashik Main Procurement Yard",
                location="Nashik, Maharashtra",
                is_active=True
            ))

        # 3. Seed Default Model Version
        if not db.query(ModelVersion).filter(ModelVersion.id == "MOD-0.1.0-MOCK").first():
            db.add(ModelVersion(
                id="MOD-0.1.0-MOCK",
                model_id="DevelopmentMockVisionModel",
                model_name="Development Mock Vision Pipeline",
                model_version="0.1.0-mock",
                source="development_mock",
                framework="Synthetic",
                weights_reference=None,
                dataset_version=None,
                metrics_reference="Synthetic pipeline mechanics test double",
                is_active=True
            ))

        # 4. Seed Experimental Grading Profiles
        for prof in list_grading_profiles():
            if not db.query(GradingProfileModel).filter(GradingProfileModel.id == prof.profile_id).first():
                db.add(GradingProfileModel(
                    id=prof.profile_id,
                    profile_id=prof.profile_id,
                    profile_name=prof.profile_name,
                    version=prof.version,
                    status=prof.status,
                    official_status=prof.official_status,
                    source=prof.source,
                    source_reference=prof.source_reference,
                    disclaimer=prof.disclaimer,
                    rules_json=json.dumps(prof.rules),
                    is_active=True
                ))

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
