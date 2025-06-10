"""
Scrapers Package

This package contains all the web scraping modules for the UI-Scraper project.
"""

# Export main functions for easy importing
from .websites_scraping_with_db import process_website_urls
from .searches_scraping import process_search_terms, process_search_urls

__all__ = [
    'process_website_urls',
    'process_search_terms', 
    'process_search_urls'
]