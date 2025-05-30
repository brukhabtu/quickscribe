# QuickScribe Textual UI Plan

## Layout Overview
```
┌─────────────────────────────────────────────────────────┐
│ 🎙️ QuickScribe - Meeting Recorder & Transcriber         │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────────────┐ │
│ │ Audio Devices       │ │ Recording Status           │ │
│ │                     │ │                            │ │
│ │ 🎤 Microphone       │ │ ⭕ Ready to Record         │ │
│ │ • AirPods Max       │ │                            │ │
│ │ • MacBook Mic       │ │ Current Device:            │ │
│ │                     │ │ AirPods Max                │ │
│ │ 🔊 System Audio     │ │                            │ │
│ │ • MS Teams Audio    │ │ ░░░░░░░░░░░░░░░░░░░░      │ │
│ │ • Zoom Audio        │ │ Volume Level               │ │
│ │ • BlackHole 2ch*    │ │                            │ │
│ │                     │ └─────────────────────────────┘ │
│ │ [Select Device]     │                                 │
│ └─────────────────────┘ ┌─────────────────────────────┐ │
│                         │ Recent Recordings           │ │
│ ┌─────────────────────┐ │                            │ │
│ │ Actions             │ │ 📄 meeting_20250529.wav    │ │
│ │                     │ │    Duration: 5:23          │ │
│ │ [▶️ Start Recording] │ │    [Transcribe]            │ │
│ │ [⏹️ Stop]           │ │                            │ │
│ │ [📝 Transcribe]     │ │ 📄 meeting_20250528.wav    │ │
│ │ [⚙️ Setup Audio]    │ │    Duration: 12:45         │ │
│ │ [❌ Exit]           │ │    ✅ Transcribed          │ │
│ └─────────────────────┘ └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Device Selection Panel (Left)
- Visual grouping: Microphones vs System Audio
- One-click device selection
- Visual indicator for current device
- Auto-detect BlackHole/virtual devices
- Show device status (active/inactive)

### 2. Recording Status (Top Right)
- Large, clear recording indicator
- Real-time audio level meter
- Current device display
- Recording timer when active
- File name preview

### 3. Actions Panel (Bottom Left)
- Big, clear buttons
- Context-sensitive (Stop only shows when recording)
- Keyboard shortcuts displayed
- Visual feedback on hover/press

### 4. Recent Recordings (Bottom Right)
- List of recent files
- Duration and status
- One-click transcribe
- Visual indicators for transcribed files
- Scrollable list

## Interaction Flow

1. **Device Selection**
   - Click any device to select
   - Automatic routing suggestions
   - Visual feedback immediately

2. **Recording**
   - Big red button to start
   - ESC or button to stop
   - Live audio meter
   - Clear status messages

3. **Transcription**
   - One-click on any file
   - Progress bar during transcription
   - Preview in modal/popup

## Color Scheme
- Background: Dark theme friendly
- Recording: Red accents
- Active: Green highlights
- System audio: Blue markers
- Transcribed: Check marks

## Keyboard Shortcuts
- `Space` - Start/Stop recording
- `t` - Transcribe latest
- `↑/↓` - Navigate devices
- `Enter` - Select device
- `q` - Quit
- `s` - Setup audio

Would you like me to start implementing this UI design?