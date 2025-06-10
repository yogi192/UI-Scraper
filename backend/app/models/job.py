from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobType(str, Enum):
    WEBSITE = "website"
    SEARCH = "search"
    PIPELINE = "pipeline"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class JobModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    type: JobType
    status: JobStatus = JobStatus.PENDING
    parameters: Dict[str, Any]
    progress: Optional[Dict[str, Any]] = Field(default=None, description="Progress tracking with current_step, total_steps, message")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress tracking fields
    current_step: int = Field(default=0, description="Current step in the process")
    total_steps: int = Field(default=0, description="Total number of steps")
    progress_message: Optional[str] = Field(default=None, description="Current progress message")
    logs: List[Dict[str, Any]] = Field(default_factory=list, description="Job execution logs")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class CreateJobRequest(BaseModel):
    type: JobType
    parameters: Dict[str, Any]