#!/usr/bin/env python3
"""
QuickScribe TUI - Textual-based Terminal User Interface
Uses quickscribe_core for all business logic
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, ListView, ListItem, Label, ProgressBar
from textual.containers import Container, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.message import Message
from textual import events
from textual.timer import Timer

from quickscribe_core import QuickScribeCore, AudioDevice, DeviceType, Recording
from datetime import datetime
import asyncio
from typing import Optional


class DeviceItem(ListItem):
    """Custom list item for audio devices"""
    
    def __init__(self, device: AudioDevice, is_selected: bool = False) -> None:
        self.device = device
        self.is_selected = is_selected
        super().__init__()
    
    def compose(self) -> ComposeResult:
        """Create device display"""
        # Selection indicator
        selector = "●" if self.is_selected else "○"
        
        # Device type indicator
        type_marker = ""
        if self.device.device_type == DeviceType.VIRTUAL_LOOPBACK:
            type_marker = "[LOOP]"
        elif self.device.device_type == DeviceType.APP_VIRTUAL:
            type_marker = "[APP]"
        elif self.device.device_type == DeviceType.AGGREGATE:
            type_marker = "[AGG]"
        
        # Status indicator
        status = ""
        if self.device.needs_setup:
            status = " (setup needed)"
        elif not self.device.is_available:
            status = " (unavailable)"
        
        display_text = f"{selector} {self.device.name} ({self.device.channels_in}ch){type_marker}{status}"
        yield Label(display_text)


class RecordingItem(ListItem):
    """Custom list item for recordings"""
    
    def __init__(self, recording: Recording) -> None:
        self.recording = recording
        super().__init__()
    
    def compose(self) -> ComposeResult:
        """Create recording display"""
        # Format duration
        duration = f"{int(self.recording.duration // 60)}:{int(self.recording.duration % 60):02d}"
        
        # Transcript indicator
        transcript = "✓" if self.recording.has_transcript else "○"
        
        # Format timestamp
        time_str = self.recording.timestamp.strftime("%H:%M")
        
        # Use Rich markup-safe format
        yield Label(
            f"{transcript} {self.recording.filename} ({duration}) - {time_str}"
        )


class AudioLevelDisplay(Static):
    """Audio level meter display"""
    
    level = reactive(-60.0)
    
    def render(self) -> str:
        """Render the audio level meter"""
        # Convert dB to 0-1 range (-60dB to 0dB)
        normalized = max(0, min(1, (self.level + 60) / 60))
        
        # Create visual meter
        bar_width = 40
        filled = int(normalized * bar_width)
        empty = bar_width - filled
        
        # Color based on level
        if normalized > 0.9:
            bar_color = "red"
        elif normalized > 0.7:
            bar_color = "yellow"
        else:
            bar_color = "green"
        
        meter = f"[{bar_color}]{'█' * filled}[/][dim]{'░' * empty}[/]"
        
        return f"Level: {meter} {self.level:.1f}dB"
    
    def update_level(self, level: float) -> None:
        """Update the audio level"""
        self.level = level


class QuickScribeTUI(App):
    """Main TUI Application"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #device-container {
        height: 50%;
        border: solid green;
        margin: 1;
        padding: 1;
    }
    
    #recordings-container {
        height: 45%;
        border: solid cyan;
        margin: 1;
        padding: 1;
    }
    
    #level-meter {
        height: 1;
        margin: 0 0 1 0;
    }
    
    .recording {
        background: $boost;
        color: red;
    }
    """
    
    BINDINGS = [
        ("space", "toggle_recording", "Start/Stop Recording"),
        ("t", "transcribe_latest", "Transcribe Latest"),
        ("r", "refresh_devices", "Refresh Devices"),
        ("enter", "select_focused_item", "Select Item"),
        ("j,down", "move_down", "Move Down"),
        ("k,up", "move_up", "Move Up"),
        ("tab", "focus_next", "Next Pane"),
        ("shift+tab", "focus_previous", "Previous Pane"),
        ("q", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.core = QuickScribeCore()
        self.selected_device: Optional[AudioDevice] = None
        self.update_timer: Optional[Timer] = None
        
    def compose(self) -> ComposeResult:
        """Create app layout"""
        yield Header()
        
        # Device selection (full width)
        with Container(id="device-container"):
            yield Label("Audio Devices - Status: Ready", id="device-header")
            yield AudioLevelDisplay(id="level-meter")
            yield ListView(id="device-list")
        
        # Recordings list
        with Container(id="recordings-container"):
            yield Label("Recent Recordings:")
            yield ListView(id="recordings-list")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize when app starts"""
        # Load devices
        await self.refresh_devices()
        
        # Load recordings
        await self.refresh_recordings()
        
        # Set up audio level callback
        self.core.recorder.set_level_callback(self.update_audio_level)
        
        # Start update timer
        self.update_timer = self.set_interval(1.0, self.update_status)
        
        # Set initial focus to device list
        device_list = self.query_one("#device-list", ListView)
        device_list.focus()
    
    def update_audio_level(self, level: float) -> None:
        """Update audio level display"""
        try:
            level_meter = self.query_one("#level-meter", AudioLevelDisplay)
            level_meter.update_level(level)
        except Exception:
            # Ignore if level meter not found
            pass
    
    async def update_status(self) -> None:
        """Update status display"""
        device_header = self.query_one("#device-header", Label)
        
        # Get current status
        status = "🔴 RECORDING" if self.core.is_recording else "Ready"
        
        # Get selected device name
        device_name = self.selected_device.name if self.selected_device else "None"
        
        # Update header
        device_header.update(f"Audio Devices - Status: {status} - Selected: {device_name}")
        
        # Apply recording style
        if self.core.is_recording:
            device_header.add_class("recording")
        else:
            device_header.remove_class("recording")
    
    async def refresh_devices(self) -> None:
        """Refresh device list"""
        device_list = self.query_one("#device-list", ListView)
        device_list.clear()
        
        devices = self.core.get_devices()
        for device in devices:
            is_selected = bool(self.selected_device and device.id == self.selected_device.id)
            device_list.append(DeviceItem(device, is_selected))
        
        # Select default device if none selected
        if not self.selected_device and devices:
            default = next((d for d in devices if d.is_default), devices[0])
            self.select_device(default)
    
    async def refresh_recordings(self) -> None:
        """Refresh recordings list"""
        recordings_list = self.query_one("#recordings-list", ListView)
        recordings_list.clear()
        
        recordings = self.core.get_recordings()
        for recording in recordings[:10]:  # Show last 10
            recordings_list.append(RecordingItem(recording))
    
    def select_device(self, device: AudioDevice) -> None:
        """Select an audio device"""
        self.selected_device = device
        self.core.set_device(device.id)
        
        # Update header with device info
        device_header = self.query_one("#device-header", Label)
        status = "🔴 RECORDING" if self.core.is_recording else "Ready"
        device_header.update(f"Audio Devices - Status: {status} - Selected: {device.name}")
        
        # Refresh device list to update selection indicators
        asyncio.create_task(self.refresh_devices())
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list selection"""
        if event.list_view.id == "device-list":
            # Device selected
            item = event.item
            if isinstance(item, DeviceItem):
                self.select_device(item.device)
        
        elif event.list_view.id == "recordings-list":
            # Recording selected - transcribe it
            item = event.item
            if isinstance(item, RecordingItem):
                await self.transcribe_recording(item.recording)
    
    async def action_toggle_recording(self) -> None:
        """Start or stop recording"""        
        if not self.core.is_recording:
            # Start recording
            if not self.selected_device:
                self.notify("Please select a device first", severity="error")
                return
            
            success, result = self.core.start_recording()
            if success:
                self.notify(f"🔴 Recording to: {result}")
            else:
                self.notify(f"Failed to start: {result}", severity="error")
        else:
            # Stop recording
            success, filepath = self.core.stop_recording()
            if success:
                self.notify("⏹️ Recording saved!")
                await self.refresh_recordings()
            else:
                self.notify(f"Failed to stop: {filepath}", severity="error")
    
    async def action_transcribe_latest(self) -> None:
        """Transcribe the latest recording"""
        recordings = self.core.get_recordings()
        if not recordings:
            self.notify("No recordings found", severity="warning")
            return
        
        await self.transcribe_recording(recordings[0])
    
    async def transcribe_recording(self, recording: Recording) -> None:
        """Transcribe a specific recording"""
        if recording.has_transcript:
            self.notify("Already transcribed", severity="info")
            return
        
        self.notify(f"Transcribing {recording.filename}...")
        
        # Run transcription in background
        def progress(msg: str):
            self.call_from_thread(self.notify, msg)
        
        success, result = await asyncio.to_thread(
            self.core.transcribe_recording,
            recording.filepath,
            progress
        )
        
        if success:
            self.notify("Transcription complete!", severity="success")
            await self.refresh_recordings()
        else:
            self.notify(f"Transcription failed: {result}", severity="error")
    
    async def action_refresh_devices(self) -> None:
        """Refresh device list"""
        await self.refresh_devices()
        self.notify("Devices refreshed")
    
    async def action_select_focused_item(self) -> None:
        """Select the currently focused item (context-aware)"""
        focused = self.focused
        
        if focused and focused.id == "device-list":
            # In device list - select device
            device_list = self.query_one("#device-list", ListView)
            if device_list.highlighted_child:
                item = device_list.highlighted_child
                if isinstance(item, DeviceItem):
                    self.select_device(item.device)
        
        elif focused and focused.id == "recordings-list":
            # In recordings list - transcribe recording
            recordings_list = self.query_one("#recordings-list", ListView)
            if recordings_list.highlighted_child:
                item = recordings_list.highlighted_child
                if isinstance(item, RecordingItem):
                    await self.transcribe_recording(item.recording)
    
    async def action_move_down(self) -> None:
        """Move down in focused list"""
        focused = self.focused
        if focused and isinstance(focused, ListView):
            focused.action_cursor_down()
    
    async def action_move_up(self) -> None:
        """Move up in focused list"""
        focused = self.focused
        if focused and isinstance(focused, ListView):
            focused.action_cursor_up()
    


def main():
    """Run the TUI application"""
    app = QuickScribeTUI()
    app.run()


if __name__ == "__main__":
    main()