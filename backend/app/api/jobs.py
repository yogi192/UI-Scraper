from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.db.mongodb import get_database
from app.models.job import JobModel, CreateJobRequest, JobStatus
from app.services.job_runner import run_scraping_job
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=JobModel)
async def create_job(job_request: CreateJobRequest, background_tasks: BackgroundTasks):
    db = get_database()
    
    # Create job document
    job_data = {
        "type": job_request.type,
        "status": JobStatus.PENDING,
        "parameters": job_request.parameters,
        "created_at": datetime.utcnow(),
        "current_step": 0,
        "total_steps": 0,
        "progress_message": None,
        "logs": []
    }
    
    result = await db.jobs.insert_one(job_data)
    job_data["_id"] = str(result.inserted_id)
    
    # Add to background tasks
    background_tasks.add_task(run_scraping_job, str(result.inserted_id))
    
    return JobModel(**job_data)

@router.get("/", response_model=List[JobModel])
async def get_jobs(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None
):
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    
    jobs = await db.jobs.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    # Convert ObjectId to string
    for job in jobs:
        if "_id" in job:
            job["_id"] = str(job["_id"])
    return jobs

@router.get("/{job_id}", response_model=JobModel)
async def get_job(job_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")
    
    job = await db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert ObjectId to string
    job["_id"] = str(job["_id"])
    return job

@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID")
    
    result = await db.jobs.update_one(
        {"_id": ObjectId(job_id), "status": JobStatus.PENDING},
        {"$set": {"status": JobStatus.FAILED, "error": "Cancelled by user"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Job not found or already running")
    
    return {"message": "Job cancelled"}