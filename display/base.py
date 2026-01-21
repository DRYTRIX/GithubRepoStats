"""Abstract base class for display drivers."""

from abc import ABC, abstractmethod
from typing import List


class DisplayDriver(ABC):
    """Abstract base class for all display drivers."""
    
    def __init__(self, width: int, height: int):
        """
        Initialize display driver.
        
        Args:
            width: Display width in characters/pixels
            height: Display height in lines/pixels
        """
        self.width = width
        self.height = height
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the display."""
        pass
    
    @abstractmethod
    def write_line(self, line: int, text: str) -> None:
        """
        Write text to a specific line.
        
        Args:
            line: Line number (0-indexed)
            text: Text to write
        """
        pass
    
    @abstractmethod
    def update(self, lines: List[str]) -> None:
        """
        Update the entire display with new content.
        
        Args:
            lines: List of strings, one per line
        """
        pass
    
    def close(self) -> None:
        """Clean up display resources. Override if needed."""
        pass
