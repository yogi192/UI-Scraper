"""
Search Results Scraping Module

This module provides comprehensive functionality for scraping Google search results
and extracting structured data about Dominican Republic businesses, attractions,
restaurants, and services using advanced LLM-based extraction strategies.

Key Features:
- Flexible search URL generation with advanced parameters
- Stealth web scraping using Playwright with anti-detection
- Batch processing of multiple search queries
- Integration with improved LLM data extraction pipeline
- Comprehensive error handling and retry mechanisms

Classes:
    SearchScrapingConfig: Configuration for search scraping parameters
    SearchResultsScraper: Main class for search results scraping and extraction

Author: Mr. Anas
Created: 5/30/2025
Updated: Enhanced for improved LLM integration and better error handling
"""

import os
import sys
import asyncio
import logging
import traceback
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from urllib.parse import quote_plus, urlencode, urlparse

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from logs.custom_logging import setup_logging
from utils.helpers import SeleniumBaseBrowserManager, HTMLContentProcessor, save_debug_files, save_output_data
from scrapers.llm_data_extraction import create_search_extractor, ExtractionConfig
from settings import SEARCH_RESULTS_EXTRACTION_PROMPT, LLM_CONFIG as default_llm_config
from schemas.search_schema import SearchExtractionResult


# Initialize module logger
logger = setup_logging(console_level=logging.DEBUG)


# =============================================================================
# Configuration Classes
# =============================================================================

@dataclass
class SearchScrapingConfig:
    """
    Configuration parameters for search scraping operations.
    
    Attributes:
        max_concurrent_searches: Maximum number of concurrent search requests
        search_delay_seconds: Delay between search requests to avoid rate limiting
        default_results_per_page: Default number of results per search page
        enable_stealth_mode: Whether to use stealth mode for scraping
        timeout_seconds: Timeout for individual page loads
    """
    max_concurrent_searches: int = 3
    search_delay_seconds: float = 2.0
    default_results_per_page: int = 50
    enable_stealth_mode: bool = True
    timeout_seconds: int = 30


# =============================================================================
# Main Search Results Scraping Class
# =============================================================================

class SearchResultsScraper:
    """
    Advanced Search Results Scraper for Dominican Republic Business Data.
    
    This class provides comprehensive functionality for scraping Google search results
    and extracting structured business data using LLM-based extraction strategies.
    It supports flexible search query generation, batch processing, and robust
    error handling with anti-detection measures.
    
    Features:
    - Advanced Google search URL generation with geo-targeting
    - Stealth web scraping with Playwright
    - Batch processing of multiple search queries
    - Integration with improved LLM data extraction pipeline
    - Comprehensive error handling and retry mechanisms
    
    Attributes:
        scraping_config: Configuration for scraping parameters
        seleniumbase_browser: Browser manager for web scraping
        html_processor: HTML content processor for cleaning and extraction
        google_base_url: Base URL for Google search queries
    """
    
    def __init__(self, scraping_config: SearchScrapingConfig = None) -> None:
        """
        Initialize the search results scraper.
        
        Args:
            scraping_config: Optional configuration for scraping parameters
        """
        self.scraping_config = scraping_config or SearchScrapingConfig()
        self.seleniumbase_browser = SeleniumBaseBrowserManager()
        self.html_processor = HTMLContentProcessor()
        self.google_base_url = "https://www.google.com/search"
        
        logger.info("Initialized SearchResultsScraper with configuration")
        logger.debug(f"Scraping config: {self.scraping_config}")

    async def generate_search_url(
        self,
        search_term: str,
        num_results: int = None,
        language: str = 'en',
        country: str = 'DO',
        geo_location: str = 'DO',
        site_restriction: str = None,
        title_requirement: str = None,
        pagination_offset: int = 0
    ) -> str:
        """
        Generate advanced Google search URLs optimized for Dominican Republic business data.
        
        This method creates sophisticated search URLs with geo-targeting, language
        restrictions, and domain filtering to maximize the relevance of search
        results for Dominican Republic business data extraction.
        
        Args:
            search_term: Primary search query term
            num_results: Number of results per page (10-100, defaults to config)
            language: Content language (2-letter ISO code)
            country: Country restriction (2-letter ISO code)
            geo_location: Physical location for results (2-letter ISO code)
            site_restriction: Domain restriction for results
            title_requirement: Word that must appear in page title
            pagination_offset: Starting offset for pagination
            
        Returns:
            Complete Google search URL with all parameters
            
        Raises:
            ValueError: If search_term is empty or invalid
        """
        # Validate required parameters
        if not search_term or not search_term.strip():
            raise ValueError("Search term cannot be empty")
        
        # Use default results per page from config if not specified
        if num_results is None:
            num_results = self.scraping_config.default_results_per_page
        
        logger.debug(f"Generating search URL for term: '{search_term}'")
        
        # Build base search parameters
        search_parameters = {
            'q': search_term.strip(),
            'num': min(100, max(10, num_results)),  # Clamp to Google's limits
            'cr': f'country{country.upper()}',  # Country restriction
            'gl': geo_location.upper(),  # Geolocation targeting
            'start': max(0, pagination_offset),  # Pagination offset
        }

        # Add language restriction using modern parameter format
        if language:
            search_parameters['tbs'] = f'lr:lang_1{language.lower()}'

        # Add domain restriction if specified
        if site_restriction:
            search_parameters['as_sitesearch'] = site_restriction
            logger.debug(f"Added site restriction: {site_restriction}")

        # Add title requirement if specified
        if title_requirement:
            search_parameters['as_title'] = title_requirement
            logger.debug(f"Added title requirement: {title_requirement}")

        # Generate complete search URL
        query_string = urlencode(search_parameters, doseq=True)
        complete_search_url = f"{self.google_base_url}?{query_string}"
        
        logger.info(f"Generated search URL for '{search_term}' with {num_results} results")
        logger.debug(f"Complete URL: {complete_search_url}")
        
        return complete_search_url

    async def scrape_multiple_search_results(
        self, 
        search_urls: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple search results pages concurrently with rate limiting.
        
        This method handles batch processing of multiple search URLs with
        concurrent execution, rate limiting, and comprehensive error handling.
        
        Args:
            search_urls: List of complete Google search URLs to scrape
            
        Returns:
            List of dictionaries containing scraped content for each URL
            
        Raises:
            ValueError: If search_urls is empty or invalid
        """
        # Validate input parameters
        if not search_urls:
            raise ValueError("Search URLs list cannot be empty")
        
        # Filter out invalid URLs
        valid_search_urls = [url for url in search_urls if url and url.strip()]
        if not valid_search_urls:
            raise ValueError("No valid search URLs provided")
        
        total_urls = len(valid_search_urls)
        logger.info(f"Starting batch scraping of {total_urls} search URLs")
        
        # Initialize results storage
        all_scraping_results = []
        
        try:
            # Process URLs in batches to respect rate limits
            batch_size = self.scraping_config.max_concurrent_searches
            
            for batch_start in range(0, total_urls, batch_size):
                batch_end = min(batch_start + batch_size, total_urls)
                current_batch = valid_search_urls[batch_start:batch_end]
                
                batch_number = (batch_start // batch_size) + 1
                total_batches = (total_urls - 1) // batch_size + 1
                
                logger.info(f"Processing batch {batch_number}/{total_batches} ({len(current_batch)} URLs)")
                
                # Scrape the entire batch concurrently
                batch_scraping_results = await self.seleniumbase_browser.batch_scrape(current_batch)
                
                # Process results
                for i, (raw_html, status_code) in enumerate(batch_scraping_results):
                    url = current_batch[i]
                    # Extract clean URL identifier for logging
                    parsed_url = urlparse(url)
                    url_identifier = f"{parsed_url.netloc}{parsed_url.path}"
                    
                    try:
                        # Validate HTML content retrieval
                        if not raw_html or status_code != 200:
                            error_message = f"Failed to retrieve HTML content (Status: {status_code})"
                            logger.warning(f"❌ {error_message} for URL: {url_identifier}")
                            result = {
                                url: {
                                    "message": error_message,
                                    "status_code": status_code,
                                    "success": False
                                }
                            }
                        else:
                            # Process HTML content for LLM consumption
                            llm_friendly_content = self.html_processor.get_llm_friendly_content(raw_html)
                            
                            # Log content processing metrics
                            logger.debug(f"Processed HTML - LLM-friendly: {len(str(llm_friendly_content))} chars")
                            logger.info(f"✅ Successfully scraped search results from: {url_identifier}")
                            
                            result = {
                                url: {
                                    "message": "Search results scraped successfully",
                                    "content": llm_friendly_content,
                                    "status_code": status_code,
                                    "success": True,
                                    "content_length": len(str(llm_friendly_content))
                                }
                            }
                        all_scraping_results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing result for {url_identifier}: {e}")
                        logger.debug(f"Error traceback: {traceback.format_exc()}")
                        all_scraping_results.append({
                            url: {
                                "message": "Result processing failed",
                                "error": str(e),
                                "success": False
                            }
                        })
                
                # Add delay between batches to avoid rate limiting
                if batch_end < total_urls:
                    logger.debug(f"Inter-batch delay: {self.scraping_config.search_delay_seconds}s")
                    await asyncio.sleep(self.scraping_config.search_delay_seconds)
        
        except Exception as batch_error:
            error_message = f"Batch scraping process failed: {str(batch_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Batch error traceback: {traceback.format_exc()}")
            raise
        
        # Calculate and log success metrics
        successful_scrapes = sum(
            1 for result in all_scraping_results 
            if any(data.get("success", False) for data in result.values())
        )
        success_rate = (successful_scrapes / len(all_scraping_results) * 100) if all_scraping_results else 0
        
        logger.info(f"✅ Batch scraping completed. Success rate: {success_rate:.1f}% ({successful_scrapes}/{len(all_scraping_results)})")
        
        # Save debug files for analysis
        save_debug_files(search_scraped_content=all_scraping_results)
        logger.debug("Scraping results saved to debug files")
        
        return all_scraping_results



    async def extract_business_urls_from_searches(
        self,
        search_urls: Optional[List[str]] = None,
        search_terms: Optional[List[str]] = None,
        llm_extraction_method: str = 'crawl4ai',
        llm_configuration: Dict[str, Any] = None,
        extraction_config: ExtractionConfig = None
    ) -> List[SearchExtractionResult]:
        """
        Extract business URLs from search results using advanced LLM processing.
        
        This is the main entry point for the complete search-to-extraction pipeline.
        It supports flexible input methods (direct URLs or search terms), performs
        web scraping, and uses LLM-based extraction to identify relevant business URLs.
        
        Args:
            search_urls: Optional list of pre-generated search URLs
            search_terms: Optional list of search terms to convert to URLs
            llm_extraction_method: LLM extraction method ('direct' or 'crawl4ai')
            llm_configuration: Optional LLM configuration (uses default if None)
            extraction_config: Optional extraction configuration (uses default if None)
            
        Returns:
            List of SearchExtractionResult objects containing extracted business URLs
            
        Raises:
            ValueError: If neither search_urls nor search_terms are provided
            Exception: For critical processing failures
        """
        logger.info("🚀 Starting business URL extraction from search results")
        
        try:
            # Validate input parameters
            if not search_urls and not search_terms:
                raise ValueError("Either search_urls or search_terms must be provided")
            
            # Generate search URLs from terms if needed
            if not search_urls and search_terms:
                logger.info(f"Generating search URLs from {len(search_terms)} search terms")
                
                url_generation_tasks = [
                    self.generate_search_url(search_term=term) 
                    for term in search_terms if term and term.strip()
                ]
                
                if not url_generation_tasks:
                    raise ValueError("No valid search terms provided")
                
                search_urls = await asyncio.gather(*url_generation_tasks)
                logger.info(f"Generated {len(search_urls)} search URLs")
            
            # Validate final URL list
            if not search_urls:
                raise ValueError("No search URLs available for processing")
            
            # Scrape search results
            logger.info(f"Scraping {len(search_urls)} search result pages")
            scraped_search_data = await self.scrape_multiple_search_results(search_urls=search_urls)
            
            if not scraped_search_data:
                logger.warning("No search data was successfully scraped")
                return []
            
            # Configure LLM extraction
            extraction_configuration = extraction_config or ExtractionConfig(
                max_batch_size=3,  # Conservative batch size for search results
                max_retry_attempts=2,
                retry_delay_seconds=1.5
            )
            
            # Create search-specific LLM extractor
            logger.info("Initializing LLM-based URL extraction")
            search_url_extractor = create_search_extractor(
                input_data_list=scraped_search_data,
                llm_configuration=llm_configuration or default_llm_config,
                extraction_config=extraction_configuration
            )
            
            # Execute LLM-based URL extraction
            logger.info(f"Executing LLM extraction using method: {llm_extraction_method}")
            extracted_business_urls = await search_url_extractor.execute_data_extraction(
                extraction_method=llm_extraction_method
            )
            
            if not extracted_business_urls:
                logger.warning("No business URLs were extracted from search results")
                return []
            
            # Convert results to proper schema objects
            validated_results = []
            for extraction_result in extracted_business_urls:
                try:
                    validated_result = SearchExtractionResult(**extraction_result)
                    validated_results.append(validated_result)
                except Exception as validation_error:
                    logger.warning(f"Result validation failed: {str(validation_error)}")
                    continue
            
            # Calculate and log final metrics
            total_urls_extracted = sum(
                len(result.urls) for result in validated_results 
                if hasattr(result, 'urls') and result.urls
            )
            
            logger.info(f"✅ Extraction completed successfully")
            logger.info(f"📊 Results: {len(validated_results)} search results processed")
            logger.info(f"📊 Total business URLs extracted: {total_urls_extracted}")
            
            try:
                validated_results_dict = [result.model_dump() for result in validated_results]
            except Exception as e:
                logger.warning(f'Error in validated_results_dict: {e}')
            # Save final results for debugging and analysis
            save_output_data(output_data=validated_results_dict, data_type='search')
            logger.debug("Final extraction results saved to debug files")
            
            return validated_results
            
        except Exception as extraction_error:
            error_message = f"Business URL extraction failed: {str(extraction_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Extraction error traceback: {traceback.format_exc()}")
            
            # Re-raise for proper error handling by caller
            raise


# =============================================================================
# Convenience Functions
# =============================================================================

def create_search_scraper(
    scraping_config: SearchScrapingConfig = None
) -> SearchResultsScraper:
    """
    Create a configured SearchResultsScraper instance.
    
    Args:
        scraping_config: Optional configuration for scraping parameters
        
    Returns:
        Configured SearchResultsScraper instance
    """
    return SearchResultsScraper(scraping_config=scraping_config)


async def quick_search_extraction(
    search_terms: List[str],
    max_concurrent: int = 2,
    results_per_search: int = 30
) -> List[SearchExtractionResult]:
    """
    Quick utility function for simple search term extraction.
    
    Args:
        search_terms: List of search terms to process
        max_concurrent: Maximum concurrent search requests
        results_per_search: Number of results per search
        
    Returns:
        List of SearchExtractionResult objects
    """
    # Create optimized configuration for quick extraction
    quick_config = SearchScrapingConfig(
        max_concurrent_searches=max_concurrent,
        default_results_per_page=results_per_search,
        search_delay_seconds=1.0
    )
    
    # Create scraper and execute extraction
    search_scraper = create_search_scraper(scraping_config=quick_config)
    
    return await search_scraper.extract_business_urls_from_searches(
        search_terms=search_terms,
        llm_extraction_method='crawl4ai'
    )


# =============================================================================
# Main Execution Block
# =============================================================================

if __name__ == "__main__":
    """
    Main execution block for testing and development.
    
    This block demonstrates how to use the SearchResultsScraper class
    with sample search terms and configurations.
    """
    try:
        # Test configuration for development
        test_search_terms = [
            "restaurantes zona colonial",
            "hoteles santo domingo",
            "servicios turisticos punta cana"
        ]
        
        # Test with optimized configuration
        test_scraping_config = SearchScrapingConfig(
            max_concurrent_searches=2,
            default_results_per_page=50,
            search_delay_seconds=2.0,
            enable_stealth_mode=True
        )
        
        logger.info("🚀 Starting test execution of SearchResultsScraper")
        
        # Create and configure scraper
        search_scraper = create_search_scraper(scraping_config=test_scraping_config)
        
        # Execute extraction
        test_results = asyncio.run(
            search_scraper.extract_business_urls_from_searches(
                search_terms=test_search_terms,
                llm_extraction_method='crawl4ai'
            )
        )
        
        # Display results summary
        total_extracted_urls = sum(len(result.urls) for result in test_results if hasattr(result, 'urls'))
        logger.info(f"✅ Test completed successfully")
        logger.info(f"📊 Processed {len(test_results)} search results")
        logger.info(f"📊 Extracted {total_extracted_urls} business URLs")
        
        # Display sample results
        for i, result in enumerate(test_results[:2]):  # Show first 2 results
            if hasattr(result, 'urls') and result.urls:
                logger.info(f"Sample result {i+1}: {len(result.urls)} URLs found")
                for url_info in result.urls[:3]:
                    title = url_info.title if hasattr(url_info, 'title') else 'N/A'
                    url = url_info.url if hasattr(url_info, 'url') else 'N/A'
                    logger.info(f"  - {title}: {url}")
        
    except Exception as main_execution_error:
        logger.error(f"❌ Main execution failed: {str(main_execution_error)}")
        logger.debug(f"Main error traceback: {traceback.format_exc()}")
        sys.exit(1)