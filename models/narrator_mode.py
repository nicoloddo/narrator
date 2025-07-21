from enum import Enum
from typing import Optional
from pydantic import BaseModel


class CameraMethod(str, Enum):
    """Camera capture methods available."""

    STANDARD = "standard"
    MOVEMENT_DETECTION = "movement_detection"
    DEBUG = "debug"
    DEBUG_MOVEMENT = "debug_movement"


class CaptureMode(str, Enum):
    """How capture should be triggered."""

    CONTINUOUS = "continuous"  # Continuous capture with sleep intervals
    RECORD_TRIGGERED = "record_triggered"  # Only capture when new record arrives
    HYBRID = "hybrid"  # Continuous with record override


class NarratorMode(str, Enum):
    """Enumeration of available narrator modes."""

    STARTUP = "startup"
    WAIT_FOR_INSTRUCTIONS = "wait_for_instructions"
    ASK_DAVIDE = "ask_davide"
    ASK_BORTIS = "ask_bortis"
    LOOK_PIERSILVIO = "look_piersilvio"
    GENERAL_NARRATION = "general_narration"
    DEBUG = "debug"
    DEBUG_MOVEMENT = "debug_movement"
    OBSERVATION = "observation"
    SECURITY_MONITOR = "security_monitor"


class ModeConfig(BaseModel):
    """Configuration for each narrator mode."""

    mode: NarratorMode
    camera_method: CameraMethod = CameraMethod.STANDARD
    capture_mode: CaptureMode = CaptureMode.CONTINUOUS
    sleep_interval: float = 3.0  # seconds between captures in continuous mode
    description: str = ""
    agent: str = "davide"  # Agent name for voice/personality (e.g., "davide", "bortis")

    class Config:
        use_enum_values = True


# Mode configurations
MODE_CONFIGS = {
    NarratorMode.STARTUP: ModeConfig(
        mode=NarratorMode.STARTUP,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.CONTINUOUS,
        sleep_interval=1.0,
        description="Initial startup mode, brief waiting period",
    ),
    NarratorMode.WAIT_FOR_INSTRUCTIONS: ModeConfig(
        mode=NarratorMode.WAIT_FOR_INSTRUCTIONS,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.RECORD_TRIGGERED,
        sleep_interval=0.5,
        description="Waiting for user instructions, only capture on new records",
    ),
    NarratorMode.ASK_DAVIDE: ModeConfig(
        mode=NarratorMode.ASK_DAVIDE,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.RECORD_TRIGGERED,
        sleep_interval=1.0,
        description="Davide interaction mode, capture triggered by questions",
        agent="davide",
    ),
    NarratorMode.ASK_BORTIS: ModeConfig(
        mode=NarratorMode.ASK_BORTIS,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.RECORD_TRIGGERED,
        sleep_interval=1.0,
        description="Bortis interaction mode, capture triggered by questions",
        agent="bortis",
    ),
    NarratorMode.LOOK_PIERSILVIO: ModeConfig(
        mode=NarratorMode.LOOK_PIERSILVIO,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.RECORD_TRIGGERED,
        sleep_interval=1.0,
        description="Piersilvio interaction mode, capture triggered by questions",
        agent="piersilvio",
    ),
    NarratorMode.GENERAL_NARRATION: ModeConfig(
        mode=NarratorMode.GENERAL_NARRATION,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.CONTINUOUS,
        sleep_interval=5.0,
        description="Continuous general narration of surroundings",
    ),
    NarratorMode.DEBUG: ModeConfig(
        mode=NarratorMode.DEBUG,
        camera_method=CameraMethod.DEBUG,
        capture_mode=CaptureMode.HYBRID,
        sleep_interval=2.0,
        description="Debug mode with enhanced capture and logging",
    ),
    NarratorMode.DEBUG_MOVEMENT: ModeConfig(
        mode=NarratorMode.DEBUG_MOVEMENT,
        camera_method=CameraMethod.DEBUG_MOVEMENT,
        capture_mode=CaptureMode.HYBRID,
        sleep_interval=2.0,
        description="Debug mode with movement detection",
    ),
    NarratorMode.OBSERVATION: ModeConfig(
        mode=NarratorMode.OBSERVATION,
        camera_method=CameraMethod.STANDARD,
        capture_mode=CaptureMode.CONTINUOUS,
        sleep_interval=10.0,
        description="Long-interval observation mode",
    ),
    NarratorMode.SECURITY_MONITOR: ModeConfig(
        mode=NarratorMode.SECURITY_MONITOR,
        camera_method=CameraMethod.MOVEMENT_DETECTION,
        capture_mode=CaptureMode.CONTINUOUS,
        sleep_interval=1.0,
        description="Security monitoring with movement detection",
    ),
}


class NarratorModeModel(BaseModel):
    """Model for narrator mode with validation."""

    mode: NarratorMode

    @property
    def config(self) -> ModeConfig:
        """Get the configuration for this mode."""
        return MODE_CONFIGS[self.mode]

    class Config:
        use_enum_values = True
