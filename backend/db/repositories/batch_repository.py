"""Batch repository for batch persistence."""

from typing import Optional, List
from sqlalchemy.orm import Session
from backend.db.models.batch import Batch


class BatchRepository:
    """Data access repository for procurement batches."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, batch_id: str) -> Optional[Batch]:
        return self.db.query(Batch).filter(Batch.id == batch_id).first()

    def get_by_code(self, batch_code: str) -> Optional[Batch]:
        return self.db.query(Batch).filter(Batch.batch_code == batch_code).first()

    def create(
        self,
        batch_id: str,
        batch_code: str,
        supplier_id: Optional[str] = None,
        procurement_center_id: Optional[str] = None,
        declared_weight_kg: Optional[float] = None,
        weight_source: str = "UNAVAILABLE",
        sampling_status: str = "SAMPLE_ONLY"
    ) -> Batch:
        batch = Batch(
            id=batch_id,
            batch_code=batch_code,
            supplier_id=supplier_id,
            procurement_center_id=procurement_center_id,
            declared_weight_kg=declared_weight_kg,
            weight_source=weight_source,
            sampling_status=sampling_status
        )
        self.db.add(batch)
        self.db.flush()
        return batch

    def get_or_create(
        self,
        batch_id: str,
        supplier_id: Optional[str] = None,
        procurement_center_id: Optional[str] = None,
        declared_weight_kg: Optional[float] = None,
        weight_source: str = "UNAVAILABLE"
    ) -> Batch:
        existing = self.get_by_id(batch_id)
        if existing:
            return existing
        return self.create(
            batch_id=batch_id,
            batch_code=f"LOT-{batch_id}",
            supplier_id=supplier_id,
            procurement_center_id=procurement_center_id,
            declared_weight_kg=declared_weight_kg,
            weight_source=weight_source
        )

    def list_all(self, limit: int = 100) -> List[Batch]:
        return self.db.query(Batch).order_by(Batch.created_at.desc()).limit(limit).all()
