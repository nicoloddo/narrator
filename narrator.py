import os
import sys
import base64
import time
import json
import asyncio

from openai import OpenAI, AsyncOpenAI

from utils.env_utils import (
    get_env_var,
    get_agent_name,
)
from utils.common_utils import (
    maybe_start_alternative_narrator,
    cut_to_n_words,
    count_tokens,
    FRAMES_DIR,
)
from tools import Camera
from tools.ai import analyze_image, analyze_image_async
import tools.audio_feedback as audio_feedback
import tools.db_parser as db
from tts_providers.provider_factory import ProviderFactory
from tts_providers.base_provider import AsyncTTSProvider
from models import NarratorMode, RecordModel, CameraMethod, CaptureMode, MODE_CONFIGS


class Narrator:
    def __init__(
        self,
        from_error=False,
        text=None,
        debug_camera=False,
        debug_movement=False,
        debug_chat=False,
        provider_name=None,
    ):
        print(f"☕ Waking up the narrator...")

        # Configuration
        self.from_error = from_error
        self.recovery_text = text  # Text to use for error recovery
        self.debug_camera = debug_camera
        self.debug_movement = debug_movement
        self.debug_chat = debug_chat
        self.provider_name = provider_name
        self.max_times = float(get_env_var("MAX_TIMES") or "inf")
        self.count = 0

        # Initialize mode
        self.current_mode = NarratorMode.STARTUP

        # Communication between tasks
        self.record_queue = asyncio.Queue()
        self.capture_trigger = asyncio.Event()
        self.shutdown_event = asyncio.Event()

        # State management
        self.last_capture_time = 0
        self.script = []
        self.tts_error_occurred = False
        self.tts_error = None
        self.current_record = None

        # Initialize camera
        self.camera = Camera(
            frames_dir=FRAMES_DIR,
            darkness_threshold=os.environ.get("DARKNESS_THRESHOLD"),
            hue_uniformity_threshold=os.environ.get("HUE_UNIFORMITY_THRESHOLD"),
            saturation_uniformity_threshold=os.environ.get(
                "SATURATION_UNIFORMITY_THRESHOLD"
            ),
            movement_threshold=os.environ.get("MOVEMENT_THRESHOLD"),
        )
        # Note: camera setup will be done async in run() method
        self.reader = None

        # Movement debugging will be handled in async initialization

        # Initialize OpenAI clients
        self.sync_client = OpenAI()
        self.async_client = AsyncOpenAI()

        # Initialize TTS provider
        self.tts_provider = None

    async def _initialize_tts_provider(self):
        """Initialize TTS provider with error handling."""
        try:
            self.tts_provider = ProviderFactory.create_provider(self.provider_name)
            if isinstance(self.tts_provider, AsyncTTSProvider):
                await self.tts_provider.initialize_async()
            else:
                self.tts_provider.initialize()
            print(f"🎵 Using {self.tts_provider.provider_name} TTS provider")
        except Exception as e:
            print(f"Failed to initialize TTS provider: {e}")
            self.tts_error_occurred = True
            self.tts_error = e

    def _get_camera_capture_method(self, camera_method: CameraMethod):
        """Get the appropriate camera capture method based on mode configuration."""
        if camera_method == CameraMethod.MOVEMENT_DETECTION:
            return lambda: self.camera.capture_movement(self.reader)
        elif camera_method == CameraMethod.DEBUG:
            return lambda: self.camera.capture(self.reader, debugging=True)
        elif camera_method == CameraMethod.DEBUG_MOVEMENT:
            return lambda: self.camera.capture_movement(self.reader, debugging=True)
        else:  # STANDARD
            return lambda: self.camera.capture(self.reader)

    async def _record_processing_task(self):
        """Continuously process incoming records."""
        print("🔄 Starting record processing task...")

        while not self.shutdown_event.is_set():
            try:
                # Fetch new record
                record_data = await db.fetch_record(self.debug_chat)

                if record_data:
                    record = await self._handle_new_record(record_data)
                    if record:
                        # Put record in queue for camera task to process
                        await self.record_queue.put(record)

                        # Trigger capture for record-triggered modes
                        mode_config = MODE_CONFIGS[self.current_mode]
                        if mode_config.capture_mode in [
                            CaptureMode.RECORD_TRIGGERED,
                            CaptureMode.HYBRID,
                        ]:
                            self.capture_trigger.set()

                await asyncio.sleep(0.5)  # Brief pause between record polls

            except Exception as e:
                print(f"Error in record processing: {e}")
                await asyncio.sleep(2)

        print("🔄 Shutdown event received. Shutting down record processing task.")

    async def _camera_capture_task(self):
        """Handle camera captures based on current mode configuration."""
        print("📸 Starting camera capture task...")

        while not self.shutdown_event.is_set():
            try:
                mode_config = MODE_CONFIGS[self.current_mode]
                current_time = time.time()

                should_capture = False

                if mode_config.capture_mode == CaptureMode.CONTINUOUS:
                    # Continuous capture with sleep intervals
                    if (
                        current_time - self.last_capture_time
                        >= mode_config.sleep_interval
                    ):
                        should_capture = True

                elif mode_config.capture_mode == CaptureMode.RECORD_TRIGGERED:
                    # Only capture when triggered by new record
                    if self.capture_trigger.is_set():
                        should_capture = True
                        self.capture_trigger.clear()

                elif mode_config.capture_mode == CaptureMode.HYBRID:
                    # Continuous with record override
                    if self.capture_trigger.is_set():
                        should_capture = True
                        self.capture_trigger.clear()
                    elif (
                        current_time - self.last_capture_time
                        >= mode_config.sleep_interval
                    ):
                        should_capture = True

                if should_capture:
                    await self._perform_capture_and_respond(mode_config)
                    self.last_capture_time = current_time

                    self.count += 1
                    if self.count >= self.max_times:
                        print(f"Reached maximum iterations ({self.max_times})")
                        self.shutdown_event.set()
                        break

                await asyncio.sleep(0.1)  # Brief pause to prevent busy waiting

            except Exception as e:
                print(f"Error in camera capture task: {e}")
                await asyncio.sleep(2)

        print("🔄 Shutdown event received. Shutting down camera capture task.")

    async def _handle_new_record(self, record_data: dict) -> RecordModel:
        """Process new record and update mode."""
        try:
            record = RecordModel(**record_data)
            print(f"🔄 New record: {record}")
            print(f"📋 Mode config: {MODE_CONFIGS[record.mode].description}")
            print()
            print(f"🔄 Old mode: {self.current_mode}")

            # Save record to file
            os.makedirs("requests", exist_ok=True)
            with open(f"requests/{record.id}.json", "w+") as file:
                json.dump(record_data, file, indent=4)

            # Ensure mode is properly converted to enum
            old_mode = self.current_mode
            self.current_mode = record.mode

            print()
            print(f"🔄 Mode changed from {old_mode.value} to {record.mode.value}")
            print(f"📝 New {record.mode.value} request: {record.content}")
            print(f"📋 Mode config: {MODE_CONFIGS[record.mode].description}")

            self.current_record = record
            return record

        except Exception as e:
            print(f"Error processing record: {e}")
            return None

    async def _perform_capture_and_respond(self, mode_config):
        """Perform camera capture and generate response."""
        agent_name = get_agent_name(self.current_mode.value)

        # Handle startup mode specially
        if self.current_mode == NarratorMode.STARTUP:
            await asyncio.sleep(mode_config.sleep_interval)
            self.current_mode = NarratorMode.WAIT_FOR_INSTRUCTIONS
            print("🚀 Startup complete, switched to waiting mode")
            return

        # Use recovery text if this is an error recovery
        if self.recovery_text and self.count == 0:
            text = self.recovery_text
            self.recovery_text = None  # Clear after use
            print(f"🔄 Using recovery text from error restart")
        else:
            # Capture image
            print(f"👀 {agent_name} is looking... (Mode: {self.current_mode.value})")
            capture_method = self._get_camera_capture_method(mode_config.camera_method)
            base64_image = await capture_method()

            # Create message object for AI analysis
            message = {
                "content": self.current_record.content if self.current_record else None,
                "mode": self.current_mode.value,
            }

            # Analyze image
            print(f"🧠 {agent_name} is thinking...")
            vlm_inputs = [
                self.current_mode.value,
                message,
                base64_image,
                self.script,
            ]
            if isinstance(self.tts_provider, AsyncTTSProvider):
                text = await analyze_image_async(
                    self.async_client,
                    *vlm_inputs,
                )
            else:
                # Run sync analysis in executor to avoid blocking
                loop = asyncio.get_running_loop()
                text = await loop.run_in_executor(
                    None,
                    analyze_image,
                    self.sync_client,
                    *vlm_inputs,
                )

        # Process and play response
        try:
            print(f"🎙️ {agent_name} says:")
            print(f"💬 {text}")
            print(f"📏 Length: {len(text)} | Tokens: {count_tokens(text)}")

            # Cut to appropriate length
            max_tokens = int(get_env_var("MAX_TOKENS"))
            text = cut_to_n_words(text, int(max_tokens * 5 / 4))

            # Play audio
            if not self.debug_chat and self.tts_provider:
                if isinstance(self.tts_provider, AsyncTTSProvider):
                    await self.tts_provider.play_audio_async(
                        text, self.current_mode.value
                    )
                else:
                    # Run sync TTS in executor if it might be slow
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        self.tts_provider.play_audio,
                        text,
                        self.current_mode.value,
                    )

            # Add to conversation script
            self.script.append({"role": "assistant", "content": text})

            # Brief pause between responses
            print(f"😴 {agent_name} taking a brief pause...")
            await asyncio.sleep(1)

        except Exception as e:
            print(f"Error during response generation: {e}")
            self.tts_error_occurred = True
            self.tts_error = e
            self.shutdown_event.set()

    async def run(self):
        """Main async run loop with concurrent record processing and camera capture."""
        try:
            # Initialize camera async
            print("📷 Initializing camera...")
            self.reader = await self.camera.get_camera("<video0>")

            # Initial camera setup - wait until camera sees something
            print("👁️ Camera waiting for clear view...")
            await self.camera.capture(self.reader, debugging=self.debug_camera)

            if self.debug_movement:
                print("🔍 Testing movement detection...")
                await self.camera.capture_movement(
                    self.reader, debugging=self.debug_movement
                )

            # Startup greeting
            if not self.from_error:
                print("👋 Hi!")
                audio_feedback.startup()
                self.current_mode = NarratorMode.WAIT_FOR_INSTRUCTIONS

            # Initialize TTS provider
            await self._initialize_tts_provider()

            if self.tts_error_occurred:
                print("Cannot continue due to TTS provider initialization failure")
                return

            print(f"🎬 Starting narrator with mode: {self.current_mode.value}")
            print(f"📖 {MODE_CONFIGS[self.current_mode].description}")

            # Create concurrent tasks
            tasks = [
                asyncio.create_task(self._record_processing_task()),
                asyncio.create_task(self._camera_capture_task()),
            ]

            # Run tasks until shutdown or error
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
            except Exception as e:
                print(f"Error in main tasks: {e}")
                self.tts_error_occurred = True
                self.tts_error = e

            # Cleanup tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            print("🏁 Narrator run completed")

        except Exception as e:
            print(f"Critical error in narrator run: {e}")
            self.tts_error_occurred = True
            self.tts_error = e

        finally:
            await self._cleanup()

    async def _cleanup(self):
        """Clean up resources."""
        try:
            print("🧹 Cleaning up resources...")

            # Set shutdown event
            self.shutdown_event.set()

            # Cleanup TTS provider
            if self.tts_provider:
                if isinstance(self.tts_provider, AsyncTTSProvider):
                    await self.tts_provider.cleanup_async()
                else:
                    self.tts_provider.cleanup()

            # Turn off audio feedback
            if not self.tts_error_occurred:
                audio_feedback.turnoff()

            # Close camera
            if self.reader:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.reader.close)

            if self.tts_error_occurred:
                await self.handle_tts_error(self.tts_error)

        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

    async def handle_tts_error(self, last_text: str):
        """Handle TTS errors by trying alternative provider."""
        if self.tts_error_occurred:
            print(f"💥 TTS error occurred: {self.tts_error}")

            # Try alternative provider
            alternative_provider = (
                "playht"
                if self.tts_provider and self.tts_provider.provider_name == "ElevenLabs"
                else "elevenlabs"
            )
            print(f"🔄 Trying alternative TTS provider: {alternative_provider}")

            # Start alternative narrator with different provider
            import subprocess

            command = [
                "python",
                "narrator.py",
                "--from-error",
                "--text",
                last_text,
                "--provider-name",
                alternative_provider,
            ]
            subprocess.run(command)
