"""
MongoDB Logging Handler

This module provides a custom logging handler that saves log records to MongoDB.
"""

import logging
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from typing import Optional

class MongoDBHandler(logging.Handler):
    """Custom logging handler that saves logs to MongoDB"""
    
    def __init__(self, mongodb_url: Optional[str] = None, database_name: Optional[str] = None):
        super().__init__()
        self.mongodb_url = mongodb_url or os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = database_name or os.getenv("DATABASE_NAME", "ui_scraper")
        self.client = None
        self.database = None
        self.collection = None
        self._loop = None
        self._connect_task = None
        
    def _get_event_loop(self):
        """Get or create event loop"""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop
    
    async def _connect(self):
        """Connect to MongoDB"""
        if not self.client:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.database = self.client[self.database_name]
            self.collection = self.database.logs
    
    def emit(self, record):
        """Emit a log record to MongoDB"""
        try:
            # Format the log record
            log_entry = {
                "timestamp": datetime.utcnow(),
                "level": record.levelname,
                "logger": record.name,
                "message": self.format(record),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "thread": record.thread,
                "thread_name": record.threadName,
                "process": record.process,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.format(record)
            
            # Get event loop and ensure connection
            loop = self._get_event_loop()
            
            # Create connection task if needed
            if not self._connect_task:
                self._connect_task = asyncio.run_coroutine_threadsafe(self._connect(), loop)
                self._connect_task.result(timeout=5)  # Wait for connection
            
            # Insert log entry
            if self.collection:
                asyncio.run_coroutine_threadsafe(
                    self.collection.insert_one(log_entry),
                    loop
                )
                
        except Exception as e:
            # Fallback to stderr if MongoDB logging fails
            import sys
            print(f"MongoDB logging error: {e}", file=sys.stderr)
            self.handleError(record)
    
    def close(self):
        """Close the MongoDB connection"""
        if self.client:
            loop = self._get_event_loop()
            asyncio.run_coroutine_threadsafe(
                self.client.close(),
                loop
            )
        super().close()

def setup_mongodb_logging(level=logging.INFO):
    """Setup MongoDB logging for the application"""
    # Create MongoDB handler
    mongo_handler = MongoDBHandler()
    mongo_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    mongo_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(mongo_handler)
    
    return mongo_handler