"""
Website Scraping and Data Extraction Module

This module provides comprehensive functionality for scraping multiple websites
and extracting structured data using LLM services. It supports both direct HTTP
requests and Crawl4AI-based scraping with robust error handling, retry mechanisms,
and comprehensive logging.

Enhanced to integrate with the improved LLM data extraction system with
standardized configurations, better error handling, and consistent styling.

Classes:
    WebsiteScrapingConfig: Configuration for website scraping parameters
    WebsitesScraping: Main class for website scraping and data extraction

Author: Mr. Anas
Created: Original implementation
Updated: Enhanced for improved LLM integration and consistency
"""

import os
import sys
import asyncio
import time
import traceback
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from logs.custom_logging import setup_logging
from utils.helpers import HtmlPageScraper, HTMLContentProcessor, save_debug_files, save_output_data
from scrapers.llm_data_extraction import create_website_extractor, ExtractionConfig
from settings import LLM_CONFIG as default_llm_config


# Initialize module logger
logger = setup_logging(console_level=logging.DEBUG)


# =============================================================================
# Configuration Classes
# =============================================================================

@dataclass
class WebsiteScrapingConfig:
    """
    Configuration parameters for website scraping operations.
    
    Attributes:
        min_html_length: Minimum HTML content length to consider valid
        max_concurrent_requests: Maximum number of concurrent scraping requests
        request_delay_seconds: Delay between consecutive requests
        browser_config: Browser configuration for Crawl4AI
        crawler_run_config: Runtime configuration for Crawl4AI crawler
        extraction_config: Configuration for LLM data extraction
    """
    min_html_length: int = 20000
    max_concurrent_requests: int = 5
    request_delay_seconds: float = 1.0
    
    browser_config: BrowserConfig = field(
        default_factory=lambda: BrowserConfig(headless=False)
    )
    
    crawler_run_config: CrawlerRunConfig = field(
        default_factory=lambda: CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            scan_full_page=True,
            scroll_delay=0.5,
            delay_before_return_html=5
        )
    )
    
    extraction_config: ExtractionConfig = field(
        default_factory=lambda: ExtractionConfig(
            max_batch_size=3,
            max_retry_attempts=2,
            retry_delay_seconds=1.0,
            enable_exponential_backoff=True
        )
    )


# =============================================================================
# Main Website Scraping Class
# =============================================================================

class WebsitesScraping:
    """
    Website Scraping and Data Extraction Service.
    
    This class provides comprehensive functionality for scraping multiple websites
    and extracting structured data using LLM services. It supports both direct
    HTTP requests and Crawl4AI-based scraping with robust error handling,
    retry mechanisms, and comprehensive logging.
    
    Enhanced to integrate with the improved LLM data extraction system.
    
    Supported scraping methods:
    - Direct HTTP requests with custom headers and error handling
    - Crawl4AI-based scraping with advanced browser automation
    
    Attributes:
        urls: List of URLs to scrape
        scraping_method: Method to use for scraping ('direct' or 'crawl4ai')
        llm_configuration: Configuration for LLM service connection
        config: Configuration for scraping parameters
        html_scraper: Direct HTML scraper instance
        html_processor: HTML content processor instance
    """
    
    def __init__(
        self,
        urls: List[str],
        scraping_method: str = 'direct',
        llm_configuration: Dict[str, Any] = None,
        scraping_config: WebsiteScrapingConfig = None
    ) -> None:
        """
        Initialize the website scraping service.
        
        Args:
            urls: List of URLs to scrape and process
            scraping_method: Scraping method ('direct' or 'crawl4ai')
            llm_configuration: LLM service configuration dictionary
            scraping_config: Optional configuration for scraping parameters
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate input parameters
        if not urls:
            raise ValueError("URLs list cannot be empty")
        if not all(isinstance(url, str) and url.strip() for url in urls):
            raise ValueError("All URLs must be non-empty strings")
        
        # Validate scraping method
        supported_methods = ['direct', 'crawl4ai']
        if scraping_method.strip().lower() not in supported_methods:
            raise ValueError(f"Unsupported scraping method: {scraping_method}. "
                           f"Supported methods: {supported_methods}")
        
        self.urls = [url.strip() for url in urls]
        self.scraping_method = scraping_method.strip().lower()
        self.llm_configuration = llm_configuration or default_llm_config
        self.config = scraping_config or WebsiteScrapingConfig()
        
        # Initialize scraping utilities
        self.html_scraper = HtmlPageScraper()
        self.html_processor = HTMLContentProcessor()
        
        logger.info(f"Initialized WebsitesScraping with {len(self.urls)} URLs")
        logger.info(f"Scraping method: {self.scraping_method}")
        logger.info(f"URLs to process: {[self._get_domain_from_url(url) for url in self.urls]}")

    def _get_domain_from_url(self, url: str) -> str:
        """
        Extract domain from URL for logging and identification.
        
        Args:
            url: Full URL string
            
        Returns:
            Domain name extracted from URL
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url

    def _create_error_response(
        self,
        url: str,
        error_message: str,
        status_code: Optional[int] = None,
        html_content: str = ""
    ) -> Dict[str, Any]:
        """
        Create a standardized error response for failed scraping operations.
        
        Args:
            url: URL that failed to scrape
            error_message: Descriptive error message
            status_code: HTTP status code (if available)
            html_content: Partial HTML content (if any)
            
        Returns:
            Dictionary containing standardized error structure
        """
        error_data = {
            'message': error_message,
            'status_code': status_code,
            'url': url,
            'domain': self._get_domain_from_url(url),
            'error_type': 'ScrapingError',
            'timestamp': time.time()
        }
        
        if html_content:
            # Process available HTML content even for errors
            try:
                cleaned_html = self.html_processor.clean_html(html_content)
                error_data['cleaned_html'] = cleaned_html
                logger.debug(f"Processed partial HTML content for error response: {url}")
            except Exception as processing_error:
                logger.warning(f"Failed to process error HTML content: {processing_error}")
                error_data['cleaned_html'] = html_content[:1000] + "..." if len(html_content) > 1000 else html_content
        
        return {url: error_data}

    async def _scrape_single_url_direct(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single URL using direct HTTP requests.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing scraped data or error information
        """
        domain = self._get_domain_from_url(url)
        logger.debug(f"Starting direct scraping for: {domain}")
        
        try:
            # Make HTTP request
            raw_html, status_code = await self.html_scraper.request_html(url=url)
            
            # Validate response
            if not raw_html:
                error_message = f"No HTML content returned for '{domain}'. Status code: {status_code}"
                logger.warning(f"❌ {error_message}")
                return self._create_error_response(url, error_message, status_code)
            
            # Check content length and status
            if status_code == 200 and len(raw_html) >= self.config.min_html_length:
                # Process successful response
                cleaned_data = self.html_processor.get_llm_friendly_content(raw_html=raw_html)
                logger.info(f"✅ Successfully scraped '{domain}' - HTML length: {len(raw_html):,}")
                return {url: cleaned_data}
            else:
                # Handle short content or non-200 status
                error_message = (
                    f"Content validation failed for '{domain}'. "
                    f"Status: {status_code}, HTML length: {len(raw_html):,} "
                    f"(minimum required: {self.config.min_html_length:,})"
                )
                logger.warning(f"⚠️ {error_message}")
                return self._create_error_response(url, error_message, status_code, raw_html)
                
        except Exception as scraping_error:
            error_message = f"Unexpected error during direct scraping of '{domain}': {str(scraping_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Direct scraping error traceback: {traceback.format_exc()}")
            return self._create_error_response(url, error_message)

    async def _scrape_single_url_crawl4ai(self, crawler: AsyncWebCrawler, url: str) -> Dict[str, Any]:
        """
        Process a single Crawl4AI result.
        
        Args:
            crawler: AsyncWebCrawler instance (not used directly but kept for consistency)
            url: URL being processed
            
        Returns:
            Dictionary containing processed data or error information
        """
        # This method will be called from the batch processing
        # The actual crawling is done in scrape_with_crawl4ai
        pass

    async def _process_crawl4ai_result(self, result) -> Dict[str, Any]:
        """
        Process a single Crawl4AI scraping result.
        
        Args:
            result: Crawl4AI result object
            
        Returns:
            Dictionary containing processed data or error information
        """
        url = str(result.url)
        domain = self._get_domain_from_url(url)
        
        try:
            # Check if scraping was successful
            if result.success and len(result.html) >= self.config.min_html_length:
                # Process successful result
                raw_html = result.html
                markdown = getattr(result, 'markdown', '')
                
                logger.info(f"✅ Successfully scraped '{domain}' - HTML length: {len(raw_html):,}")
                
                # Process content for LLM
                cleaned_data = self.html_processor.get_llm_friendly_content(
                    raw_html=raw_html,
                    markdown=markdown
                )
                return {url: cleaned_data}
            else:
                # Handle failed or insufficient content
                error_message = (
                    f"Crawl4AI scraping failed for '{domain}'. "
                    f"Success: {result.success}, Status: {result.status_code}, "
                    f"HTML length: {len(result.html):,} "
                    f"(minimum required: {self.config.min_html_length:,}), "
                    f"Error: {result.error_message}"
                )
                logger.warning(f"⚠️ {error_message}")
                
                return self._create_error_response(
                    url,
                    error_message,
                    result.status_code,
                    getattr(result, 'cleaned_html', result.html) if hasattr(result, 'html') else ""
                )
                
        except Exception as processing_error:
            error_message = f"Error processing Crawl4AI result for '{domain}': {str(processing_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Crawl4AI processing error traceback: {traceback.format_exc()}")
            return self._create_error_response(url, error_message)

    async def scrape_with_crawl4ai(self) -> List[Dict[str, Any]]:
        """
        Scrape multiple websites using Crawl4AI with advanced browser automation.
        
        Returns:
            List of dictionaries containing scraped data or error information
            
        Raises:
            Exception: Re-raises unexpected exceptions after logging
        """
        logger.info(f"Starting Crawl4AI scraping for {len(self.urls)} URLs")
        
        try:
            async with AsyncWebCrawler(config=self.config.browser_config) as crawler:
                # Execute batch scraping
                crawl_results = await crawler.arun_many(
                    urls=self.urls,
                    config=self.config.crawler_run_config
                )
                
                # Process all results
                processed_results = await asyncio.gather(*[
                    self._process_crawl4ai_result(result) for result in crawl_results
                ])
                
                # Log summary
                successful_scrapes = sum(1 for result in processed_results 
                                       if not any('error_type' in str(v) for v in result.values()))
                logger.info(f"Crawl4AI scraping completed - Success: {successful_scrapes}/{len(processed_results)}")
                
                return processed_results
                
        except Exception as crawl4ai_error:
            error_message = f"Crawl4AI scraping operation failed: {str(crawl4ai_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Crawl4AI error traceback: {traceback.format_exc()}")
            
            # Return error responses for all URLs
            return [self._create_error_response(url, error_message) for url in self.urls]

    async def scrape_with_direct_requests(self) -> List[Dict[str, Any]]:
        """
        Scrape multiple websites using direct HTTP requests with concurrency control.
        
        Returns:
            List of dictionaries containing scraped data or error information
        """
        logger.info(f"Starting direct HTTP scraping for {len(self.urls)} URLs")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def scrape_with_semaphore(url: str) -> Dict[str, Any]:
            """Wrapper to control concurrent requests."""
            async with semaphore:
                result = await self._scrape_single_url_direct(url)
                
                # Add delay between requests to avoid overwhelming servers
                if self.config.request_delay_seconds > 0:
                    await asyncio.sleep(self.config.request_delay_seconds)
                
                return result
        
        try:
            # Execute concurrent scraping with limits
            processed_results = await asyncio.gather(*[
                scrape_with_semaphore(url) for url in self.urls
            ])
            
            # Log summary
            successful_scrapes = sum(1 for result in processed_results 
                                   if not any('error_type' in str(v) for v in result.values()))
            logger.info(f"Direct scraping completed - Success: {successful_scrapes}/{len(processed_results)}")
            
            return processed_results
            
        except Exception as direct_error:
            error_message = f"Direct scraping operation failed: {str(direct_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Direct scraping error traceback: {traceback.format_exc()}")
            
            # Return error responses for all URLs
            return [self._create_error_response(url, error_message) for url in self.urls]

    async def scrape_multiple_websites(self) -> List[Dict[str, Any]]:
        """
        Execute website scraping using the configured method.
        
        This is the main entry point for scraping operations. It delegates
        to the appropriate scraping method and handles results consistently.
        
        Returns:
            List of dictionaries containing scraped data or error information
            
        Raises:
            ValueError: If scraping method is not supported
        """
        if not self.urls:
            logger.error("No URLs provided for scraping")
            return []
        
        logger.info(f"🚀 Starting website scraping using method: {self.scraping_method}")
        start_time = time.time()
        
        try:
            # Execute scraping based on method
            if self.scraping_method == 'crawl4ai':
                results = await self.scrape_with_crawl4ai()
            elif self.scraping_method == 'direct':
                results = await self.scrape_with_direct_requests()
            else:
                raise ValueError(f"Unsupported scraping method: {self.scraping_method}")
            
            # Calculate timing and save debug files
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Scraping completed in {elapsed_time:.2f} seconds")
            
            # Save debug files for analysis
            save_debug_files(website_scraped_content=results)
            logger.debug("Debug files saved successfully")
            
            return results
            
        except Exception as scraping_error:
            elapsed_time = time.time() - start_time
            error_message = f"Website scraping failed after {elapsed_time:.2f} seconds: {str(scraping_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Scraping error traceback: {traceback.format_exc()}")
            
            # Return error responses for all URLs
            return [self._create_error_response(url, error_message) for url in self.urls]

    async def scrape_and_extract_data(
        self,
        extraction_method: str = 'crawl4ai',
        save_results: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Complete pipeline: scrape websites and extract structured data using LLM.
        
        This method combines website scraping with LLM-based data extraction
        to provide a complete end-to-end solution for structured data extraction
        from websites.
        
        Args:
            extraction_method: LLM extraction method ('direct' or 'crawl4ai')
            save_results: Whether to save results to output files
            
        Returns:
            List of extracted structured data or error information
            
        Raises:
            Exception: Re-raises unexpected exceptions after logging
        """
        logger.info("🚀 Starting complete scrape-and-extract pipeline")
        pipeline_start_time = time.time()
        
        try:
            # Step 1: Scrape websites
            logger.info("📡 Phase 1: Website scraping")
            scraped_data = await self.scrape_multiple_websites()
            
            if not scraped_data:
                logger.error("No scraped data available for extraction")
                return []
            
            # Filter out error responses for LLM processing
            valid_scraped_data = [
                data for data in scraped_data
                if not any('error_type' in str(v) for v in data.values())
            ]
            
            logger.info(f"Valid scraped data for LLM processing: {len(valid_scraped_data)}/{len(scraped_data)}")
            
            if not valid_scraped_data:
                logger.warning("No valid scraped data available for LLM extraction")
                return scraped_data  # Return original data with errors
            
            # Step 2: Extract structured data using LLM
            logger.info("🤖 Phase 2: LLM data extraction")
            llm_extractor = create_website_extractor(
                input_data_list=valid_scraped_data,
                llm_configuration=self.llm_configuration,
                extraction_config=self.config.extraction_config
            )
            
            extracted_data = await llm_extractor.execute_data_extraction(
                extraction_method=extraction_method
            )
            
            # Step 3: Save results if requested
            if save_results and extracted_data:
                save_output_data(output_data=extracted_data)
                logger.info("📁 Results saved to output files")
            
            # Calculate and log pipeline metrics
            pipeline_elapsed_time = time.time() - pipeline_start_time
            successful_extractions = sum(
                1 for result in extracted_data
                if result.get('metadata', {}).get('result', {}).get('success', False)
            )
            
            logger.info(
                f"✅ Complete pipeline finished in {pipeline_elapsed_time:.2f} seconds. "
                f"Successful extractions: {successful_extractions}/{len(extracted_data)}"
            )
            
            return extracted_data
            
        except Exception as pipeline_error:
            pipeline_elapsed_time = time.time() - pipeline_start_time
            error_message = f"Pipeline failed after {pipeline_elapsed_time:.2f} seconds: {str(pipeline_error)}"
            logger.error(f"❌ {error_message}")
            logger.debug(f"Pipeline error traceback: {traceback.format_exc()}")
            raise


# =============================================================================
# Convenience Functions
# =============================================================================

def create_website_scraper(
    urls: List[str],
    scraping_method: str = 'direct',
    llm_configuration: Dict[str, Any] = None,
    min_html_length: int = 20000,
    max_concurrent_requests: int = 5
) -> WebsitesScraping:
    """
    Create a configured WebsitesScraping instance with common parameters.
    
    Args:
        urls: List of URLs to scrape
        scraping_method: Scraping method ('direct' or 'crawl4ai')
        llm_configuration: LLM configuration (uses default if None)
        min_html_length: Minimum HTML content length
        max_concurrent_requests: Maximum concurrent requests for direct method
        
    Returns:
        Configured WebsitesScraping instance
    """
    config = WebsiteScrapingConfig(
        min_html_length=min_html_length,
        max_concurrent_requests=max_concurrent_requests
    )
    
    return WebsitesScraping(
        urls=urls,
        scraping_method=scraping_method,
        llm_configuration=llm_configuration,
        scraping_config=config
    )


# =============================================================================
# Main Execution Block
# =============================================================================

if __name__ == "__main__":
    """
    Main execution block for testing and development.
    
    This block demonstrates how to use the WebsitesScraping class
    with sample URLs and different scraping methods.
    """
    # Sample URLs for testing
    test_urls = [
        "https://paginasamarillas.com.do/en/business/search/republica-dominicana/c/directorios-telefonicos-y-guias",
        "http://www.hoteltoachi.com/"
    ]
    
    async def run_scraping_test(method: str) -> List[Dict[str, Any]]:
        """
        Run scraping test with specified method.
        
        Args:
            method: Scraping method to test
            
        Returns:
            List of extraction results
        """
        logger.info(f"🧪 Testing scraping with method: {method}")
        
        try:
            # Create scraper instance
            scraper = create_website_scraper(
                urls=test_urls,
                scraping_method=method,
                min_html_length=15000,  # Lower threshold for testing
                max_concurrent_requests=3
            )
            
            # Execute complete pipeline
            results = await scraper.scrape_and_extract_data(
                extraction_method='crawl4ai',
                save_results=True
            )
            
            return results
            
        except Exception as test_error:
            logger.error(f"❌ Test execution failed: {str(test_error)}")
            logger.debug(f"Test error traceback: {traceback.format_exc()}")
            return []
    
    # Test different scraping methods
    async def main():
        """Main test execution function."""
        logger.info("🚀 Starting website scraping tests")
        
        # Test direct scraping method
        logger.info("=" * 60)
        logger.info("Testing Direct HTTP Scraping Method")
        logger.info("=" * 60)
        
        start_time = time.time()
        direct_results = await run_scraping_test(method='direct')
        direct_elapsed = time.time() - start_time
        
        logger.info(f"✅ Direct method completed in {direct_elapsed:.2f} seconds")
        logger.info(f"📊 Direct results count: {len(direct_results)}")
        
        # Uncomment to test Crawl4AI method
        # logger.info("=" * 60)
        # logger.info("Testing Crawl4AI Scraping Method")
        # logger.info("=" * 60)
        # 
        # start_time = time.time()
        # crawl4ai_results = await run_scraping_test(method='crawl4ai')
        # crawl4ai_elapsed = time.time() - start_time
        # 
        # logger.info(f"✅ Crawl4AI method completed in {crawl4ai_elapsed:.2f} seconds")
        # logger.info(f"📊 Crawl4AI results count: {len(crawl4ai_results)}")
        
        logger.info("🎉 All tests completed successfully")

    # Run the tests
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Test execution interrupted by user")
    except Exception as main_error:
        logger.error(f"❌ Main execution failed: {str(main_error)}")
        logger.debug(f"Main error traceback: {traceback.format_exc()}")
        sys.exit(1)