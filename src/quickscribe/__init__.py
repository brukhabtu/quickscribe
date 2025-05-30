"""
QuickScribe - Privacy-focused meeting recorder and transcriber for macOS.

A simple, local AI-powered tool for recording and transcribing meetings
with complete privacy - nothing sent to external servers.
"""

__version__ = "0.1.0"
__author__ = "QuickScribe"

from .core import QuickScribeCore
from .main import main

__all__ = ["QuickScribeCore", "main"]