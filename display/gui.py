"""Full-screen GUI display driver using tkinter for HDMI screens."""

import tkinter as tk
from tkinter import font
from typing import List, Optional, Dict, Any
from .base import DisplayDriver

# Import truncate_text - handle both relative and absolute imports
try:
    from utils import truncate_text
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import truncate_text


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
            self.medium_font = font.Font(family=font_family, size=body_font_size - 4, weight="normal")
        except:
            # Fallback to system default
            self.title_font = font.Font(size=title_font_size, weight="bold")
            self.body_font = font.Font(size=body_font_size)
            self.small_font = font.Font(size=small_font_size)
            self.large_font = font.Font(size=body_font_size + 16, weight="bold")
            self.medium_font = font.Font(size=body_font_size - 4)
        
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
    
    def _create_section_header(self, parent: tk.Widget, title: str, subtitle: str = "") -> tk.Frame:
        """Create a section header with title and optional subtitle."""
        header_frame = tk.Frame(parent, bg=self.bg_color)
        header_frame.pack(pady=(0, 40))
        
        title_label = tk.Label(
            header_frame,
            text=title,
            font=self.title_font,
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack()
        
        if subtitle:
            subtitle_label = tk.Label(
                header_frame,
                text=subtitle,
                font=self.medium_font,
                fg="#888888",
                bg=self.bg_color
            )
            subtitle_label.pack(pady=(8, 0))
        
        return header_frame
    
    def _create_divider(self, parent: tk.Widget) -> tk.Frame:
        """Create a visual divider line."""
        divider = tk.Frame(parent, bg="#2a2f4a", height=2)
        divider.pack(fill=tk.X, pady=20)
        return divider
    
    def update_summary(self, data: Dict[str, Any]) -> None:
        """
        Update display with summary view.
        
        Args:
            data: Dictionary containing summary statistics
        """
        self.clear()
        
        # Header section
        self._create_section_header(
            self.content_frame,
            "📊 GitHub Statistics",
            "Overview of All Repositories"
        )
        
        # Main stats grid with better spacing
        stats_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        stats_frame.pack(expand=True)
        
        # Row 1: Stars and Forks
        row1 = tk.Frame(stats_frame, bg=self.bg_color)
        row1.pack(pady=20)
        
        stars_card = self._create_enhanced_stat_card(
            row1, "Total Stars", data.get("total_stars_formatted", "0"), 
            "★", "#ffd700", "All repositories"
        )
        stars_card.pack(side=tk.LEFT, padx=20)
        
        forks_card = self._create_enhanced_stat_card(
            row1, "Total Forks", data.get("total_forks_formatted", "0"),
            "🍴", "#4a9eff", "Contributions"
        )
        forks_card.pack(side=tk.LEFT, padx=20)
        
        # Row 2: Issues and Active Repos
        row2 = tk.Frame(stats_frame, bg=self.bg_color)
        row2.pack(pady=20)
        
        issues_card = self._create_enhanced_stat_card(
            row2, "Open Issues", str(data.get("total_open_issues", 0)),
            "📋", "#ff6b6b", "To resolve"
        )
        issues_card.pack(side=tk.LEFT, padx=20)
        
        active = data.get("active_repos", 0)
        total = data.get("total_repos", 0)
        active_card = self._create_enhanced_stat_card(
            row2, "Active Repos", f"{active}/{total}",
            "⚡", "#51cf66", "Last 7 days"
        )
        active_card.pack(side=tk.LEFT, padx=20)
        
        # Row 3: Package downloads if available
        if "total_downloads" in data and data.get("total_downloads", 0) > 0:
            row3 = tk.Frame(stats_frame, bg=self.bg_color)
            row3.pack(pady=20)
            
            downloads_card = self._create_enhanced_stat_card(
                row3, "Package Downloads", data.get("total_downloads_formatted", "0"),
                "📦", "#a78bfa", "Container pulls"
            )
            downloads_card.pack(side=tk.LEFT, padx=20)
        
        # Donations if available
        if "total_donations" in data and data.get("total_donations", 0) > 0:
            donations_row = tk.Frame(stats_frame, bg=self.bg_color)
            donations_row.pack(pady=20)
            
            donations_card = self._create_enhanced_stat_card(
                donations_row, "Donations", data.get("total_donations_formatted", "$0"),
                "💝", "#f472b6", "Support"
            )
            donations_card.pack(side=tk.LEFT, padx=20)
        
        # Divider before additional info
        if data.get("most_starred"):
            self._create_divider(stats_frame)
        
        # Most starred repo with better styling
        most_starred = data.get("most_starred")
        if most_starred:
            highlight_frame = tk.Frame(self.content_frame, bg=self.bg_color)
            highlight_frame.pack(pady=30)
            
            # Create a styled info box
            info_box = tk.Frame(highlight_frame, bg="#1a1f3a", relief=tk.FLAT, bd=0)
            info_box.pack(padx=20, pady=15)
            
            highlight_label = tk.Label(
                info_box,
                text="⭐ Most Popular Repository",
                font=self.medium_font,
                fg="#888888",
                bg="#1a1f3a"
            )
            highlight_label.pack(pady=(20, 5))
            
            # Truncate repo name if too long
            repo_name = truncate_text(most_starred['name'], 40)
            top_label = tk.Label(
                info_box,
                text=repo_name,
                font=self.large_font,
                fg=self.accent_color,
                bg="#1a1f3a"
            )
            top_label.pack(pady=5)
            
            stars_text = f"★ {most_starred['stars']} stars"
            stars_label = tk.Label(
                info_box,
                text=stars_text,
                font=self.body_font,
                fg="#ffd700",
                bg="#1a1f3a"
            )
            stars_label.pack(pady=(5, 20))
        
        self._current_content = "summary"
    
    def update_repo(self, repo_data: Dict[str, Any]) -> None:
        """
        Update display with single repository view.
        
        Args:
            repo_data: Dictionary containing repository statistics
        """
        self.clear()
        
        # Repository header
        repo_name = repo_data.get("name", "Unknown")
        full_name = repo_data.get("full_name", repo_name)
        
        header_frame = self._create_section_header(
            self.content_frame,
            f"📁 {repo_name}",
            full_name if full_name != repo_name else ""
        )
        
        # Description if available - properly truncated
        description = repo_data.get("description", "")
        if description:
            desc_frame = tk.Frame(self.content_frame, bg=self.bg_color)
            desc_frame.pack(pady=(0, 30), padx=40)
            
            # Truncate description to reasonable length
            max_desc_length = 100
            display_desc = truncate_text(description, max_desc_length)
            
            desc_label = tk.Label(
                desc_frame,
                text=display_desc,
                font=self.medium_font,
                fg="#aaaaaa",
                bg=self.bg_color
            )
            desc_label.pack()
        
        # Stats grid
        stats_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        stats_frame.pack(expand=True)
        
        # Row 1: Stars and Forks
        row1 = tk.Frame(stats_frame, bg=self.bg_color)
        row1.pack(pady=20)
        
        stars_card = self._create_enhanced_stat_card(
            row1, "Stars", repo_data.get("stars_formatted", "0"),
            "★", "#ffd700", "Favorites"
        )
        stars_card.pack(side=tk.LEFT, padx=15)
        
        forks_card = self._create_enhanced_stat_card(
            row1, "Forks", repo_data.get("forks_formatted", "0"),
            "🍴", "#4a9eff", "Copies"
        )
        forks_card.pack(side=tk.LEFT, padx=15)
        
        # Row 2: Issues and Language
        row2 = tk.Frame(stats_frame, bg=self.bg_color)
        row2.pack(pady=20)
        
        issues_card = self._create_enhanced_stat_card(
            row2, "Issues", str(repo_data.get("open_issues", 0)),
            "📋", "#ff6b6b", "Open"
        )
        issues_card.pack(side=tk.LEFT, padx=15)
        
        lang = repo_data.get("language", "N/A")
        # Truncate language name if too long
        lang_display = truncate_text(lang, 12)
        lang_card = self._create_enhanced_stat_card(
            row2, "Language", lang_display,
            "💻", "#51cf66", "Tech"
        )
        lang_card.pack(side=tk.LEFT, padx=15)
        
        # Row 3: Version and Downloads if available
        if "latest_version" in repo_data and repo_data.get("latest_version"):
            row3 = tk.Frame(stats_frame, bg=self.bg_color)
            row3.pack(pady=20)
            
            version = repo_data.get("latest_version", "N/A")
            version_display = truncate_text(version, 15)
            version_card = self._create_enhanced_stat_card(
                row3, "Version", version_display,
                "🏷️", "#a78bfa", "Release"
            )
            version_card.pack(side=tk.LEFT, padx=15)
            
            downloads = repo_data.get("release_downloads", 0)
            downloads_formatted = self._format_number(downloads)
            downloads_card = self._create_enhanced_stat_card(
                row3, "Downloads", downloads_formatted,
                "📦", "#f472b6", "Assets"
            )
            downloads_card.pack(side=tk.LEFT, padx=15)
        
        # Additional info section
        info_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        info_frame.pack(pady=40)
        
        # Divider
        self._create_divider(info_frame)
        
        # Info box with multiple details
        info_box = tk.Frame(info_frame, bg="#1a1f3a", relief=tk.FLAT, bd=0)
        info_box.pack(padx=20, pady=15)
        
        # Last commit
        last_commit = repo_data.get("last_commit_relative", "Never")
        commit_frame = tk.Frame(info_box, bg="#1a1f3a")
        commit_frame.pack(pady=10)
        
        commit_icon = tk.Label(
            commit_frame,
            text="🕒",
            font=self.body_font,
            fg="#888888",
            bg="#1a1f3a"
        )
        commit_icon.pack(side=tk.LEFT, padx=(20, 10))
        
        commit_text_frame = tk.Frame(commit_frame, bg="#1a1f3a")
        commit_text_frame.pack(side=tk.LEFT)
        
        commit_label = tk.Label(
            commit_text_frame,
            text="Last Commit",
            font=self.small_font,
            fg="#888888",
            bg="#1a1f3a"
        )
        commit_label.pack(anchor=tk.W)
        
        commit_value = tk.Label(
            commit_text_frame,
            text=last_commit,
            font=self.body_font,
            fg=self.text_color,
            bg="#1a1f3a"
        )
        commit_value.pack(anchor=tk.W)
        
        # Contributors if available
        contributors = repo_data.get("contributors_count", 0)
        if contributors > 0:
            contrib_frame = tk.Frame(info_box, bg="#1a1f3a")
            contrib_frame.pack(pady=10)
            
            contrib_icon = tk.Label(
                contrib_frame,
                text="👥",
                font=self.body_font,
                fg="#888888",
                bg="#1a1f3a"
            )
            contrib_icon.pack(side=tk.LEFT, padx=(20, 10))
            
            contrib_text_frame = tk.Frame(contrib_frame, bg="#1a1f3a")
            contrib_text_frame.pack(side=tk.LEFT)
            
            contrib_label = tk.Label(
                contrib_text_frame,
                text="Contributors",
                font=self.small_font,
                fg="#888888",
                bg="#1a1f3a"
            )
            contrib_label.pack(anchor=tk.W)
            
            contrib_value = tk.Label(
                contrib_text_frame,
                text=str(contributors),
                font=self.body_font,
                fg=self.text_color,
                bg="#1a1f3a"
            )
            contrib_value.pack(anchor=tk.W)
        
        self._current_content = "repo"
    
    def _truncate_for_display(self, text: str, max_chars: int) -> str:
        """Truncate text to fit display, handling emojis and special chars."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."
    
    def _create_enhanced_stat_card(
        self,
        parent: tk.Widget,
        label: str,
        value: str,
        icon: str = "",
        icon_color: str = "#00d4ff",
        description: str = ""
    ) -> tk.Frame:
        """
        Create an enhanced stat card with better clarity and text handling.
        
        Args:
            parent: Parent widget
            label: Label text
            value: Value to display
            icon: Optional icon/emoji
            icon_color: Color for the icon/accents
            description: Optional description text below the label
            
        Returns:
            Frame containing the stat card
        """
        # Truncate text to fit card width (accounting for padding)
        max_label_chars = 25
        max_value_chars = 15
        max_desc_chars = 30
        
        truncated_label = self._truncate_for_display(label, max_label_chars)
        truncated_value = self._truncate_for_display(value, max_value_chars)
        truncated_desc = self._truncate_for_display(description, max_desc_chars) if description else ""
        
        # Outer frame with subtle border
        outer_frame = tk.Frame(parent, bg="#1a1f3a")
        outer_frame.pack()
        
        # Main card - wider and with min height
        card = tk.Frame(
            outer_frame,
            bg="#1a1f3a",
            relief=tk.FLAT,
            bd=0,
            width=360,
            height=240
        )
        card.pack(padx=3, pady=3)
        card.pack_propagate(False)
        
        # Inner content frame with padding
        content = tk.Frame(card, bg="#1a1f3a")
        content.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)
        
        # Icon and value with larger, bolder styling
        value_frame = tk.Frame(content, bg="#1a1f3a")
        value_frame.pack(pady=(8, 10))
        
        if icon:
            icon_label = tk.Label(
                value_frame,
                text=icon,
                font=self.large_font,
                fg=icon_color,
                bg="#1a1f3a"
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Value label - truncated to fit
        value_label = tk.Label(
            value_frame,
            text=truncated_value,
            font=self.large_font,
            fg=self.accent_color,
            bg="#1a1f3a"
        )
        value_label.pack(side=tk.LEFT)
        
        # Label with better styling - use bold font variant, truncated
        bold_body_font = font.Font(font=self.body_font)
        bold_body_font.configure(weight="bold")
        
        label_widget = tk.Label(
            content,
            text=truncated_label,
            font=bold_body_font,
            fg=self.text_color,
            bg="#1a1f3a"
        )
        label_widget.pack(pady=(0, 6))
        
        # Description if provided - truncated
        if truncated_desc:
            desc_widget = tk.Label(
                content,
                text=truncated_desc,
                font=self.small_font,
                fg="#666666",
                bg="#1a1f3a"
            )
            desc_widget.pack()
        
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
