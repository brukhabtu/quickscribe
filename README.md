# QuickScribe

A simple, privacy-focused meeting recorder and transcriber for macOS. Perfect for engineering managers who need meeting notes but can't rely on host-enabled recordings or easy transcript downloads.

## ✨ Features

- 🎙️ **One-click recording** - Space to start/stop, Enter to transcribe/view
- 🖥️ **Record system audio** from Zoom, Teams, etc. without host permissions
- 🎤 **Select any audio input** device (microphone, virtual devices)
- 🤖 **Local AI transcription** using OpenAI Whisper (same tech as ChatGPT voice)
- 🔒 **Complete privacy** - nothing sent to external servers, all processing local
- 📁 **Smart file organization** - auto-saves to `~/.quickscribe/` with timestamps
- 💻 **Clean TUI + CLI interfaces** - both interactive and scriptable modes
- 🚀 **No GUI dependencies** - works on any terminal, perfect for engineers

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   # Install ffmpeg (required for audio processing)
   brew install ffmpeg
   
   # Install uv (modern Python package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup:**
   ```bash
   git clone https://github.com/brukhabtu/quickscribe.git
   cd quickscribe
   uv sync
   ```

3. **Start recording meetings:**
   ```bash
   uv run quickscribe
   ```

## 🎯 Usage

### Interactive TUI (Recommended)
```bash
uv run quickscribe
```

**Smart controls:**
- **Space** - Start/Stop recording
- **Enter** - View transcript (if exists) OR start transcription (if not)
- **Tab** - Switch between device selection and recordings
- **j/k or ↑/↓** - Navigate lists
- **r** - Refresh devices
- **q** - Quit

### Command Line Interface
```bash
# List available audio devices
uv run quickscribe devices

# Start recording (Ctrl+C to stop)
uv run quickscribe record

# Record for 5 minutes and auto-transcribe
uv run quickscribe record --duration 300 --auto-transcribe

# List recordings with transcript status
uv run quickscribe list

# Transcribe a specific file
uv run quickscribe transcribe ~/.quickscribe/meeting_20240529_143022.wav

# View transcript content
uv run quickscribe show ~/.quickscribe/meeting_20240529_143022.wav
```

## 🎬 Recording Virtual Meetings

### For Zoom, Teams, Discord, etc.

**Option 1: Automatic Setup (Recommended)**
1. Install BlackHole: `brew install blackhole-2ch`
2. Run QuickScribe, select "BlackHole 2ch" as input device
3. Set your Mac's audio output to BlackHole (you won't hear audio while recording)

**Option 2: Monitor While Recording**
1. Open Audio MIDI Setup (in Applications/Utilities)
2. Create a "Multi-Output Device" 
3. Check both BlackHole and your speakers/headphones
4. Set this multi-output as your system audio output
5. Select BlackHole as input in QuickScribe

**Pro Tips:**
- QuickScribe auto-detects BlackHole and labels it clearly
- System audio recordings get "_system" suffix automatically
- Works with any meeting app - no plugins or permissions needed

## 📁 File Organization

All recordings auto-save to `~/.quickscribe/`:

```
~/.quickscribe/
├── meeting_20240529_143022.wav           # Microphone recording
├── meeting_20240529_143022_transcript.txt # AI-generated transcript
├── meeting_20240529_160230_system.wav    # System audio (Zoom/Teams)
├── meeting_20240529_160230_system_transcript.txt
└── quickscribe_errors.log                # Debug logs (if needed)
```

**Naming Convention:**
- `meeting_YYYYMMDD_HHMMSS.wav` - Microphone recordings  
- `meeting_YYYYMMDD_HHMMSS_system.wav` - System audio recordings
- `*_transcript.txt` - AI-generated transcripts

## 🔧 System Requirements

- **macOS** with Python 3.9+
- **FFmpeg** (`brew install ffmpeg`)
- **Microphone permissions** (System Settings → Privacy & Security → Microphone)
- **~1GB free space** for Whisper AI model (auto-downloaded on first use)

## 🛡️ Privacy & Security

- **100% local processing** - your audio never leaves your computer
- **No cloud services** - no OpenAI API calls, no external transcription services
- **No telemetry** - zero data collection or tracking
- **Open source** - audit the code yourself

## ⚡ Performance

- **Whisper "base" model** (~140MB) - good balance of speed/accuracy
- **~2-3x realtime transcription** on Apple Silicon Macs
- **Handles 1+ hour meetings** easily
- **Upgrade to "small"/"medium"/"large"** models in `src/quickscribe/core/transcriber.py` for better accuracy

## 🔨 Development

This project uses modern Python packaging with UV:

```bash
# Add dependencies
uv add package-name

# Update dependencies  
uv sync --upgrade

# Run tests
uv run pytest  # (when tests are added)

# Build package
uv build
```

**Architecture:**
- `src/quickscribe/core/` - Business logic (recording, transcription, device management)
- `src/quickscribe/interfaces/` - User interfaces (TUI and CLI)
- `src/quickscribe/utils/` - Utilities (audio setup helpers)

## 🤝 Contributing

This tool was built to solve a real problem for engineering teams. If you have suggestions or improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🙋‍♂️ Use Cases

**Perfect for:**
- Engineering managers who need meeting notes but hosts don't enable recording
- 1:1s, team syncs, and planning meetings where you want searchable transcripts
- Recording your own presentations or demos for later review
- Backup recordings when you can't trust the primary recording setup

**Engineering-friendly features:**
- Terminal-based interface (no GUI bloat)
- Keyboard-driven workflow
- Local processing (no dependencies on external services)
- Clean, organized file output
- Scriptable CLI for automation

## 📜 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for engineering teams who value privacy and local control.**