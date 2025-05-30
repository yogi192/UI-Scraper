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

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logs.custom_logging import setup_logging
import logging
logger = setup_logging(console_level=logging.DEBUG)



#======================================================
# PlaywrightBrowserManager → Handles browser operations
#======================================================

class PlaywrightBrowserManager:
    """
    Manages Playwright browser instances and provides robust methods for
    asynchronously fetching and validating HTML content from dynamic websites.
    Includes scrolling for lazy-loaded content, timeout-safe loading,
    and basic bot detection.
    """

    def __init__(self, browser_type: str = "chromium",
                 page_load_timeout: int = 450000, min_html_length: int = 30000):

        self.browser_type = browser_type
        self.page_load_timeout = page_load_timeout
        self.min_html_length = min_html_length

    async def _scroll_and_for_content(self, page: Page):
        """
        Scrolls down to the bottom and back to the top with dynamic steps
        to trigger content loading efficiently.
        """
        try:
            logger.info(f"Scrolling to load content for {page.url}")
            
            # Get initial page dimensions
            viewport_height = await page.evaluate("window.innerHeight")
            total_height = await page.evaluate("document.body.scrollHeight")
            
            # Calculate optimal number of scroll steps (3-5 steps)
            num_steps = max(3, min(5, total_height // viewport_height))
            step_size = total_height // num_steps
            
            # Scroll down to bottom in smooth increments
            logger.info(f"Scrolling down ({num_steps} steps)")
            for i in range(1, num_steps + 1):
                target = step_size * i
                await page.evaluate(f"""
                    window.scrollTo({{
                        top: {target},
                        behavior: 'smooth'
                    }});
                """)
                # Wait dynamically based on step size (faster for smaller pages)
                await asyncio.sleep(max(0.3, min(1.0, step_size / 2000)))
                
                # Update total height in case content expanded
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > total_height:
                    total_height = new_height
                    step_size = total_height // num_steps

            # Scroll back to top quickly
            logger.info("Scrolling back to top")
            await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
            await asyncio.sleep(1)

            # Wait for page to stabilize
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                logger.debug("Network idle state not reached within timeout")

        except Exception as e:
            logger.warning(f"Error during scrolling: {e}", exc_info=True)
            
    async def get_html_content(self, url: str, page: Page) -> Tuple[str, Union[str, int]]:
        """
        Main HTML content extractor.
        Handles scrolling, waits for content, validates HTML, and detects common bot checks or issues.
        Returns raw HTML and status code string (or 200 if success).
        """
        try:
            await page.goto(url, timeout=self.page_load_timeout)
            await asyncio.sleep(random.uniform(0.5, 2.0))

            await page.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in {"image", "stylesheet", "font"} 
            else route.continue_()
    )         
            # Add human-like mouse movements
            await page.mouse.move(
                random.randint(0, 100),
                random.randint(0, 100),
                steps=random.randint(5, 20)
            )
            await asyncio.sleep(random.uniform(0.5, 2.0))
            await self._scroll_and_for_content(page)
            raw_html = await page.content()

            # Content validation
            lower_html = raw_html.lower()
            if len(raw_html) < self.min_html_length:
                logger.warning(f"HTML content too short for {url} ({len(raw_html)} characters). Potentially incomplete.")
                cleaned_url = url.split('://')[-1].split('/')[0]
                await page.screenshot(path=f"debug_files/search_results_scraping.{cleaned_url}_short_screenshot.png", full_page=True)
                
                blocking_terms = [
                        "captcha",
                        "bot verification",
                        "are you a robot",
                        "human verification",
                        "prove you're not a robot",
                        "security check required",
                        "solve the CAPTCHA",
                        "please verify",
                        "access denied",
                        "forbidden",
                        "error 403", # HTML might contain this string
                        "rate limit",
                        "ip address blocked",
                        "unusual traffic",
                        "checking your browser", # Cloudflare
                        "just a moment", # Cloudflare/similar
                        "ddos protection",
                        "cloudflare", # If mentioned explicitly in text
                        "recaptcha",
                        "g-recaptcha", # Class/ID
                        "h-captcha",
                        "blocked by firewall",
                        "robot detected"
                    ]
                
                if any(term in lower_html for term in blocking_terms):
                    logger.warning(f"CAPTCHA detected on {url}. HTML capture aborted.")
                    status_code = 'CAPTCHA_DETECTED'
                    await page.screenshot(path=f"{cleaned_url}_captcha_screenshot.png", full_page=True)
                    input()
                    return raw_html, status_code
                
                status_code = 'HTML_TOO_SHORT'
                return raw_html, status_code
            else:
                logger.info(f"Successfully captured HTML from {url} (length: {len(raw_html)}).")
                status_code = 200

        except Exception as e:
            logger.error(f"Unexpected error during HTML capture for {url}: {e}", exc_info=True)
            status_code = 'UNEXPECTED_ERROR'
            return raw_html, status_code

        return raw_html, status_code


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


# def deduplicate_dict_list_ordered(dict_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """Remove duplicate dictionaries while preserving their original order."""
#     seen: Set[str] = set()
#     unique_items: List[Dict[str, Any]] = []

#     for item in dict_list:
#         try:
#             serialized = json.dumps(item, sort_keys=True)
#         except TypeError:
#             logger.warning("Skipping unserializable item during deduplication.")
#             continue

#         if serialized not in seen:
#             seen.add(serialized)
#             unique_items.append(item)

#     return unique_items


# def save_output_data(output_data: List[Dict[str, Any]]):
#     """
#     Save raw and cleaned output data to separate files. Automatically appends and deduplicates content.

#     - Raw data is saved to: output/raw_extracted_data.json
#     - Cleaned data (only items with 'data' key) is saved to: output/cleaned_extracted_data.json

#     Args:
#         output_data (List[Dict[str, Any]]): Extracted output to save.
#     """
#     raw_path = "output/raw_extracted_data.json"
#     cleaned_path = "output/cleaned_extracted_data.json"

#     os.makedirs(os.path.dirname(raw_path), exist_ok=True)

#     try:
#         # Initialize existing data
#         existing_data = []
        
#         # Check if file exists and has content
#         if os.path.exists(raw_path) and os.path.getsize(raw_path) > 0:
#             try:
#                 with open(raw_path, "r", encoding="utf-8") as f:
#                     existing_data = json.load(f)
#             except json.JSONDecodeError:
#                 logger.warning("Raw data file contains invalid JSON. Starting fresh.")
#                 existing_data = []
        
#         # Combine and deduplicate
#         combined = existing_data + output_data
#         # deduplicated = deduplicate_dict_list(combined)
#         deduplicated = combined

#         # Save raw data
#         with open(raw_path, "w", encoding="utf-8") as f:
#             json.dump(deduplicated, f, indent=4, ensure_ascii=False)

#         # Filter and save cleaned data
#         cleaned = []
#         for item in deduplicated:
#             # Handle both dictionary items and lists of items
#             if isinstance(item, dict):
#                 if item.get("entities") and isinstance(item["entities"], list):
#                     cleaned.append(item)
#             elif isinstance(item, list):
#                 for subitem in item:
#                     if isinstance(subitem, dict) and subitem.get("entities") and isinstance(subitem["entities"], list):
#                         cleaned.append(subitem)
#             else:
#                 logger.warning(f"Unexpected item type in output_data: {type(item)}")
                
    
#         with open(cleaned_path, "w", encoding="utf-8") as f:
#             json.dump(cleaned, f, indent=4, ensure_ascii=False)

#         logger.info(f"💾 Saved {len(deduplicated)} raw and {len(cleaned)} cleaned items.")

#     except Exception as e:
#         logger.error(f"❌ Error saving output data: {e}")
#         logger.debug(traceback.format_exc())



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