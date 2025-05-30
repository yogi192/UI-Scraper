# AI-Powered Business Data Crawler

An advanced web scraping and data extraction tool designed to collect business information from websites in the Dominican Republic.

## Features

- **Website Scraping**: Directly scrape business data from specific websites
- **Search Scraping**: Scrape search results to find relevant business websites
- **End-to-End Pipeline**: Search → Extract URLs → Scrape Websites → Extract Data
- **LLM Data Extraction**: Use AI to extract structured business data from raw HTML
- **Multiple Scraping Methods**: Support for direct HTTP requests and browser-based scraping

## Project Structure

```
ai_powered_bussineses_data_crawler/
├── debug_files/            # Temporary files for debugging
├── input/                  # Input data files
│   ├── search_terms_list.json
│   ├── search_urls_list.json
│   └── website_urls_list.json
├── logs/                   # Log files
├── output/                 # Output data files
│   ├── backups/            # Timestamped backups
│   ├── cleaned/            # Processed data
│   └── raw/                # Raw scraped data
├── schemas/                # Data schemas
├── scrapers/               # Scraper modules
│   ├── websites_scraping.py
│   ├── searches_scraping.py
│   └── llm_data_extraction.py
├── utils/                  # Utility functions
└── main.py                 # Main controller script
```

## Usage

### Basic Usage

```bash
# Scrape websites from input/website_urls_list.json
python main.py --mode website

# Scrape search results from input/search_terms_list.json
python main.py --mode search

# Run full pipeline from search to data extraction
python main.py --mode pipeline
```

### Advanced Options

```bash
# Specify custom URLs to scrape
python main.py --mode website --urls "https://example1.com" "https://example2.com"

# Specify custom search terms
python main.py --mode search --search-terms "restaurants santo domingo" "hotels punta cana"

# Use crawl4ai method for website scraping
python main.py --mode website --scrape-method crawl4ai

# Specify custom input file
python main.py --mode website --input-file "my_urls.json"
```

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   # Create .env file with API keys
   OPEN_ROUTER_API_KEY=your_api_key_here
   ```

3. Prepare input data:
   - Add website URLs to `input/website_urls_list.json`
   - Add search terms to `input/search_terms_list.json`

4. Run the scraper:
   ```bash
   python main.py --mode website
   ```

## Output

The tool generates output files in the following locations:

- Raw scraped data: `output/raw/website_raw_data.json`
- Processed data: `output/cleaned/website_cleaned_data.json`
- Backups: `output/backups/website_raw_YYYYMMDD_HHMMSS.json`

## License

This project is proprietary and confidential.