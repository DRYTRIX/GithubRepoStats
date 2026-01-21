"""Full-screen GUI display driver using tkinter for HDMI screens."""

import tkinter as tk
from tkinter import font
from typing import List, Optional, Dict, Any
from .base import DisplayDriver


class GUIDisplay(DisplayDriver):
    """Full-screen GUI display for HDMI screens using tkinter."""
    
    def __init__(
        self,
        fullscreen: bool = True,
        bg_color: str = "#0a0e27",
        text_color: str = "#ffffff",
        accent_color: str = "#00d4ff",
        font_family: str = "Segoe UI",
        title_font_size: int = 64,
        body_font_size: int = 32,
        small_font_size: int = 20
    ):
        """
        Initialize GUI display.
        
        Args:
            fullscreen: Whether to run in fullscreen mode
            bg_color: Background color (hex)
            text_color: Text color (hex)
            accent_color: Accent color for highlights (hex)
            font_family: Font family name
            title_font_size: Font size for titles
            body_font_size: Font size for body text
            small_font_size: Font size for small text
        """
        # Initialize base class with screen dimensions (will be updated)
        super().__init__(width=1920, height=1080)  # Default, will be updated
        
        self.root = tk.Tk()
        self.fullscreen = fullscreen
        self.bg_color = bg_color
        self.text_color = text_color
        self.accent_color = accent_color
        
        # Configure window
        self.root.configure(bg=bg_color)
        self.root.title("GitHub Repository Statistics")
        
        if fullscreen:
            self.root.attributes("-fullscreen", True)
            # Bind Escape key to exit fullscreen
            self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Get screen dimensions and update base class
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # Create fonts with better styling
        try:
            self.title_font = font.Font(family=font_family, size=title_font_size, weight="bold")
            self.body_font = font.Font(family=font_family, size=body_font_size, weight="normal")
            self.small_font = font.Font(family=font_family, size=small_font_size, weight="normal")
            self.large_font = font.Font(family=font_family, size=body_font_size + 16, weight="bold")
        except:
            # Fallback to system default
            self.title_font = font.Font(size=title_font_size, weight="bold")
            self.body_font = font.Font(size=body_font_size)
            self.small_font = font.Font(size=small_font_size)
            self.large_font = font.Font(size=body_font_size + 16, weight="bold")
        
        # Create main container with gradient-like effect
        self.container = tk.Frame(self.root, bg=bg_color)
        self.container.pack(fill=tk.BOTH, expand=True, padx=60, pady=60)
        
        # Content frames (will be populated by update methods)
        self.content_frame = None
        self._current_content = None
    
    def clear(self) -> None:
        """Clear the display."""
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = tk.Frame(self.container, bg=self.bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        self._current_content = None
    
    def update_summary(self, data: Dict[str, Any]) -> None:
        """
        Update display with summary view.
        
        Args:
            data: Dictionary containing summary statistics
        """
        self.clear()
        
        # Title with gradient-like effect using multiple labels
        title_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        title_frame.pack(pady=(0, 50))
        
        title_label = tk.Label(
            title_frame,
            text="GitHub Statistics",
            font=self.title_font,
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            title_frame,
            text="Repository & Package Analytics",
            font=self.small_font,
            fg="#888888",
            bg=self.bg_color
        )
        subtitle_label.pack(pady=(10, 0))
        
        # Main stats grid with better spacing
        stats_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        stats_frame.pack(expand=True)
        
        # Create stat cards in a grid layout
        cards = []
        
        # Row 1: Stars and Forks
        row1 = tk.Frame(stats_frame, bg=self.bg_color)
        row1.pack(pady=25)
        
        stars_card = self._create_modern_stat_card(
            row1, "Total Stars", data.get("total_stars_formatted", "0"), "★", "#ffd700"
        )
        stars_card.pack(side=tk.LEFT, padx=25)
        
        forks_card = self._create_modern_stat_card(
            row1, "Total Forks", data.get("total_forks_formatted", "0"), "🍴", "#4a9eff"
        )
        forks_card.pack(side=tk.LEFT, padx=25)
        
        # Row 2: Issues and Active Repos
        row2 = tk.Frame(stats_frame, bg=self.bg_color)
        row2.pack(pady=25)
        
        issues_card = self._create_modern_stat_card(
            row2, "Open Issues", str(data.get("total_open_issues", 0)), "📋", "#ff6b6b"
        )
        issues_card.pack(side=tk.LEFT, padx=25)
        
        active = data.get("active_repos", 0)
        total = data.get("total_repos", 0)
        active_card = self._create_modern_stat_card(
            row2, "Active Repos", f"{active}/{total}", "⚡", "#51cf66"
        )
        active_card.pack(side=tk.LEFT, padx=25)
        
        # Row 3: Package downloads if available
        if "total_downloads" in data and data.get("total_downloads", 0) > 0:
            row3 = tk.Frame(stats_frame, bg=self.bg_color)
            row3.pack(pady=25)
            
            downloads_card = self._create_modern_stat_card(
                row3, "Package Downloads", data.get("total_downloads_formatted", "0"), "📦", "#a78bfa"
            )
            downloads_card.pack(side=tk.LEFT, padx=25)
        
        # Donations if available
        if "total_donations" in data and data.get("total_donations", 0) > 0:
            donations_row = tk.Frame(stats_frame, bg=self.bg_color)
            donations_row.pack(pady=25)
            
            donations_card = self._create_modern_stat_card(
                donations_row, "Total Donations", data.get("total_donations_formatted", "$0"), "💝", "#f472b6"
            )
            donations_card.pack(side=tk.LEFT, padx=25)
        
        # Most starred repo with better styling
        most_starred = data.get("most_starred")
        if most_starred:
            bottom_frame = tk.Frame(self.content_frame, bg=self.bg_color)
            bottom_frame.pack(pady=40)
            
            # Create a styled info box
            info_box = tk.Frame(bottom_frame, bg="#1a1f3a", relief=tk.FLAT, bd=0)
            info_box.pack(padx=20, pady=10)
            
            top_repo_text = f"⭐ Most Starred: {most_starred['name']} ({most_starred['stars']} stars)"
            top_label = tk.Label(
                info_box,
                text=top_repo_text,
                font=self.body_font,
                fg=self.text_color,
                bg="#1a1f3a"
            )
            top_label.pack(padx=30, pady=15)
        
        self._current_content = "summary"
    
    def update_repo(self, repo_data: Dict[str, Any]) -> None:
        """
        Update display with single repository view.
        
        Args:
            repo_data: Dictionary containing repository statistics
        """
        self.clear()
        
        # Repository name with better styling
        name_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        name_frame.pack(pady=(0, 30))
        
        repo_name = repo_data.get("name", "Unknown")
        name_label = tk.Label(
            name_frame,
            text=repo_name,
            font=self.title_font,
            fg=self.accent_color,
            bg=self.bg_color
        )
        name_label.pack()
        
        # Description if available
        description = repo_data.get("description", "")
        if description:
            desc_label = tk.Label(
                name_frame,
                text=description[:100] + "..." if len(description) > 100 else description,
                font=self.small_font,
                fg="#888888",
                bg=self.bg_color
            )
            desc_label.pack(pady=(10, 0))
        
        # Stats grid
        stats_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        stats_frame.pack(expand=True)
        
        # Row 1: Stars and Forks
        row1 = tk.Frame(stats_frame, bg=self.bg_color)
        row1.pack(pady=20)
        
        stars_card = self._create_modern_stat_card(
            row1, "Stars", repo_data.get("stars_formatted", "0"), "★", "#ffd700"
        )
        stars_card.pack(side=tk.LEFT, padx=20)
        
        forks_card = self._create_modern_stat_card(
            row1, "Forks", repo_data.get("forks_formatted", "0"), "🍴", "#4a9eff"
        )
        forks_card.pack(side=tk.LEFT, padx=20)
        
        # Row 2: Issues and Language
        row2 = tk.Frame(stats_frame, bg=self.bg_color)
        row2.pack(pady=20)
        
        issues_card = self._create_modern_stat_card(
            row2, "Issues", str(repo_data.get("open_issues", 0)), "📋", "#ff6b6b"
        )
        issues_card.pack(side=tk.LEFT, padx=20)
        
        lang = repo_data.get("language", "N/A")
        lang_card = self._create_modern_stat_card(
            row2, "Language", lang, "💻", "#51cf66"
        )
        lang_card.pack(side=tk.LEFT, padx=20)
        
        # Latest version if available
        if "latest_version" in repo_data and repo_data.get("latest_version"):
            row3 = tk.Frame(stats_frame, bg=self.bg_color)
            row3.pack(pady=20)
            
            version_card = self._create_modern_stat_card(
                row3, "Latest Version", repo_data.get("latest_version", "N/A"), "🏷️", "#a78bfa"
            )
            version_card.pack(side=tk.LEFT, padx=20)
            
            downloads = repo_data.get("release_downloads", 0)
            downloads_formatted = self._format_number(downloads)
            downloads_card = self._create_modern_stat_card(
                row3, "Release Downloads", downloads_formatted, "📦", "#f472b6"
            )
            downloads_card.pack(side=tk.LEFT, padx=20)
        
        # Last commit with styled box
        bottom_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        bottom_frame.pack(pady=40)
        
        commit_box = tk.Frame(bottom_frame, bg="#1a1f3a", relief=tk.FLAT, bd=0)
        commit_box.pack(padx=20, pady=10)
        
        last_commit = repo_data.get("last_commit_relative", "Never")
        commit_text = f"🕒 Last commit: {last_commit}"
        commit_label = tk.Label(
            commit_box,
            text=commit_text,
            font=self.body_font,
            fg=self.text_color,
            bg="#1a1f3a"
        )
        commit_label.pack(padx=30, pady=15)
        
        self._current_content = "repo"
    
    def _create_modern_stat_card(
        self,
        parent: tk.Widget,
        label: str,
        value: str,
        icon: str = "",
        icon_color: str = "#00d4ff"
    ) -> tk.Frame:
        """
        Create a modern stat card widget with enhanced styling.
        
        Args:
            parent: Parent widget
            label: Label text
            value: Value to display
            icon: Optional icon/emoji
            icon_color: Color for the icon/accents
            
        Returns:
            Frame containing the stat card
        """
        # Outer frame with subtle border
        outer_frame = tk.Frame(parent, bg="#1a1f3a")
        outer_frame.pack()
        
        # Main card with gradient-like background
        card = tk.Frame(
            outer_frame,
            bg="#1a1f3a",
            relief=tk.FLAT,
            bd=0,
            width=280,
            height=200
        )
        card.pack(padx=3, pady=3)
        card.pack_propagate(False)
        
        # Inner content frame with padding
        content = tk.Frame(card, bg="#1a1f3a")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icon and value with larger, bolder styling
        value_frame = tk.Frame(content, bg="#1a1f3a")
        value_frame.pack(pady=(10, 15))
        
        if icon:
            icon_label = tk.Label(
                value_frame,
                text=icon,
                font=self.large_font,
                fg=icon_color,
                bg="#1a1f3a"
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        value_label = tk.Label(
            value_frame,
            text=value,
            font=self.large_font,
            fg=self.accent_color,
            bg="#1a1f3a"
        )
        value_label.pack(side=tk.LEFT)
        
        # Label with subtle styling
        label_widget = tk.Label(
            content,
            text=label,
            font=self.small_font,
            fg="#aaaaaa",
            bg="#1a1f3a"
        )
        label_widget.pack()
        
        return outer_frame
    
    def _format_number(self, num: int) -> str:
        """Format large numbers with K/M suffixes."""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)
    
    def write_line(self, line: int, text: str) -> None:
        """Write text to a specific line (fallback for compatibility)."""
        if self.content_frame is None:
            self.clear()
        # For GUI, we use update() or update_summary/update_repo instead
        # This is a fallback for compatibility
        pass
    
    def update(self, lines: List[str]) -> None:
        """Update display with text lines (fallback for compatibility)."""
        self.clear()
        for i, line in enumerate(lines):
            label = tk.Label(
                self.content_frame,
                text=line,
                font=self.body_font,
                fg=self.text_color,
                bg=self.bg_color
            )
            label.pack(pady=10)
    
    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()
    
    def close(self) -> None:
        """Close the GUI."""
        if self.root:
            self.root.quit()
            self.root.destroy()
