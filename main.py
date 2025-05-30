#!/usr/bin/env python3
"""
AI-Powered Business Data Crawler - Main Controller

This script provides a simple interface to control all scraper modules.
It loads data from input files and passes it to the appropriate scraper.
"""

import os
import sys
import json
import asyncio
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from scrapers.websites_scraping import create_website_scraper
from scrapers.searches_scraping import create_search_scraper
from logs.custom_logging import setup_logging
import logging

# Initialize logging
logger = setup_logging(console_level=logging.INFO)


def load_input_data(file_path: str) -> List[str]:
    """
    Load input data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of strings from the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} items from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading input file {file_path}: {e}")
        return []


async def main():
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