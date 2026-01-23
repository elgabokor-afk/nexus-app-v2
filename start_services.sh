#!/bin/bash

# Navigate to data-engine directory
cd data-engine

# Start the scanner in the background
python scanner.py &

# Start the paper trader in the background
python paper_trader.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
