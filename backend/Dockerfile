FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend app
COPY backend/app /app/app

# Copy shared modules
COPY scrapers /app/scrapers
COPY schemas /app/schemas
COPY utils /app/utils
COPY logs /app/logs
COPY scripts /app/scripts
COPY settings.py /app/settings.py
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/input /app/output/raw /app/output/cleaned

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]