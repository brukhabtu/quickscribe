# QuickScribe

A simple, privacy-focused CLI meeting recorder and transcriber for macOS.

## Features

- 🎙️ Quick recording with simple Enter key to stop
- 🖥️ Record system audio from Zoom, Teams, etc.
- 🎤 Select any audio input device
- 🤖 Local AI transcription using OpenAI Whisper
- 🔒 Complete privacy - nothing sent to external servers
- 📁 Automatic file organization with timestamps
- 💻 Clean command-line interface
- 🚀 No GUI dependencies - works on any system

## Installation

1. **Install system dependencies:**
   ```bash
   # Install ffmpeg (required for audio processing)
   brew install ffmpeg
   ```

2. **Install uv** (if you don't have it):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Navigate to the project directory:**
   ```bash
   cd quickscribe
   ```

4. **Install Python dependencies:**
   ```bash
   uv sync
   ```

## Usage

```bash
# Interactive TUI mode (default)
uv run quickscribe

# Simple CLI mode
uv run quickscribe --cli
```

### Quick Recording (TUI Mode)
1. Run `uv run quickscribe`
2. Use arrow keys or j/k to navigate
3. Press Space to start/stop recording
4. Press Enter to select items
5. Press 't' to transcribe latest recording

### CLI Mode
```bash
# List available audio devices
uv run python quickscribe_cli.py devices

# Start recording (Ctrl+C to stop)
uv run python quickscribe_cli.py record

# Record for 5 minutes and auto-transcribe
uv run python quickscribe_cli.py record --duration 300 --auto-transcribe

# List recordings
uv run python quickscribe_cli.py list

# Transcribe a specific file
uv run python quickscribe_cli.py transcribe ~/.quickscribe/meeting_20240529_143022.wav

# Show transcript content
uv run python quickscribe_cli.py show ~/.quickscribe/meeting_20240529_143022.wav
```

### TUI Controls
- **Space** - Start/Stop recording
- **Enter** - Select highlighted item
- **t** - Transcribe latest recording
- **r** - Refresh device list
- **j/k or ↑/↓** - Navigate lists
- **Tab/Shift+Tab** - Switch between panels
- **q** - Quit application

### Recording Virtual Meetings (Zoom, Teams, etc.)

QuickScribe can now automatically set up system audio recording!

#### Easy Setup (Recommended)
1. Run QuickScribe and select **option 6** - "Setup system audio recording"
2. Follow the guided setup to install BlackHole and configure audio routing
3. Select **option 5** and choose "BlackHole 2ch" as your input device
4. Start recording!

#### Manual Setup
If you prefer manual configuration:

1. **Install BlackHole** (free virtual audio driver):
   ```bash
   brew install blackhole-2ch
   ```

2. **For System Audio Only:**
   - Set system output to "BlackHole 2ch" 
   - You won't hear audio while recording

3. **For Audio Monitoring (hear while recording):**
   - Create a multi-output device in Audio MIDI Setup
   - Include both BlackHole and your headphones/speakers
   - Set this as your system output

#### Pro Tips
- QuickScribe automatically detects BlackHole and suggests it for system audio
- Files are named with "_system" suffix when using BlackHole
- Original audio settings are restored when you exit QuickScribe

## How it works

1. Choose "Start new recording" from the menu
2. Press Enter to stop recording
3. Your audio is saved with a timestamp
4. Choose to transcribe immediately or later
5. Transcripts are saved as text files alongside the audio

## File Storage

All recordings are automatically saved to `~/.quickscribe/` in your home directory:

```
~/.quickscribe/
├── meeting_20240529_143022.wav           # Microphone recording
├── meeting_20240529_143022_transcript.txt # Generated transcript
├── meeting_20240529_160230_system.wav    # System audio recording
├── meeting_20240529_160230_system_transcript.txt
└── ...
```

**File naming convention:**
- `meeting_YYYYMMDD_HHMMSS.wav` - Microphone recordings
- `meeting_YYYYMMDD_HHMMSS_system.wav` - System audio (BlackHole)
- `meeting_YYYYMMDD_HHMMSS_app.wav` - App-specific virtual devices
- `*_transcript.txt` - Generated transcripts

## System Requirements

- macOS with Python 3.9+
- FFmpeg (install with `brew install ffmpeg`)
- Microphone access permissions
- ~1GB free space for Whisper model (downloaded on first run)

## Important Notes

- **Privacy First**: All processing happens locally - your audio never leaves your computer
- **First Run**: Downloads the Whisper "base" model (~140MB) automatically
- **Model Selection**: Edit `quickscribe_core.py` to use "small", "medium", or "large" models for better accuracy
- **Storage**: Recordings are saved to `~/.quickscribe/` and persist between sessions
- **Permissions**: Requires microphone access permissions in System Settings

## Development

To add new dependencies:
```bash
uv add package-name
```

To update dependencies:
```bash
uv sync --upgrade
```

## Troubleshooting

If you get permission errors, make sure Python has microphone access in System Preferences > Security & Privacy > Privacy > Microphone.
