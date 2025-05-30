"""
Data models and types for QuickScribe core functionality.
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional


class DeviceType(Enum):
    """Types of audio devices"""
    PHYSICAL_INPUT = "physical_input"
    VIRTUAL_LOOPBACK = "virtual_loopback"
    APP_VIRTUAL = "app_virtual"
    AGGREGATE = "aggregate"
    UNKNOWN = "unknown"


class RecordingState(Enum):
    """Recording states"""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class AudioDevice:
    """Audio device information"""
    id: int
    name: str
    channels_in: int
    channels_out: int
    sample_rate: float
    is_default: bool
    device_type: DeviceType
    is_available: bool = True
    needs_setup: bool = False

    @property
    def is_input(self) -> bool:
        return self.channels_in > 0

    @property
    def is_output(self) -> bool:
        return self.channels_out > 0


@dataclass
class Recording:
    """Recording metadata"""
    filename: str
    filepath: str
    duration: float
    timestamp: datetime
    device_name: str
    has_transcript: bool = False
    transcript_path: Optional[str] = None