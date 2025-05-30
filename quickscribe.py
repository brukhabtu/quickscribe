#!/usr/bin/env python3
"""
QuickScribe - Simple Meeting Recorder & Transcriber
Main entry point - chooses between TUI and CLI
"""

import sys
import os


def main():
    """Main entry point"""
    # Check if we're in a terminal that supports TUI
    if sys.stdout.isatty() and os.environ.get('TERM'):
        # Check for --cli flag
        if '--cli' in sys.argv:
            from quickscribe_cli import main as cli_main
            cli_main()
        else:
            # Default to TUI
            try:
                from quickscribe_tui import main as tui_main
                print("Starting QuickScribe TUI...")
                print("(Use --cli flag for simple CLI mode)")
                tui_main()
            except ImportError:
                print("TUI not available, falling back to CLI")
                from quickscribe_cli import main as cli_main
                cli_main()
    else:
        # Not in interactive terminal, use CLI
        from quickscribe_cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()