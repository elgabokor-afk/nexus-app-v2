#!/bin/bash

# Navigate to data-engine directory
cd data-engine

# Start the scanner in the background
python scanner.py &

# Start the paper trader in the background
python paper_trader.py &

# V900/V1000: Start the WebSocket Bridge for real-time UI
python websocket_bridge.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
