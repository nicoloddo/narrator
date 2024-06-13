import simpleaudio as sa
import os

# Reference the audio feedback folder
AUDIO_FEEDBACK_DIR = os.path.join(os.getcwd(), "assets")

def play_audio(audio_file, audio_feedback_dir=AUDIO_FEEDBACK_DIR):
	# The file needs to be .wav
	audio_path = os.path.join(frames_dir, audio_file)

	# Check if the .wav file exists
    if not os.path.exists(audio_path):
        print("Warning: Audio file does not exist:", audio_path)
        return

	# Load the wave file
	wave_obj = sa.WaveObject.from_wave_file(audio_path)

	# Play the wave file
	play_obj = wave_obj.play()

	# Wait for playback to finish
	play_obj.wait_done()

def startup():
	play_audio("startup.wav")

def turnoff():
	play_audio("turnoff.wav")

def cant_see():
	play_audio("icantsee.wav")
def i_see():
	play_audio("isee.wav")
def im_sir_david():
	play_audio("imsirdavid.wav")