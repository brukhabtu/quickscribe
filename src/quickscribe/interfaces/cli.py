#!/usr/bin/env python3
"""
QuickScribe CLI - Non-interactive command-line interface
"""

import argparse
import sys
import os
import time
import signal
from pathlib import Path
from ..core import QuickScribeCore, DeviceType


class QuickScribeCLI:
    """Non-interactive CLI wrapper around QuickScribeCore"""
    
    def __init__(self, quiet=False):
        if not quiet:
            print("Loading QuickScribe...", file=sys.stderr)
        self.core = QuickScribeCore()
        self.quiet = quiet
        
        # Load Whisper model
        if not quiet:
            self.core.transcriber.load_model(lambda msg: print(msg, file=sys.stderr))
        else:
            self.core.transcriber.load_model(lambda msg: None)
    
    def log(self, message, error=False):
        """Print message unless in quiet mode"""
        if not self.quiet:
            print(message, file=sys.stderr if error else sys.stdout)
    
    def list_devices(self, format_output="human"):
        """List available devices"""
        devices = self.core.get_devices()
        
        if format_output == "json":
            import json
            device_list = []
            for device in devices:
                device_list.append({
                    "id": device.id,
                    "name": device.name,
                    "type": device.device_type.value,
                    "channels": device.channels_in,
                    "is_default": device.is_default,
                    "needs_setup": device.needs_setup,
                    "is_available": device.is_available
                })
            print(json.dumps(device_list, indent=2))
        elif format_output == "tsv":
            print("ID\tNAME\tTYPE\tCHANNELS\tDEFAULT\tNEEDS_SETUP\tAVAILABLE")
            for device in devices:
                print(f"{device.id}\t{device.name}\t{device.device_type.value}\t"
                      f"{device.channels_in}\t{device.is_default}\t{device.needs_setup}\t{device.is_available}")
        else:  # human readable
            print("Available Audio Input Devices:")
            print("-" * 40)
            for device in devices:
                # Status
                status = ""
                if device.needs_setup:
                    status = " (needs setup)"
                elif not device.is_available:
                    status = " (unavailable)"
                
                default_marker = " [DEFAULT]" if device.is_default else ""
                type_marker = f" [{device.device_type.value}]" if device.device_type != DeviceType.PHYSICAL_INPUT else ""
                print(f"{device.id}: {device.name} ({device.channels_in}ch){type_marker}{status}{default_marker}")
    
    def record(self, device_id=None, output_file=None, duration=None, auto_transcribe=False):
        """Start recording"""
        # Set device if specified
        if device_id is not None:
            devices = self.core.get_devices()
            device = next((d for d in devices if d.id == device_id), None)
            if not device:
                self.log(f"Device ID {device_id} not found", error=True)
                return False
            self.core.set_device(device_id)
            self.log(f"Using device: {device.name}")
        elif not self.core.current_device:
            # Use default device
            devices = self.core.get_devices()
            if not devices:
                self.log("No audio devices found", error=True)
                return False
            default_device = next((d for d in devices if d.is_default), devices[0])
            self.core.set_device(default_device.id)
            self.log(f"Using default device: {default_device.name}")
        
        # Start recording
        # Note: The new core interface doesn't support custom output files yet
        # For now, we'll ignore the output_file parameter and use default naming
        if output_file:
            self.log("Warning: Custom output file names not yet supported in new core", error=True)
        
        success, result = self.core.start_recording()
        if not success:
            self.log(f"Failed to start recording: {result}", error=True)
            return False
        
        filename = result
        # For compatibility, we need to get the full path
        filepath = os.path.join(self.core.recorder.output_dir, filename)
        self.log(f"Recording to: {filepath}")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(signum, frame):
            self.log("\nStopping recording...")
            success, result = self.core.stop_recording()
            if success:
                self.log(f"Recording saved: {result}")
                if auto_transcribe:
                    self.transcribe(result)
            else:
                self.log(f"Error stopping recording: {result}", error=True)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Record for specified duration or until interrupted
        if duration:
            self.log(f"Recording for {duration} seconds... (Ctrl+C to stop early)")
            time.sleep(duration)
            success, result = self.core.stop_recording()
            if success:
                self.log(f"Recording completed: {result}")
                if auto_transcribe:
                    self.transcribe(result)
                return True
            else:
                self.log(f"Error stopping recording: {result}", error=True)
                return False
        else:
            self.log("Recording... (Ctrl+C to stop)")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass  # Signal handler will take care of stopping
    
    def list_recordings(self, format_output="human", limit=None):
        """List recordings"""
        recordings = self.core.get_recordings()
        
        if limit:
            recordings = recordings[:limit]
        
        if format_output == "json":
            import json
            rec_list = []
            for rec in recordings:
                rec_list.append({
                    "filename": rec.filename,
                    "filepath": str(rec.filepath),
                    "timestamp": rec.timestamp.isoformat(),
                    "duration": rec.duration,
                    "device_name": rec.device_name,
                    "has_transcript": rec.has_transcript
                })
            print(json.dumps(rec_list, indent=2))
        elif format_output == "tsv":
            print("FILENAME\tFILEPATH\tTIMESTAMP\tDURATION\tDEVICE\tTRANSCRIPT")
            for rec in recordings:
                print(f"{rec.filename}\t{rec.filepath}\t{rec.timestamp.isoformat()}\t"
                      f"{rec.duration:.1f}\t{rec.device_name}\t{rec.has_transcript}")
        else:  # human readable
            if not recordings:
                print("No recordings found.")
                return
            
            print("Recordings:")
            for rec in recordings:
                duration = f"{int(rec.duration // 60)}:{int(rec.duration % 60):02d}"
                transcript = "✓" if rec.has_transcript else " "
                timestamp = rec.timestamp.strftime("%Y-%m-%d %H:%M")
                print(f"[{transcript}] {rec.filename} ({duration}) - {timestamp} - {rec.device_name}")
    
    def transcribe(self, filepath, output_file=None):
        """Transcribe a recording"""
        if not os.path.exists(filepath):
            self.log(f"File not found: {filepath}", error=True)
            return False
        
        self.log(f"Transcribing {os.path.basename(filepath)}...")
        
        def progress(msg):
            if not self.quiet:
                self.log(f"  {msg}")
        
        # Note: The new core interface doesn't support custom output files yet
        # For now, we'll ignore the output_file parameter
        if output_file:
            self.log("Warning: Custom transcript output files not yet supported in new core", error=True)
        
        success, result = self.core.transcribe_recording(filepath, progress)
        
        if success:
            self.log(f"Transcript saved: {result}")
            return True
        else:
            self.log(f"Transcription failed: {result}", error=True)
            return False
    
    def show_transcript(self, filepath, lines=None):
        """Show transcript content"""
        # Find transcript file
        if filepath.endswith('.wav'):
            transcript_path = filepath.replace('.wav', '_transcript.txt')
        else:
            transcript_path = filepath
        
        if not os.path.exists(transcript_path):
            self.log(f"Transcript not found: {transcript_path}", error=True)
            return False
        
        try:
            # Try UTF-8 first, fallback if needed
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(transcript_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Skip header if present
                if "-" * 50 in content:
                    parts = content.split("-" * 50, 2)
                    if len(parts) >= 2:
                        content = parts[1].strip()
                
                if lines:
                    content_lines = content.split('\n')
                    content = '\n'.join(content_lines[:lines])
                
                print(content)
            return True
        except Exception as e:
            self.log(f"Error reading transcript: {e}", error=True)
            return False


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="QuickScribe - Meeting Recorder & Transcriber",
        epilog="Examples:\n"
               "  quickscribe record --duration 300 --auto-transcribe\n"
               "  quickscribe devices --format json\n"
               "  quickscribe transcribe recording.wav\n"
               "  quickscribe list --limit 5",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress messages")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Devices command
    devices_parser = subparsers.add_parser("devices", help="List audio devices")
    devices_parser.add_argument("--format", choices=["human", "json", "tsv"], default="human",
                               help="Output format")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Start recording")
    record_parser.add_argument("-d", "--device", type=int, help="Device ID to use")
    record_parser.add_argument("-o", "--output", help="Output file path")
    record_parser.add_argument("-t", "--duration", type=int, help="Recording duration in seconds")
    record_parser.add_argument("--auto-transcribe", action="store_true", 
                              help="Automatically transcribe after recording")
    
    # List recordings command
    list_parser = subparsers.add_parser("list", help="List recordings")
    list_parser.add_argument("--format", choices=["human", "json", "tsv"], default="human",
                            help="Output format")
    list_parser.add_argument("--limit", type=int, help="Limit number of results")
    
    # Transcribe command
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe a recording")
    transcribe_parser.add_argument("file", help="Audio file to transcribe")
    transcribe_parser.add_argument("-o", "--output", help="Output transcript file")
    
    # Show transcript command
    show_parser = subparsers.add_parser("show", help="Show transcript content")
    show_parser.add_argument("file", help="Audio file or transcript file")
    show_parser.add_argument("--lines", type=int, help="Show only first N lines")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        cli = QuickScribeCLI(quiet=args.quiet)
        
        if args.command == "devices":
            cli.list_devices(args.format)
        
        elif args.command == "record":
            success = cli.record(
                device_id=args.device,
                output_file=args.output,
                duration=args.duration,
                auto_transcribe=args.auto_transcribe
            )
            sys.exit(0 if success else 1)
        
        elif args.command == "list":
            cli.list_recordings(args.format, args.limit)
        
        elif args.command == "transcribe":
            success = cli.transcribe(args.file, args.output)
            sys.exit(0 if success else 1)
        
        elif args.command == "show":
            success = cli.show_transcript(args.file, args.lines)
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        if not args.quiet:
            print("\nInterrupted", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()