#!/bin/bash
git reset --hard
git pull
amixer set Master 80%
source venv/bin/activate
. setenv.sh
. agent.sh