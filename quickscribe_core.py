#!/usr/bin/env python3
"""
QuickScribe Core - Domain/Business Logic
No UI dependencies, pure functionality for recording and transcription
"""

import sounddevice as sd
import soundfile as sf
import whisper
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import os
import threading
import queue


class DeviceType(Enum):
    """Types of audio devices"""
    PHYSICAL_INPUT = "physical_input"
    VIRTUAL_LOOPBACK = "virtual_loopback"
    APP_VIRTUAL = "app_virtual"
    AGGREGATE = "aggregate"
    UNKNOWN = "unknown"


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


class RecordingState(Enum):
    """Recording states"""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


class AudioDeviceManager:
    """Manages audio device detection and configuration"""
    
    KNOWN_LOOPBACK_DEVICES = ['BlackHole', 'Soundflower', 'Loopback']
    KNOWN_APP_DEVICES = ['Teams', 'Zoom', 'Discord', 'Skype']
    
    def __init__(self):
        self._devices_cache = None
        
    def get_devices(self, force_refresh: bool = False) -> List[AudioDevice]:
        """Get all audio devices"""
        if force_refresh or self._devices_cache is None:
            self._devices_cache = self._query_devices()
        return self._devices_cache
    
    def _query_devices(self) -> List[AudioDevice]:
        """Query system for audio devices"""
        devices = []
        sd_devices = sd.query_devices()
        
        for idx, device in enumerate(sd_devices):
            device_type = self._determine_device_type(device['name'])
            needs_setup = (device_type == DeviceType.VIRTUAL_LOOPBACK and 
                          'BlackHole' in device['name'] and 
                          not self._is_blackhole_configured())
            
            audio_device = AudioDevice(
                id=idx,
                name=device['name'],
                channels_in=device['max_input_channels'],
                channels_out=device['max_output_channels'],
                sample_rate=device['default_samplerate'],
                is_default=device.get('default_input', False),
                device_type=device_type,
                needs_setup=needs_setup
            )
            devices.append(audio_device)
        
        return devices
    
    def _determine_device_type(self, device_name: str) -> DeviceType:
        """Determine the type of audio device based on its name"""
        # Check for loopback devices
        for loopback in self.KNOWN_LOOPBACK_DEVICES:
            if loopback.lower() in device_name.lower():
                return DeviceType.VIRTUAL_LOOPBACK
        
        # Check for app virtual devices
        for app in self.KNOWN_APP_DEVICES:
            if app.lower() in device_name.lower():
                return DeviceType.APP_VIRTUAL
        
        # Check for aggregate devices
        if 'aggregate' in device_name.lower() or 'multi-output' in device_name.lower():
            return DeviceType.AGGREGATE
        
        # Default to physical input
        return DeviceType.PHYSICAL_INPUT
    
    def _is_blackhole_configured(self) -> bool:
        """Check if BlackHole is properly configured"""
        # This is a simplified check - could be expanded
        return os.path.exists(os.path.expanduser("~/Library/Audio/Plug-Ins/HAL/BlackHole.driver"))
    
    def get_device_by_id(self, device_id: int) -> Optional[AudioDevice]:
        """Get a specific device by ID"""
        devices = self.get_devices()
        for device in devices:
            if device.id == device_id:
                return device
        return None
    
    def get_input_devices(self) -> List[AudioDevice]:
        """Get only input-capable devices"""
        return [d for d in self.get_devices() if d.is_input]
    
    def get_default_input_device(self) -> Optional[AudioDevice]:
        """Get the default input device"""
        for device in self.get_devices():
            if device.is_default and device.is_input:
                return device
        # Fallback to first input device
        input_devices = self.get_input_devices()
        return input_devices[0] if input_devices else None


class Recorder:
    """Core recording functionality"""
    
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = os.path.expanduser("~/.quickscribe")
        self.output_dir = output_dir
        self.sample_rate = 44100
        self.channels = 1
        self.is_recording = False
        self.current_device: Optional[AudioDevice] = None
        self.current_filename: Optional[str] = None
        self._audio_queue = queue.Queue()
        self._recording_thread: Optional[threading.Thread] = None
        self._stream: Optional[sd.InputStream] = None
        self._audio_data = []
        self._level_callback: Optional[Callable[[float], None]] = None
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def set_device(self, device: AudioDevice):
        """Set the recording device"""
        if self.is_recording:
            raise RuntimeError("Cannot change device while recording")
        self.current_device = device
    
    def set_level_callback(self, callback: Callable[[float], None]):
        """Set callback for audio level updates"""
        self._level_callback = callback
    
    def start_recording(self) -> str:
        """Start recording, returns filename"""
        if self.is_recording:
            raise RuntimeError("Already recording")
        
        if not self.current_device:
            raise RuntimeError("No device selected")
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        device_suffix = ""
        if self.current_device.device_type == DeviceType.VIRTUAL_LOOPBACK:
            device_suffix = "_system"
        elif self.current_device.device_type == DeviceType.APP_VIRTUAL:
            device_suffix = "_app"
        
        self.current_filename = f"meeting_{timestamp}{device_suffix}.wav"
        self.is_recording = True
        self._audio_data = []
        
        # Start audio stream
        self._stream = sd.InputStream(
            device=self.current_device.id,
            channels=self.channels,
            samplerate=self.sample_rate,
            callback=self._audio_callback
        )
        self._stream.start()
        
        return self.current_filename
    
    def stop_recording(self) -> Tuple[bool, str]:
        """Stop recording, returns (success, filepath)"""
        if not self.is_recording:
            return False, "Not recording"
        
        self.is_recording = False
        
        # Stop stream
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        # Save audio file
        if self._audio_data:
            audio_array = np.concatenate(self._audio_data, axis=0)
            filepath = os.path.join(self.output_dir, self.current_filename)
            sf.write(filepath, audio_array, self.sample_rate)
            return True, filepath
        
        return False, "No audio data recorded"
    
    def _audio_callback(self, indata, frames, time, status):
        """Audio stream callback"""
        if self.is_recording:
            self._audio_data.append(indata.copy())
            
            # Calculate audio level for visualization
            if self._level_callback:
                # RMS level in dB
                rms = np.sqrt(np.mean(indata**2))
                db = 20 * np.log10(rms) if rms > 0 else -60
                self._level_callback(db)
    
    def get_recordings(self) -> List[Recording]:
        """Get list of recordings"""
        recordings = []
        
        if not os.path.exists(self.output_dir):
            return recordings
        
        for filename in sorted(os.listdir(self.output_dir), reverse=True):
            if filename.endswith('.wav'):
                filepath = os.path.join(self.output_dir, filename)
                
                # Get file info
                stat = os.stat(filepath)
                timestamp = datetime.fromtimestamp(stat.st_mtime)
                
                # Get duration
                try:
                    data, sr = sf.read(filepath)
                    duration = len(data) / sr
                except:
                    duration = 0
                
                # Check for transcript
                transcript_path = filepath.replace('.wav', '_transcript.txt')
                has_transcript = os.path.exists(transcript_path)
                
                # Determine device from filename
                device_name = "Unknown"
                if "_system" in filename:
                    device_name = "System Audio"
                elif "_app" in filename:
                    device_name = "App Audio"
                else:
                    device_name = "Microphone"
                
                recording = Recording(
                    filename=filename,
                    filepath=filepath,
                    duration=duration,
                    timestamp=timestamp,
                    device_name=device_name,
                    has_transcript=has_transcript,
                    transcript_path=transcript_path if has_transcript else None
                )
                recordings.append(recording)
        
        return recordings


class Transcriber:
    """Handles transcription using Whisper"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._load_lock = threading.Lock()
    
    def load_model(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Load Whisper model"""
        with self._load_lock:
            if self.model is None:
                if progress_callback:
                    progress_callback("Loading Whisper model...")
                self.model = whisper.load_model(self.model_size)
                if progress_callback:
                    progress_callback("Model loaded!")
    
    def transcribe(self, 
                   audio_file: str, 
                   progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Transcribe an audio file"""
        if not self.model:
            self.load_model(progress_callback)
        
        try:
            if progress_callback:
                progress_callback("Transcribing...")
            
            result = self.model.transcribe(audio_file)
            text = result["text"]
            
            # Save transcript
            transcript_file = audio_file.replace('.wav', '_transcript.txt')
            with open(transcript_file, 'w') as f:
                f.write(f"Transcript for: {os.path.basename(audio_file)}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                f.write(text)
            
            if progress_callback:
                progress_callback("Transcription complete!")
            
            return True, transcript_file
            
        except Exception as e:
            return False, str(e)


class QuickScribeCore:
    """Main API for QuickScribe functionality"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.device_manager = AudioDeviceManager()
        self.recorder = Recorder(output_dir)
        self.transcriber = Transcriber()
        self.state = RecordingState.IDLE
        
    def get_devices(self) -> List[AudioDevice]:
        """Get available audio devices"""
        return self.device_manager.get_input_devices()
    
    def set_device(self, device_id: int) -> bool:
        """Set recording device by ID"""
        device = self.device_manager.get_device_by_id(device_id)
        if device and device.is_input:
            self.recorder.set_device(device)
            return True
        return False
    
    def start_recording(self) -> Tuple[bool, str]:
        """Start recording"""
        try:
            self.state = RecordingState.RECORDING
            filename = self.recorder.start_recording()
            return True, filename
        except Exception as e:
            self.state = RecordingState.ERROR
            return False, str(e)
    
    def stop_recording(self) -> Tuple[bool, str]:
        """Stop recording"""
        self.state = RecordingState.IDLE
        return self.recorder.stop_recording()
    
    def get_recordings(self) -> List[Recording]:
        """Get list of recordings"""
        return self.recorder.get_recordings()
    
    def transcribe_recording(self, filepath: str, 
                           progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Transcribe a recording"""
        self.state = RecordingState.PROCESSING
        success, result = self.transcriber.transcribe(filepath, progress_callback)
        self.state = RecordingState.IDLE
        return success, result
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.state == RecordingState.RECORDING
    
    @property
    def current_device(self) -> Optional[AudioDevice]:
        """Get current recording device"""
        return self.recorder.current_device