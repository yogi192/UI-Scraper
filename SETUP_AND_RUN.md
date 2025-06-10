# Setup and Run Guide - AI-Powered Business Data Crawler

This guide provides step-by-step instructions to set up and run the web application.

## Prerequisites

1. **Python 3.13+** with `uv` package manager
2. **Node.js 20+** with npm
3. **Docker** and **Docker Compose**
4. **Google Gemini API Key** (get it from https://makersuite.google.com/app/apikey)

## Quick Setup

### 1. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key:
```
API_KEY=your_actual_google_gemini_api_key
GOOGLE_API_KEY=your_actual_google_gemini_api_key
```

### 2. Option A: Run with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Check if services are running
docker ps

# View logs
docker-compose logs -f
```

Access the application:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### 2. Option B: Run Locally (Development)

```bash
# Start MongoDB and Redis
docker-compose up -d mongodb redis

# In Terminal 1 - Backend
uv sync
uv run uvicorn backend.app.main:app --reload --port 8000

# In Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

Or use the convenience script:
```bash
./scripts/start_local_dev.sh
```

## First Time Setup

1. **Access the Application**
   - Open http://localhost:3000 in your browser

2. **Configure API Key**
   - Go to Settings (http://localhost:3000/settings)
   - Enter your Google Gemini API key
   - Click "Save API Key"

3. **Import Existing Data (Optional)**
   ```bash
   # If using Docker
   docker exec ui-scraper-backend python scripts/ingest_json_to_mongodb.py --dir output/cleaned

   # If running locally
   uv run python scripts/ingest_json_to_mongodb.py --dir output/cleaned
   ```

## Using the Application

### Dashboard
- View total businesses collected
- Monitor job statistics
- See top business categories
- Track recent jobs

### Data Explorer
- Browse all collected businesses
- Search by name, address, or description
- Filter by category
- Sort by date or name
- Click on any business for full details

### Creating Jobs

1. **Website Scraping**
   - Click "New Job" on Jobs page
   - Select "Website Scraping"
   - Enter URLs (one per line)
   - Click "Create Job"

2. **Search Scraping**
   - Click "New Job" on Jobs page
   - Select "Search Scraping"
   - Enter search terms (one per line)
   - Click "Create Job"

3. **Full Pipeline**
   - Click "New Job" on Jobs page
   - Select "Full Pipeline"
   - Enter search terms
   - System will search and then scrape found URLs

### Monitoring Jobs
- Jobs page shows all jobs with real-time status
- Click on any job to see detailed progress
- Running jobs update automatically
- Cancel pending jobs if needed

## Testing the Setup

Run the test script to verify everything is working:

```bash
uv run python scripts/test_setup.py
```

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
docker ps | grep mongodb

# Test connection
docker exec -it ui-scraper-mongodb mongosh
```

### Backend Not Starting
```bash
# Check logs
uv run uvicorn backend.app.main:app --reload --log-level debug

# Verify MongoDB is accessible
curl http://localhost:27017
```

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules .nuxt
npm install
npm run dev
```

### API Key Issues
- Ensure your API key is valid
- Check .env file has correct format
- Try setting in Settings page instead

## Stopping Services

### Docker
```bash
docker-compose down
```

### Local Development
- Press Ctrl+C in terminal windows
- Or kill specific processes:
  ```bash
  pkill -f uvicorn
  pkill -f "npm run dev"
  docker-compose down
  ```

## Data Management

### Export Data
```bash
# Export from MongoDB to JSON
docker exec ui-scraper-mongodb mongoexport \
  --db ui_scraper \
  --collection businesses \
  --out /data/db/businesses.json
```

### Backup Database
```bash
# Create backup
docker exec ui-scraper-mongodb mongodump \
  --db ui_scraper \
  --out /data/db/backup

# Copy to host
docker cp ui-scraper-mongodb:/data/db/backup ./mongodb_backup
```

## Performance Tips

1. **Adjust Concurrency**
   - Default: 3-5 concurrent requests
   - Increase for faster scraping (may trigger rate limits)
   - Decrease for more reliable scraping

2. **Monitor Resources**
   ```bash
   docker stats
   ```

3. **Clear Old Logs**
   ```bash
   # In MongoDB
   docker exec -it ui-scraper-mongodb mongosh
   use ui_scraper
   db.logs.deleteMany({ timestamp: { $lt: new Date(Date.now() - 7*24*60*60*1000) } })
   ```

## Security Notes

- Never commit .env file to git
- Keep your API keys secure
- Use strong passwords for production MongoDB
- Consider using HTTPS for production deployment

## Need Help?

1. Check the test script: `uv run python scripts/test_setup.py`
2. View logs: `docker-compose logs -f`
3. Check README_WEB_APP.md for more details
4. Review the original CLI documentation in README.md