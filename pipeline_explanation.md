# Pipeline Job Explanation

## What Went Wrong

Your pipeline job failed to extract data because you used it incorrectly:

```json
{
  "type": "pipeline",
  "parameters": {
    "terms": ["https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"]
  }
}
```

**Issue**: You provided a URL as a search term. The pipeline job expects search keywords, not URLs.

## How Pipeline Jobs Work

1. **Search Phase**: Takes search terms and searches Google for relevant URLs
2. **Scraping Phase**: Takes the found URLs and scrapes them for business data

## Correct Usage

### Option 1: Pipeline Job (Search + Scrape)
Use when you have search terms and want to find AND scrape businesses:

```json
{
  "type": "pipeline",
  "parameters": {
    "terms": ["ferreterias santo domingo", "hardware stores dominican republic"]
  }
}
```

### Option 2: Website Job (Direct Scrape)
Use when you already have URLs:

```json
{
  "type": "website",
  "parameters": {
    "urls": ["https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"]
  }
}
```

### Option 3: Search Job (Find URLs Only)
Use when you want to find URLs but not scrape them yet:

```json
{
  "type": "search",
  "parameters": {
    "terms": ["ferreterias santo domingo"]
  }
}
```

## Why Your Job "Succeeded" But Found Nothing

1. The pipeline tried to search Google for your URL
2. Google doesn't return meaningful results when searching for a full URL
3. No URLs were found in the search phase
4. The scraping phase had nothing to scrape
5. Job completed "successfully" but with 0 results

## Testing the Correct Way

Let me create the correct jobs for you...