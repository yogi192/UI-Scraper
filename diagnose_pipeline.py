#!/usr/bin/env python3
"""
Diagnose pipeline issues
"""

import asyncio
import os
import sys
import json
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.searches_scraping import SearchesScraping
from scrapers.websites_scraping import WebsitesScraping
from logs.custom_logging import setup_logging

# Setup logging
logger = setup_logging(console_level='DEBUG')

async def diagnose_search_phase(search_term):
    """Test just the search phase"""
    logger.info(f"\n🔍 TESTING SEARCH PHASE for: '{search_term}'")
    
    try:
        # Create search scraper
        scraper = SearchesScraping(search_terms=[search_term])
        
        # First, let's see what HTML we get from Google
        search_url = scraper._generate_search_url(search_term)
        logger.info(f"Search URL: {search_url}")
        
        # Scrape search results
        scraped_results = await scraper.scrape_multiple_search_results()
        logger.info(f"Scraped {len(scraped_results)} search result pages")
        
        # Check what we got
        for result in scraped_results:
            for url, content in result.items():
                if isinstance(content, dict) and 'error_type' in content:
                    logger.error(f"❌ Search scraping failed: {content.get('message')}")
                else:
                    logger.info(f"✅ Successfully scraped search results")
                    logger.info(f"   Content length: {len(str(content))}")
        
        # Now extract URLs
        extracted_urls = await scraper.scrape_and_extract_urls()
        logger.info(f"\n📊 SEARCH RESULTS:")
        logger.info(f"Total items returned: {len(extracted_urls)}")
        
        # Analyze what we got
        all_urls = []
        for item in extracted_urls:
            if isinstance(item, dict):
                if 'urls' in item:
                    urls = item['urls']
                    all_urls.extend(urls)
                    logger.info(f"Found {len(urls)} URLs in result")
                elif 'metadata' in item:
                    # Check if extraction failed
                    success = item.get('metadata', {}).get('result', {}).get('success', False)
                    if not success:
                        error = item.get('metadata', {}).get('result', {}).get('error_details', 'Unknown')
                        logger.error(f"❌ URL extraction failed: {error}")
        
        logger.info(f"\n📌 TOTAL URLs FOUND: {len(all_urls)}")
        if all_urls:
            logger.info("Sample URLs:")
            for url in all_urls[:5]:
                logger.info(f"  - {url}")
        
        return all_urls
        
    except Exception as e:
        logger.error(f"Search phase error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

async def test_specific_url():
    """Test a known working URL"""
    test_url = "https://www.ferreteriaalbert.com/"
    logger.info(f"\n🔧 TESTING SPECIFIC URL: {test_url}")
    
    try:
        scraper = WebsitesScraping(
            urls=[test_url],
            scraping_method='direct'
        )
        
        results = await scraper.scrape_and_extract_data()
        
        # Check results
        for result in results:
            if isinstance(result, dict) and 'metadata' in result:
                success = result.get('metadata', {}).get('result', {}).get('success', False)
                entities = result.get('entities', [])
                
                logger.info(f"Extraction success: {success}")
                logger.info(f"Entities found: {len(entities)}")
                
                if entities:
                    logger.info("Sample entity:")
                    logger.info(json.dumps(entities[0], indent=2, ensure_ascii=False))
                    
        return results
        
    except Exception as e:
        logger.error(f"URL test error: {str(e)}")
        return []

async def check_google_blocking():
    """Check if Google is blocking us"""
    logger.info("\n🚫 CHECKING FOR GOOGLE BLOCKING")
    
    try:
        from utils.helpers import HtmlPageScraper
        scraper = HtmlPageScraper()
        
        # Try to fetch Google search page
        test_url = "https://www.google.com/search?q=test"
        html, status = await scraper.request_html(test_url)
        
        if status == 200:
            # Check for common blocking indicators
            blocking_indicators = [
                "unusual traffic",
                "captcha",
                "sorry",
                "automated requests",
                "recaptcha"
            ]
            
            html_lower = html.lower() if html else ""
            blocked = any(indicator in html_lower for indicator in blocking_indicators)
            
            if blocked:
                logger.error("❌ Google appears to be blocking requests (CAPTCHA/rate limit)")
            else:
                logger.info("✅ Google search accessible")
                
            logger.info(f"Response length: {len(html) if html else 0}")
            
            # Save sample for debugging
            with open("google_response_sample.html", "w", encoding="utf-8") as f:
                f.write(html[:5000] if html else "No content")
            logger.info("Saved sample response to google_response_sample.html")
            
        else:
            logger.error(f"❌ Failed to access Google: Status {status}")
            
    except Exception as e:
        logger.error(f"Google check error: {str(e)}")

async def main():
    """Run diagnostics"""
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY not set!")
        return
    
    logger.info("🏥 PIPELINE DIAGNOSTICS")
    logger.info("=" * 60)
    
    # 1. Check Google blocking
    await check_google_blocking()
    
    # 2. Test search phase with your term
    search_term = "ferreteria samana"
    urls = await diagnose_search_phase(search_term)
    
    # 3. Test a specific URL
    await test_specific_url()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DIAGNOSIS SUMMARY:")
    logger.info("=" * 60)
    
    if urls:
        logger.info(f"✅ Search phase works - found {len(urls)} URLs")
        logger.info("→ Pipeline should work if these URLs contain business data")
    else:
        logger.info("❌ Search phase failed - no URLs found")
        logger.info("Possible causes:")
        logger.info("- Google blocking/CAPTCHA")
        logger.info("- No results for search term")
        logger.info("- Network issues")
        logger.info("- Search scraping errors")
        
    logger.info("\nRECOMMENDATIONS:")
    logger.info("1. Use website jobs with known URLs instead of pipeline")
    logger.info("2. Try different search terms")
    logger.info("3. Check google_response_sample.html for blocking")
    logger.info("4. Consider using a proxy or different search method")

if __name__ == "__main__":
    # Set API key from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())