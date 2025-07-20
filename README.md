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

Make an [OpenAI](https://beta.openai.com/) and [ElevenLabs](https://elevenlabs.io) account and set your tokens in a .env file. You can fill in the variables as suggested in the .env.example.

If you want to use an alternative narrator like playht, make an account at PlayHT and set your tokens in the same .env.

The .env files must be copied into the raspberry for the application to work. Pulling this repository will not include the .env file nor any custom agent that you added to the agents folder.

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
./run --playht_narrator
```
Note that if one gives an error, the other will start. The --option only gives the opportunity to specify which one to start as default narrator.

## To automate its running on startup:
Move the narrator.service to ```/etc/systemd/system/```:
```bash
sudo cp narrator.service /etc/systemd/system/
```
Then activate the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable narrator.service
```
The service will run one time on startup, speaking at most as much as specified in the agent.sh MAX_TIMES variable.

You can check the service output with:
```bash
sudo systemctl status narrator.service
```
Or for more extensive logs with:
```bash
journalctl -u narrator.service
```

## Optional modifications:

### To change voice:
Make a new voice in Eleven Labs and get the voice id of that voice using their [get voices](https://elevenlabs.io/docs/api-reference/voices) API, or by clicking the flask icon next to the voice in the VoiceLab tab.

Add an agent.env in the agents folder with new.
```
ELEVENLABS_VOICE_ID=<voice-id>
```
If using alt providers:
```
PLAYHT_VOICE_ID=<voice-id>
```

Inside the agent.env you can also change:
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

These steps are automated by simply running the run.sh.