"""
search_schema.py

Pydantic models for search result extraction and validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class SearchContext(BaseModel):
    """Context of the search operation"""
    query: str = Field(..., description="Original search query")
    url: str = Field(..., description="Actual search URL used")
    results: int = Field(..., description="Total results found by search engine")

class SearchResult(BaseModel):
    """Search operation outcome"""
    success: bool = Field(..., description="URL extraction succeeded")
    urls_found: int = Field(..., description="Number of relevant URLs extracted")
    error: Optional[str] = Field(
        None, 
        description="Error type if extraction failed"
    )
    error_details: Optional[str] = Field(
        None, 
        description="Detailed failure reason (captcha, short HTML, irrelevant results etc)"
    )

class SearchMetadata(BaseModel):
    """Search operation metadata"""
    context: SearchContext
    result: SearchResult

class RelevantURL(BaseModel):
    """Relevant URL from search results"""
    title: str = Field(..., description="Result title from search")
    reason: str = Field(..., description="Why this URL matches our criteria")
    url: str = Field(..., description="Complete, crawlable URL")

class SearchExtractionResult(BaseModel):
    """Final structured search extraction"""
    metadata: SearchMetadata
    urls: List[RelevantURL]