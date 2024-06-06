#!/bin/bash

# Terminal 1: Runs capture.py
lxterminal --command="bash -c 'source venv/bin/activate; . setenv.sh; . setvoice.sh; python3 capture.py; exec bash'" &

# Terminal 2: Runs narrator.py
lxterminal --command="bash -c 'source venv/bin/activate; . setenv.sh; . setvoice.sh; python3 narrator.py; exec bash'" &

echo "Both scripts are now running in separate terminals."
