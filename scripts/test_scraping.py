#!/usr/bin/env python3
"""Test scraping functionality directly"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scrapers.websites_scraping_with_db import process_website_urls

async def test_website_scraping():
    print("Testing website scraping...")
    
    urls = ["https://www.yelu.do/category/agentes_de_estado"]
    
    try:
        result = await process_website_urls(urls)
        print("Result:", result)
        
        if result.get("urls_processed", 0) > 0:
            print(f"✓ Successfully processed {result['urls_processed']} URLs")
            print(f"✓ Found {result.get('entities_found', 0)} entities")
        else:
            print("✗ No URLs were processed")
            
    except Exception as e:
        print(f"✗ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_website_scraping())