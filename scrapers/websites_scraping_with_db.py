"""
Enhanced Website Scraping Module with MongoDB Persistence

This module extends the original website scraping functionality to include
automatic MongoDB persistence for all scraped data.
"""

import asyncio
from typing import Dict, Any, List, Optional
from scrapers.websites_scraping import WebsitesScraping, WebsiteScrapingConfig
from utils.mongodb_client import mongodb_client
from utils.helpers import save_output_data
import logging

logger = logging.getLogger(__name__)

class WebsitesScrapingWithDB(WebsitesScraping):
    """Extended website scraping class with MongoDB persistence"""
    
    def __init__(self, config: Optional[WebsiteScrapingConfig] = None):
        super().__init__(config)
        self.job_id = None
    
    async def process_urls(
        self,
        urls: List[str],
        job_id: Optional[str] = None,
        save_to_file: bool = True,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Process multiple URLs with optional MongoDB persistence.
        
        Args:
            urls: List of website URLs to process
            job_id: Optional job ID for progress tracking
            save_to_file: Whether to save to JSON files (default: True)
            save_to_db: Whether to save to MongoDB (default: True)
        
        Returns:
            Processing results summary
        """
        self.job_id = job_id
        
        # Process URLs using parent class method
        results = await self.process_urls_batch(urls)
        
        # Extract successful results
        successful_results = []
        for result in results.get("results", []):
            if result.get("success") and result.get("entities"):
                for entity in result["entities"]:
                    # Add source information
                    entity["source_url"] = result.get("url")
                    entity["source_name"] = result.get("source", {}).get("name")
                    successful_results.append(entity)
        
        # Save to files if requested
        if save_to_file and successful_results:
            save_output_data(successful_results, data_type="website")
        
        # Save to MongoDB if requested
        if save_to_db and successful_results:
            try:
                await mongodb_client.save_businesses(successful_results, source_type="website")
            except Exception as e:
                logger.error(f"Failed to save to MongoDB: {e}")
        
        # Update job progress if job_id provided
        if job_id:
            await mongodb_client.update_job_progress(job_id, {
                "processed": len(urls),
                "successful": len(successful_results),
                "failed": len(urls) - len([r for r in results.get("results", []) if r.get("success")])
            })
        
        return {
            "urls_processed": len(urls),
            "entities_found": len(successful_results),
            "results": results,
            "saved_to_db": save_to_db and len(successful_results) > 0
        }

# Wrapper functions for job runner
async def process_website_urls(urls: List[str], job_id: Optional[str] = None) -> Dict[str, Any]:
    """Process website URLs with MongoDB persistence"""
    scraper = WebsitesScrapingWithDB()
    return await scraper.process_urls(urls, job_id=job_id)