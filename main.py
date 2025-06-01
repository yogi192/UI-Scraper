#!/usr/bin/env python3
"""
🤖 AI-Powered Business Data Crawler - Main Controller

A high-performance web scraping and data extraction system for collecting
business information from websites in the Dominican Republic. Built with
advanced async techniques and AI-powered data extraction.

Key Features:
- Website Scraping: Directly extract data from business websites
- Search Scraping: Find business URLs from search results
- Full Pipeline: Automated end-to-end data collection
- AI-Powered: Intelligent data extraction using advanced LLMs
- Flexible: Multiple scraping methods and configuration options
- Robust: Comprehensive error handling and retry mechanisms
- Fast: Concurrent processing and optimized performance

Usage Examples:
1. Basic website scraping:
   python main.py website --urls input/website_urls_list.json

2. Search scraping with custom options:
   python main.py search --terms "restaurants punta cana" \
                        --concurrent 5 \
                        --method crawl4ai

3. Full pipeline with configuration:
   python main.py pipeline --config pipeline_config.json \
                          --debug \
                          --save-raw

4. Help and documentation:
   python main.py --help
   python main.py <command> --help

Author: Mr. Anas
Website: https://github.com/yogi291
Created: June 2023
"""

import os
import sys
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import project modules
import logging
import argparse
from scrapers.websites_scraping import (
    create_website_scraper, 
    WebsiteScrapingConfig,
    WebsitesScraping
)
from scrapers.searches_scraping import (
    create_search_scraper, 
    SearchScrapingConfig,
    SearchResultsScraper
)
from scrapers.claude_advance_searches_generator_exp import (
    AdvancedGoogleSearchGenerator, 
    SearchConfig, 
    SearchType
)
from scrapers.llm_data_extraction import (
    ExtractionConfig,
    Crawl4AIConfig
)
from logs.custom_logging import setup_logging
from utils.helpers import save_output_data
from schemas.search_schema import SearchExtractionResult


# Constants
DEFAULT_CONFIG_FILE = "crawler_config.json"
DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_MAX_CONCURRENT = 3
DEFAULT_BATCH_SIZE = 5
DEFAULT_RETRY_ATTEMPTS = 2


class ScrapeMethod(str, Enum):
    """Supported scraping methods"""
    DIRECT = "direct"
    CRAWL4AI = "crawl4ai"


@dataclass
class CrawlerConfig:
    """Configuration for the AI-powered business data crawler

    This class centralizes all configuration options for the crawler,
    including scraping methods, concurrency settings, input/output paths,
    and other operational parameters.

    Attributes:
        mode: Operation mode (website/search/pipeline)
        method: Scraping method to use (direct/crawl4ai)
        input_file: Path to input file (URLs or search terms)
        output_dir: Directory for saving results
        max_concurrent: Maximum concurrent requests
        batch_size: Number of items per batch
        retry_attempts: Number of retry attempts
        save_raw: Whether to save raw HTML content
        debug: Enable debug logging
        timeout: Request timeout in seconds
        custom_config: Path to custom config file
    """
    mode: str
    method: ScrapeMethod = ScrapeMethod.DIRECT
    input_file: Optional[Path] = None
    output_dir: Path = field(default_factory=lambda: Path(DEFAULT_OUTPUT_DIR))
    max_concurrent: int = DEFAULT_MAX_CONCURRENT
    batch_size: int = DEFAULT_BATCH_SIZE
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    save_raw: bool = False
    debug: bool = False
    timeout: int = 30
    custom_config: Optional[Path] = None

    def __post_init__(self):
        """Validate and process configuration after initialization"""
        # Convert string paths to Path objects
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.input_file, str):
            self.input_file = Path(self.input_file)
        if isinstance(self.custom_config, str):
            self.custom_config = Path(self.custom_config)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load custom config if specified
        if self.custom_config and self.custom_config.exists():
            self._load_custom_config()

    def _load_custom_config(self):
        """Load and apply settings from custom config file"""
        with open(self.custom_config) as f:
            custom_config = json.load(f)
            for key, value in custom_config.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def to_website_config(self) -> WebsiteScrapingConfig:
        """Convert to website scraping configuration"""
        return WebsiteScrapingConfig(
            max_concurrent_requests=self.max_concurrent,
            extraction_config=ExtractionConfig(
                max_batch_size=self.batch_size,
                max_retry_attempts=self.retry_attempts
            )
        )

    def to_search_config(self) -> SearchScrapingConfig:
        """Convert to search scraping configuration"""
        return SearchScrapingConfig(
            max_concurrent_searches=self.max_concurrent,
            default_results_per_page=self.batch_size
        )


# Initialize logging
logger = setup_logging(
    console_level=logging.DEBUG if "--debug" in sys.argv else logging.INFO
)


def load_input_data(path: Union[str, Path], expected_type: str = "list") -> Union[List[str], Dict[str, Any]]:
    """Load and validate input data from a JSON file.

    This function handles loading both list-based (URLs, search terms) and 
    dictionary-based (configuration) JSON files, with type validation.

    Args:
        path: Path to the JSON file to load
        expected_type: Expected data type ("list" or "dict")

    Returns:
        List of strings or dictionary, depending on expected_type

    Raises:
        ValueError: If file doesn't exist or content doesn't match expected type
        json.JSONDecodeError: If file contains invalid JSON
    """
    path = Path(path) if isinstance(path, str) else path
    
    if not path.exists():
        raise ValueError(f"Input file not found: {path}")
        
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")
            
    if expected_type == "list" and not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data)}")
    elif expected_type == "dict" and not isinstance(data, dict):
        raise ValueError(f"Expected dict in {path}, got {type(data)}")
            
    return data


def parse_arguments() -> CrawlerConfig:
    """Parse command line arguments and return crawler configuration.

    The function sets up the command-line interface with subcommands for
    different modes (website/search/pipeline) and their specific options.

    Returns:
        CrawlerConfig object with parsed settings

    Example usage:
        python main.py website --urls urls.json --method crawl4ai
        python main.py search --terms "hotels" "restaurants" --concurrent 5
        python main.py pipeline --config pipeline_config.json --debug
    """
    parser = argparse.ArgumentParser(
        description="AI-Powered Business Data Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--save-raw",
        action="store_true",
        help="Save raw HTML content"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom configuration file"
    )
    
    # Create subcommands
    subparsers = parser.add_subparsers(
        dest="mode",
        required=True,
        help="Operation mode"
    )
    
    # Website scraping mode
    website_parser = subparsers.add_parser(
        "website",
        help="Scrape data from website URLs"
    )
    website_parser.add_argument(
        "--urls",
        type=str,
        required=True,
        help="Path to JSON file with website URLs"
    )
    
    # Search scraping mode
    search_parser = subparsers.add_parser(
        "search",
        help="Extract URLs from search results"
    )
    search_source = search_parser.add_mutually_exclusive_group(required=True)
    search_source.add_argument(
        "--terms",
        nargs="+",
        help="Search terms to use"
    )
    search_source.add_argument(
        "--urls",
        type=str,
        help="Path to JSON file with search URLs"
    )
    
    # Pipeline mode
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run full pipeline (search → extract → scrape)"
    )
    pipeline_source = pipeline_parser.add_mutually_exclusive_group(required=True)
    pipeline_source.add_argument(
        "--terms",
        nargs="+",
        help="Search terms to use"
    )
    pipeline_source.add_argument(
        "--urls",
        type=str,
        help="Path to JSON file with search URLs"
    )
    
    # Common options for all modes
    for sub in [website_parser, search_parser, pipeline_parser]:
        sub.add_argument(
            "--method",
            type=str,
            choices=["direct", "crawl4ai"],
            default="direct",
            help="Scraping method to use"
        )
        sub.add_argument(
            "--output",
            type=str,
            default=DEFAULT_OUTPUT_DIR,
            help="Output directory"
        )
        sub.add_argument(
            "--concurrent",
            type=int,
            default=DEFAULT_MAX_CONCURRENT,
            help="Maximum concurrent requests"
        )
        sub.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            help="Items per batch"
        )
        sub.add_argument(
            "--retries",
            type=int,
            default=DEFAULT_RETRY_ATTEMPTS,
            help="Number of retry attempts"
        )
        sub.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Request timeout in seconds"
        )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set input file based on mode and arguments
    input_file = None
    if args.mode == "website":
        input_file = args.urls
    elif args.mode == "search" or args.mode == "pipeline":
        if args.urls:
            input_file = args.urls
        elif args.terms:
            # Create temporary file with search terms
            terms_file = Path(DEFAULT_INPUT_DIR) / "temp_search_terms.json"
            terms_file.parent.mkdir(parents=True, exist_ok=True)
            with open(terms_file, "w") as f:
                json.dump(args.terms, f)
            input_file = terms_file
    
    # Create and return config object
    return CrawlerConfig(
        mode=args.mode,
        method=ScrapeMethod(args.method),
        input_file=input_file,
        output_dir=args.output,
        max_concurrent=args.concurrent,
        batch_size=args.batch_size,
        retry_attempts=args.retries,
        save_raw=args.save_raw,
        debug=args.debug,
        timeout=args.timeout,
        custom_config=args.config
    )


# Functions to parse arguments, load input data, etc. defined above...

async def scrape_websites(config: CrawlerConfig) -> None:
    """Execute website scraping operation

    Args:
        config: Crawler configuration
    """
    logger.info("Starting website scraping operation...")
    
    # Load website URLs
    try:
        urls = load_input_data(config.input_file, "list")
    except ValueError as e:
        logger.error(f"Failed to load URLs: {e}")
        return
    
    logger.info(f"Starting website scraping with method '{config.method}' for {len(urls)} URLs")
    
    # Create and configure website scraper
    website_scraper = create_website_scraper(
        urls=urls,
        scraping_method=config.method.value,
        max_concurrent_requests=config.max_concurrent,
        llm_configuration=None  # Can be loaded from custom config
    )
    
    # Execute scraping and extraction
    results = await website_scraper.scrape_and_extract_data(
        extraction_method='crawl4ai',
        save_results=True,
        output_dir=config.output_dir,
        save_raw=config.save_raw
    )
    
    logger.info(f"Website scraping completed. Processed {len(results)} websites.")


async def scrape_searches(config: CrawlerConfig) -> Optional[List[SearchExtractionResult]]:
    """Execute search scraping operation

    Args:
        config: Crawler configuration

    Returns:
        List of search extraction results if successful, None otherwise
    """
    logger.info("Starting search scraping operation...")
    
    try:
        # Input could be either terms or URLs depending on CLI args
        search_input = load_input_data(config.input_file, "list")
    except ValueError as e:
        logger.error(f"Failed to load search input: {e}")
        return None
    
    # Create and configure search scraper
    search_scraper = create_search_scraper(
        scraping_config=config.to_search_config()
    )
    
    # Execute search based on input type
    if any(isinstance(x, str) and x.startswith(('http://', 'https://')) for x in search_input):
        logger.info(f"Processing {len(search_input)} search URLs")
        search_results = await search_scraper.extract_business_urls_from_searches(
            search_urls=search_input,
            llm_extraction_method='crawl4ai'
        )
    else:
        logger.info(f"Processing {len(search_input)} search terms")
        search_results = await search_scraper.extract_business_urls_from_searches(
            search_terms=search_input,
            llm_extraction_method='crawl4ai'
        )
    
    # Count and report results
    total_urls = sum(len(result.urls) for result in search_results if hasattr(result, 'urls'))
    logger.info(f"Search scraping completed. Found {total_urls} business URLs.")
    
    return search_results


async def run_pipeline(config: CrawlerConfig) -> None:
    """Execute the full pipeline operation

    Args:
        config: Crawler configuration
    """
    logger.info("Starting full pipeline operation...")
    
    # Step 1: Extract URLs from search results
    search_results = await scrape_searches(config)
    if not search_results:
        logger.error("Pipeline terminated: No search results found")
        return
    
    # Step 2: Extract and deduplicate website URLs
    website_urls = []
    for result in search_results:
        if hasattr(result, 'urls'):
            for url_info in result.urls:
                if hasattr(url_info, 'url') and url_info.url not in website_urls:
                    website_urls.append(url_info.url)
    
    if not website_urls:
        logger.error("Pipeline terminated: No website URLs extracted")
        return
    
    logger.info(f"Extracted {len(website_urls)} unique website URLs")
    
    # Create temporary file with website URLs
    urls_file = Path(DEFAULT_INPUT_DIR) / "temp_website_urls.json"
    urls_file.parent.mkdir(parents=True, exist_ok=True)
    with open(urls_file, "w") as f:
        json.dump(website_urls, f)
    
    # Update config for website scraping
    website_config = CrawlerConfig(
        mode="website",
        method=config.method,
        input_file=urls_file,
        output_dir=config.output_dir,
        max_concurrent=config.max_concurrent,
        batch_size=config.batch_size,
        retry_attempts=config.retry_attempts,
        save_raw=config.save_raw,
        debug=config.debug,
        timeout=config.timeout
    )
    
    # Step 3: Scrape websites
    await scrape_websites(website_config)
    
    # Clean up temporary file
    try:
        urls_file.unlink()
    except OSError:
        pass


async def main():
    """Main entry point for the crawler

    Parses command line arguments, sets up configuration,
    and executes the requested operation mode.
    """
    print("\n" + "="*60)
    print("🤖 AI-POWERED BUSINESS DATA CRAWLER".center(60))
    print("="*60 + "\n")
    
    print("Select an option:")
    print("1. Scrape websites (from website_urls_list.json)")
    print("2. Scrape search results (from search_terms_list.json)")
    print("3. Scrape search results (from search_urls_list.json)")
    print("4. Run full pipeline (search → extract URLs → scrape websites)")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == "1":
        # Website scraping
        print("\n--- Website Scraping ---")
        
        # Load website URLs
        urls = load_input_data("input/website_urls_list.json")
        if not urls:
            print("No URLs found in input/website_urls_list.json. Exiting.")
            return
        
        # Select scraping method
        method = input("Select scraping method (direct/crawl4ai) [default: direct]: ").lower() or "direct"
        if method not in ["direct", "crawl4ai"]:
            method = "direct"
        
        print(f"\nStarting website scraping with method '{method}' for {len(urls)} URLs...")
        
        # Create website scraper
        website_scraper = create_website_scraper(
            urls=urls,
            scraping_method=method,
            max_concurrent_requests=3
        )
        
        # Execute scraping and extraction
        results = await website_scraper.scrape_and_extract_data(
            extraction_method='crawl4ai',
            save_results=True
        )
        
        print(f"Website scraping completed. Processed {len(results)} websites.")
        
    elif choice == "2":
        # Search scraping with search terms
        print("\n--- Search Scraping (using search terms) ---")
        
        # Load search terms
        search_terms = load_input_data("input/search_terms_list.json")
        if not search_terms:
            print("No search terms found in input/search_terms_list.json. Exiting.")
            return
        
        print(f"\nStarting search scraping for {len(search_terms)} search terms...")
        
        # Create search scraper
        search_scraper = create_search_scraper()
        
        # Execute search extraction
        results = await search_scraper.extract_business_urls_from_searches(
            search_terms=search_terms,
            llm_extraction_method='crawl4ai'
        )
        
        # Count extracted URLs
        total_urls = sum(len(result.urls) for result in results if hasattr(result, 'urls'))
        print(f"Search scraping completed. Found {total_urls} business URLs.")
        
    elif choice == "3":
        # Search scraping with search URLs
        print("\n--- Search Scraping (using search URLs) ---")
        
        # Load search URLs
        search_urls = load_input_data("input/search_urls_list.json")
        if not search_urls:
            print("No search URLs found in input/search_urls_list.json. Exiting.")
            return
        
        print(f"\nStarting search scraping for {len(search_urls)} search URLs...")
        
        # Create search scraper
        search_scraper = create_search_scraper()
        
        # Execute search extraction
        results = await search_scraper.extract_business_urls_from_searches(
            search_urls=search_urls,
            llm_extraction_method='crawl4ai'
        )
        
        # Count extracted URLs
        total_urls = sum(len(result.urls) for result in results if hasattr(result, 'urls'))
        print(f"Search scraping completed. Found {total_urls} business URLs.")
        
    elif choice == "4":
        # Full pipeline
        print("\n--- Full Pipeline ---")
        
        # Ask which input file to use
        print("Select input file for pipeline:")
        print("1. search_terms_list.json")
        print("2. search_urls_list.json")
        
        file_choice = input("\nEnter your choice (1-2): ")
        
        if file_choice == "1":
            # Load search terms
            search_terms = load_input_data("input/search_terms_list.json")
            if not search_terms:
                print("No search terms found in input/search_terms_list.json. Exiting.")
                return
            
            print(f"\nStarting pipeline with {len(search_terms)} search terms...")
            
            # Create search scraper
            search_scraper = create_search_scraper()
            
            # Step 1: Extract business URLs from search results
            search_results = await search_scraper.extract_business_urls_from_searches(
                search_terms=search_terms,
                llm_extraction_method='crawl4ai'
            )
            
        elif file_choice == "2":
            # Load search URLs
            search_urls = load_input_data("input/search_urls_list.json")
            if not search_urls:
                print("No search URLs found in input/search_urls_list.json. Exiting.")
                return
            
            print(f"\nStarting pipeline with {len(search_urls)} search URLs...")
            
            # Create search scraper
            search_scraper = create_search_scraper()
            
            # Step 1: Extract business URLs from search results
            search_results = await search_scraper.extract_business_urls_from_searches(
                search_urls=search_urls,
                llm_extraction_method='crawl4ai'
            )
            
        else:
            print("Invalid choice. Exiting.")
            return
        
        if not search_results:
            print("No search results found. Pipeline terminated.")
            return
        
        # Step 2: Extract website URLs from search results
        website_urls = []
        for result in search_results:
            if hasattr(result, 'urls'):
                for url_info in result.urls:
                    if hasattr(url_info, 'url') and url_info.url not in website_urls:
                        website_urls.append(url_info.url)
        
        if not website_urls:
            print("No website URLs extracted. Pipeline terminated.")
            return
        
        print(f"Extracted {len(website_urls)} unique website URLs from search results.")
        
        # Step 3: Select scraping method for websites
        method = input("Select website scraping method (direct/crawl4ai) [default: direct]: ").lower() or "direct"
        if method not in ["direct", "crawl4ai"]:
            method = "direct"
        
        # Step 4: Scrape websites
        print(f"Starting website scraping with method '{method}' for {len(website_urls)} URLs...")
        
        # Create website scraper
        website_scraper = create_website_scraper(
            urls=website_urls,
            scraping_method=method,
            max_concurrent_requests=3
        )
        
        # Execute scraping and extraction
        results = await website_scraper.scrape_and_extract_data(
            extraction_method='crawl4ai',
            save_results=True
        )
        
        print(f"Pipeline completed successfully. Processed {len(results)} websites.")
        
    elif choice == "5":
        print("Exiting program.")
        return
        
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())