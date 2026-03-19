FROM python:3.12-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY vsco.py .
COPY api.py .

# Expose port 3000 (Coolify default)
EXPOSE 3000

# Run the API server on port 3000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "3000", "--proxy-headers"]
