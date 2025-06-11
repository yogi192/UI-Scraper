#!/usr/bin/env python3
"""
Test the pipeline job through the API
"""

import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000/api/jobs"

def create_pipeline_job(search_terms):
    """Create a pipeline job via API"""
    
    # Pipeline job should use search terms, not URLs
    payload = {
        "type": "pipeline",
        "parameters": {
            "terms": search_terms
        }
    }
    
    print(f"Creating pipeline job with terms: {search_terms}")
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        job = response.json()
        print(f"✅ Job created successfully: {job.get('_id')}")
        return job.get('_id')
    else:
        print(f"❌ Failed to create job: {response.status_code}")
        print(response.text)
        return None

def monitor_job(job_id):
    """Monitor job progress"""
    
    print(f"\nMonitoring job {job_id}...")
    
    previous_message = ""
    while True:
        response = requests.get(f"{API_URL}/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            status = job.get('status')
            progress_msg = job.get('progress_message', '')
            
            # Print progress if changed
            if progress_msg != previous_message:
                print(f"📊 Progress: {progress_msg}")
                previous_message = progress_msg
            
            # Check if job is done
            if status in ['completed', 'failed']:
                print(f"\n{'✅' if status == 'completed' else '❌'} Job {status}")
                
                # Print result
                result = job.get('result', {})
                if result:
                    print("\nResult:")
                    print(json.dumps(result, indent=2))
                
                # Check for error
                if job.get('error'):
                    print(f"\nError: {job['error']}")
                
                return job
            
        else:
            print(f"Failed to get job status: {response.status_code}")
            break
            
        time.sleep(2)

def test_correct_pipeline():
    """Test pipeline with correct search terms"""
    
    print("="*60)
    print("TEST 1: Pipeline with proper search terms")
    print("="*60)
    
    # Use actual search terms, not URLs
    search_terms = ["ferreterias santo domingo", "hardware stores dominican republic"]
    
    job_id = create_pipeline_job(search_terms)
    if job_id:
        result = monitor_job(job_id)
        
        # Analyze result
        if result and result.get('result'):
            job_result = result['result']
            
            print("\n📊 Pipeline Summary:")
            print(f"URLs processed: {job_result.get('urls_processed', 0)}")
            print(f"Entities found: {job_result.get('entities_found', 0)}")
            print(f"Saved to DB: {job_result.get('saved_to_db', False)}")
            
            # Check if we got actual data
            if job_result.get('entities_found', 0) > 0:
                print("\n✅ Pipeline successfully extracted business data!")
            else:
                print("\n⚠️  Pipeline completed but no entities were extracted")
                print("This might be due to:")
                print("- Google blocking/captcha")
                print("- No results for search terms")
                print("- LLM extraction issues")

def test_website_job_with_url():
    """Test website job with the URL"""
    
    print("\n" + "="*60)
    print("TEST 2: Website job with direct URL")
    print("="*60)
    
    # For URLs, use website job type, not pipeline
    payload = {
        "type": "website",
        "parameters": {
            "urls": ["https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"]
        }
    }
    
    print("Creating website job with URL...")
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        job = response.json()
        job_id = job.get('_id')
        print(f"✅ Job created: {job_id}")
        
        result = monitor_job(job_id)
        
        if result and result.get('result'):
            job_result = result['result']
            print("\n📊 Website Scraping Summary:")
            print(f"URLs processed: {job_result.get('urls_processed', 0)}")
            print(f"Entities found: {job_result.get('entities_found', 0)}")

def main():
    print("🚀 Testing Pipeline Jobs\n")
    
    # Test 1: Correct pipeline usage
    test_correct_pipeline()
    
    # Test 2: Website job for URL
    test_website_job_with_url()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("- Pipeline jobs: Use search terms (e.g., 'ferreterias santo domingo')")
    print("- Website jobs: Use direct URLs")
    print("- Search jobs: Use search terms to get URLs only")
    print("="*60)

if __name__ == "__main__":
    main()