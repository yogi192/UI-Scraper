#!/bin/bash
# Local development startup script for AI-Powered Business Data Crawler

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Local Development Environment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please edit it with your API keys.${NC}"
fi

# Start MongoDB and Redis with Docker
echo -e "\n${YELLOW}Starting MongoDB and Redis...${NC}"
docker-compose up -d mongodb redis

# Wait for services
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
sleep 5

# Install backend dependencies
echo -e "\n${YELLOW}Installing backend dependencies...${NC}"
uv sync

# Start backend
echo -e "\n${YELLOW}Starting backend API...${NC}"
uv run uvicorn backend.app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Install frontend dependencies
echo -e "\n${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install

# Start frontend
echo -e "\n${YELLOW}Starting frontend...${NC}"
npm run dev &
FRONTEND_PID=$!

cd ..

# Show access information
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All services are starting!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Access the application at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  MongoDB:  ${GREEN}mongodb://localhost:27017${NC}"

echo -e "\n${YELLOW}Process IDs:${NC}"
echo -e "  Backend PID: $BACKEND_PID"
echo -e "  Frontend PID: $FRONTEND_PID"

echo -e "\n${YELLOW}To stop all services:${NC}"
echo -e "  Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo -e "  docker-compose down"

# Keep script running
echo -e "\n${GREEN}Press Ctrl+C to stop all services${NC}"
wait