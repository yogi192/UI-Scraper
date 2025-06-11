#!/usr/bin/env python3
"""Test dashboard API endpoint"""
import requests

try:
    response = requests.get("http://localhost:8000/api/dashboard/stats")
    if response.status_code == 200:
        data = response.json()
        print("Dashboard API Response:")
        print(f"Total Businesses: {data['stats']['total_businesses']}")
        print(f"Total Jobs: {data['stats']['total_jobs']}")
        print(f"Completed Jobs: {data['stats']['completed_jobs']}")
        print(f"Failed Jobs: {data['stats']['failed_jobs']}")
        print(f"Categories: {len(data['categories'])}")
        print(f"Recent Jobs: {len(data['recent_jobs'])}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error calling API: {e}")