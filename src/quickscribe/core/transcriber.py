#!/usr/bin/env python3
"""
Transcriber module - Handles transcription using Whisper AI
"""

import os
import threading
import whisper
import warnings
from datetime import datetime
from typing import Optional, Callable, Tuple


class Transcriber:
    """Handles transcription using Whisper"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self._load_lock = threading.Lock()
    
    def load_model(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Load Whisper model"""
        with self._load_lock:
            if self.model is None:
                if progress_callback:
                    progress_callback("Loading Whisper model...")
                self.model = whisper.load_model(self.model_size)
                if progress_callback:
                    progress_callback("Model loaded!")
    
    def transcribe(self, 
                   audio_file: str, 
                   progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Transcribe an audio file"""
        if not self.model:
            self.load_model(progress_callback)
        
        try:
            if progress_callback:
                progress_callback("Transcribing...")
            
            # Simple transcription with just warning suppression
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
                result = self.model.transcribe(audio_file)
            text = result["text"]
            
            # Save transcript with explicit UTF-8 encoding and error handling
            transcript_file = audio_file.replace('.wav', '_transcript.txt')
            
            # Ensure text is properly encoded
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            elif not isinstance(text, str):
                text = str(text)
            
            # Clean text of any problematic characters
            text = text.encode('utf-8', errors='replace').decode('utf-8')
            
            with open(transcript_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(f"Transcript for: {os.path.basename(audio_file)}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 50 + "\n\n")
                f.write(text)
            
            if progress_callback:
                progress_callback("Transcription complete!")
            
            return True, transcript_file
            
        except Exception as e:
            return False, str(e)