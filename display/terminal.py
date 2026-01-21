"""Terminal/console display driver for development and testing."""

import os
from typing import List
from .base import DisplayDriver


class TerminalDisplay(DisplayDriver):
    """Display driver that outputs to terminal/console."""
    
    def __init__(self, width: int = 80, height: int = 4):
        """
        Initialize terminal display.
        
        Args:
            width: Terminal width in characters (default: 80)
            height: Number of lines to display (default: 4)
        """
        super().__init__(width, height)
        self._current_lines = [""] * height
    
    def clear(self) -> None:
        """Clear the terminal display."""
        # Use ANSI escape codes for cross-platform compatibility
        print("\033[2J\033[H", end="")
        self._current_lines = [""] * self.height
    
    def write_line(self, line: int, text: str) -> None:
        """Write text to a specific line."""
        if 0 <= line < self.height:
            # Truncate to width
            truncated = text[:self.width].ljust(self.width)
            self._current_lines[line] = truncated
            self._refresh()
    
    def update(self, lines: List[str]) -> None:
        """Update the entire display."""
        for i, line in enumerate(lines[:self.height]):
            truncated = line[:self.width].ljust(self.width)
            self._current_lines[i] = truncated
        self._refresh()
    
    def _refresh(self) -> None:
        """Refresh the terminal display."""
        # Move cursor to top-left
        print("\033[H", end="")
        # Print all lines
        for line in self._current_lines:
            print(line)
        # Clear remaining lines if any
        remaining = self.height - len(self._current_lines)
        if remaining > 0:
            print("\n" * remaining, end="")
