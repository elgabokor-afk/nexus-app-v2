
FROM hummingbot/hummingbot:latest

# Switch to root to install dependencies
USER root

# Install Supabase client for Python
RUN pip install supabase postgrest

# Create directories for our custom scripts
RUN mkdir -p /home/hummingbot/scripts

# Switch back to default user
USER hummingbot

# Copy our custom strategy script
COPY nexus_connector.py /home/hummingbot/scripts/nexus_connector.py

# Entrypoint is already handled by the base image, but we can override CMD if needed
# For now, we'll stick to the default which starts the HB client.
# In production (Railway), we might want to start the script directly using:
# CMD ["python", "bin/hummingbot_quickstart.py", "--script", "nexus_connector.py"]
