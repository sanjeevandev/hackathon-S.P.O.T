import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.ai.annotation.workstation import AnnotationWorkstationManager

router = APIRouter(prefix="/api/annotation", tags=["Internal Annotation Workstation"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PILOT_IMAGES_DIR = PROJECT_ROOT / "artifacts" / "ml" / "defect_annotations" / "pilot_100" / "images"

manager = AnnotationWorkstationManager()


class SaveAnnotationRequest(BaseModel):
    annotation_id: str
    image_id: str
    annotator_id: str
    semantic_attributes: Dict[str, Any]
    multi_label_defects: Dict[str, bool]
    size_assessment: Dict[str, Any]
    evidence_regions: List[Dict[str, Any]] = Field(default_factory=list)
    annotation_confidence: str = "HIGH"
    uncertainty_reason: Optional[str] = None
    notes: Optional[str] = None


@router.get("/queue")
async def get_annotation_queue(annotator_id: str = Query(default="HUMAN_ANNOTATOR_01")):
    """Returns annotation queue for specified annotator."""
    queue = manager.get_queue(annotator_id)
    return {
        "annotator_id": annotator_id,
        "total_count": len(queue),
        "queue": queue
    }


@router.get("/progress")
async def get_annotation_progress(annotator_id: str = Query(default="HUMAN_ANNOTATOR_01")):
    """Returns completion progress for specified annotator."""
    progress = manager.get_progress(annotator_id)
    return progress


@router.get("/status")
async def get_phase_13_status():
    """Returns aggregate Phase 13 human annotation statistics."""
    status = manager.get_phase_13_status()
    return status


@router.get("/pilot_image/{filename}")
async def get_pilot_image(filename: str):
    """Serves raw pilot image file directly from pilot_100/images/."""
    image_path = PILOT_IMAGES_DIR / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Pilot image {filename} not found.")
    return FileResponse(path=image_path, media_type="image/jpeg")


@router.post("/save")
async def save_annotation(payload: SaveAnnotationRequest):
    """Validates and persists human multi-label annotation record."""
    record = payload.model_dump()
    is_valid, errors, status = manager.save_annotation(record)
    return {
        "is_valid": is_valid,
        "errors": errors,
        "annotation_status": status,
        "record_id": f"{payload.image_id}:{payload.annotator_id}"
    }
