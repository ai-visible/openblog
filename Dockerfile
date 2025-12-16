FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip
RUN curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py --break-system-packages && \
    python -m pip install --upgrade pip setuptools wheel --break-system-packages

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python -m pip install -r requirements.txt --break-system-packages

# Install Playwright Chromium
RUN python -m playwright install chromium

# Copy application code
COPY . .

# Copy and make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Use entrypoint script with shell to ensure variable expansion
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]

