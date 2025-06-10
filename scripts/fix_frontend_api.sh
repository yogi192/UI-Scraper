#!/bin/bash

echo "🔧 Applying Frontend API Fix..."

# Update all frontend pages to use direct backend URL
cd frontend

# Update pages to use localhost:8000 directly
echo "📝 Updating API calls in frontend pages..."

# Update index.vue
sed -i.bak "s|await \$fetch('/api/|await \$fetch('http://localhost:8000/api/|g" pages/index.vue

# Update data.vue  
sed -i.bak "s|await \$fetch('/api/|await \$fetch('http://localhost:8000/api/|g" pages/data.vue

# Update jobs.vue
sed -i.bak "s|await \$fetch('/api/|await \$fetch('http://localhost:8000/api/|g" pages/jobs.vue

# Update jobs/[id].vue
sed -i.bak "s|await \$fetch(\`/api/|await \$fetch(\`http://localhost:8000/api/|g" pages/jobs/[id].vue

# Update businesses/[id].vue
sed -i.bak "s|await \$fetch(\`/api/|await \$fetch(\`http://localhost:8000/api/|g" pages/businesses/[id].vue

# Update settings.vue
sed -i.bak "s|await \$fetch('/api/|await \$fetch('http://localhost:8000/api/|g" pages/settings.vue

# Update NewJobModal.vue
sed -i.bak "s|await \$fetch('/api/|await \$fetch('http://localhost:8000/api/|g" components/NewJobModal.vue

# Remove backup files
rm -f pages/*.bak pages/*/*.bak components/*.bak

cd ..

echo "✅ Frontend API calls updated!"
echo "🔄 Rebuilding frontend container..."

docker-compose up -d --build frontend

echo "✅ Fix applied! The frontend should now be able to connect to the backend."
echo "🌐 Access the application at http://localhost:3000"