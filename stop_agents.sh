#!/bin/bash

# This script finds and kills the Solar and Utility agent processes
# by looking for processes listening on ports 8000 and 8001.

echo "---"
echo "Attempting to stop any running agents..."
echo "---"

# Find and kill the process on port 8000 (Utility Agent)
UTILITY_PID=$(lsof -ti :8000)
if [ -n "$UTILITY_PID" ]; then
    echo "Found Utility Agent running on PID $UTILITY_PID. Stopping..."
    kill -9 $UTILITY_PID
    echo "Utility Agent stopped."
else
    echo "No agent found on port 8000."
fi

# Find and kill the process on port 8001 (Solar Agent)
SOLAR_PID=$(lsof -ti :8001)
if [ -n "$SOLAR_PID" ]; then
    echo "Found Solar Agent running on PID $SOLAR_PID. Stopping..."
    kill -9 $SOLAR_PID
    echo "Solar Agent stopped."
else
    echo "No agent found on port 8001."
fi

echo "---"
echo "Agent shutdown process complete." 