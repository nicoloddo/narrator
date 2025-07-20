# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 17:29:36 2024

@author: nicol
"""
import os
import dotenv

dotenv.load_dotenv()


class Environment:

    AGENT_NAME = None
    AGENT_PROMPT = None
    ELEVENLABS_VOICE_ID = None
    FIRST_IMAGE_PROMPT = None
    NEW_IMAGE_PROMPT = None
    ELEVENLABS_STABILITY = None
    ELEVENLABS_SIMILARITY = None
    ELEVENLABS_STYLE = None

    ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
    MAX_TOKENS = os.environ.get("MAX_TOKENS")
    MAX_TIMES = os.environ.get("MAX_TIMES")
    AWS_QUEUE_API_KEY = os.environ.get("AWS_QUEUE_API_KEY")
    AWS_QUEUE_KEY_ID = os.environ.get("AWS_QUEUE_KEY_ID")
    AWS_REGION = os.environ.get("AWS_REGION")
    AWS_QUEUE = os.environ.get("AWS_QUEUE")

    def get(self, key, mode=None):
        if mode is not None:
            self.mode_selector(mode)

        if key == "MAX_TOKENS":
            return self.MAX_TOKENS

        elif key == "AGENT_NAME":
            return self.AGENT_NAME

        elif key == "AGENT_PROMPT":
            return self.AGENT_PROMPT

        elif key == "ELEVENLABS_VOICE_ID":
            return self.ELEVENLABS_VOICE_ID

        elif key == "ELEVENLABS_API_KEY":
            return self.ELEVENLABS_API_KEY

        elif key == "MAX_TIMES":
            return self.MAX_TIMES

        elif key == "FIRST_IMAGE_PROMPT":
            return self.FIRST_IMAGE_PROMPT

        elif key == "NEW_IMAGE_PROMPT":
            return self.NEW_IMAGE_PROMPT

        elif key == "AWS_QUEUE_API_KEY":
            return self.AWS_QUEUE_API_KEY

        elif key == "AWS_QUEUE_KEY_ID":
            return self.AWS_QUEUE_KEY_ID

        elif key == "AWS_REGION":
            return self.AWS_REGION

        elif key == "AWS_QUEUE":
            return self.AWS_QUEUE

        elif key == "ELEVENLABS_STABILITY":
            return self.ELEVENLABS_STABILITY

        elif key == "ELEVENLABS_SIMILARITY":
            return self.ELEVENLABS_SIMILARITY

        elif key == "ELEVENLABS_STYLE":
            return self.ELEVENLABS_STYLE

    def mode_selector(self, mode):

        if mode == "ask_roberto":
            dotenv.load_dotenv("agents/roberto.env")
            self.AGENT_NAME = os.environ.get("ROBERTO_AGENT_NAME")

            self.AGENT_PROMPT = os.environ.get("ROBERTO_AGENT_PROMPT")
            self.ELEVENLABS_VOICE_ID = os.environ.get("ROBERTO_ELEVENLABS_VOICE_ID")

            self.FIRST_IMAGE_PROMPT = os.environ.get("ROBERTO_FIRST_IMAGE_PROMPT")
            self.NEW_IMAGE_PROMPT = os.environ.get("ROBERTO_NEW_IMAGE_PROMPT")

            self.ELEVENLABS_STABILITY = os.environ.get("ROBERTO_ELEVENLABS_STABILITY")
            self.ELEVENLABS_SIMILARITY = os.environ.get("ROBERTO_ELEVENLABS_SIMILARITY")

        if mode == "ask_bortis":
            dotenv.load_dotenv("agents/bortis.env")
            self.AGENT_NAME = os.environ.get("BORTIS_AGENT_NAME")

            self.AGENT_PROMPT = os.environ.get("BORTIS_AGENT_PROMPT")
            self.ELEVENLABS_VOICE_ID = os.environ.get("BORTIS_ELEVENLABS_VOICE_ID")
            self.FIRST_IMAGE_PROMPT = os.environ.get("BORTIS_FIRST_IMAGE_PROMPT")

            self.NEW_IMAGE_PROMPT = self.FIRST_IMAGE_PROMPT

            self.ELEVENLABS_STABILITY = os.environ.get("BORTIS_ELEVENLABS_STABILITY")
            self.ELEVENLABS_SIMILARITY = os.environ.get("BORTIS_ELEVENLABS_SIMILARITY")
            self.ELEVENLABS_STYLE = os.environ.get("BORTIS_ELEVENLABS_STYLE")

        elif mode == "look_piersilvio":
            dotenv.load_dotenv("agents/piersilvio.env")
            self.AGENT_NAME = os.environ.get("PIERSILVIO_AGENT_NAME")

            self.AGENT_PROMPT = os.environ.get("PIERSILVIO_AGENT_PROMPT")
            self.ELEVENLABS_VOICE_ID = os.environ.get("PIERSILVIO_ELEVENLABS_VOICE_ID")
            self.FIRST_IMAGE_PROMPT = os.environ.get("GIUDICAMI_PIERSILVIO")

            self.NEW_IMAGE_PROMPT = self.FIRST_IMAGE_PROMPT

            self.ELEVENLABS_STABILITY = os.environ.get(
                "PIERSILVIO_ELEVENLABS_STABILITY"
            )
            self.ELEVENLABS_SIMILARITY = os.environ.get(
                "PIERSILVIO_ELEVENLABS_SIMILARITY"
            )
            self.ELEVENLABS_STYLE = os.environ.get("PIERSILVIO_ELEVENLABS_STYLE")


env = Environment()
