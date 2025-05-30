"""
Audio device management for QuickScribe.
"""

import sounddevice as sd
import os
from typing import List, Optional
from .models import AudioDevice, DeviceType


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