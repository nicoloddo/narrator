#!/bin/bash

git reset --hard

while ! ping -c 1 -W 1 github.com; do
    echo "Waiting for github - network interface might be down..."
    sleep 1
done

git pull