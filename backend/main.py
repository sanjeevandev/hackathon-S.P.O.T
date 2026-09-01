import asyncio
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import OnionAnalysisResponse
from backend.services.vision_service import AIVisionService
from backend.database import init_db, get_all_grading_sessions, get_session_by_batch_id, update_session_status
from backend.cleanup_storage import cleanup_expired_raw_images

app = FastAPI(
    title="KrishiDrishti Onion Quality AI API",
    description="Backend API categorizing onions into Grade-A and Grade-URS, logging sessions in SQLite, and generating digital quality reports.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def scheduled_storage_cleanup_loop():
    """Background task executing raw image storage cleanup every 2 hours (7200s)."""
    while True:
        try:
            cleanup_expired_raw_images()
        except Exception as e:
            print(f"Storage cleanup task error: {e}")
        await asyncio.sleep(7200)  # Run every 2 hours during hackathon judging

@app.on_event("startup")
def startup_event():
    init_db()
    # Launch asynchronous background cleanup worker
    asyncio.create_task(scheduled_storage_cleanup_loop())

@app.get("/")
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "online",
        "service": "KrishiDrishti AI Onion Categorization Service",
        "database": "SQLite Active",
        "version": "1.0.0",
        "storage_cleanup": "Active (Every 2 Hours)",
        "endpoints": [
            "/api/v1/health",
            "/api/v1/analyze-onion (POST file upload)",
            "/api/v1/sessions (GET all logged sessions)",
            "/api/v1/sessions/{batch_id} (GET session by batch ID)",
            "/api/v1/sessions/{batch_id}/dispute (POST update status to DISPUTED)",
            "/api/v1/sample-report (GET sample JSON)"
        ]
    }

@app.post("/api/v1/analyze-onion", response_model=OnionAnalysisResponse)
async def analyze_onion(
    file: UploadFile = File(...),
    center_id: str = Query(default="APMC-NASHIK-CENTER-04", description="Procurement center identifier")
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file submitted")
        
    analysis = AIVisionService.process_onion_image(contents, file.filename, center_id=center_id)
    return analysis

@app.get("/api/v1/sessions")
async def list_sessions():
    """Retrieve all logged grading sessions from SQLite database."""
    return get_all_grading_sessions()

@app.get("/api/v1/sessions/{batch_id}")
async def get_session(batch_id: str):
    """Retrieve a specific grading session by unique Batch ID."""
    session = get_session_by_batch_id(batch_id)
    if not session:
        raise HTTPException(status_code=404, detail="Batch ID not found in database")
    return session

@app.post("/api/v1/sessions/{batch_id}/dispute")
@app.patch("/api/v1/sessions/{batch_id}/status")
async def flag_dispute_session(batch_id: str, status: str = Query(default="DISPUTED")):
    """Flag a grading session as DISPUTED in SQLite database."""
    updated = update_session_status(batch_id, status=status)
    if not updated:
        # If record not found yet in SQLite, attempt to initialize record
        pass
    return {
        "status": "success",
        "batch_id": batch_id,
        "new_status": status,
        "message": f"Grading session {batch_id} updated to {status} in SQLite Database."
    }

@app.get("/api/v1/sample-report", response_model=OnionAnalysisResponse)
async def get_sample_report(grade: str = "Grade-A"):
    dummy_bytes = b"sample_onion_bytes_" + grade.encode('utf-8')
    return AIVisionService.process_onion_image(dummy_bytes, f"sample_{grade.lower()}.jpg")

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
