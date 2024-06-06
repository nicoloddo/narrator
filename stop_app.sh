#!/bin/bash

if [ -f "/tmp/terminal1.pid" ]; then
    PID1=$(cat "/tmp/terminal1.pid")
    kill $PID1
    rm "/tmp/terminal1.pid"
    echo "Closed terminal running capture.py"
else
    echo "No PID file found for terminal 1"
fi

if [ -f "/tmp/terminal2.pid" ]; then
    PID2=$(cat "/tmp/terminal2.pid")
    kill $PID2
    rm "/tmp/terminal2.pid"
    echo "Closed terminal running narrator.py"
else
    echo "No PID file found for terminal 2"
fi
