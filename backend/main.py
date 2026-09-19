import io
import uuid
from typing import List, Optional
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.ai.schemas import ImageInput, VisionResult
from backend.ai.status import AIHealthDiagnostics, AIStatusResponse
from backend.pipeline.pipeline import InspectionPipeline
from backend.pipeline.schemas import PipelineResult
from backend.grading.schemas import (
    BatchAggregationRequest,
    BatchAggregationResult,
    GradingProfile,
    GradingRequest,
    GradingResult,
)
from backend.grading.batch_engine import BatchIntelligenceEngine
from backend.grading.grading_engine import GradingPolicyEngine
from backend.grading.profiles import list_grading_profiles, get_grading_profile, register_grading_profile
from backend.db import get_db, init_database
from backend.db.repositories.inspection_repository import InspectionRepository
from backend.database import get_all_grading_sessions, get_session_by_batch_id, update_session_status
from backend.schemas import OnionAnalysisResponse
from backend.services.vision_service import AIVisionService, validate_onion_image

from backend.contracts.schemas import CanonicalInspectionResult
from backend.reporting.report_contract import InspectionReport
from backend.reporting.report_renderer import ReportRenderer
from backend.reporting.service import ReportingService
from backend.api.annotation_router import router as annotation_router

app = FastAPI(
    title="S.P.O.T. AI Onion Quality & Grading API",
    description="Refactored modular inspection & grading policy API with Phase 5 Canonical Presentation & Digital Reporting Layer.",
    version="5.0.0"
)

app.include_router(annotation_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = InspectionPipeline()


@app.on_event("startup")
def startup_event():
    init_database()


@app.get("/")
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "online",
        "service": "S.P.O.T. Onion Quality Assessment & Digital Reporting API",
        "database": "SQLAlchemy 2.0 ORM Active",
        "version": "5.0.0",
        "pipeline": "Active (Quality Gate + Modular VisionModel)",
        "grading_engine": "Active (Batch Intelligence + Decoupled Grading Profiles)",
        "reporting_engine": "Active (Canonical InspectionResult + Structured & HTML Reporting)",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/ai/status",
            "/api/v1/inspect (POST file upload)",
            "/api/v1/inspections (GET list history)",
            "/api/v1/inspections/{inspection_id} (GET details)",
            "/api/v1/inspections/{inspection_id}/result (GET canonical presentation)",
            "/api/v1/inspections/{inspection_id}/report (GET/POST digital report)",
            "/api/v1/batches/{batch_id}/aggregate (POST aggregation)",
            "/api/v1/grade (POST evaluation)",
            "/api/v1/profiles (GET/POST policy profiles)"
        ]
    }


@app.get("/api/v1/ai/status", response_model=AIStatusResponse)
async def get_ai_status():
    """Retrieve detailed runtime health, availability, and diagnostics for the AI vision engine."""
    return AIHealthDiagnostics.get_status()


@app.post("/api/v1/inspect", response_model=PipelineResult)
async def inspect_onion(
    file: UploadFile = File(...),
    center_id: str = Query(default="APMC-NASHIK-CENTER-04", description="Procurement center identifier"),
    batch_id: Optional[str] = Query(default=None, description="Optional procurement batch identifier"),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file submitted")

    try:
        pil_img = Image.open(io.BytesIO(contents))
        width, height = pil_img.size
    except Exception as img_err:
        raise HTTPException(status_code=400, detail=f"Invalid image file format: {str(img_err)}")

    request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
    image_input = ImageInput(
        image_id=request_id,
        width=width,
        height=height,
        mime_type=file.content_type or "image/jpeg",
        file_reference=file.filename
    )

    pipeline_result: PipelineResult = pipeline.execute(image_input, contents)

    # Automatically persist inspection if vision model was executed
    target_batch_id = batch_id or f"BATCH-{request_id}"
    try:
        grading_res = None
        declared_weight = None
        w_source = "UNAVAILABLE"

        if pipeline_result.status == "SUCCESS" and pipeline_result.vision_result:
            agg_res = BatchIntelligenceEngine.aggregate_batch(target_batch_id, [pipeline_result.vision_result])
            declared_weight = agg_res.weight_distribution.total_batch_weight_kg
            w_source = agg_res.weight_distribution.weight_source
            grading_req = GradingRequest(
                batch_id=target_batch_id,
                percentages=agg_res.percentages,
                weight_distribution=agg_res.weight_distribution,
                inspection_confidence=pipeline_result.vision_result.overall_confidence
            )
            grading_res = GradingPolicyEngine.evaluate(grading_req)

            repo = InspectionRepository(db)
            repo.save_inspection_result(
                batch_id=target_batch_id,
                pipeline_result=pipeline_result,
                grading_result=grading_res,
                center_id=center_id,
                declared_weight_kg=declared_weight,
                weight_source=w_source
            )
    except Exception as db_err:
        import logging
        logging.error(f"Failed to persist inspection to database: {str(db_err)}")

    return pipeline_result


@app.post("/api/v1/analyze-onion", response_model=OnionAnalysisResponse)
async def analyze_onion(
    file: UploadFile = File(...),
    center_id: str = Query(default="APMC-NASHIK-CENTER-04", description="Procurement center identifier")
):
    """
    Dedicated onion quality inspection endpoint for frontend PWA.
    Runs input validation heuristic, OpenCV bulb detection, YOLO defect classification,
    and returns full analysis payload with SHA-256 tamper hash.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file submitted")

    # Real input validation heuristic
    is_valid, validation_msg, metrics = validate_onion_image(contents)
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": validation_msg,
                "metrics": metrics,
                "recommendation": "Scan onion only. Please place onion bulbs inside the camera frame and retake."
            }
        )

    try:
        response = AIVisionService.process_onion_image(
            image_bytes=contents,
            filename=file.filename,
            center_id=center_id
        )
        return response
    except Exception as e:
        import logging
        logging.exception(f"Error analyzing onion: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/v1/inspections")
async def list_inspections(
    batch_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve inspection history with optional filtering."""
    repo = InspectionRepository(db)
    inspections = repo.list_inspections(batch_id=batch_id, status=status, limit=limit)
    out = []
    for insp in inspections:
        gr = insp.grading_result
        out.append({
            "inspection_id": insp.id,
            "batch_id": insp.batch_id,
            "status": insp.status,
            "started_at": insp.started_at.isoformat() if insp.started_at else None,
            "confidence": insp.inspection_confidence,
            "review_status": insp.review_status,
            "model_version_id": insp.model_version_id,
            "grading_result": {
                "grade": gr.grade if gr else "Grade-C",
                "quality_score": gr.quality_score if gr else 0.0,
                "profile_id": gr.grading_profile_id if gr else None,
                "sampling_status": gr.sampling_status if gr else "SAMPLE_ONLY",
            } if gr else None
        })
    return out


@app.get("/api/v1/inspections/{inspection_id}")
async def get_inspection_details(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve complete inspection record by ID."""
    repo = InspectionRepository(db)
    insp = repo.get_by_id(inspection_id)
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection record not found")

    gr = insp.grading_result
    return {
        "inspection_id": insp.id,
        "batch_id": insp.batch_id,
        "status": insp.status,
        "started_at": insp.started_at.isoformat() if insp.started_at else None,
        "completed_at": insp.completed_at.isoformat() if insp.completed_at else None,
        "inspection_confidence": insp.inspection_confidence,
        "review_status": insp.review_status,
        "review_reason": insp.review_reason,
        "model_version": {
            "id": insp.model_version.id,
            "name": insp.model_version.model_name,
            "version": insp.model_version.model_version,
            "source": insp.model_version.source,
        } if insp.model_version else None,
        "grading_result": {
            "grade": gr.grade,
            "quality_score": gr.quality_score,
            "profile_id": gr.grading_profile_id,
            "grade_a_percent": gr.grade_a_percent,
            "urs_percent": gr.urs_percent,
            "sampling_status": gr.sampling_status,
            "explanation": gr.explanation,
        } if gr else None,
        "images": [
            {
                "id": img.id,
                "filename": img.original_filename,
                "width": img.width,
                "height": img.height,
                "quality_status": img.quality_status,
                "detections_count": len(img.detections)
            } for img in insp.images
        ]
    }


@app.get("/api/v1/inspections/{inspection_id}/result", response_model=CanonicalInspectionResult)
async def get_canonical_inspection_result(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """Returns the unified canonical inspection result data contract for frontend consumption."""
    try:
        return ReportingService.get_canonical_result(inspection_id, db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.get("/api/v1/inspections/{inspection_id}/report")
async def get_inspection_report(
    inspection_id: str,
    format: str = Query(default="json", description="json or html"),
    db: Session = Depends(get_db)
):
    """Returns the digital inspection report in structured JSON or human-readable HTML format."""
    try:
        report = ReportingService.get_or_create_report(inspection_id, db)
        if format.lower() == "html":
            html_content = ReportRenderer.render_html(report)
            return Response(content=html_content, media_type="text/html")
        return report
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.post("/api/v1/inspections/{inspection_id}/report", response_model=InspectionReport)
async def generate_inspection_report_endpoint(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """Triggers generation and persistence of a digital inspection report."""
    try:
        return ReportingService.generate_and_persist_report(inspection_id, db)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.post("/api/v1/batches/{batch_id}/aggregate", response_model=BatchAggregationResult)
async def aggregate_batch_inspections(
    batch_id: str,
    vision_results: List[VisionResult],
    declared_weight_kg: Optional[float] = Query(default=None, ge=0.1, description="Optional sample batch weight in KG")
):
    """Aggregate multi-image vision results into lot statistics."""
    return BatchIntelligenceEngine.aggregate_batch(batch_id, vision_results, declared_weight_kg)


@app.post("/api/v1/grade", response_model=GradingResult)
async def evaluate_lot_grade(request: GradingRequest):
    """Evaluate batch lot percentages against commercial grading policy profiles."""
    return GradingPolicyEngine.evaluate(request)


@app.get("/api/v1/profiles", response_model=List[GradingProfile])
async def get_profiles():
    """Retrieve all available commercial grading policy profiles."""
    return list_grading_profiles()


@app.post("/api/v1/profiles", response_model=GradingProfile)
async def create_profile(profile: GradingProfile):
    """Register or update a commercial grading policy profile."""
    register_grading_profile(profile)
    return profile


@app.get("/api/v1/sessions")
async def list_sessions():
    """Retrieve logged sessions from database."""
    return get_all_grading_sessions()


@app.get("/api/v1/sessions/{batch_id}")
async def get_session(batch_id: str):
    """Retrieve specific session by batch ID."""
    session = get_session_by_batch_id(batch_id)
    if not session:
        raise HTTPException(status_code=404, detail="Batch ID not found in database")
    return session


@app.post("/api/v1/sessions/{batch_id}/dispute")
async def flag_dispute(batch_id: str):
    """Flags a batch session as disputed in SQLite database. Returns 404 if batch_id not found."""
    success = update_session_status(batch_id, "DISPUTED")
    if not success:
        raise HTTPException(status_code=404, detail=f"Batch ID '{batch_id}' not found in database")
    return {"status": "success", "batch_id": batch_id, "review_status": "DISPUTED"}


if __name__ == "__main__":
    import uvicorn
    init_database()
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
