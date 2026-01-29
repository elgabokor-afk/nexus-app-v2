#!/bin/bash

# Navigate to data-engine directory
cd data-engine

# Start the Cosmos Worker (Scanner + AI)
# V2000: Force Retrain to match current container environment
python force_retrain.py

python cosmos_worker.py &

# Start the paper trader in the background
python paper_trader.py &

# V900/V1000: Start the WebSocket Bridge for real-time UI
python websocket_bridge.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
