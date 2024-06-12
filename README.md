# David Attenborough narrates your life from a Raspberry Pi Zero 2W. 
OpenCV has been deleted from the requirements and substituted by ImageIO

https://twitter.com/charliebholtz/status/1724815159590293764

## Setup

First install python and an important numpy dependency:
```bash
sudo apt-get install libopenblas-dev
```

Clone this repo, and setup and activate a virtualenv:

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
```

Then, install the dependencies:
```bash
pip install -r requirements.txt
```

Make an [OpenAI](https://beta.openai.com/) and [ElevenLabs](https://elevenlabs.io) account and set your tokens in a new .sh script named:
```
setenv.sh
```
with this content:
```
export OPENAI_API_KEY=<openai-key>
export ELEVENLABS_API_KEY=<eleven-key>
```
If you want to use the instant narrator, make an account at PlayHT and set your tokens in the same setenv.sh:
```
export PLAYHT_USER_ID=<playht-user>
export PLAYHT_API_KEY=<playht-key>
```

Then make the necessary scripts executable:
```bash
chmod +x setenv.sh
chmod +x agent.sh
chmod +x run.sh
chmod +x run_instant_narrator.sh
chmod +x pre_run.sh
```

## Run it!s
```bash
./run.sh
```
OR:
```bash
./run_instant_narrator.sh
```

## To automate its running on startup:
You can set a cronjob to start at the boot of the raspberry:
```bash
crontab -e
```
Place this line in a new line at the end of the file:
```bash
@reboot cd /home/path/to/ && /bin/bash -c 'echo -e "\n$(date) - Script started\n" >> ./run.log; /bin/bash ./run.sh >> ./run.log 2>&1; echo -e "\n$(date) - Script ended\n" >> ./run.log'
```
Remember to change home/path/to to the actual path where you cloned this repo.

## Optional modifications:

### To change voice:
Make a new voice in Eleven and get the voice id of that voice using their [get voices](https://elevenlabs.io/docs/api-reference/voices) API, or by clicking the flask icon next to the voice in the VoiceLab tab.

Then change the agent.sh file to the id you prefer.
```
export ELEVENLABS_VOICE_ID=<voice-id>
export PLAYHT_VOICE_ID=<voice-id>
```

Inside the agent.sh you can also change:
- the system prompt of the agent, 
- the first prompt and the recurring prompt to the agent,
- the amount of times the agent will speak before turning off.

### run.sh customization notes:
Notice that the two .sh shouldn't be run directly but rather sourced, otherwise they will run in a new subshell and the exports will not persist:
```bash
. setenv.sh
. agent.sh
```
OR:
```bash
source setenv.sh
source agent.sh
```

Remember to activate the venv:
```bash
source venv/bin/activate
```
Then run the software:
```bash
python narrator.py
```

These steps are automated by simply running the run.sh or run_instant_narrator.sh file.