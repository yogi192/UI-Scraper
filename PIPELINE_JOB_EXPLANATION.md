# Pipeline Job Explanation

## ❌ Why Your Pipeline Job Found Zero Businesses

Your pipeline job completed but found 0 businesses because **you used it incorrectly**.

### What You Did:
```json
{
  "type": "pipeline",
  "parameters": {
    "terms": ["https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"]
  }
}
```

### The Problem:
You passed a **URL** as a search term. Pipeline jobs expect **search keywords**, not URLs!

## 📊 Understanding Job Types

### 1️⃣ Pipeline Job (Search + Scrape)
**Purpose**: Find businesses by searching Google, then scrape the results

**Flow**:
```
Search Terms → Google Search → Extract URLs → Scrape URLs → Business Data
```

**Example**:
```json
{
  "type": "pipeline",
  "parameters": {
    "terms": ["ferreterias santo domingo", "hardware stores DR"]
  }
}
```

### 2️⃣ Website Job (Direct Scrape)
**Purpose**: Scrape business data from specific URLs you already have

**Flow**:
```
URLs → Direct Scraping → Business Data
```

**Example**:
```json
{
  "type": "website",
  "parameters": {
    "urls": ["https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"]
  }
}
```

### 3️⃣ Search Job (Find URLs Only)
**Purpose**: Search Google and return URLs without scraping

**Flow**:
```
Search Terms → Google Search → URLs (no scraping)
```

## 💡 What Happened in Your Case

1. You gave the pipeline job a URL: `https://paginasamarillas.com.do/...`
2. The pipeline searched Google for that exact URL string
3. Google doesn't return useful results when searching for full URLs
4. No URLs were found in search results
5. With no URLs to scrape, the job completed with 0 results

## ✅ The Solution

Since you already have the URL, use a **Website Job**:

```json
{
  "type": "website", 
  "parameters": {
    "urls": ["https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"]
  }
}
```

**Result**: This correctly scraped the page and found **15 ferreterías** (as shown in your `ferreterias_job_result.json`)!

## 🎯 Quick Reference

| I have... | Use job type | Example input |
|-----------|--------------|---------------|
| Search terms | `pipeline` | "ferreterias santo domingo" |
| URLs | `website` | "https://example.com" |
| Need URLs only | `search` | "restaurants punta cana" |

## Summary

- **Pipeline jobs**: For when you want to search AND scrape
- **Website jobs**: For when you already have URLs
- Your job failed because you used a pipeline job with a URL instead of search terms