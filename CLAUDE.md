# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

QuickScribe is a privacy-focused CLI meeting recorder and transcriber for macOS that uses local AI (OpenAI Whisper) for transcription. The project is structured with a modular architecture separating UI from business logic.

## Development Commands

This project uses UV for Python package management:

```bash
# Install dependencies
uv sync

# Run the application (TUI mode by default)
uv run quickscribe

# Run in CLI mode
uv run quickscribe --cli

# Quick launch via shell script
./run.sh

# Add new dependencies
uv add package-name

# Update dependencies
uv sync --upgrade
```

## Architecture

### Core Components

- **quickscribe.py**: Main entry point that chooses between TUI and CLI interfaces
- **quickscribe_core.py**: Pure business logic with no UI dependencies
  - `QuickScribeCore`: Main API class 
  - `Recorder`: Audio recording functionality
  - `Transcriber`: Whisper-based transcription
  - `AudioDeviceManager`: Device detection and categorization
- **quickscribe_cli.py**: Non-interactive command-line interface
- **quickscribe_tui.py**: Textual-based terminal user interface
- **audio_setup.py**: BlackHole installation and audio routing management

### Key Design Patterns

- **Separation of Concerns**: UI layers (CLI/TUI) are completely separate from business logic (core)
- **Device Type Classification**: Automatically detects and categorizes audio devices (physical, virtual loopback, app virtual, aggregate)
- **Async/Await**: TUI uses asyncio for non-blocking operations
- **Reactive UI**: TUI uses Textual's reactive system for real-time updates

### Audio Device Architecture

The system categorizes audio devices into types:
- `PHYSICAL_INPUT`: Regular microphones
- `VIRTUAL_LOOPBACK`: BlackHole, Soundflower (for system audio)
- `APP_VIRTUAL`: Teams, Zoom, Discord virtual devices
- `AGGREGATE`: Multi-output devices

### File Storage

All recordings are saved to `~/.quickscribe/` in the user's home directory. Files are automatically named with timestamps and device type suffixes:
- `meeting_20240529_143022.wav` (microphone)
- `meeting_20240529_143022_system.wav` (system audio via BlackHole)
- `meeting_20240529_143022_app.wav` (app virtual device)
- `*_transcript.txt` (generated transcripts)

## System Requirements

- macOS with Python 3.9+
- FFmpeg (installed via brew)
- Optional: BlackHole for system audio recording
- Optional: SwitchAudioSource for automatic audio routing

## Dependencies

Key dependencies managed in pyproject.toml:
- `sounddevice`: Audio I/O
- `openai-whisper`: Local AI transcription
- `soundfile`: Audio file handling
- `textual`: TUI framework
- `numpy`: Audio processing

## Entry Points

The project defines `quickscribe = "quickscribe:main"` in pyproject.toml, making the main module the primary entry point that intelligently chooses between TUI and CLI based on terminal capabilities.