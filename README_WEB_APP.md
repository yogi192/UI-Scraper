# Web Application Setup Guide

This guide explains how to run the new web application interface for the AI-Powered Business Data Crawler.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.13+ (for local development)
- Node.js 20+ (for frontend development)

## Quick Start with Docker

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MongoDB: localhost:27017

3. **Import existing data (optional):**
   ```bash
   docker exec -it ui-scraper-backend python scripts/ingest_json_to_mongodb.py --dir output/cleaned
   ```

## Local Development Setup

### Backend

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Start MongoDB and Redis:**
   ```bash
   docker-compose up -d mongodb redis
   ```

3. **Run the backend:**
   ```bash
   uv run uvicorn backend.app.main:app --reload --port 8000
   ```

### Frontend

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the development server:**
   ```bash
   npm run dev
   ```

3. **Access at:** http://localhost:3000

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Keys
API_KEY=your_google_gemini_api_key
GOOGLE_API_KEY=your_google_gemini_api_key

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ui_scraper

# Redis
REDIS_URL=redis://localhost:6379
```

### First Time Setup

1. Navigate to http://localhost:3000/settings
2. Enter your Google Gemini API key
3. Start creating scraping jobs!

## Features Overview

### Dashboard
- View total businesses collected
- Monitor job statistics
- See top business categories
- Track recent jobs

### Data Explorer
- Search and filter businesses
- Sort by various fields
- Paginated data table
- Click to view full details

### Jobs Management
- Create new scraping jobs
- Monitor job progress in real-time
- View job details and results
- Cancel pending jobs

### Business Details
- View complete business information
- See all structured data fields
- Access source URLs
- View location on map

## API Endpoints

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

### Businesses
- `GET /api/businesses` - List businesses with pagination
- `GET /api/businesses/{id}` - Get business details
- `GET /api/businesses/categories/list` - Get category list
- `GET /api/businesses/count` - Get total count

### Jobs
- `GET /api/jobs` - List jobs
- `POST /api/jobs` - Create new job
- `GET /api/jobs/{id}` - Get job details
- `DELETE /api/jobs/{id}` - Cancel job

### Settings
- `GET /api/settings` - Check API key status
- `PUT /api/settings` - Update API key

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
docker ps | grep mongodb

# View MongoDB logs
docker logs ui-scraper-mongodb
```

### Frontend Build Issues
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules .nuxt
npm install
npm run dev
```

### Backend Import Issues
```bash
# Check Python path
uv run python -c "import sys; print(sys.path)"

# Run with explicit path
PYTHONPATH=/path/to/UI-Scraper uv run python backend/app/main.py
```

## Development Tips

1. **Hot Reload:** Both frontend and backend support hot reload in development mode

2. **Database GUI:** Use MongoDB Compass to connect to `mongodb://localhost:27017`

3. **API Testing:** Access FastAPI docs at http://localhost:8000/docs

4. **Logs:** MongoDB logs are saved to the `logs` collection

5. **Data Import:** Use the ingestion script to import existing JSON data:
   ```bash
   uv run python scripts/ingest_json_to_mongodb.py --file output/cleaned/website_cleaned_data.json
   ```