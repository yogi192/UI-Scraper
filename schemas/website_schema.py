"""
website_schema.py

Pydantic models for structured output from website content extraction.
Focuses on business listings in the Dominican Republic.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union

class SourceMetadata(BaseModel):
    """Information about the crawled website"""
    name: str = Field(..., description="Website title or main heading")
    url: str = Field(..., description="Actual URL of the crawled page")
    type: Optional[str] = Field(
        None, 
        description="Website category (e.g., Business Directory, Tourism Site)"
    )
    summary: str = Field(
        ..., 
        description="2-3 sentence analysis of website's purpose and content"
    )

class ExtractionResult(BaseModel):
    """Results of the data extraction process"""
    success: bool = Field(..., description="Extraction succeeded")
    entities_found: int = Field(..., description="Number of valid entities extracted")
    error: Optional[str] = Field(
        None, 
        description="Error type if extraction failed (e.g., 'NoEntitiesFound')"
    )
    error_details: Optional[str] = Field(
        None, 
        description="Detailed explanation of error or data limitations"
    )

class RelevantURL(BaseModel):
    """URL potentially containing more target data"""
    title: str = Field(..., description="Page title or context")
    reason: str = Field(..., description="Why this URL is relevant to our goals")
    url: str = Field(..., description="Complete, crawlable URL")

class ExtractionMetadata(BaseModel):
    """Comprehensive extraction metadata"""
    source: SourceMetadata
    result: ExtractionResult
    relevant_urls: List[RelevantURL] = Field(
        default_factory=list,
        description="URLs for potential follow-up crawling"
    )

class BusinessEntity(BaseModel):
    """A business entity in the Dominican Republic"""
    name: str = Field(..., description="Official business name")
    address: str = Field(..., description="Full physical address with city")
    phone: Optional[str] = Field(
        None, 
        description="Phone in format (XXX) XXX-XXXX"
    )
    website: Optional[str] = Field(
        None, 
        description="Full URL to official website"
    )
    category: str = Field(
        ..., 
        description="Entity type: Business, Attraction, Restaurant, Service etc"
    )
    rating: Optional[Union[str, float]] = Field(
        None, 
        description="Original rating format from source"
    )
    hours: Optional[Union[str, Dict, List]] = Field(
        None, 
        description="Operating hours in any structured format"
    )
    location: Optional[Dict[str, float]] = Field(
        None, 
        description="Lat/Long coordinates {'lat': 0.0, 'lng': 0.0}"
    )

class WebsiteExtractionResult(BaseModel):
    """Final structured extraction output"""
    metadata: ExtractionMetadata
    entities: List[BusinessEntity]