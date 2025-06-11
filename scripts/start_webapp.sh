#!/bin/bash
# Startup script for AI-Powered Business Data Crawler Web Application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI-Powered Business Data Crawler${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cat > .env << EOF
# API Keys
GOOGLE_API_KEY=your_google_gemini_api_key_here

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ui_scraper

# Redis
REDIS_URL=redis://localhost:6379

# API Base URL for frontend
API_BASE_URL=http://localhost:8000
EOF
    echo -e "${GREEN}Created .env file. Please edit it with your Google API key.${NC}"
fi

# Stop any existing containers
echo -e "\n${YELLOW}Stopping any existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"

# Function to wait for a service
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is ready${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "\n${RED}✗ $service_name failed to start${NC}"
    return 1
}

echo -n "Waiting for MongoDB"
wait_for_service "MongoDB" "http://localhost:27017" || true

echo -n "Waiting for Redis"
wait_for_service "Redis" "http://localhost:6379" || true

echo -n "Waiting for Backend API"
wait_for_service "Backend API" "http://localhost:8000/api/health"

echo -n "Waiting for Frontend"
wait_for_service "Frontend" "http://localhost:3000"

# Import existing data if available
if [ -d "output/cleaned" ] && [ "$(ls -A output/cleaned/*.json 2>/dev/null)" ]; then
    echo -e "\n${YELLOW}Found existing data files. Importing to MongoDB...${NC}"
    docker exec ui-scraper-backend python scripts/ingest_json_to_mongodb.py --dir output/cleaned || true
fi

# Show status
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All services are running!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Access the application at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  MongoDB:  ${GREEN}mongodb://localhost:27017${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "1. Visit ${GREEN}http://localhost:3000/settings${NC}"
echo -e "2. Add your Google Gemini API key"
echo -e "3. Create your first scraping job!"

echo -e "\n${YELLOW}To view logs:${NC}"
echo -e "  docker-compose logs -f"

echo -e "\n${YELLOW}To stop all services:${NC}"
echo -e "  docker-compose down"