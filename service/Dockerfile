FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy parent directory (to access v2/)
COPY ../v2 /app/v2
COPY ../requirements.txt /app/parent_requirements.txt
RUN pip install --no-cache-dir -r /app/parent_requirements.txt

# Copy service code
COPY api.py .

# Expose port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

