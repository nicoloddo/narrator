#!/bin/bash

# just some checks to make sure the service environment matches the user environment. You can comment this printenv when deploying
# printenv > /home/ananaspi/service_environment.txt

git reset --hard

while ! ping -c 1 -W 1 github.com; do
    echo "Waiting for github - network interface might be down..."
    sleep 1
done

git pull

source venv/bin/activate

# Check command line arguments
if [[ "$1" == "--narrator" ]]; then
    # Remove the first argument and pass the rest
    shift
    # Run narrator.py with all remaining arguments
    echo "Running narrator.py"
    python narrator.py "$@" # uncomment this and comment the next line when you want to default to the instant narrator
    #python narrator.py "$@"
elif [[ "$1" == "--playht_narrator" ]]; then
    # Remove the first argument and pass the rest
    shift
    # Run alt_narrator_providers/playht_narrator.py with all remaining arguments
    echo "Running playht_narrator.py"
    python alt_narrator_providers/playht_narrator.py "$@"
else
    echo "Invalid argument. Please use --narrator or --playht_narrator."
    exit 1
fi