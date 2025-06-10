# AI Business Crawler Backend API

This is the FastAPI backend for the AI Business Crawler application.

## Prerequisites

- Python 3.8+
- MongoDB (running on localhost:27017)
- Redis (optional, for job queue - running on localhost:6379)

## Quick Start

1. **Install MongoDB** (if not already installed):
   ```bash
   # macOS
   brew tap mongodb/brew
   brew install mongodb-community
   brew services start mongodb-community
   
   # Ubuntu/Debian
   sudo apt-get install mongodb
   sudo systemctl start mongodb
   ```

2. **Clone and setup**:
   ```bash
   cd backend
   
   # Copy environment file
   cp .env.example .env
   
   # Run the server
   ./run.sh
   ```

   The script will:
   - Create a virtual environment
   - Install dependencies
   - Start the FastAPI server on http://localhost:8000

## Manual Setup

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/health

## Available Endpoints

- `GET /api/health` - Health check
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/businesses` - List businesses
- `GET /api/businesses/{id}` - Get specific business
- `GET /api/jobs` - List scraping jobs
- `POST /api/jobs` - Create new scraping job
- `GET /api/settings` - Get application settings

## Troubleshooting

### MongoDB Connection Error
If you see "Failed to connect to MongoDB", ensure MongoDB is running:
```bash
# Check if MongoDB is running
pgrep mongod

# Start MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongodb           # Linux
```

### CORS Issues
The backend is configured to accept requests from `http://localhost:3000` (the frontend). If you're running the frontend on a different port, update the CORS origins in `app/main.py`.

### 500 Errors
Check the console output for detailed error messages. Common issues:
- MongoDB not running
- Missing environment variables
- Import errors (ensure all dependencies are installed)

## Development

To add new endpoints:
1. Create a new router in `app/api/`
2. Add the router to `app/main.py`
3. Create corresponding models in `app/models/`
4. Add any database operations to `app/db/`

## Environment Variables

See `.env.example` for all available configuration options.