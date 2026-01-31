FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    procps \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY data-engine/ ./data-engine/
COPY config/ ./config/
COPY start_services_simple.sh ./start_services.sh
RUN chmod +x start_services.sh

# Create log directory
RUN mkdir -p /tmp

# Set environment
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Start services
CMD ["bash", "./start_services.sh"]
