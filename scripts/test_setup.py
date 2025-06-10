#!/usr/bin/env python3
"""
Setup Test Script for AI-Powered Business Data Crawler

This script verifies that all components are properly configured and running.
"""

import sys
import os
import asyncio
import subprocess
import json
import time
from typing import Dict, Tuple, List
import requests

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_status(message: str, status: str = "info"):
    """Print colored status messages"""
    if status == "success":
        print(f"{GREEN}✓{ENDC} {message}")
    elif status == "error":
        print(f"{RED}✗{ENDC} {message}")
    elif status == "warning":
        print(f"{YELLOW}!{ENDC} {message}")
    elif status == "info":
        print(f"{BLUE}ℹ{ENDC} {message}")

def check_command(command: str) -> bool:
    """Check if a command is available"""
    try:
        subprocess.run([command, "--version"], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def check_docker_service(service_name: str) -> bool:
    """Check if a Docker service is running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        return service_name in result.stdout
    except:
        return False

def check_port(port: int, host: str = "localhost") -> bool:
    """Check if a port is accessible"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

async def check_mongodb():
    """Check MongoDB connection"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        await client.server_info()
        await client.close()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)

def check_api_health(base_url: str = "http://localhost:8000") -> Tuple[bool, str]:
    """Check if API is healthy"""
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            return True, "API is healthy"
        return False, f"API returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to API"
    except Exception as e:
        return False, str(e)

def check_frontend(base_url: str = "http://localhost:3000") -> Tuple[bool, str]:
    """Check if frontend is accessible"""
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            return True, "Frontend is accessible"
        return False, f"Frontend returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to frontend"
    except Exception as e:
        return False, str(e)

def check_environment():
    """Check environment variables"""
    required_vars = ["API_KEY", "MONGODB_URL", "DATABASE_NAME"]
    optional_vars = ["REDIS_URL", "GOOGLE_API_KEY"]
    
    print("\n" + "="*50)
    print("ENVIRONMENT VARIABLES")
    print("="*50)
    
    missing_required = []
    for var in required_vars:
        if os.getenv(var):
            print_status(f"{var}: Set", "success")
        else:
            print_status(f"{var}: Not set", "error")
            missing_required.append(var)
    
    for var in optional_vars:
        if os.getenv(var):
            print_status(f"{var}: Set", "success")
        else:
            print_status(f"{var}: Not set (optional)", "warning")
    
    return len(missing_required) == 0

def check_file_structure():
    """Check if all required files and directories exist"""
    required_paths = [
        "backend/app/main.py",
        "frontend/app.vue",
        "docker-compose.yml",
        "scrapers/websites_scraping.py",
        "scrapers/llm_data_extraction.py",
        "schemas/website_schema.py",
        "utils/helpers.py",
        "scripts/ingest_json_to_mongodb.py"
    ]
    
    print("\n" + "="*50)
    print("FILE STRUCTURE")
    print("="*50)
    
    all_exist = True
    for path in required_paths:
        if os.path.exists(path):
            print_status(f"{path}: Found", "success")
        else:
            print_status(f"{path}: Missing", "error")
            all_exist = False
    
    return all_exist

async def run_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("AI-POWERED BUSINESS DATA CRAWLER - SETUP TEST")
    print("="*50)
    
    all_passed = True
    
    # 1. Check prerequisites
    print("\n" + "="*50)
    print("PREREQUISITES")
    print("="*50)
    
    if check_command("docker"):
        print_status("Docker: Installed", "success")
    else:
        print_status("Docker: Not installed", "error")
        all_passed = False
    
    if check_command("docker-compose"):
        print_status("Docker Compose: Installed", "success")
    else:
        print_status("Docker Compose: Not installed", "error")
        all_passed = False
    
    if check_command("python3"):
        print_status("Python 3: Installed", "success")
    else:
        print_status("Python 3: Not installed", "error")
        all_passed = False
    
    if check_command("node"):
        print_status("Node.js: Installed", "success")
    else:
        print_status("Node.js: Not installed", "error")
        all_passed = False
    
    # 2. Check file structure
    if not check_file_structure():
        all_passed = False
    
    # 3. Check environment
    if not check_environment():
        all_passed = False
        print_status("\nCreate a .env file with required variables", "warning")
    
    # 4. Check services
    print("\n" + "="*50)
    print("SERVICES")
    print("="*50)
    
    # Check Docker services
    services = {
        "ui-scraper-mongodb": 27017,
        "ui-scraper-redis": 6379,
        "ui-scraper-backend": 8000,
        "ui-scraper-frontend": 3000
    }
    
    for service, port in services.items():
        if check_docker_service(service):
            print_status(f"{service}: Running", "success")
        else:
            print_status(f"{service}: Not running", "warning")
            
        if check_port(port):
            print_status(f"Port {port}: Open", "success")
        else:
            print_status(f"Port {port}: Closed", "warning")
    
    # 5. Check MongoDB connection
    print("\n" + "="*50)
    print("DATABASE CONNECTION")
    print("="*50)
    
    mongo_ok, mongo_msg = await check_mongodb()
    if mongo_ok:
        print_status(f"MongoDB: {mongo_msg}", "success")
    else:
        print_status(f"MongoDB: {mongo_msg}", "error")
        all_passed = False
    
    # 6. Check API
    print("\n" + "="*50)
    print("API STATUS")
    print("="*50)
    
    api_ok, api_msg = check_api_health()
    if api_ok:
        print_status(f"Backend API: {api_msg}", "success")
    else:
        print_status(f"Backend API: {api_msg}", "warning")
    
    # 7. Check Frontend
    print("\n" + "="*50)
    print("FRONTEND STATUS")
    print("="*50)
    
    frontend_ok, frontend_msg = check_frontend()
    if frontend_ok:
        print_status(f"Frontend: {frontend_msg}", "success")
    else:
        print_status(f"Frontend: {frontend_msg}", "warning")
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    
    if all_passed and api_ok and frontend_ok:
        print_status("All tests passed! The application is ready to use.", "success")
        print(f"\n{GREEN}Access the application at:{ENDC}")
        print(f"  Frontend: {BLUE}http://localhost:3000{ENDC}")
        print(f"  API Docs: {BLUE}http://localhost:8000/docs{ENDC}")
    else:
        print_status("Some tests failed. Please check the errors above.", "error")
        print(f"\n{YELLOW}To start all services, run:{ENDC}")
        print(f"  {BLUE}docker-compose up -d{ENDC}")
    
    # Quick start guide
    print(f"\n{YELLOW}Quick Start Guide:{ENDC}")
    print("1. Create a .env file with your API keys")
    print("2. Run: docker-compose up -d")
    print("3. Visit: http://localhost:3000")
    print("4. Go to Settings and add your Google Gemini API key")
    print("5. Create your first scraping job!")

if __name__ == "__main__":
    asyncio.run(run_tests())