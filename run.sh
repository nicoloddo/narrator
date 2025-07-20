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

# Initialize variables
PROVIDER=""
NARRATOR_ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --provider=*)
            PROVIDER="${1#*=}"
            shift
            ;;
        *)
            # Collect all other arguments for narrator.py
            NARRATOR_ARGS="$NARRATOR_ARGS $1"
            shift
            ;;
    esac
done

# Build the command
CMD="python narrator.py"

# Add provider if specified
if [[ -n "$PROVIDER" ]]; then
    CMD="$CMD --provider-name $PROVIDER"
    echo "Running narrator.py with $PROVIDER provider"
else
    echo "Running narrator.py with default provider"
fi

# Add any remaining arguments
if [[ -n "$NARRATOR_ARGS" ]]; then
    CMD="$CMD $NARRATOR_ARGS"
fi

# Execute the command
echo "Command: $CMD"
eval $CMD