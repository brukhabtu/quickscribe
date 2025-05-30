#!/usr/bin/env python3
"""
QuickScribe - Simple Meeting Recorder & Transcriber
Main entry point - chooses between TUI and CLI
"""

import sys
import os

class MeetingRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_data = []
        self.sample_rate = 44100
        self.output_dir = "recordings"
        self.current_file = None
        self.stream = None
        self.selected_device = None
        self.recording_mode = "mic"  # "mic", "system", or "both"
        self.audio_setup = AudioSetupManager()
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check for system audio setup on first run
        self.check_initial_setup()
        
        # Load Whisper model (download on first run)
        print("\nLoading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        print("Model loaded!")
        
        # List available devices on startup
        self.list_audio_devices()
    
    def check_initial_setup(self):
        """Check if system audio recording is set up on first run"""
        # Check if setup has been done before
        setup_file = os.path.join(self.output_dir, ".audio_setup_complete")
        
        if not os.path.exists(setup_file):
            print("\n🎙️ Welcome to QuickScribe!")
            print("\nThis app can record from your microphone or system audio.")
            
            # Check if BlackHole is installed
            if not self.audio_setup.check_blackhole_installed():
                print("\n💡 System audio recording requires BlackHole (free virtual audio driver)")
                print("This lets you record YouTube, Zoom, Teams, etc.")
                
                choice = input("\nWould you like to set it up now? (y/n): ").strip().lower()
                if choice == 'y':
                    if self.audio_setup.setup_system_audio_recording():
                        # Mark setup as complete
                        with open(setup_file, 'w') as f:
                            f.write("Setup completed")
                else:
                    print("\n✅ You can set it up later using option 6")
            else:
                print("\n✅ BlackHole detected! You can record system audio.")
                # Mark setup as complete since BlackHole is already installed
                with open(setup_file, 'w') as f:
                    f.write("BlackHole already installed")
    
    def list_audio_devices(self, show_output=False):
        """List available audio input devices"""
        devices = sd.query_devices()
        input_devices = []
        
        if show_output:
            print("\n🎤 Available Audio Input Devices:")
            print("-" * 50)
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append((i, device))
                if show_output:
                    print(f"{len(input_devices)}. {device['name']} ({device['max_input_channels']} channels)")
                    if 'BlackHole' in device['name']:
                        print("   ⚡ Virtual device for system audio")
                    elif 'Aggregate' in device['name']:
                        print("   🔀 Multi-device input")
        
        return input_devices
    
    def select_audio_device(self):
        """Allow user to select audio input device"""
        devices = self.list_audio_devices(show_output=True)
        
        if not devices:
            print("❌ No audio input devices found!")
            return False
        
        # Check if BlackHole is available
        blackhole_idx = None
        for idx, (dev_id, dev_info) in enumerate(devices):
            if 'BlackHole' in dev_info['name']:
                blackhole_idx = idx + 1
                break
        
        print(f"\nCurrent device: {sd.query_devices(self.selected_device)['name'] if self.selected_device else 'Default'}")
        
        if blackhole_idx:
            print(f"\n💡 Tip: Select {blackhole_idx} for system audio recording")
        
        try:
            choice = input("\nSelect device number (or Enter for default): ").strip()
            if choice == "":
                self.selected_device = None
                print("✅ Using default audio device")
            else:
                device_idx = int(choice) - 1
                if 0 <= device_idx < len(devices):
                    self.selected_device = devices[device_idx][0]
                    selected_name = devices[device_idx][1]['name']
                    print(f"✅ Selected: {selected_name}")
                    
                    # Provide helpful tips based on selection
                    if 'BlackHole' in selected_name:
                        print("\n📋 To record system audio:")
                        print("1. Set your system output to 'BlackHole 2ch'")
                        print("2. Or use a multi-output device (option 6)")
                else:
                    print("❌ Invalid device number")
                    return False
            return True
        except ValueError:
            print("❌ Please enter a valid number")
            return False
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio recording"""
        if self.is_recording:
            self.audio_data.append(indata.copy())
    
    def start_recording(self):
        self.is_recording = True
        self.audio_data = []
        
        # Generate filename with timestamp and device info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        device_info = ""
        if self.selected_device is not None:
            device_name = sd.query_devices(self.selected_device)['name']
            if 'BlackHole' in device_name:
                device_info = "_system"
            elif 'Aggregate' in device_name:
                device_info = "_mixed"
        self.current_file = f"{self.output_dir}/meeting_{timestamp}{device_info}.wav"
        
        # Start audio stream with selected device
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            device=self.selected_device,
            channels=1,
            samplerate=self.sample_rate
        )
        self.stream.start()
        
        device_name = sd.query_devices(self.selected_device)['name'] if self.selected_device else "Default"
        print(f"🔴 Recording started from: {device_name}")
        print(f"📁 File: {self.current_file}")
        print("Press Enter to stop recording...")
    
    def stop_recording(self):
        self.is_recording = False
        
        # Stop audio stream
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Save audio file
        if self.audio_data:
            audio_array = np.concatenate(self.audio_data, axis=0)
            sf.write(self.current_file, audio_array, self.sample_rate)
            
            print(f"✅ Recording saved: {self.current_file}")
            return True
        else:
            print("❌ No audio recorded")
            return False
    
    def transcribe_file(self, audio_file):
        print(f"🤖 Transcribing {audio_file}...")
        
        try:
            # Transcribe
            result = self.whisper_model.transcribe(audio_file)
            
            # Save transcript
            transcript_file = audio_file.replace('.wav', '_transcript.txt')
            with open(transcript_file, 'w') as f:
                f.write(f"Transcript for: {os.path.basename(audio_file)}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                f.write(result["text"])
            
            print(f"✅ Transcript saved: {transcript_file}")
            print("\n--- Transcript Preview ---")
            print(result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"])
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
    
    def list_recordings(self):
        """List recent recordings"""
        if os.path.exists(self.output_dir):
            files = sorted([f for f in os.listdir(self.output_dir) 
                          if f.endswith('.wav')], reverse=True)
            if files:
                print("\n📁 Recent recordings:")
                for i, file in enumerate(files[:10], 1):
                    print(f"{i}. {file}")
                return files[:10]
            else:
                print("No recordings found.")
        return []
    
    def run(self):
        """Main CLI loop"""
        print("\n🎙️ QuickScribe - Meeting Recorder & Transcriber")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Start new recording")
            print("2. Transcribe latest recording")
            print("3. List recordings")
            print("4. Transcribe specific recording")
            print("5. Select audio device")
            print("6. Setup system audio recording")
            print("7. Exit")
            
            current_device = sd.query_devices(self.selected_device)['name'] if self.selected_device else "Default"
            print(f"\n📱 Current device: {current_device}")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == "1":
                # Quick check if BlackHole is selected
                current = sd.query_devices(self.selected_device)['name'] if self.selected_device else "Default"
                
                if 'BlackHole' not in current:
                    # Ask what they want to record
                    print("\n🎤 What would you like to record?")
                    print("1. Microphone (current)")
                    print("2. System audio (YouTube, Zoom, etc.)")
                    
                    rec_choice = input("\nSelect (1-2, or Enter for current): ").strip()
                    
                    if rec_choice == "2":
                        # Auto-select BlackHole if available
                        devices = self.list_audio_devices(show_output=False)
                        blackhole_found = False
                        
                        for dev_id, dev_info in devices:
                            if 'BlackHole' in dev_info['name']:
                                self.selected_device = dev_id
                                print(f"\n✅ Switched to: {dev_info['name']}")
                                print("📋 Remember to set your system output to BlackHole!")
                                blackhole_found = True
                                break
                        
                        if not blackhole_found:
                            print("\n❌ BlackHole not found. Run option 6 to set it up.")
                            continue
                
                self.start_recording()
                input()  # Wait for Enter
                if self.stop_recording():
                    transcribe = input("\nTranscribe now? (y/n): ").strip().lower()
                    if transcribe == 'y':
                        self.transcribe_file(self.current_file)
            
            elif choice == "2":
                if self.current_file and os.path.exists(self.current_file):
                    self.transcribe_file(self.current_file)
                else:
                    print("No recent recording to transcribe.")
            
            elif choice == "3":
                self.list_recordings()
            
            elif choice == "4":
                files = self.list_recordings()
                if files:
                    try:
                        num = int(input("\nEnter recording number: ")) - 1
                        if 0 <= num < len(files):
                            self.transcribe_file(f"{self.output_dir}/{files[num]}")
                        else:
                            print("Invalid number.")
                    except ValueError:
                        print("Please enter a valid number.")
            
            elif choice == "5":
                self.select_audio_device()
            
            elif choice == "6":
                self.audio_setup.setup_system_audio_recording()
                print("\n✅ System audio setup complete!")
                print("Don't forget to select 'BlackHole 2ch' as your input device (option 5)")
            
            elif choice == "7":
                print("\n👋 Goodbye!")
                # Restore audio settings if changed
                self.audio_setup.restore_audio_settings()
                break
            
            else:
                print("Invalid choice. Please try again.")

def main():
    """Entry point for the application"""
    try:
        app = MeetingRecorder()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()