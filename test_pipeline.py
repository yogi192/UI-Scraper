#!/usr/bin/env python3
"""
Test script for the full pipeline workflow
Tests: Search -> URL Extraction -> Website Scraping -> Data Extraction
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.searches_scraping import SearchesScraping
from scrapers.websites_scraping import WebsitesScraping
from utils.mongodb_client import mongodb_client
from logs.custom_logging import setup_logging

# Setup logging
logger = setup_logging(console_level='DEBUG')

async def test_pipeline():
    """Test the complete pipeline workflow"""
    
    # Test data
    search_term = "ferreterias santo domingo"
    test_url = "https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"
    
    logger.info("="*60)
    logger.info("PIPELINE TEST STARTING")
    logger.info("="*60)
    
    try:
        # Phase 1: Search for URLs
        logger.info("\n📍 PHASE 1: Search for business URLs")
        logger.info(f"Search term: {search_term}")
        
        search_scraper = SearchesScraping(search_terms=[search_term])
        search_results = await search_scraper.scrape_and_extract_urls()
        
        logger.info(f"Search results: {len(search_results)} items returned")
        
        # Check if we got URLs
        urls_found = []
        for result in search_results:
            if isinstance(result, dict):
                # Check for URLs in the result
                if 'urls' in result:
                    urls_found.extend(result.get('urls', []))
                elif 'url' in result:
                    urls_found.append(result['url'])
                    
        logger.info(f"URLs extracted: {len(urls_found)}")
        if urls_found:
            logger.info("Sample URLs:")
            for url in urls_found[:3]:
                logger.info(f"  - {url}")
        
        # Phase 2: Direct URL test (using the provided URL)
        logger.info(f"\n📍 PHASE 2: Testing direct URL scraping")
        logger.info(f"Test URL: {test_url}")
        
        # First, let's just scrape the HTML
        website_scraper = WebsitesScraping(
            urls=[test_url],
            scraping_method='direct'
        )
        
        # Just get the HTML content first
        scraped_data = await website_scraper.scrape_multiple_websites()
        logger.info(f"Scraped data: {len(scraped_data)} pages")
        
        # Check what we got
        for item in scraped_data:
            for url, content in item.items():
                if isinstance(content, dict):
                    if 'error_type' in content:
                        logger.error(f"Scraping error for {url}: {content.get('message', 'Unknown error')}")
                    else:
                        logger.info(f"Successfully scraped {url}")
                        logger.info(f"  Content length: {len(str(content))}")
                        # Save a sample for debugging
                        debug_file = "debug_scraped_content.json"
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            json.dump(content, f, indent=2, ensure_ascii=False)
                        logger.info(f"  Saved debug content to {debug_file}")
        
        # Phase 3: Full extraction pipeline
        logger.info(f"\n📍 PHASE 3: Testing full extraction pipeline")
        
        # Now test the full scrape_and_extract_data method
        extraction_results = await website_scraper.scrape_and_extract_data()
        
        logger.info(f"Extraction results: {len(extraction_results)} items")
        
        # Analyze results
        total_entities = 0
        successful_extractions = 0
        failed_extractions = 0
        
        for result in extraction_results:
            if isinstance(result, dict):
                metadata = result.get('metadata', {})
                entities = result.get('entities', [])
                
                if metadata.get('result', {}).get('success', False):
                    successful_extractions += 1
                    total_entities += len(entities)
                    logger.info(f"✅ Successful extraction: {len(entities)} entities found")
                    
                    # Show sample entity
                    if entities:
                        logger.info("Sample entity:")
                        logger.info(json.dumps(entities[0], indent=2, ensure_ascii=False))
                else:
                    failed_extractions += 1
                    error = metadata.get('result', {}).get('error_details', 'Unknown error')
                    logger.error(f"❌ Failed extraction: {error}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("PIPELINE TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Search phase: {len(search_results)} results")
        logger.info(f"URLs found: {len(urls_found)}")
        logger.info(f"Pages scraped: {len(scraped_data)}")
        logger.info(f"Successful extractions: {successful_extractions}")
        logger.info(f"Failed extractions: {failed_extractions}")
        logger.info(f"Total entities extracted: {total_entities}")
        
        # Phase 4: Test MongoDB save
        logger.info(f"\n📍 PHASE 4: Testing MongoDB save")
        
        if total_entities > 0:
            # Test saving to MongoDB
            businesses_to_save = []
            for result in extraction_results:
                if result.get('metadata', {}).get('result', {}).get('success', False):
                    businesses_to_save.extend(result.get('entities', []))
            
            if businesses_to_save:
                save_result = await mongodb_client.save_businesses(
                    businesses_to_save[:5],  # Save only first 5 for test
                    source_type="pipeline_test"
                )
                logger.info(f"MongoDB save result: {save_result}")
        
        # Save full results for analysis
        output_file = f"pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'search_results': search_results,
                'urls_found': urls_found,
                'extraction_results': extraction_results,
                'summary': {
                    'search_results': len(search_results),
                    'urls_found': len(urls_found),
                    'successful_extractions': successful_extractions,
                    'failed_extractions': failed_extractions,
                    'total_entities': total_entities
                }
            }, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"\nFull results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Close MongoDB connection
        await mongodb_client.close()

if __name__ == "__main__":
    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "AIzaSyA9ZInLikGGl2-Nm7IPVzzz_4jTed_DCk0":
        logger.error("❌ Please set a valid GOOGLE_API_KEY environment variable")
        logger.error("Export it with: export GOOGLE_API_KEY='your-actual-api-key'")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_pipeline())