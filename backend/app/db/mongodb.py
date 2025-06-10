from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

db = MongoDB()

async def connect_to_mongo():
    try:
        logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000
        )
        db.database = db.client[settings.database_name]
        
        # Test the connection
        await db.client.server_info()
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes if they don't exist
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        logger.error("Make sure MongoDB is running on localhost:27017")
        raise

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Businesses collection indexes
        await db.database.businesses.create_index("name")
        await db.database.businesses.create_index("category")
        await db.database.businesses.create_index("created_at")
        await db.database.businesses.create_index([("name", "text"), ("description", "text")])
        
        # Jobs collection indexes
        await db.database.jobs.create_index("status")
        await db.database.jobs.create_index("created_at")
        await db.database.jobs.create_index("type")
        
        logger.info("Database indexes created/verified")
    except Exception as e:
        logger.warning(f"Could not create indexes: {str(e)}")

async def close_mongo_connection():
    if db.client:
        logger.info("Closing MongoDB connection")
        db.client.close()

def get_database():
    if db.database is None:
        logger.error("Database not initialized. Make sure MongoDB is connected.")
        raise RuntimeError("Database not initialized")
    return db.database