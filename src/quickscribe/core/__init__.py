"""
Core business logic for QuickScribe.

This module contains the main API and business logic components
without any UI dependencies.
"""

from .models import AudioDevice, Recording, DeviceType, RecordingState
from .devices import AudioDeviceManager
from .recorder import Recorder
from .transcriber import Transcriber

class QuickScribeCore:
    """Main API for QuickScribe functionality"""
    
    def __init__(self, output_dir=None):
        self.device_manager = AudioDeviceManager()
        self.recorder = Recorder(output_dir)
        self.transcriber = Transcriber()
        self.state = RecordingState.IDLE
        
    def get_devices(self):
        """Get available audio devices"""
        return self.device_manager.get_input_devices()
    
    def set_device(self, device_id):
        """Set recording device by ID"""
        device = self.device_manager.get_device_by_id(device_id)
        if device and device.is_input:
            self.recorder.set_device(device)
            return True
        return False
    
    def start_recording(self):
        """Start recording"""
        try:
            self.state = RecordingState.RECORDING
            filename = self.recorder.start_recording()
            return True, filename
        except Exception as e:
            self.state = RecordingState.ERROR
            return False, str(e)
    
    def stop_recording(self):
        """Stop recording"""
        self.state = RecordingState.IDLE
        return self.recorder.stop_recording()
    
    def get_recordings(self):
        """Get list of recordings"""
        return self.recorder.get_recordings()
    
    def transcribe_recording(self, filepath, progress_callback=None):
        """Transcribe a recording"""
        self.state = RecordingState.PROCESSING
        success, result = self.transcriber.transcribe(filepath, progress_callback)
        self.state = RecordingState.IDLE
        return success, result
    
    @property
    def is_recording(self):
        """Check if currently recording"""
        return self.state == RecordingState.RECORDING
    
    @property
    def current_device(self):
        """Get current recording device"""
        return self.recorder.current_device

__all__ = [
    "QuickScribeCore",
    "AudioDevice", 
    "Recording", 
    "DeviceType", 
    "RecordingState",
    "AudioDeviceManager",
    "Recorder",
    "Transcriber"
]