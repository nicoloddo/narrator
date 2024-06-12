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

Then make the run.sh script executable:
```bash
chmod +x run.sh
```

## Run it!
```bash
./run.sh --narrator
```
OR:
```bash
./run --instant_narrator
```
Note that if one gives an error, the other will start. The --option only gives the opportunity to specify which one to start as default narrator.

## To automate its running on startup:
You can set a cronjob to start at the boot of the raspberry:
```bash
crontab -e
```
Place this line in a new line at the end of the file:
```bash
@reboot cd /home/path/to/ && /bin/bash -c 'echo -e "\n$(date) - Script started\n" >> ./run.log; /bin/bash ./run.sh --narrator >> ./run.log 2>&1; echo -e "\n$(date) - Script ended\n" >> ./run.log'
```
Remember to change home/path/to to the actual path where you cloned this repo.
Remember also to change:
./run.sh --narrator
to:
./run.sh --instant_narrator
If you want to use the instant narrator.

#### OR:
Move the narrator.service to ```/etc/systemd/system/```:
```bash
sudo cp narrator.service /etc/systemd/system/
sudo systemctl enable narrator.service
```
Then activate the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable narrator.service
```
You can try the service with:
```bash
sudo systemctl start narrator.service
```
You can check the service with:
```bash
sudo systemctl status narrator.service
```
Or for more extensive logs with:
```bash
journalctl -u narrator.service
```

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