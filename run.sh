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
. setenv.sh
. agent.sh

# Check command line arguments
if [[ "$1" == "--narrator" ]]; then
    # Remove the first argument and pass the rest
    shift
    # Run narrator.py with all remaining arguments
    echo "Running narrator.py"
    python instant_narrator.py "$@" # uncomment this and comment the next line when you want to default to the instant narrator
    #python narrator.py "$@"
elif [[ "$1" == "--instant_narrator" ]]; then
    # Remove the first argument and pass the rest
    shift
    # Run instant_narrator.py with all remaining arguments
    echo "Running instant_narrator.py"
    python instant_narrator.py "$@"
else
    echo "Invalid argument. Please use --narrator or --instant_narrator."
    exit 1
fi