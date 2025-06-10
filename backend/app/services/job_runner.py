import asyncio
import sys
import os
from datetime import datetime
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.job import JobStatus, JobType
import logging

# Add parent directory to path to import scrapers
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

logger = logging.getLogger(__name__)

async def update_job_progress(job_id: str, current_step: int, total_steps: int, message: str):
    """Update job progress in the database"""
    db = get_database()
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
        "step": current_step
    }
    await db.jobs.update_one(
        {"_id": ObjectId(job_id)},
        {
            "$set": {
                "current_step": current_step,
                "total_steps": total_steps,
                "progress_message": message
            },
            "$push": {
                "logs": log_entry
            }
        }
    )

async def run_scraping_job(job_id: str):
    """Run a scraping job in the background"""
    db = get_database()
    
    try:
        # Update job status to running
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {
                "status": JobStatus.RUNNING, 
                "started_at": datetime.utcnow(),
                "current_step": 0,
                "total_steps": 1,
                "progress_message": "Initializing..."
            }}
        )
        
        # Get job details
        job = await db.jobs.find_one({"_id": ObjectId(job_id)})
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        # Import scrapers
        try:
            from scrapers.websites_scraping_with_db import process_website_urls
            from scrapers.searches_scraping import process_search_terms, process_search_urls
            logger.info("Successfully imported scraper modules")
        except ImportError as e:
            logger.error(f"Failed to import scraper modules: {str(e)}")
            raise Exception(f"Scraper modules not found. Please ensure the scrapers package is properly installed: {str(e)}")
        
        result = None
        
        if job["type"] == JobType.WEBSITE:
            # Process website URLs
            urls = job["parameters"].get("urls", [])
            total_urls = len(urls)
            await update_job_progress(job_id, 0, total_urls, f"Processing {total_urls} website URLs...")
            
            result = await process_website_urls(urls, job_id=job_id)
            
        elif job["type"] == JobType.SEARCH:
            # Process search terms or URLs
            if "terms" in job["parameters"]:
                terms = job["parameters"]["terms"]
                total_terms = len(terms)
                await update_job_progress(job_id, 0, total_terms, f"Processing {total_terms} search terms...")
                
                result = await process_search_terms(terms, job_id=job_id)
            elif "urls" in job["parameters"]:
                urls = job["parameters"]["urls"]
                total_urls = len(urls)
                await update_job_progress(job_id, 0, total_urls, f"Processing {total_urls} search URLs...")
                
                result = await process_search_urls(urls, job_id=job_id)
                
        elif job["type"] == JobType.PIPELINE:
            # Run full pipeline
            terms = job["parameters"].get("terms", [])
            await update_job_progress(job_id, 0, 2, "Starting pipeline: Search phase...")
            
            # First, get URLs from search
            search_result = await process_search_terms(terms, job_id=job_id)
            await update_job_progress(job_id, 1, 2, "Search complete. Starting scraping phase...")
            
            if search_result and search_result.get("urls"):
                # Then scrape the URLs
                result = await process_website_urls(search_result["urls"], job_id=job_id)
                await update_job_progress(job_id, 2, 2, "Pipeline complete!")
        
        # Update job as completed
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": JobStatus.COMPLETED,
                    "completed_at": datetime.utcnow(),
                    "result": result or {"message": "Job completed successfully"}
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error running job {job_id}: {str(e)}")
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": JobStatus.FAILED,
                    "completed_at": datetime.utcnow(),
                    "error": str(e)
                }
            }
        )