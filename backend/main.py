import os
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

import io
import csv
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from .store import init_db, create_job, get_job, update_job_status
from .pipeline import run_pipeline
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/jobs")
async def create_enrichment_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)
    
    import hashlib
    job_id = hashlib.md5(content).hexdigest()
    
    job = get_job(job_id)
    if not job:
        create_job(job_id, len(rows))
    else:
        # Reset status if it failed before, so it can try again
        if job["status"] == "failed":
            update_job_status(job_id, "processing")
    
    # Run pipeline in background (will skip already completed rows)
    background_tasks.add_task(run_pipeline, job_id, rows)
    
    return {"job_id": job_id, "total": len(rows)}

@app.get("/jobs/{job_id}/status")
def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    return {"status": job["status"], "processed": job["processed"], "total": job["total"]}

@app.get("/jobs/{job_id}/results")
def get_job_results(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    return {"results": job["results"]}

@app.get("/jobs/{job_id}/export")
def export_job_results(job_id: str):
    job = get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    
    results = job["results"]
    if not results:
        return {"error": "No results yet"}
    
    output = io.StringIO()
    
    if len(results) > 0:
        first_result = results[0]["output"]
        headers = list(first_result.keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in results:
            writer.writerow(row["output"])
            
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_export.csv"}
    )
