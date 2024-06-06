#!/bin/bash

# Terminal 1: Runs capture.py
lxterminal --command="bash -c 'source venv/bin/activate; . setenv.sh; . setvoice.sh; python3 capture.py; exec bash'" &
PID1=$!

# Terminal 2: Runs narrator.py
lxterminal --command="bash -c 'source venv/bin/activate; . setenv.sh; . setvoice.sh; python3 narrator.py; exec bash'" &
PID2=$!

echo "Capture.py running in terminal with PID $PID1"
echo "Narrator.py running in terminal with PID $PID2"
echo $PID1 > "/tmp/terminal1.pid"
echo $PID2 > "/tmp/terminal2.pid"

echo "Both scripts are now running in separate terminals."
