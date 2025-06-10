from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import businesses, jobs, dashboard, settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    await connect_to_mongo()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await close_mongo_connection()

app = FastAPI(
    title="AI Business Crawler API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Nuxt dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(businesses.router, prefix="/api/businesses", tags=["businesses"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])

@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation"""
    return {
        "message": "AI Business Crawler API",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Check MongoDB connection
        db_status = "healthy"
        try:
            from app.db.mongodb import db
            if db.client:
                await db.client.server_info()
            else:
                db_status = "unhealthy: Not connected"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "service": "AI Business Crawler API",
            "version": "1.0.0",
            "dependencies": {
                "mongodb": db_status
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "AI Business Crawler API",
            "error": str(e)
        }