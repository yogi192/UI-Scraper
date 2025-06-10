# Data Explorer Page Fix

## Problem
The Data Explorer page was showing "Loading..." indefinitely and never displaying any data.

## Root Causes
1. **API Endpoint URLs**: The page was trying to fetch from `/api/businesses` instead of the full backend URL `http://localhost:8000/api/businesses`
2. **Empty Database**: There was no test data in the MongoDB database to display

## Solutions Applied

### 1. Fixed API Endpoints
Updated the Data Explorer page (`frontend/pages/data.vue`) to use the correct backend URLs:
- Changed `/api/businesses` → `http://localhost:8000/api/businesses`
- Changed `/api/businesses/count` → `http://localhost:8000/api/businesses/count`

### 2. Added Test Data
Created a script (`scripts/add_test_data.py`) that adds 10 sample Dominican Republic businesses to the database including:
- Supermercado Nacional
- Restaurant El Conuco
- Blue Mall Punta Cana
- Hotel Barceló Santo Domingo
- Farmacia Carol
- La Sirena
- Banco Popular Dominicano
- Plaza Lama
- Caribbean Cinemas
- Hospital General Plaza de la Salud

### 3. Features Now Working
- ✅ Data loads properly from MongoDB
- ✅ Search functionality
- ✅ Category filtering
- ✅ Sorting by Date Added, Name, or Last Updated
- ✅ Pagination for large datasets
- ✅ View links to business detail pages

## How to Add More Data

1. **Via Web Interface**: Create a job to scrape real business data
2. **Via Script**: Run `docker exec ui-scraper-backend python scripts/add_test_data.py`
3. **Via Import Tool**: Use the data ingestion script to import existing JSON files

The Data Explorer now properly displays all businesses in the database with full search, filter, and sort capabilities!