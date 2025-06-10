import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    def __init__(self):
        self.client = None
        self.database = None
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "ui_scraper")
    
    async def connect(self):
        """Connect to MongoDB"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.database = self.client[self.database_name]
            logger.info(f"Connected to MongoDB at {self.mongodb_url}")
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
    
    async def save_businesses(self, businesses: List[Dict[str, Any]], source_type: str = "website"):
        """Save businesses to MongoDB with duplicate detection"""
        if not self.database:
            await self.connect()
        
        collection = self.database.businesses
        saved_count = 0
        updated_count = 0
        
        for business in businesses:
            # Add metadata
            business["updated_at"] = datetime.utcnow()
            business["source_type"] = source_type
            
            # Check for duplicates by name and address
            existing = None
            if business.get("name") and business.get("address"):
                existing = await collection.find_one({
                    "name": business["name"],
                    "address": business["address"]
                })
            elif business.get("website"):
                existing = await collection.find_one({
                    "website": business["website"]
                })
            
            if existing:
                # Merge data
                merged = self._merge_business_data(existing, business)
                await collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": merged}
                )
                updated_count += 1
            else:
                # New business
                business["created_at"] = datetime.utcnow()
                await collection.insert_one(business)
                saved_count += 1
        
        logger.info(f"Saved {saved_count} new businesses, updated {updated_count} existing")
        return {"saved": saved_count, "updated": updated_count}
    
    def _merge_business_data(self, existing: Dict, new: Dict) -> Dict:
        """Merge business data, preferring non-null new values"""
        merged = existing.copy()
        
        for key, value in new.items():
            if value and (not existing.get(key) or key in ["updated_at", "description"]):
                merged[key] = value
            elif key == "hours" and value:
                # Merge hours
                merged["hours"] = {**existing.get("hours", {}), **value}
            elif key == "social_media" and value:
                # Merge social media
                merged["social_media"] = {**existing.get("social_media", {}), **value}
        
        return merged
    
    async def save_search_results(self, results: List[Dict[str, Any]]):
        """Save search results to MongoDB"""
        if not self.database:
            await self.connect()
        
        collection = self.database.search_results
        
        for result in results:
            result["created_at"] = datetime.utcnow()
            await collection.insert_one(result)
        
        logger.info(f"Saved {len(results)} search results")
    
    async def update_job_progress(self, job_id: str, progress: Dict[str, Any]):
        """Update job progress"""
        if not self.database:
            await self.connect()
        
        if job_id:
            from bson import ObjectId
            await self.database.jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": {"progress": progress}}
            )

# Global instance
mongodb_client = MongoDBClient()