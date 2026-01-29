#!/bin/bash

# Navigate to data-engine directory
cd data-engine

# Start the Cosmos Worker (Scanner + AI)
# V2000: Force Retrain to match current container environment
python force_retrain.py

# V4200: PhD Mode - Seed Academic Knowledge (Arxiv)
python seed_academic_knowledge.py


python cosmos_worker.py &

# V410: Start the AI Oracle (Neural Link)
python cosmos_oracle.py &

# V3600: Start Macro Brain (Correlation Engine)
python macro_feed.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
