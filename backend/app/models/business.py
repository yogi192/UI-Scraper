from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class BusinessModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[str] = None
    hours: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, float]] = None
    social_media: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    email: Optional[str] = None
    source_url: str
    source_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True