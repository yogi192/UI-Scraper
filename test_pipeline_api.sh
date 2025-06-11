#!/bin/bash

echo "🚀 Testing Pipeline Jobs"
echo ""
echo "============================================================"
echo "TEST 1: Creating a CORRECT pipeline job with search terms"
echo "============================================================"

# Create pipeline job with proper search terms
RESPONSE=$(curl -s -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "type": "pipeline",
    "parameters": {
      "terms": ["ferreterias santo domingo", "hardware stores punta cana"]
    }
  }')

JOB_ID=$(echo $RESPONSE | jq -r '._id')
echo "✅ Pipeline job created: $JOB_ID"

# Monitor job
echo "Monitoring job progress..."
sleep 2

while true; do
  JOB_STATUS=$(curl -s http://localhost:8000/api/jobs/$JOB_ID)
  STATUS=$(echo $JOB_STATUS | jq -r '.status')
  PROGRESS=$(echo $JOB_STATUS | jq -r '.progress_message // empty')
  
  if [ ! -z "$PROGRESS" ]; then
    echo "📊 Progress: $PROGRESS"
  fi
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    echo ""
    echo "Job $STATUS!"
    
    # Show result
    echo ""
    echo "Result:"
    echo $JOB_STATUS | jq '.result'
    
    # Show summary
    URLS_PROCESSED=$(echo $JOB_STATUS | jq -r '.result.urls_processed // 0')
    ENTITIES_FOUND=$(echo $JOB_STATUS | jq -r '.result.entities_found // 0')
    
    echo ""
    echo "📊 Summary:"
    echo "- URLs processed: $URLS_PROCESSED"
    echo "- Entities found: $ENTITIES_FOUND"
    
    break
  fi
  
  sleep 3
done

echo ""
echo "============================================================"
echo "TEST 2: Creating a website job with direct URL"
echo "============================================================"

# Create website job with URL
RESPONSE=$(curl -s -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "type": "website",
    "parameters": {
      "urls": ["https://paginasamarillas.com.do/es/business/search/santo-domingo/c/ferreterias"]
    }
  }')

JOB_ID=$(echo $RESPONSE | jq -r '._id')
echo "✅ Website job created: $JOB_ID"

# Monitor job
echo "Monitoring job progress..."
sleep 2

while true; do
  JOB_STATUS=$(curl -s http://localhost:8000/api/jobs/$JOB_ID)
  STATUS=$(echo $JOB_STATUS | jq -r '.status')
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    echo ""
    echo "Job $STATUS!"
    
    # Show result summary
    URLS_PROCESSED=$(echo $JOB_STATUS | jq -r '.result.urls_processed // 0')
    ENTITIES_FOUND=$(echo $JOB_STATUS | jq -r '.result.entities_found // 0')
    
    echo ""
    echo "📊 Summary:"
    echo "- URLs processed: $URLS_PROCESSED"
    echo "- Entities found: $ENTITIES_FOUND"
    
    break
  fi
  
  sleep 3
done

echo ""
echo "============================================================"
echo "KEY POINTS:"
echo "============================================================"
echo "1. Pipeline jobs: Use search terms like 'ferreterias santo domingo'"
echo "2. Website jobs: Use direct URLs"
echo "3. Your original job failed because you gave a URL to a pipeline job"
echo "============================================================"