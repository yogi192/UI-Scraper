"""JSON utilities for handling MongoDB types"""
import json
from datetime import datetime
from bson import ObjectId
from typing import Any

class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB types"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def convert_mongo_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable format"""
    if not doc:
        return doc
    
    # Convert ObjectId
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    
    # Convert datetime fields
    datetime_fields = ["created_at", "started_at", "completed_at", "updated_at"]
    for field in datetime_fields:
        if field in doc and doc[field] and isinstance(doc[field], datetime):
            doc[field] = doc[field].isoformat()
    
    # Handle nested logs
    if "logs" in doc and isinstance(doc["logs"], list):
        for log in doc["logs"]:
            if isinstance(log, dict) and "timestamp" in log:
                if isinstance(log["timestamp"], datetime):
                    log["timestamp"] = log["timestamp"].isoformat()
                elif isinstance(log["timestamp"], str):
                    # Already a string, leave it as is
                    pass
    
    return doc