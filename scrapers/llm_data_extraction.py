"""
Large Language Model Data Extraction Module

This module provides functionality for extracting structured data from web content
using LLM services. It supports both direct API calls and Crawl4AI-based extraction
with comprehensive error handling and retry mechanisms.

Enhanced to handle multiple schema types (Website and Search extraction).

Classes:
    ExtractionConfig: Configuration for extraction parameters
    Crawl4AIConfig: Configuration for Crawl4AI web crawler
    LLMDataExtractor: Main class for LLM-based data extraction

Author: Mr. Anas
Created: 5/30/2025
Updated: Enhanced for multi-schema support
"""

import os
import sys
import json
import asyncio
import random
import logging
import traceback
from typing import Dict, List, Any, Optional, Union, Type
from dataclasses import dataclass, field

import litellm
from pydantic import BaseModel, ValidationError

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from logs.custom_logging import setup_logging
from utils.helpers import save_debug_files, load_debug_files
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from settings import (
    WEBSITES_DATA_EXTRACTION_PROMPT, 
    SEARCH_RESULTS_EXTRACTION_PROMPT,
    LLM_CONFIG as default_llm_config
)
from schemas.website_schema import WebsiteExtractionResult
from schemas.search_schema import SearchExtractionResult


# Initialize module logger
logger = setup_logging(console_level=logging.DEBUG)


# =============================================================================
# Configuration Classes
# =============================================================================

@dataclass
class ExtractionConfig:
    """
    Configuration parameters for LLM data extraction operations.
    
    Attributes:
        max_batch_size: Maximum number of items to process in a single batch
        max_retry_attempts: Maximum number of retry attempts for failed extractions
        retry_delay_seconds: Base delay between retry attempts in seconds
        enable_exponential_backoff: Whether to use exponential backoff for retries
    """
    max_batch_size: int = 5
    max_retry_attempts: int = 2
    retry_delay_seconds: float = 1.0
    enable_exponential_backoff: bool = True


@dataclass
class Crawl4AIConfig:
    """
    Configuration for Crawl4AI web crawler instances.
    
    Attributes:
        browser_config: Browser-specific configuration settings
        crawler_run_config: Runtime configuration for crawler operations
    """
    browser_config: BrowserConfig = field(
        default_factory=lambda: BrowserConfig(headless=False)
    )
    crawler_run_config: CrawlerRunConfig = field(
        default_factory=lambda: CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    )


# =============================================================================
# Main LLM Data Extraction Class
# =============================================================================

class LLMDataExtractor:
    """
    Large Language Model Data Extraction Service.
    
    This class provides comprehensive functionality for extracting structured data
    from web content using LLM services. It supports multiple extraction methods,
    automatic retries, batch processing, and robust error handling.
    
    Enhanced to handle multiple schema types (Website and Search extraction).
    
    Supported extraction methods:
    - Direct API calls to LLM services
    - Crawl4AI-based extraction with advanced strategies
    
    Attributes:
        input_data_list: List of input data items for processing
        llm_configuration: Configuration for LLM service connection
        validation_schema: Pydantic schema class for output validation
        extraction_prompt: System prompt for LLM instructions
        extraction_config: Configuration for extraction parameters
        crawl4ai_config: Configuration for Crawl4AI operations
        schema_type: Type of schema being used ('website' or 'search')
    """
    
    def __init__(
        self,
        input_data_list: List[Dict[str, Any]],
        llm_configuration: Dict[str, Any],
        validation_schema: Type[BaseModel],
        extraction_prompt: str,
        extraction_config: ExtractionConfig = None,
        schema_type: str = 'website'
    ) -> None:
        """
        Initialize the LLM data extraction service.
        
        Args:
            input_data_list: List of input data dictionaries to process
            llm_configuration: LLM service configuration dictionary
            validation_schema: Pydantic schema class for validating extracted data
            extraction_prompt: System prompt with extraction instructions
            extraction_config: Optional configuration for extraction parameters
            schema_type: Type of schema ('website' or 'search')
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate required parameters
        if not input_data_list:
            raise ValueError("Input data list cannot be empty")
        if not extraction_prompt.strip():
            raise ValueError("Extraction prompt cannot be empty")
        if schema_type not in ['website', 'search']:
            raise ValueError("Schema type must be 'website' or 'search'")
            
        self.input_data_list = input_data_list
        self.llm_configuration = llm_configuration
        self.validation_schema = validation_schema
        self.extraction_prompt = extraction_prompt
        self.extraction_config = extraction_config or ExtractionConfig()
        self.crawl4ai_config = Crawl4AIConfig()
        self.schema_type = schema_type
        
        logger.info(f"Initialized LLMDataExtractor with {len(input_data_list)} input items")
     

    def _create_standardized_error_response(
        self, 
        error_reason: str, 
        source_url: str = ""
    ) -> Dict[str, Any]:
        """
        Create a standardized error response structure for failed extractions.
        
        This method ensures consistent error reporting across different extraction
        methods and failure scenarios, adapting to the schema type.
        
        Args:
            error_reason: Descriptive reason for the extraction failure
            source_url: URL associated with the failed extraction (if available)
            
        Returns:
            Dictionary containing standardized error structure with metadata
        """
        if self.schema_type == 'website':
            return {
                "metadata": {
                    "source": {
                        "name": "ExtractionError",
                        "url": source_url,
                        "type": "Error",
                        "summary": f"Data extraction failed: {error_reason}"
                    },
                    "result": {
                        "success": False,
                        "entities_found": 0,
                        "error": "ExtractionError",
                        "error_details": error_reason
                    },
                    "relevant_urls": []
                },
                "entities": []
            }
        else:  # search schema
            return {
                "metadata": {
                    "context": {
                        "query": "unknown",
                        "url": source_url,
                        "results": 0
                    },
                    "result": {
                        "success": False,
                        "urls_found": 0,
                        "error": "ExtractionError",
                        "error_details": error_reason
                    }
                },
                "urls": []
            }

    async def _extract_via_direct_api(
        self, 
        content_text: str, 
        source_url: str = ""
    ) -> Dict[str, Any]:
        """
        Extract structured data using direct LLM API calls.
        
        This method bypasses Crawl4AI and directly communicates with the LLM
        service for data extraction. It includes comprehensive error handling
        and response validation.
        
        Args:
            content_text: Raw text content to process and extract data from
            source_url: Source URL for context and error reporting
            
        Returns:
            Dictionary containing extracted data or error information
            
        Raises:
            Exception: Re-raises unexpected exceptions after logging
        """
        logger.debug(f"Starting direct API extraction for URL: '{source_url}'")
        
        try:
            # Make async API call to LLM service
            api_response = await litellm.acompletion(
                model=self.llm_configuration.get('provider'),
                api_key=self.llm_configuration.get('api_token'),
                messages=[
                    {"role": "system", "content": self.extraction_prompt},
                    {"role": "user", "content": content_text}
                ],
                response_format={
                    "type": "json_object",
                    "schema": self.validation_schema.model_json_schema(),
                }
            )

            # Extract and validate response content
            raw_response_content = api_response.choices[0].message.content
            
            try:
                # Parse JSON response
                parsed_response = json.loads(raw_response_content)
                
                # Validate against Pydantic schema
                validated_response = self.validation_schema(**parsed_response)
                
                logger.info(f"✅ Successfully extracted data via direct API for URL: {source_url}")
                return validated_response.model_dump()
                
            except (json.JSONDecodeError, ValidationError) as validation_error:
                error_message = f"Response validation failed: {str(validation_error)}"
                logger.error(error_message)
                logger.debug(f"Raw API response preview: {raw_response_content[:500]}...")
                return self._create_standardized_error_response(error_message, source_url)
                
        except Exception as api_error:
            error_message = f"Direct API request failed: {str(api_error)}"
            logger.error(error_message)
            logger.debug(f"API error traceback: {traceback.format_exc()}")
            return self._create_standardized_error_response(error_message, source_url)
    
    async def _extract_via_crawl4ai(
        self, 
        input_data_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured data using Crawl4AI's LLM extraction strategy.
        
        This method leverages Crawl4AI's advanced extraction capabilities,
        including chunking, retry logic, and specialized LLM strategies.
        
        Args:
            input_data_item: Dictionary containing URL and content data
            
        Returns:
            Dictionary containing extracted data or error information
        """
        # Extract URL for logging and error reporting
        source_url = next(iter(input_data_item.keys())) if input_data_item else "unknown"
        logger.info(f"Starting Crawl4AI extraction for URL: '{source_url}'")

        try:
            # Configure LLM extraction strategy
            llm_extraction_strategy = LLMExtractionStrategy(
                llm_config=LLMConfig(
                    provider=self.llm_configuration.get('provider'),
                    api_token=self.llm_configuration.get('api_token'),
                ),
                schema=self.validation_schema.model_json_schema(),
                extraction_type="schema",
                instruction=self.extraction_prompt,
                force_json_response=True,
                apply_chunking=True,
                verbose=False
            )
            
            # Create crawler run configuration
            crawler_run_config = self.crawl4ai_config.crawler_run_config.clone(
                extraction_strategy=llm_extraction_strategy,
            )
            
        except Exception as config_error:
            error_message = f"Extraction strategy configuration failed: {str(config_error)}"
            logger.error(error_message)
            return self._create_standardized_error_response(error_message, source_url)

        # Execute extraction with retry logic
        async with AsyncWebCrawler(config=self.crawl4ai_config.browser_config) as crawler:
            for attempt_number in range(self.extraction_config.max_retry_attempts + 1):
                try:
                    # Execute crawl and extraction
                    extraction_result = await crawler.arun(
                        url=f"raw://{json.dumps(input_data_item)}",
                        config=crawler_run_config,
                    )
                    
                    # Check extraction success
                    if extraction_result.success and extraction_result.extracted_content:
                        return await self._process_extraction_result(
                            extraction_result.extracted_content, 
                            source_url
                        )
                    else:
                        # Handle extraction failure
                        error_message = (
                            extraction_result.error_message 
                            if extraction_result 
                            else "No extraction result returned"
                        )
                        logger.warning(f"Extraction attempt {attempt_number + 1} failed: {error_message}")
                        
                        # Retry logic
                        if attempt_number < self.extraction_config.max_retry_attempts:
                            retry_delay = self._calculate_retry_delay(attempt_number)
                            logger.info(
                                f"Retrying in {retry_delay:.1f}s "
                                f"(attempt {attempt_number + 1}/{self.extraction_config.max_retry_attempts})"
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                            
                        return self._create_standardized_error_response(
                            f"All extraction attempts failed: {error_message}", 
                            source_url
                        )
                        
                except Exception as extraction_error:
                    error_message = f"Unexpected extraction error: {str(extraction_error)}"
                    logger.error(error_message)
                    logger.debug(f"Extraction error traceback: {traceback.format_exc()}")
                    return self._create_standardized_error_response(error_message, source_url)

    async def _process_extraction_result(
        self, 
        extracted_content: str, 
        source_url: str
    ) -> Dict[str, Any]:
        """
        Process and validate extracted content from Crawl4AI.
        
        Args:
            extracted_content: Raw extracted content string
            source_url: Source URL for error reporting
            
        Returns:
            Dictionary containing processed and validated data
        """
        try:
            parsed_content = json.loads(extracted_content)
            
            # Handle array responses (take first element if it contains our structure)
            if isinstance(parsed_content, list):
                if parsed_content:
                    first_item = parsed_content[0]
                    # Check for either website or search schema structure
                    if self._is_valid_schema_structure(first_item):
                        parsed_content = first_item
                        logger.debug("Processed array response by selecting first valid element")
                    else:
                        error_message = "Invalid array structure in LLM response"
                        logger.error(error_message)
                        logger.debug(f"Response preview: {extracted_content[:500]}...")
                        return self._create_standardized_error_response(error_message, source_url)
                else:
                    error_message = "Empty array received from LLM"
                    logger.warning(error_message)
                    return self._create_standardized_error_response(error_message, source_url)
            
            # Validate against schema
            validated_content = self.validation_schema(**parsed_content)
            logger.info(f"✅ Successfully extracted and validated data via Crawl4AI for URL: {source_url}")
            
            return validated_content.model_dump()
        
        except (ValidationError, json.JSONDecodeError) as processing_error:
            error_message = f"Content processing failed: {str(processing_error)}"
            logger.error(error_message)
            logger.debug(f"Content preview: {extracted_content[:500]}...")
            return self._create_standardized_error_response(error_message, source_url)

    def _is_valid_schema_structure(self, data: Dict[str, Any]) -> bool:
        """
        Check if the data has the expected structure for the current schema type.
        
        Args:
            data: Dictionary to validate structure
            
        Returns:
            Boolean indicating if structure matches expected schema type
        """
        if self.schema_type == 'website':
            return "metadata" in data and "entities" in data
        else:  # search schema
            return "metadata" in data and "urls" in data
# Add this helper method to check success
    def _is_successful(self, result: Dict[str, Any]) -> bool:
        """Check if extraction result indicates success"""
        metadata = result.get('metadata', {})
        result_info = metadata.get('result', {})
        return result_info.get('success', False)


    async def _process_extraction_batch(
        self, 
        data_batch: List[Dict[str, Any]], 
        extraction_method: str
    ) -> List[Dict[str, Any]]:
        """
        Process batch with automatic method fallback
        """
        async def process_item(data_item: Dict[str, Any]) -> Dict[str, Any]:
            """Process single item with fallback logic"""
            source_url = next(iter(data_item.keys())) if data_item else "unknown"
            
            # First try with primary method
            if extraction_method == 'crawl4ai':
                result = await self._extract_via_crawl4ai(data_item)
                if self._is_successful(result):
                    return result
                else:
                    logger.warning(f"❌ Crawl4ai method failed for {source_url}. Trying direct API...")
                    return await self._extract_via_direct_api(str(data_item), source_url)
            else:  # direct method
        
                result = await self._extract_via_direct_api(str(data_item), source_url)
                if self._is_successful(result):
                    return result
                else:
                    logger.warning(f"❌ Direct API failed for {source_url}. Trying Crawl4ai...")
                    return await self._extract_via_crawl4ai(data_item)
        
        # Process all items concurrently
        tasks = [process_item(item) for item in data_batch]
        return await asyncio.gather(*tasks)


    async def execute_data_extraction(
        self, 
        extraction_method: str = 'crawl4ai'
    ) -> List[Dict[str, Any]]:
        """
        Execute the complete data extraction process.
        
        This is the main entry point for data extraction. It processes all input
        data in batches, handles errors gracefully, and provides comprehensive
        progress reporting.
        
        Args:
            extraction_method: Method to use ('direct' or 'crawl4ai')
            
        Returns:
            List of extraction results with success/failure information
            
        Raises:
            ValueError: If extraction method is not supported
        """
        # Validate extraction method
        supported_methods = ['direct', 'crawl4ai']
        if extraction_method not in supported_methods:
            raise ValueError(f"Unsupported extraction method: {extraction_method}. "
                           f"Supported methods: {supported_methods}")
        
        # Validate input data
        if not self.input_data_list:
            logger.error("No input data available for extraction")
            return [self._create_standardized_error_response("No input data provided")]
        
        extraction_results = []
        total_items = len(self.input_data_list)
        
        logger.info(f"Starting extraction of {total_items} items using method: {extraction_method}")
        logger.info(f"Schema type: {self.schema_type}")
        
        # Process data in batches
        for batch_start_index in range(0, total_items, self.extraction_config.max_batch_size):
            # Create current batch
            batch_end_index = batch_start_index + self.extraction_config.max_batch_size
            current_batch = self.input_data_list[batch_start_index:batch_end_index]
            
            # Calculate batch information
            current_batch_number = (batch_start_index // self.extraction_config.max_batch_size) + 1
            total_batches = (total_items - 1) // self.extraction_config.max_batch_size + 1
            
            logger.info(
                f"Processing batch {current_batch_number}/{total_batches} "
                f"with {len(current_batch)} items"
            )
            
            try:
                # Process current batch
                batch_results = await self._process_extraction_batch(current_batch, extraction_method)
                extraction_results.extend(batch_results)
                
                # Add inter-batch delay to avoid rate limiting
                if batch_start_index + self.extraction_config.max_batch_size < total_items:
                    inter_batch_delay = random.uniform(0.5, 1.5)
                    logger.debug(f"Inter-batch delay: {inter_batch_delay:.2f}s")
                    await asyncio.sleep(inter_batch_delay)
                    
            except Exception as batch_error:
                error_message = f"Batch {current_batch_number} processing failed: {str(batch_error)}"
                logger.error(error_message)
                logger.debug(f"Batch error traceback: {traceback.format_exc()}")
                
                # Create error entries for each item in the failed batch
                for batch_item in current_batch:
                    item_url = next(iter(batch_item.keys())) if batch_item else "unknown"
                    extraction_results.append(
                        self._create_standardized_error_response(error_message, item_url)
                    )
        
        # Calculate and log success metrics
        successful_extractions = self._count_successful_extractions(extraction_results)
        total_results = len(extraction_results)
        success_rate = (successful_extractions / total_results * 100) if total_results > 0 else 0
        
        logger.info(f"✅ Extraction completed. Total results: {total_results}")
        logger.info(f"📊 Success rate: {success_rate:.1f}% ({successful_extractions}/{total_results})")
        
        # Debug output (truncated)
        results_json = json.dumps(extraction_results, indent=2)
        if len(results_json) > 1000:
            logger.debug(f"Results preview: {results_json[:1000]}...")
        else:
            logger.debug(f"Complete results: {results_json}")
        
        return extraction_results

    def _count_successful_extractions(self, results: List[Dict[str, Any]]) -> int:
        """
        Count successful extractions based on schema type.
        
        Args:
            results: List of extraction results
            
        Returns:
            Number of successful extractions
        """
        successful_count = 0
        for result in results:
            metadata = result.get('metadata', {})
            if self.schema_type == 'website':
                success = metadata.get('result', {}).get('success', False)
            else:  # search schema
                success = metadata.get('result', {}).get('success', False)
            
            if success:
                successful_count += 1
        
        return successful_count


# =============================================================================
# Convenience Functions
# =============================================================================

def create_website_extractor(
    input_data_list: List[Dict[str, Any]],
    llm_configuration: Dict[str, Any] = None,
    extraction_config: ExtractionConfig = None
) -> LLMDataExtractor:
    """
    Create a configured LLMDataExtractor for website extraction.
    
    Args:
        input_data_list: List of input data items
        llm_configuration: LLM configuration (uses default if None)
        extraction_config: Extraction configuration (uses default if None)
        
    Returns:
        Configured LLMDataExtractor instance
    """
    return LLMDataExtractor(
        input_data_list=input_data_list,
        llm_configuration=llm_configuration or default_llm_config,
        validation_schema=WebsiteExtractionResult,
        extraction_prompt=WEBSITES_DATA_EXTRACTION_PROMPT,
        extraction_config=extraction_config,
        schema_type='website'
    )


def create_search_extractor(
    input_data_list: List[Dict[str, Any]],
    llm_configuration: Dict[str, Any] = None,
    extraction_config: ExtractionConfig = None
) -> LLMDataExtractor:
    """
    Create a configured LLMDataExtractor for search result extraction.
    
    Args:
        input_data_list: List of input data items
        llm_configuration: LLM configuration (uses default if None)
        extraction_config: Extraction configuration (uses default if None)
        
    Returns:
        Configured LLMDataExtractor instance
    """
    return LLMDataExtractor(
        input_data_list=input_data_list,
        llm_configuration=llm_configuration or default_llm_config,
        validation_schema=SearchExtractionResult,
        extraction_prompt=SEARCH_RESULTS_EXTRACTION_PROMPT,
        extraction_config=extraction_config,
        schema_type='search'
    )


# =============================================================================
# Main Execution Block
# =============================================================================

if __name__ == "__main__":
    """
    Main execution block for testing and development.
    
    This block demonstrates how to use the LLMDataExtractor class
    with sample data and configurations for both schema types.
    """
    try:
        # Load configuration and test data
        test_input_data = load_debug_files('debug_files/website_scraping/temp_processed_data.json')
        
        # Test website extraction
        logger.info("🚀 Testing website extraction...")
        website_extractor = create_website_extractor(
            input_data_list=test_input_data,  # Test with first 2 items
            extraction_config=ExtractionConfig(
                max_batch_size=2, 
                max_retry_attempts=1
            )
        )
        
        website_results = asyncio.run(
            website_extractor.execute_data_extraction(extraction_method='crawl4ai')
        )
        
        logger.info(f"Website extraction completed. Results: {len(website_results)}")
        
        # Uncomment to test search extraction with appropriate data
        # logger.info("🔍 Testing search extraction...")
        # search_extractor = create_search_extractor(
        #     input_data_list=search_test_data,
        #     extraction_config=ExtractionConfig(max_batch_size=1)
        # )
        # 
        # search_results = asyncio.run(
        #     search_extractor.execute_data_extraction(extraction_method='crawl4ai')
        # )
        
        # Save results for debugging
        save_debug_files(website_scraped_content=website_results)
        logger.info("✅ Extraction completed successfully and results saved")
        
    except Exception as main_error:
        logger.error(f"❌ Main execution failed: {str(main_error)}")
        logger.debug(f"Main error traceback: {traceback.format_exc()}")
        sys.exit(1)