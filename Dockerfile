FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (for building some python packages)
RUN apt-get update && apt-get install -y gcc

# Copy requirements (Create this if missing, but usually defined in python projects)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire data-engine and necessary SQL files
# Copy the entire data-engine and necessary SQL files
# Copy the entire data-engine and necessary SQL files
COPY data-engine/ ./data-engine/
COPY start_services.sh .
RUN chmod +x start_services.sh

# FORCE RETRAIN MODEL to match container's scikit-learn version
RUN python data-engine/force_retrain.py

# Note: We do NOT copy .env.local. Secrets must be injected by Railway/Docker Env.

# Default command (overridden by docker-compose)
CMD ["python", "data-engine/cosmos_worker.py"]
