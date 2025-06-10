# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The UI-Scraper is an AI-powered business data crawler specifically designed to collect business information from Dominican Republic websites. It leverages Google Gemini 2.0 LLM for intelligent data extraction and validation, reducing data collection time by 95% while maintaining high accuracy.

## Common Development Commands

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Set required environment variable
export API_KEY=your_google_gemini_api_key

# Website scraping (direct from URLs)
python main.py website --urls input/website_urls_list.json

# Search-based scraping (find URLs from search terms)
python main.py search --terms "restaurants punta cana" --concurrent 5

# Full pipeline (search → extract → scrape)
python main.py pipeline --config pipeline_config.json --debug

# Interactive mode with menu
python main.py
```

### Command Options

- `--debug`: Enable detailed logging output
- `--concurrent <N>`: Set concurrent request limit (default: 3-5)
- `--method <crawl4ai|http>`: Choose scraping method
- `--save-raw`: Save raw data before cleaning
- `--config <file>`: Use custom configuration file

## High-Level Architecture

### Core Flow
```
Input Sources → Processing Pipeline → LLM Extraction → Output Processing
```

1. **Entry Point**: `main.py` provides CLI and interactive menu interface
2. **Search Processing**: `scrapers/searches_scraping.py` finds business URLs from search results
3. **Website Scraping**: `scrapers/websites_scraping.py` fetches HTML content using multiple strategies
4. **LLM Extraction**: `scrapers/llm_data_extraction.py` uses Google Gemini 2.0 for intelligent parsing
5. **Output**: Structured JSON with schema validation via Pydantic models

### Key Design Patterns

- **Async-First**: All scraping operations use async/await for concurrent processing
- **Strategy Pattern**: Multiple scraping methods (Crawl4AI vs direct HTTP) with automatic fallback
- **Schema Validation**: Pydantic models in `schemas/` ensure data quality
- **Retry Mechanisms**: Built-in exponential backoff for resilient scraping
- **Rate Limiting**: Configurable concurrency to avoid detection

### Critical Components

1. **LLM Integration** (`scrapers/llm_data_extraction.py`):
   - Uses OpenRouter API with Google Gemini 2.0
   - Batch processing for efficiency
   - Multiple extraction strategies with fallback
   - Handles Spanish/English content seamlessly

2. **Website Scraping** (`scrapers/websites_scraping.py`):
   - Primary: Crawl4AI for JavaScript-heavy sites
   - Fallback: Direct HTTP requests for simple pages
   - HTML cleaning and normalization
   - Progress tracking and error handling

3. **Data Validation** (`schemas/`):
   - `website_schema.py`: Defines business entity structure
   - `search_schema.py`: Defines search result structure
   - Automatic phone number formatting for Dominican Republic
   - Geographic validation for relevance

### Performance Considerations

- Default concurrency: 3-5 requests (configurable)
- Processing speed: 50+ websites per minute
- LLM batch size: 10 items per request
- Retry attempts: 3 with exponential backoff
- Request timeout: 30 seconds

### Output Structure

Data is saved to `output/` directory:
- `raw/`: Original scraped data (if --save-raw flag used)
- `cleaned/`: Processed and validated data
- Automatic backups created with timestamps

## Important Notes

- **API Key Required**: Set `API_KEY` environment variable for Google Gemini access
- **Dominican Republic Focus**: All extraction logic optimized for DR businesses
- **Language Support**: Handles both Spanish and English content
- **No Test Framework**: Currently no automated tests; manual testing required
- **No Linting Setup**: Code style conventions should match existing code
- **Logging**: Comprehensive logging via `logs/custom_logging.py`
- **Configuration**: Main prompts and settings in `settings.py`