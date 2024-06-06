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
export OPENAI_API_KEY=<token>
export ELEVENLABS_API_KEY=<eleven-token>
```
Then make it executable, as well as the setvoice.sh:
```bash
chmod +x setenv.sh
chmod +x setvoice.sh
```

To change voice:
Make a new voice in Eleven and get the voice id of that voice using their [get voices](https://elevenlabs.io/docs/api-reference/voices) API, or by clicking the flask icon next to the voice in the VoiceLab tab.

Then change the setvoice.sh file to the id you prefer.
```
export ELEVENLABS_VOICE_ID=<voice-id>
```


Run the two .sh by sourcing them, otherwise they will run in a new subshell and the exports will not persist:
```bash
. setenv.sh
. setvoice.sh
```
OR:
```bash
source setenv.sh
source setvoice.sh
```

## Run it!

In on terminal, run the webcam capture:
```bash
python capture.py
```
In another terminal, run the narrator:

```bash
python narrator.py
```

