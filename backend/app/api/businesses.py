from fastapi import APIRouter, Query, HTTPException
from app.db.mongodb import get_database
from app.models.business import BusinessModel
from typing import List, Optional
from bson import ObjectId

router = APIRouter()

@router.get("/")
async def get_businesses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(name|created_at|updated_at)$"),
    sort_order: int = Query(-1, ge=-1, le=1)
):
    db = get_database()
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"address": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if category:
        query["category"] = category
    
    # Execute query
    cursor = db.businesses.find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
    businesses = await cursor.to_list(length=limit)
    
    # Clean up data for response
    cleaned_businesses = []
    for business in businesses:
        # Convert ObjectId to string
        if "_id" in business:
            business["_id"] = str(business["_id"])
        
        # Ensure hours is either a dict or None
        if "hours" in business and isinstance(business["hours"], str):
            business["hours"] = {"text": business["hours"]}
        
        # Add default source_url if missing
        if "source_url" not in business:
            business["source_url"] = business.get("url", "")
            
        cleaned_businesses.append(business)
    
    return cleaned_businesses

@router.get("/count")
async def get_businesses_count(
    search: Optional[str] = None,
    category: Optional[str] = None
):
    db = get_database()
    
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"address": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    if category:
        query["category"] = category
    
    count = await db.businesses.count_documents(query)
    return {"count": count}

@router.get("/{business_id}")
async def get_business(business_id: str):
    db = get_database()
    
    if not ObjectId.is_valid(business_id):
        raise HTTPException(status_code=400, detail="Invalid business ID")
    
    business = await db.businesses.find_one({"_id": ObjectId(business_id)})
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Convert ObjectId to string
    business["_id"] = str(business["_id"])
    
    # Ensure hours is either a dict or None
    if "hours" in business and isinstance(business["hours"], str):
        business["hours"] = {"text": business["hours"]}
    
    # Add default source_url if missing
    if "source_url" not in business:
        business["source_url"] = business.get("url", "")
        
    return business

@router.get("/categories/list")
async def get_categories():
    db = get_database()
    
    categories = await db.businesses.distinct("category")
    return {"categories": [cat for cat in categories if cat]}