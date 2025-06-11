from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.db.mongodb import get_database
from app.utils.json_utils import convert_mongo_doc, MongoJSONEncoder
from typing import Dict, List
from bson import ObjectId
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

@router.get("/stats")
async def get_dashboard_stats() -> Dict:
    try:
        db = get_database()
        
        # Get counts
        total_businesses = await db.businesses.count_documents({})
        total_jobs = await db.jobs.count_documents({})
        completed_jobs = await db.jobs.count_documents({"status": "completed"})
        failed_jobs = await db.jobs.count_documents({"status": "failed"})
        
        # Get category distribution
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        categories = await db.businesses.aggregate(pipeline).to_list(length=10)
        
        # Get recent jobs
        recent_jobs = await db.jobs.find({}).sort("created_at", -1).limit(5).to_list(length=5)
        
        # Convert MongoDB documents to JSON-serializable format
        recent_jobs_converted = [convert_mongo_doc(job) for job in recent_jobs]
        
        result = {
            "stats": {
                "total_businesses": total_businesses,
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs
            },
            "categories": [{"name": cat["_id"] or "Uncategorized", "count": cat["count"]} for cat in categories],
            "recent_jobs": recent_jobs_converted
        }
        
        # Return as JSON response with custom encoder
        json_str = json.dumps(result, cls=MongoJSONEncoder)
        return Response(content=json_str, media_type="application/json")
    except Exception as e:
        logger.error(f"Error in get_dashboard_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))