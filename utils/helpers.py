import re
import json
import html
import random
import traceback
from bs4 import BeautifulSoup
from lxml.html.clean import Cleaner
from html_to_markdown import convert_to_markdown
import asyncio
from typing import Optional, List, Dict, Any, Tuple, Union, Set
from playwright.async_api import Page
import aiohttp, time
from datetime import datetime
from dataclasses import dataclass
from seleniumbase import SB
from concurrent.futures import ThreadPoolExecutor

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logs.custom_logging import setup_logging
import logging
logger = setup_logging(console_level=logging.DEBUG)



#======================================================
# SeleniumBaseBrowserManager → Handles browser operations
#======================================================

class SeleniumBaseBrowserManager:
    """
    Manages browser operations using SeleniumBase with undetected-chromedriver (UC) mode.
    Provides robust methods for fetching HTML content from websites, especially Google search,
    with CAPTCHA solving capabilities and human-like interactions.
    """

    def __init__(self, min_html_length: int = 30000, headless: bool = False):
        self.min_html_length = min_html_length
        self.headless = headless
        self.cookies = self.load_google_cookies()

    def load_google_cookies(self) -> List[Dict[str, str]]:
        """Load Google cookies from environment variable or file"""
        cookies = []
        try:
            # Try loading from environment variable first
            if os.getenv("GOOGLE_COOKIES"):
                cookies = json.loads(os.getenv("GOOGLE_COOKIES"))
                logger.info(f"Loaded {len(cookies)} cookies from environment")
            # Fallback to file
            elif os.path.exists("utils/google_cookies.json"):
                with open("utils/google_cookies.json", "r") as f:
                    cookies = json.load(f)
                logger.info(f"Loaded {len(cookies)} cookies from file")
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
        return cookies

    def _scrape_with_seleniumbase(self, url: str) -> Tuple[str, Union[str, int]]:
        """
        Synchronously scrape the given URL using SeleniumBase with UC mode and CAPTCHA handling.

        Args:
            url (str): URL to scrape

        Returns:
            Tuple of (raw_html, status_code) where status_code is 200 for success or a string error code
        """
        try:
            with SB(
                uc=True,
                headless=self.headless,
                undetected=True,
            ) as sb:
                # Open URL with human-like delay
                sb.open(url)
                sb.sleep(random.uniform(1.5, 3.5))

                # Add Google cookies if available
                if self.cookies:
                    for cookie in self.cookies:
                        sb.add_cookie(cookie)
                    sb.refresh()
                    sb.sleep(random.uniform(1.0, 2.0))

                # Initial content check
                html_content = sb.get_page_source()
                
                # Check for blocking indicators
                blocking_detected = (
                    "Our systems have detected unusual traffic from your computer network." in html_content or
                    sb.is_element_visible('iframe[title="reCAPTCHA"]') or
                    sb.is_element_visible('form[id="captcha-form"]')
                )
                
                # Handle CAPTCHA if detected
                if len(html_content) < self.min_html_length and blocking_detected:
                    logger.warning(f"CAPTCHA detected on {url}. Attempting to solve...")
                    
                    # Use SeleniumBase's built-in CAPTCHA handling
                    sb.uc_open_with_reconnect(url, 4)
                    sb.uc_gui_handle_captcha()
                    
                    # Check if manual solving is needed
                    if sb.is_element_visible('div[id="rc-imageselect"]'):
                        logger.warning("Manual CAPTCHA solving required")
                        input("Please solve CAPTCHA and press Enter to continue...")
                    
                    # Refresh after solving
                    sb.sleep(2)
                    html_content = sb.get_page_source()

                # Human-like scrolling to trigger lazy loading
                if len(html_content) < self.min_html_length:
                    logger.info("Performing human-like scrolling to load content")
                    sb.scroll_to_bottom()
                    sb.sleep(random.uniform(0.5, 1.5))
                    sb.scroll_to_top()
                    sb.sleep(random.uniform(0.5, 1.0))
                    html_content = sb.get_page_source()

                # Final validation
                if len(html_content) < self.min_html_length:
                    logger.warning(f"HTML content too short ({len(html_content)} chars)")
                    status_code = 'HTML_TOO_SHORT'
                else:
                    logger.info(f"Successfully captured HTML ({len(html_content)} chars)")
                    status_code = 200

                return html_content, status_code

        except Exception as e:
            logger.error(f"SeleniumBase scraping error: {e}")
            logger.debug(traceback.format_exc())
            return "", f'UNEXPECTED_ERROR: {str(e)}'

    async def batch_scrape(self, urls: List[str]) -> List[Tuple[str, Union[str, int]]]:
        """
        Scrape multiple URLs concurrently using thread pool execution.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of tuples (raw_html, status_code) in the same order as input URLs
        """
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=3) as executor:  # Conservative concurrency
            tasks = [loop.run_in_executor(executor, self._scrape_with_seleniumbase, url) for url in urls]
            return await asyncio.gather(*tasks)


#==================================================================
# HTMLContentProcessor → HTML cleaning and transformation
#==================================================================

class HTMLContentProcessor:
    """
    Utility class to:
    => Clean HTML
    => Extract <script type="application/json"> blocks
    => Convert HTML to LLM-friendly Markdown
    """

    def normalize_whitespace(self, text: str) -> str:
        """
        Replace multiple spaces/newlines with single space and trim.

        Args:
            text (str): Input string

        Returns:
            str: Normalized, space-trimmed string
        """
        return re.sub(r'\s+', ' ', text).strip()

    def parse_json_scripts(self, script_contents: List[str]) -> List[Dict[str, Any]]:
        """
        Parses JSON content from script blocks, stripping HTML comments if needed.

        Args:
            script_contents (List[str]): Raw <script> contents.

        Returns:
            List[Dict[str, Any]]: Successfully parsed JSON objects.
        """
        parsed_scripts = []
        for i, raw_script in enumerate(script_contents):
            try:
                # Unescape HTML entities (e.g., &lt; becomes <)
                unescaped = html.unescape(raw_script)
                
                # Remove HTML comments which sometimes wrap JSON-LD
                clean_content = re.sub(r'<!--.*?-->', '', unescaped, flags=re.DOTALL).strip()

                if not clean_content:
                    logger.debug(f"Skipping empty script content after cleaning for script index {i}.")
                    continue

                parsed_json = json.loads(clean_content)
                parsed_scripts.append(parsed_json)

            except json.JSONDecodeError as jde:
                logger.warning(f"JSONDecodeError parsing script content (index {i}, first 100 chars: '{clean_content[:100]}...'): {jde}")
                logger.debug(f"Full traceback for JSONDecodeError:\n{traceback.format_exc()}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error parsing script content (index {i}): {e}")
                logger.debug(f"Full traceback for unexpected error:\n{traceback.format_exc()}")
                continue

        return parsed_scripts
    
    def backup_html_cleaner(self, raw_html: str) -> str:
        """
        A simpler, BeautifulSoup-based HTML cleaner used as a fallback or for specific tag removal.
        It keeps only <script type="application/json"> tags and removes other specified tags.

        Args:
            raw_html (str): Raw HTML string

        Returns:
            str: Cleaned HTML string
        """
        try:
            soup = BeautifulSoup(raw_html, 'lxml')

            # Keep only script tags with type="application/json", remove all others
            for script in soup.find_all('script'):
                if script.get('type') != 'application/json':
                    script.decompose()
            
            # Remove other unnecessary tags for the main content
            tags_to_remove = ['style', 'img', 'svg', 'video', 'audio', 'nav', 'header', 'noscript']

            for tag_name in tags_to_remove:
                for tag in soup.find_all(tag_name):
                    tag.decompose()
            
            return self.normalize_whitespace(str(soup))
        except Exception as e:
            logger.warning(f"Backup HTML cleaner failed: {e}")
            logger.debug(f"Full traceback for backup_html_cleaner failure:\n{traceback.format_exc()}")
            return raw_html
            
    def clean_html(self, raw_html: str) -> str:
        """
        Cleans HTML using lxml's Cleaner to remove scripts, styles, media, ads, etc.
        NOTE: This cleaner is intended to be used AFTER JSON-LD and other
        specific metadata have been extracted, as its settings are aggressive.

        Args:
            raw_html (str): Raw HTML string

        Returns:
            str: Cleaned HTML string
        """
        # IMPORTANT: These settings are designed assuming you've already extracted
        # application/json scripts and other critical metadata before calling this.
        cleaner = Cleaner(
            scripts=True,          # Remove ALL script tags (incl. inline and non-JSON)
            javascript=True,       # Remove JavaScript events (e.g., onclick)
            comments=True,         # Remove HTML comments
            style=True,            # Remove <style> tags
            inline_style=True,     # Remove inline style attributes
            links=False,           # IMPORTANT: DO NOT remove <a> tags; allow Markdown converter to handle.
            meta=True,             # Remove <meta> tags
            page_structure=True,   # Remove <html>, <head>, <body> tags
            processing_instructions=True,
            embedded=True,         # Remove <embed>, <applet> tags
            forms=False,           # Keep forms (content might be useful)
            annoying_tags=True,    # Remove tags like <blink>, <marquee>
            kill_tags=['header', 'nav', 'noscript', 'img', 'video', 'audio', 'svg', '#taw', '.M8OgIe', '.ULSxyf'], # Remove more non relevant tags

            safe_attrs_only=False  # IMPORTANT: Keep all attributes for links and potential tool interaction if needed
        )
        return self.normalize_whitespace(cleaner.clean_html(raw_html))
    
    def get_llm_friendly_content(self, raw_html: str, markdown: str = None) -> dict:
        """
        Converts raw HTML into clean Markdown and extracts JSON from <script type="application/json">.

        Args:
            raw_html (str): Raw HTML input

        Returns:
            dict: {
                'html_content': {
                    'markdown/html': LLM-ready Markdown (or cleaned HTML if markdown fails),
                    'json_scripts': Parsed JSON content from scripts
                }
            }
        """
        # Use a copy of the soup for extraction, leaving the original raw_html intact for lxml.Cleaner
        soup_for_extraction = BeautifulSoup(raw_html, 'lxml')

        parsed_scripts_list = []
        try:
            json_scripts_tags = soup_for_extraction.find_all('script', type='application/json')
            raw_script_contents = [script.get_text() for script in json_scripts_tags]
            parsed_scripts_list = self.parse_json_scripts(raw_script_contents)
            if not parsed_scripts_list:
                parsed_scripts_list = raw_script_contents
            
            # Decompose the JSON script tags from this soup so they don't interfere if it were used for MD
            # (though in current flow, we're cleaning raw_html directly for markdown)
            for script_tag in json_scripts_tags:
                script_tag.decompose()
            
        except Exception as e:
            logger.error(f'Error extracting or parsing <script type="application/json">: {e}', exc_info=True)
        
        # Clean and convert HTML to Markdown using the lxml.Cleaner
        if not markdown:
            cleaned_html_for_markdown = self.clean_html(raw_html) 
            
            converted_markdown = None
            try:
                converted_markdown = convert_to_markdown(cleaned_html_for_markdown)
                final_markdown = self.normalize_whitespace(converted_markdown)
            except Exception as e:
                logger.warning(f"Markdown conversion failed: {e}. Falling back to backup HTML cleaner.", exc_info=True)
                final_markdown = None # Set to None so the fallback can be used
        else:
            final_markdown = markdown

        # If Markdown conversion failed or produced empty/bad content, use the backup cleaner
        if not final_markdown or len(final_markdown.strip()) < 50: # Heuristic for "bad" markdown
            logger.info("Using backup HTML cleaner for content as primary Markdown conversion was insufficient.")
            final_content = self.normalize_whitespace(self.backup_html_cleaner(raw_html))
        else:
            final_content = final_markdown

        return {
                'markdown/cleaned_html': final_content,
                'json_scripts': parsed_scripts_list 
            }
        


#==================================================================

def get_fake_header(device_name:str = None, all_headers:bool = False) -> Dict[str, str]:
        """
        Generate a random user agent and accept headers for HTTP requests.

        Returns:
            Dictionary containing user agent and accept headers
        """
        try:
            with open("utils/fake_headers.json", "r") as f:
                fake_headers = json.load(f)
                if all_headers:
                    if device_name:
                        return fake_headers[device_name]
                    else:
                        return fake_headers
                else:
                    random_browser = random.choice(list(fake_headers.keys()))
                    return fake_headers[random_browser]
        except Exception as e:
            logger.error(f"❌ Error in get_fake_header: {e}")
            logger.debug(traceback.format_exc())
            return {}



# ========================================================================
# HtmlPageScraper → Handles HTTP requests to fetch HTML content
# ========================================================================
        
class HtmlPageScraper:
    """Class for making HTTP requests to fetch contract information from the website."""
    
    def __init__(self):
        """Initialize the HtmlPageScraper with necessary URLs, headers and request parameters."""
        self.logger = logger

    async def request_html(self, url) -> Optional[str]:

        async with aiohttp.ClientSession() as session:
            try:
                
                response = await session.get(url=url, headers=get_fake_header(), ssl=False, timeout=30)

                raw_html = await response.text()

                return raw_html, response.status
            except Exception as e:
                self.logger.error(f"❌ Unexpected error during fetching: {e}")
                self.logger.debug(traceback.format_exc())
                return None, f'Error: {str(e)}'
            
#======================================================================

def save_debug_files(website_scraped_content: List[Dict[str, Any]] = None,
                     search_scraped_content: List[Dict[str, Any]] = None):
    if not website_scraped_content and not search_scraped_content:
        logger.warning("No content provided to save debug file.")
        return

    # Use a filename-safe timestamp
    formatted_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def convert_models(data):
        if isinstance(data, list):
            return [convert_models(item) for item in data]
        elif hasattr(data, 'model_dump'):
            return data.model_dump()
        return data
        
    # Determine output path and content
    if website_scraped_content:
        file_path = f'debug_files/website_scraping/temp_processed_data ({formatted_time}).json'
        scraped_content = convert_models(website_scraped_content)
    else:
        file_path = f'debug_files/search_scraping/temp_processed_data ({formatted_time}).json'
        scraped_content = convert_models(search_scraped_content)

    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    
    # Write the file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scraped_content, f, indent=4, ensure_ascii=False)
        logger.info(f"💾 Saved debug file for LLM to '{file_path}'")
    except Exception as e:
        logger.error(f"❌ Error saving debug file to '{file_path}': {e}")
        logger.debug(traceback.format_exc())

def load_debug_files(file_path: str):
    
    try:
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        if not data:
            logger.warning(f"⚠️ Debug file for llm is empty at '{file_path}'")
            raise ValueError(f"Debug file for llm is empty at '{file_path}'")

        # logger.info(f"📂 Loaded debug file for llm from '{file_path}'")
        return data

    except Exception as e:
        logger.error(f"❌ Error loading debug file for llm from '{file_path}': {e}")
        logger.debug(traceback.format_exc())


def load_input_data(search_terms: bool = False, search_urls: bool = False, website_urls: bool = False) -> List[str]:
    """
    Load input data based on the user's selection.

    Args:
        search_terms (bool): Load search terms (to generate search URLs).
        search_urls (bool): Load pre-built search URLs.
        website_urls (bool): Load direct website URLs for scraping.

    Returns:
        List[str]: A list of strings representing input data (terms or URLs).
    """
    try:
        if search_terms:
            file_path = 'input/search_terms_list.json'
        elif search_urls:
            file_path = 'input/search_urls_list.json'
        elif website_urls:
            file_path = 'input/website_urls_list.json'
        else:
            logger.error("⚠️ No input type selected. Please choose one input source.")
            return []

        if not os.path.exists(file_path):
            logger.error(f"🚫 File not found: '{file_path}'")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        if not isinstance(input_data, list):
            logger.error(f"Invalid input format in '{file_path}'. Expected a list.")
            return []

        logger.info(f"📂 Loaded {len(input_data)} items from '{file_path}'")
        return input_data

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error in '{file_path}': {e}")
        logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"❌ Unexpected error loading '{file_path}': {e}")
        logger.debug(traceback.format_exc())

    return []



def deduplicate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate dictionaries while preserving original order.
    
    Args:
        data: List of dictionaries to deduplicate
        
    Returns:
        Deduplicated list preserving original order
    """
    seen: Set[str] = set()
    unique_items: List[Dict[str, Any]] = []

    for item in data:
        try:
            # Create a stable representation for comparison
            serialized = json.dumps(item, sort_keys=True)
        except (TypeError, ValueError):
            logger.warning("Skipping unserializable item during deduplication")
            continue

        if serialized not in seen:
            seen.add(serialized)
            unique_items.append(item)

    return unique_items

def save_output_data(
    output_data: List[Dict[str, Any]],
    data_type: str = "website",
    deduplicate: bool = True,
    timestamp: bool = True
) -> None:
    """
    Save raw and cleaned output data to type-specific files.
    
    Features:
    - Automatic directory creation
    - Data deduplication
    - Timestamped backups
    - Separate files for website/search data
    - Comprehensive error handling
    
    Args:
        output_data: Extracted data to save
        data_type: Type of data ('website' or 'search')
        deduplicate: Whether to remove duplicates
        timestamp: Whether to create timestamped backups
    """
    # Validate data type
    if data_type not in ["website", "search"]:
        logger.error(f"Invalid data type: {data_type}. Must be 'website' or 'search'")
        return

    try:
        # Create output directories if needed
        os.makedirs("output/raw", exist_ok=True)
        os.makedirs("output/cleaned", exist_ok=True)
        os.makedirs("output/backups", exist_ok=True)
        
        # Base file paths
        base_raw = f"output/raw/{data_type}_raw_data.json"
        base_cleaned = f"output/cleaned/{data_type}_cleaned_data.json"
        
        # Timestamped backup paths
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_raw = f"output/backups/{data_type}_raw_{timestamp_str}.json"
        backup_cleaned = f"output/backups/{data_type}_cleaned_{timestamp_str}.json"
        
        # Read existing data
        existing_raw = []
        if os.path.exists(base_raw) and os.path.getsize(base_raw) > 0:
            try:
                with open(base_raw, "r", encoding="utf-8") as f:
                    existing_raw = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Raw {data_type} data file contains invalid JSON. Starting fresh.")
        
        # Combine and deduplicate
        combined_raw = existing_raw + output_data
        final_raw = deduplicate_data(combined_raw) if deduplicate else combined_raw
        
        # Create cleaned data
        cleaned_data = []
        for item in final_raw:
            # Handle both website and search data structures
            if data_type == "website":
                if isinstance(item, dict) and item.get("entities"):
                    cleaned_data.extend(item["entities"])
            elif data_type == "search":
                if isinstance(item, dict) and item.get("urls"):
                    cleaned_data.extend(item["urls"])
        
        # Create backups before overwriting
        if timestamp:
            try:
                with open(backup_raw, "w", encoding="utf-8") as f:
                    json.dump(final_raw, f, indent=4, ensure_ascii=False)
                with open(backup_cleaned, "w", encoding="utf-8") as f:
                    json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error creating backups: {str(e)}")
        
        # Save main files
        with open(base_raw, "w", encoding="utf-8") as f:
            json.dump(final_raw, f, indent=4, ensure_ascii=False)
        with open(base_cleaned, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
        
        # Log success
        logger.info(
            f"💾 Saved {data_type} data: "
            f"{len(final_raw)} raw items, "
            f"{len(cleaned_data)} cleaned entities"
        )
        
    except Exception as e:
        logger.error(f"❌ Error saving {data_type} data: {str(e)}")
        logger.debug(f"Error traceback:\n{traceback.format_exc()}")