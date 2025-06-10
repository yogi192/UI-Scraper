#!/usr/bin/env python3
"""
JSON to MongoDB Data Ingestion Tool

This script imports business data from JSON files into MongoDB database.
It handles duplicate detection and data merging automatically.

Usage:
    python scripts/ingest_json_to_mongodb.py [--file <json_file>] [--dir <directory>]
"""

import asyncio
import json
import os
import sys
import argparse
from typing import List, Dict, Any
from datetime import datetime
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mongodb_client import mongodb_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Load data from a JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Check if it's wrapped in a results key
            if 'results' in data:
                return data['results']
            elif 'entities' in data:
                return data['entities']
            elif 'data' in data:
                return data['data']
            else:
                # Single business object
                return [data]
        else:
            logger.error(f"Unexpected data format in {file_path}")
            return []
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []

async def ingest_file(file_path: str) -> Dict[str, int]:
    """Ingest a single JSON file into MongoDB"""
    logger.info(f"Processing file: {file_path}")
    
    businesses = await load_json_file(file_path)
    if not businesses:
        return {"saved": 0, "updated": 0}
    
    # Determine source type from file name
    source_type = "search" if "search" in file_path.lower() else "website"
    
    # Save to MongoDB
    result = await mongodb_client.save_businesses(businesses, source_type=source_type)
    
    logger.info(f"Completed {file_path}: {result}")
    return result

async def ingest_directory(directory: str) -> Dict[str, int]:
    """Ingest all JSON files from a directory"""
    total_saved = 0
    total_updated = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                result = await ingest_file(file_path)
                total_saved += result["saved"]
                total_updated += result["updated"]
    
    return {"saved": total_saved, "updated": total_updated}

async def main():
    parser = argparse.ArgumentParser(description="Import JSON data into MongoDB")
    parser.add_argument("--file", "-f", help="Path to a single JSON file to import")
    parser.add_argument("--dir", "-d", help="Path to directory containing JSON files")
    parser.add_argument("--output-dir", default="output/cleaned", help="Default output directory to scan")
    
    args = parser.parse_args()
    
    try:
        # Connect to MongoDB
        await mongodb_client.connect()
        
        if args.file:
            # Process single file
            result = await ingest_file(args.file)
            print(f"\nIngestion complete: {result['saved']} new records, {result['updated']} updated")
            
        elif args.dir:
            # Process directory
            result = await ingest_directory(args.dir)
            print(f"\nIngestion complete: {result['saved']} new records, {result['updated']} updated")
            
        else:
            # Process default output directory
            logger.info(f"No file or directory specified, scanning {args.output_dir}")
            result = await ingest_directory(args.output_dir)
            print(f"\nIngestion complete: {result['saved']} new records, {result['updated']} updated")
            
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
    finally:
        await mongodb_client.close()

if __name__ == "__main__":
    asyncio.run(main())