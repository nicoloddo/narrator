# David Attenborough narrates your life from a Raspberry Pi Zero 2W. 
OpenCV has been deleted from the requirements and substituted by ImageIO

https://twitter.com/charliebholtz/status/1724815159590293764

## Setup

Clone this repo, and setup and activate a virtualenv:

```bash
python3 -m pip install virtualenv
python3 -m virtualenv venv --system-site-packages
source venv/bin/activate
```

Then, install the dependencies:
```bash
pip install -r requirements.txt
```

Make an [OpenAI](https://beta.openai.com/) and [ElevenLabs](https://elevenlabs.io) account and set your tokens:

```
export OPENAI_API_KEY=<token>
export ELEVENLABS_API_KEY=<eleven-token>
```

Make a new voice in Eleven and get the voice id of that voice using their [get voices](https://elevenlabs.io/docs/api-reference/voices) API, or by clicking the flask icon next to the voice in the VoiceLab tab.

```
export ELEVENLABS_VOICE_ID=<voice-id>
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

