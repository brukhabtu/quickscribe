#!/usr/bin/env python3
"""
QuickScribe Recorder - Audio recording functionality
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple, Callable
import os
import threading
import queue

from .models import AudioDevice, Recording, DeviceType


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