#!/usr/bin/env python3
"""
Audio device setup and routing management for QuickScribe
Handles BlackHole installation, multi-output devices, and audio routing
"""

import subprocess
import json
import os
import sys
import time

class AudioSetupManager:
    def __init__(self):
        self.original_output = None
        self.multi_output_device = None
        
    def check_blackhole_installed(self):
        """Check if BlackHole is installed"""
        try:
            result = subprocess.run(['brew', 'list', 'blackhole-2ch'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def install_blackhole(self):
        """Install BlackHole via Homebrew"""
        print("📦 Installing BlackHole virtual audio driver...")
        print("This may take a few minutes...")
        
        try:
            # First install via brew
            result = subprocess.run(['brew', 'install', 'blackhole-2ch'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ BlackHole downloaded!")
                
                # Find the installer package
                pkg_path = None
                try:
                    result = subprocess.run(['brew', 'list', 'blackhole-2ch'], 
                                          capture_output=True, text=True)
                    for line in result.stdout.splitlines():
                        if line.endswith('.pkg'):
                            pkg_path = line.strip()
                            break
                except:
                    pass
                
                if pkg_path:
                    print("\n⚠️  BlackHole requires manual installation:")
                    print(f"1. Open Finder and go to: {os.path.dirname(pkg_path)}")
                    print(f"2. Double-click: {os.path.basename(pkg_path)}")
                    print("3. Follow the installer prompts")
                    print("4. You may need to restart your Mac")
                    input("\nPress Enter after installing...")
                    
                    # Check if it's now available
                    time.sleep(2)
                    if self.check_blackhole_in_audio_devices():
                        print("✅ BlackHole is now available!")
                        return True
                    else:
                        print("⚠️  BlackHole not detected. You may need to restart.")
                        return True  # Return true since install was initiated
                
                return True
            else:
                print(f"❌ Installation failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error installing BlackHole: {e}")
            return False
    
    def check_blackhole_in_audio_devices(self):
        """Check if BlackHole appears in audio devices"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for device in devices:
                if 'BlackHole' in device.get('name', ''):
                    return True
        except:
            pass
        return False
    
    def get_audio_devices(self):
        """Get list of audio devices using system_profiler"""
        try:
            result = subprocess.run(['system_profiler', 'SPAudioDataType', '-json'],
                                  capture_output=True, text=True)
            data = json.loads(result.stdout)
            devices = []
            
            # Parse audio devices
            for item in data.get('SPAudioDataType', []):
                if '_items' in item:
                    for device in item['_items']:
                        device_info = {
                            'name': device.get('_name', 'Unknown'),
                            'manufacturer': device.get('coreaudio_device_manufacturer', 'Unknown'),
                            'input': device.get('coreaudio_device_input', 0),
                            'output': device.get('coreaudio_device_output', 0),
                            'uid': device.get('coreaudio_device_uid', '')
                        }
                        devices.append(device_info)
            
            return devices
        except Exception as e:
            print(f"Error getting audio devices: {e}")
            return []
    
    def get_current_output_device(self):
        """Get current audio output device"""
        try:
            # Use SwitchAudioSource if available
            result = subprocess.run(['SwitchAudioSource', '-c'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # Fallback: check if we can determine from system
        return "System Default"
    
    def set_output_device(self, device_name):
        """Set audio output device"""
        try:
            # Try using SwitchAudioSource
            result = subprocess.run(['SwitchAudioSource', '-s', device_name], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            print("⚠️  SwitchAudioSource not found. Install with: brew install switchaudio-osx")
            return False
    
    def create_multi_output_device(self, name="QuickScribe Multi-Output"):
        """Create a multi-output device using macOS Audio MIDI Setup"""
        script = f'''
        tell application "Audio MIDI Setup"
            activate
        end tell
        
        tell application "System Events"
            tell process "Audio MIDI Setup"
                -- Open the Audio Devices window
                click menu item "Show Audio Devices" of menu "Window" of menu bar 1
                delay 1
                
                -- Create multi-output device
                click button 1 of window "Audio Devices"
                delay 0.5
                click menu item "Create Multi-Output Device" of menu 1 of button 1 of window "Audio Devices"
                delay 1
                
                -- The device is created, user needs to configure it manually
            end tell
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], capture_output=True)
            print("✅ Opened Audio MIDI Setup. Please:")
            print("1. Check both 'BlackHole 2ch' and your headphones/speakers")
            print("2. Optionally rename it to 'QuickScribe Multi-Output'")
            print("3. Close Audio MIDI Setup when done")
            input("\nPress Enter when you've configured the multi-output device...")
            return True
        except Exception as e:
            print(f"❌ Error creating multi-output device: {e}")
            return False
    
    def setup_system_audio_recording(self):
        """Complete setup for system audio recording"""
        print("\n🎵 Setting up system audio recording...")
        
        # Check if BlackHole is installed
        if not self.check_blackhole_installed():
            print("BlackHole is not installed.")
            install = input("Would you like to install it now? (y/n): ").strip().lower()
            if install == 'y':
                if not self.install_blackhole():
                    print("❌ Failed to install BlackHole. Please install manually:")
                    print("   brew install blackhole-2ch")
                    return False
            else:
                print("❌ BlackHole is required for system audio recording.")
                return False
        
        # Store original output device
        self.original_output = self.get_current_output_device()
        print(f"📱 Current output device: {self.original_output}")
        
        # Check for SwitchAudioSource
        try:
            subprocess.run(['SwitchAudioSource', '-h'], capture_output=True)
        except:
            print("\n⚠️  SwitchAudioSource not found.")
            print("Install it for automatic audio routing:")
            print("   brew install switchaudio-osx")
            print("\nContinuing with manual setup...")
        
        # Offer to create multi-output device
        print("\n🔊 For system audio recording with monitoring:")
        print("1. Record system audio only (no monitoring)")
        print("2. Create multi-output device (hear while recording)")
        
        choice = input("\nSelect option (1-2): ").strip()
        
        if choice == "1":
            print("\n📋 To record system audio:")
            print("1. Go to System Settings → Sound → Output")
            print("2. Select 'BlackHole 2ch'")
            print("3. In QuickScribe, select 'BlackHole 2ch' as input device")
            print("\n⚠️  Note: You won't hear audio while recording!")
        
        elif choice == "2":
            if self.create_multi_output_device():
                print("\n📋 To use the multi-output device:")
                print("1. Go to System Settings → Sound → Output")
                print("2. Select your new multi-output device")
                print("3. In QuickScribe, select 'BlackHole 2ch' as input device")
                print("\n✅ You'll hear audio while recording!")
        
        return True
    
    def restore_audio_settings(self):
        """Restore original audio settings"""
        if self.original_output:
            print(f"\n🔄 Restoring audio output to: {self.original_output}")
            if self.set_output_device(self.original_output):
                print("✅ Audio settings restored!")
            else:
                print("⚠️  Please manually restore your audio output device")

def main():
    """Standalone setup utility"""
    manager = AudioSetupManager()
    manager.setup_system_audio_recording()

if __name__ == "__main__":
    main()