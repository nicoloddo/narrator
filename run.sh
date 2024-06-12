#!/bin/bash

git reset --hard

while ! ping -c 1 -W 1 github.com; do
    echo "Waiting for github - network interface might be down..."
    sleep 1
done

git pull

source venv/bin/activate
. setenv.sh
. agent.sh

# Check command line arguments
if [[ "$1" == "--narrator" ]]; then
    # Run narrator.py
    python narrator.py
elif [[ "$1" == "--instant_narrator" ]]; then
    # Run instant_narrator.py
    python instant_narrator.py
else
    echo "Invalid argument. Please use --narrator or --instant_narrator."
    exit 1
fi