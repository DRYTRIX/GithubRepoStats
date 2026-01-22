"""Full-screen GUI display driver using tkinter for HDMI screens."""

import tkinter as tk
from tkinter import font
from typing import List, Optional, Dict, Any, Tuple, Callable
from .base import DisplayDriver

# Import truncate_text and format_number - handle both relative and absolute imports
try:
    from utils import truncate_text, format_number
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import truncate_text, format_number

# Default theme (unified with main.py and config)
_DEFAULT_BG = "#0a0e27"
_DEFAULT_ACCENT = "#00d4ff"
_DEFAULT_FONT_FAMILY = "Segoe UI"
_FONT_FALLBACKS = ("Segoe UI", "Arial")


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(round(r)))),
        max(0, min(255, int(round(g)))),
        max(0, min(255, int(round(b)))),
    )


def _blend(c1: str, c2: str, t: float) -> str:
    """Blend two hex colors. t=0 -> c1, t=1 -> c2."""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = r1 + (r2 - r1) * t
    g = g1 + (g2 - g1) * t
    b = b1 + (b2 - b1) * t
    return _rgb_to_hex(r, g, b)


def _build_palette(
    bg_color: str,
    text_color: str,
    accent_color: str,
    card_border_color: Optional[str] = None,
    divider_color: Optional[str] = None,
) -> Dict[str, str]:
    """Build semantic color palette from base colors (dark theme)."""
    white = "#ffffff"
    # Slightly lighter than bg for cards
    card_bg = _blend(bg_color, white, 0.06)
    divider = _blend(bg_color, card_bg, 0.6) if divider_color is None else divider_color
    border = _blend(card_bg, white, 0.08) if card_border_color is None else card_border_color
    muted = _blend(text_color, bg_color, 0.5)
    return {
        "card_bg": card_bg,
        "card_border": border,
        "divider": divider,
        "muted": muted,
    }


def _resolve_font_family(font_family: str) -> str:
    """Use font_family if non-empty, else Segoe UI, else Arial, else TkDefaultFont."""
    if font_family and str(font_family).strip():
        return str(font_family).strip()
    for f in _FONT_FALLBACKS:
        if f:
            return f
    return "TkDefaultFont"


class GUIDisplay(DisplayDriver):
    """Full-screen GUI display for HDMI screens using tkinter."""
    
    def __init__(
        self,
        fullscreen: bool = True,
        bg_color: str = _DEFAULT_BG,
        text_color: str = "#ffffff",
        accent_color: str = _DEFAULT_ACCENT,
        font_family: str = _DEFAULT_FONT_FAMILY,
        title_font_size: int = 64,
        body_font_size: int = 32,
        small_font_size: int = 20,
        card_border_color: Optional[str] = None,
        divider_color: Optional[str] = None,
        show_rotation_indicator: bool = True,
        transition_type: str = "fade",
    ):
        """
        Initialize GUI display.
        
        Args:
            fullscreen: Whether to run in fullscreen mode
            bg_color: Background color (hex)
            text_color: Text color (hex)
            accent_color: Accent color for highlights (hex)
            font_family: Font family name (fallbacks: Segoe UI, Arial)
            title_font_size: Font size for titles
            body_font_size: Font size for body text
            small_font_size: Font size for small text / eyebrow labels
            card_border_color: Optional override for card border (hex)
            divider_color: Optional override for divider (hex)
            show_rotation_indicator: Whether to show rotation dots/bar
            transition_type: "none" or "fade" when rotating views
        """
        # Initialize base class with screen dimensions (will be updated)
        super().__init__(width=1920, height=1080)  # Default, will be updated
        
        self.root = tk.Tk()
        self.fullscreen = fullscreen
        self.bg_color = bg_color
        self.text_color = text_color
        self.accent_color = accent_color
        self.show_rotation_indicator = show_rotation_indicator
        self.transition_type = transition_type if transition_type in ("none", "fade") else "fade"
        
        self.palette = _build_palette(
            bg_color, text_color, accent_color,
            card_border_color=card_border_color,
            divider_color=divider_color,
        )
        
        # Configure window
        self.root.configure(bg=bg_color)
        self.root.title("GitHub Repository Statistics")
        
        if fullscreen:
            self.root.attributes("-fullscreen", True)
            self.root.bind("<Escape>", lambda e: self.root.quit())
        
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        resolved_family = _resolve_font_family(font_family)
        try:
            self.title_font = font.Font(family=resolved_family, size=title_font_size, weight="bold")
            self.body_font = font.Font(family=resolved_family, size=body_font_size, weight="normal")
            self.small_font = font.Font(family=resolved_family, size=small_font_size, weight="normal")
            self.large_font = font.Font(family=resolved_family, size=body_font_size + 16, weight="bold")
            self.medium_font = font.Font(family=resolved_family, size=body_font_size - 4, weight="normal")
            self.eyebrow_font = font.Font(family=resolved_family, size=small_font_size, weight="normal")
        except Exception:
            self.title_font = font.Font(size=title_font_size, weight="bold")
            self.body_font = font.Font(size=body_font_size)
            self.small_font = font.Font(size=small_font_size)
            self.large_font = font.Font(size=body_font_size + 16, weight="bold")
            self.medium_font = font.Font(size=body_font_size - 4)
            self.eyebrow_font = font.Font(size=small_font_size)
        
        self.container = tk.Frame(self.root, bg=bg_color)
        self.container.pack(fill=tk.BOTH, expand=True, padx=80, pady=80)
        
        self._rotation_indicator_frame = tk.Frame(self.container, bg=bg_color)
        self._rotation_indicator_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        self.content_frame = None
        self._current_content = None
        self._transitioning = False
        self._alpha_supported = self._check_alpha_support()
    
    def _check_alpha_support(self) -> bool:
        """Check if root.attributes('-alpha') is supported (e.g. not on some Linux)."""
        try:
            self.root.attributes("-alpha", 1.0)
            return True
        except Exception:
            return False
    
    def _fade_out(self, callback: Callable[[], None]) -> None:
        """Animate alpha 1 -> 0, invoke callback, then fade in."""
        if not self._alpha_supported or self._transitioning or self.transition_type != "fade":
            callback()
            return
        self._transitioning = True
        steps, step_ms = 8, 25
        
        def step(n: int) -> None:
            if n > steps:
                try:
                    self.root.attributes("-alpha", 0.0)
                except Exception:
                    pass
                callback()
                self._fade_in()
                return
            alpha = 1.0 - (n / steps)
            try:
                self.root.attributes("-alpha", max(0.0, alpha))
            except Exception:
                pass
            self.root.after(step_ms, lambda: step(n + 1))
        
        step(0)
    
    def _fade_in(self) -> None:
        """Animate alpha 0 -> 1."""
        if not self._alpha_supported:
            self._transitioning = False
            return
        steps, step_ms = 8, 25
        
        def step(n: int) -> None:
            if n > steps:
                try:
                    self.root.attributes("-alpha", 1.0)
                except Exception:
                    pass
                self._transitioning = False
                return
            alpha = n / steps
            try:
                self.root.attributes("-alpha", min(1.0, alpha))
            except Exception:
                pass
            self.root.after(step_ms, lambda: step(n + 1))
        
        step(0)
    
    def clear(self) -> None:
        """Clear the display."""
        if self.content_frame:
            self.content_frame.destroy()
        self.content_frame = tk.Frame(self.container, bg=self.bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        self._current_content = None
    
    def update_rotation_index(self, index: int, total: int) -> None:
        """
        Update the rotation indicator (dots) at bottom. Shows which view is active.
        Call with total <= 1 to hide the indicator.
        """
        for w in list(self._rotation_indicator_frame.winfo_children()):
            w.destroy()
        if not self.show_rotation_indicator or total <= 1:
            return
        dot_size = 10
        gap = 8
        for i in range(total):
            is_active = i == index
            color = self.accent_color if is_active else self.palette["muted"]
            dot = tk.Frame(
                self._rotation_indicator_frame,
                bg=color,
                width=dot_size,
                height=dot_size,
                relief=tk.FLAT
            )
            dot.pack(side=tk.LEFT, padx=gap // 2)
            dot.pack_propagate(False)
    
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
                fg=self.palette["muted"],
                bg=self.bg_color
            )
            subtitle_label.pack(pady=(8, 0))
        
        return header_frame
    
    def _create_divider(self, parent: tk.Widget) -> tk.Frame:
        """Create a visual divider line using palette divider color."""
        divider = tk.Frame(parent, bg=self.palette["divider"], height=1)
        divider.pack(fill=tk.X, pady=30)
        return divider
    
    def update_summary(self, data: Dict[str, Any]) -> None:
        """
        Update display with summary view.
        
        Args:
            data: Dictionary containing summary statistics
        """
        def do() -> None:
            self.clear()
            self._build_summary(data)
        
        if self.transition_type == "fade" and self._alpha_supported and not self._transitioning:
            self._fade_out(do)
        else:
            do()
    
    def _calculate_progress(self, value: int, max_value: int) -> float:
        """Calculate progress percentage for visual indicator."""
        if max_value == 0:
            return 0
        return min(100, (value / max_value) * 100)
    
    def _build_summary(self, data: Dict[str, Any]) -> None:
        """Build summary view content (called after clear)."""
        # Enhanced header with better styling
        header_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        header_frame.pack(pady=(0, 50))
        
        title_label = tk.Label(
            header_frame,
            text="GitHub Statistics",
            font=font.Font(family=self.title_font.cget("family"), size=int(self.title_font.cget("size")), weight="bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Comprehensive Overview of All Repositories",
            font=self.medium_font,
            fg=self.palette["muted"],
            bg=self.bg_color
        )
        subtitle_label.pack(pady=(12, 0))
        
        stats_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        stats_frame.pack(expand=True, fill=tk.BOTH)
        
        cards: List[tk.Frame] = []
        
        # Calculate max values for progress indicators
        total_stars = data.get("total_stars", 0)
        total_forks = data.get("total_forks", 0)
        total_issues = data.get("total_open_issues", 0)
        total_repos = data.get("total_repos", 1)
        active_repos = data.get("active_repos", 0)
        
        # Stars card with progress indicator
        max_stars = max(total_stars, 1000)  # Use a reasonable max or actual max
        stars_progress = self._calculate_progress(total_stars, max_stars * 2)  # Scale for visual appeal
        stars_card = self._create_enhanced_stat_card(
            stats_frame, "Total Stars", data.get("total_stars_formatted", "0"),
            "★", "#ffd700", "Across all repositories", 
            progress_value=stars_progress
        )
        cards.append(stars_card)
        
        # Forks card
        max_forks = max(total_forks, 500)
        forks_progress = self._calculate_progress(total_forks, max_forks * 2)
        forks_card = self._create_enhanced_stat_card(
            stats_frame, "Total Forks", data.get("total_forks_formatted", "0"),
            "🍴", "#4a9eff", "Community contributions",
            progress_value=forks_progress
        )
        cards.append(forks_card)
        
        # Issues card
        max_issues = max(total_issues, 100)
        issues_progress = self._calculate_progress(total_issues, max_issues * 2)
        issues_card = self._create_enhanced_stat_card(
            stats_frame, "Open Issues", str(total_issues),
            "📋", "#ff6b6b", "Awaiting resolution",
            progress_value=issues_progress
        )
        cards.append(issues_card)
        
        # Active repos with percentage
        active = active_repos
        total = total_repos
        active_percentage = (active / total * 100) if total > 0 else 0
        active_card = self._create_enhanced_stat_card(
            stats_frame, "Active Repositories", f"{active}/{total}",
            "⚡", "#51cf66", f"{active_percentage:.0f}% active in last 7 days",
            progress_value=active_percentage
        )
        cards.append(active_card)
        
        # Downloads card if available
        if "total_downloads" in data and data.get("total_downloads", 0) > 0:
            downloads = data.get("total_downloads", 0)
            max_downloads = max(downloads, 10000)
            downloads_progress = self._calculate_progress(downloads, max_downloads * 2)
            downloads_card = self._create_enhanced_stat_card(
                stats_frame, "Package Downloads", data.get("total_downloads_formatted", "0"),
                "📦", "#a78bfa", "Container & package pulls",
                progress_value=downloads_progress
            )
            cards.append(downloads_card)
        
        # Donations card if available
        if "total_donations" in data and data.get("total_donations", 0) > 0:
            donations_card = self._create_enhanced_stat_card(
                stats_frame, "Donations", data.get("total_donations_formatted", "$0"),
                "💝", "#f472b6", "Community support"
            )
            cards.append(donations_card)
        
        # Improved grid layout with better spacing
        padx_card = 30
        pady_card = 30
        for i, card in enumerate(cards):
            row, col = i // 2, i % 2
            card.grid(row=row, column=col, padx=padx_card, pady=pady_card, sticky="nsew")
        
        stats_frame.columnconfigure(0, weight=1, uniform="equal")
        stats_frame.columnconfigure(1, weight=1, uniform="equal")
        
        # Enhanced most starred repository highlight
        most_starred = data.get("most_starred")
        if most_starred:
            self._create_divider(self.content_frame)
            
            highlight_frame = tk.Frame(self.content_frame, bg=self.bg_color)
            highlight_frame.pack(pady=(40, 20), fill=tk.X, padx=40)
            
            card_bg = self.palette["card_bg"]
            border_color = self.palette["card_border"]
            
            # Premium highlight box with border
            outer_box = tk.Frame(highlight_frame, bg=border_color)
            outer_box.pack()
            
            info_box = tk.Frame(outer_box, bg=card_bg, relief=tk.FLAT, bd=0)
            info_box.pack(padx=2, pady=2)
            
            # Badge-style header
            badge_frame = tk.Frame(info_box, bg=card_bg)
            badge_frame.pack(pady=(24, 16))
            
            badge_label = tk.Label(
                badge_frame,
                text="⭐ MOST POPULAR",
                font=font.Font(family=self.eyebrow_font.cget("family"), size=int(self.eyebrow_font.cget("size")), weight="bold"),
                fg="#ffd700",
                bg=card_bg
            )
            badge_label.pack()
            
            repo_name = truncate_text(most_starred['name'], 50)
            top_label = tk.Label(
                info_box,
                text=repo_name,
                font=font.Font(family=self.large_font.cget("family"), size=int(self.large_font.cget("size")) + 4, weight="bold"),
                fg=self.accent_color,
                bg=card_bg
            )
            top_label.pack(pady=(0, 12))
            
            stars_text = f"★ {format_number(most_starred['stars'])} stars"
            stars_label = tk.Label(
                info_box,
                text=stars_text,
                font=font.Font(family=self.body_font.cget("family"), size=int(self.body_font.cget("size")) + 4, weight="normal"),
                fg="#ffd700",
                bg=card_bg
            )
            stars_label.pack(pady=(0, 24))
        
        self._current_content = "summary"
    
    def update_repo(self, repo_data: Dict[str, Any]) -> None:
        """
        Update display with single repository view.
        
        Args:
            repo_data: Dictionary containing repository statistics
        """
        def do() -> None:
            self.clear()
            self._build_repo(repo_data)
        
        if self.transition_type == "fade" and self._alpha_supported and not self._transitioning:
            self._fade_out(do)
        else:
            do()
    
    def _build_repo(self, repo_data: Dict[str, Any]) -> None:
        """Build repository view content (called after clear)."""
        repo_name = repo_data.get("name", "Unknown")
        full_name = repo_data.get("full_name", repo_name)
        
        # Enhanced header
        header_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        header_frame.pack(pady=(0, 40))
        
        title_label = tk.Label(
            header_frame,
            text=repo_name,
            font=font.Font(family=self.title_font.cget("family"), size=int(self.title_font.cget("size")), weight="bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack()
        
        if full_name != repo_name:
            subtitle_label = tk.Label(
                header_frame,
                text=full_name,
                font=self.medium_font,
                fg=self.palette["muted"],
                bg=self.bg_color
            )
            subtitle_label.pack(pady=(12, 0))
        
        # Description with better styling
        description = repo_data.get("description", "")
        if description:
            desc_frame = tk.Frame(self.content_frame, bg=self.bg_color)
            desc_frame.pack(pady=(0, 40), padx=60, fill=tk.X)
            
            max_desc_length = 120
            display_desc = truncate_text(description, max_desc_length)
            
            desc_label = tk.Label(
                desc_frame,
                text=display_desc,
                font=self.medium_font,
                fg=self.palette["muted"],
                bg=self.bg_color,
                wraplength=1200,
                justify=tk.CENTER
            )
            desc_label.pack()
        
        stats_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        stats_frame.pack(expand=True, fill=tk.BOTH)
        
        repo_cards: List[tk.Frame] = []
        
        # Get values for progress calculations
        stars = repo_data.get("stars", 0)
        forks = repo_data.get("forks", 0)
        issues = repo_data.get("open_issues", 0)
        
        # Stars card with progress
        max_stars = max(stars, 100)
        stars_progress = self._calculate_progress(stars, max_stars * 2)
        stars_card = self._create_enhanced_stat_card(
            stats_frame, "Stars", repo_data.get("stars_formatted", "0"),
            "★", "#ffd700", "Community favorites",
            progress_value=stars_progress
        )
        repo_cards.append(stars_card)
        
        # Forks card
        max_forks = max(forks, 50)
        forks_progress = self._calculate_progress(forks, max_forks * 2)
        forks_card = self._create_enhanced_stat_card(
            stats_frame, "Forks", repo_data.get("forks_formatted", "0"),
            "🍴", "#4a9eff", "Repository copies",
            progress_value=forks_progress
        )
        repo_cards.append(forks_card)
        
        # Issues card
        max_issues = max(issues, 10)
        issues_progress = self._calculate_progress(issues, max_issues * 2)
        issues_card = self._create_enhanced_stat_card(
            stats_frame, "Open Issues", str(issues),
            "📋", "#ff6b6b", "Awaiting attention",
            progress_value=issues_progress
        )
        repo_cards.append(issues_card)
        
        # Language card with badge style
        lang = repo_data.get("language", "N/A")
        lang_display = truncate_text(lang, 15)
        lang_card = self._create_enhanced_stat_card(
            stats_frame, "Primary Language", lang_display,
            "💻", "#51cf66", "Technology stack"
        )
        repo_cards.append(lang_card)
        
        # Version card if available
        if "latest_version" in repo_data and repo_data.get("latest_version"):
            version = repo_data.get("latest_version", "N/A")
            version_display = truncate_text(version, 18)
            version_card = self._create_enhanced_stat_card(
                stats_frame, "Latest Version", version_display,
                "🏷️", "#a78bfa", "Current release"
            )
            repo_cards.append(version_card)
            
            # Downloads card
            downloads = repo_data.get("release_downloads", 0)
            downloads_formatted = format_number(downloads)
            max_downloads = max(downloads, 1000)
            downloads_progress = self._calculate_progress(downloads, max_downloads * 2) if downloads > 0 else None
            downloads_card = self._create_enhanced_stat_card(
                stats_frame, "Release Downloads", downloads_formatted,
                "📦", "#f472b6", "Asset downloads",
                progress_value=downloads_progress
            )
            repo_cards.append(downloads_card)
        
        # Improved grid layout
        padx_card = 30
        pady_card = 30
        for i, card in enumerate(repo_cards):
            row, col = i // 2, i % 2
            card.grid(row=row, column=col, padx=padx_card, pady=pady_card, sticky="nsew")
        
        stats_frame.columnconfigure(0, weight=1, uniform="equal")
        stats_frame.columnconfigure(1, weight=1, uniform="equal")
        
        # Enhanced info section
        info_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        info_frame.pack(pady=(50, 20), fill=tk.X, padx=60)
        
        self._create_divider(info_frame)
        
        card_bg = self.palette["card_bg"]
        border_color = self.palette["card_border"]
        
        # Premium info box with border
        outer_info = tk.Frame(info_frame, bg=border_color)
        outer_info.pack(pady=20)
        
        info_box = tk.Frame(outer_info, bg=card_bg, relief=tk.FLAT, bd=0)
        info_box.pack(padx=2, pady=2)
        
        # Last commit with better styling
        last_commit = repo_data.get("last_commit_relative", "Never")
        commit_frame = tk.Frame(info_box, bg=card_bg)
        commit_frame.pack(pady=16, padx=30, fill=tk.X)
        
        commit_icon = tk.Label(
            commit_frame,
            text="🕒",
            font=font.Font(family=self.body_font.cget("family"), size=int(self.body_font.cget("size")) + 4),
            fg=self.accent_color,
            bg=card_bg
        )
        commit_icon.pack(side=tk.LEFT, padx=(0, 16))
        
        commit_text_frame = tk.Frame(commit_frame, bg=card_bg)
        commit_text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        commit_label = tk.Label(
            commit_text_frame,
            text="LAST COMMIT",
            font=font.Font(family=self.eyebrow_font.cget("family"), size=int(self.eyebrow_font.cget("size")), weight="bold"),
            fg=self.palette["muted"],
            bg=card_bg,
            anchor=tk.W
        )
        commit_label.pack(anchor=tk.W)
        
        commit_value = tk.Label(
            commit_text_frame,
            text=last_commit,
            font=font.Font(family=self.body_font.cget("family"), size=int(self.body_font.cget("size")) + 2, weight="normal"),
            fg=self.text_color,
            bg=card_bg,
            anchor=tk.W
        )
        commit_value.pack(anchor=tk.W, pady=(4, 0))
        
        # Contributors with better styling
        contributors = repo_data.get("contributors_count", 0)
        if contributors > 0:
            contrib_frame = tk.Frame(info_box, bg=card_bg)
            contrib_frame.pack(pady=(0, 16), padx=30, fill=tk.X)
            
            contrib_icon = tk.Label(
                contrib_frame,
                text="👥",
                font=font.Font(family=self.body_font.cget("family"), size=int(self.body_font.cget("size")) + 4),
                fg=self.accent_color,
                bg=card_bg
            )
            contrib_icon.pack(side=tk.LEFT, padx=(0, 16))
            
            contrib_text_frame = tk.Frame(contrib_frame, bg=card_bg)
            contrib_text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            contrib_label = tk.Label(
                contrib_text_frame,
                text="CONTRIBUTORS",
                font=font.Font(family=self.eyebrow_font.cget("family"), size=int(self.eyebrow_font.cget("size")), weight="bold"),
                fg=self.palette["muted"],
                bg=card_bg,
                anchor=tk.W
            )
            contrib_label.pack(anchor=tk.W)
            
            contrib_value = tk.Label(
                contrib_text_frame,
                text=str(contributors),
                font=font.Font(family=self.body_font.cget("family"), size=int(self.body_font.cget("size")) + 2, weight="normal"),
                fg=self.text_color,
                bg=card_bg,
                anchor=tk.W
            )
            contrib_value.pack(anchor=tk.W, pady=(4, 0))
        
        self._current_content = "repo"
    
    def show_error(self, title: str, message: str) -> None:
        """
        Show a styled error view (title + message) using palette and section header.
        Used for fetch failures, etc.
        """
        self.update_rotation_index(0, 0)
        self.clear()
        self._create_section_header(self.content_frame, f"⚠ {title}", "")
        card_bg = self.palette["card_bg"]
        info_box = tk.Frame(self.content_frame, bg=card_bg, relief=tk.FLAT, bd=0)
        info_box.pack(padx=40, pady=30)
        msg_label = tk.Label(
            info_box,
            text=truncate_text(message, 80),
            font=self.body_font,
            fg=self.palette["muted"],
            bg=card_bg,
            wraplength=800,
            justify=tk.LEFT
        )
        msg_label.pack(pady=20, padx=20)
        self._current_content = "error"
    
    def show_empty(self, message: str) -> None:
        """
        Show a styled empty-state view (message only) using palette and section header.
        Used for no repos configured, no data available, etc.
        """
        self.update_rotation_index(0, 0)
        self.clear()
        self._create_section_header(self.content_frame, "GitHub Statistics", "")
        card_bg = self.palette["card_bg"]
        info_box = tk.Frame(self.content_frame, bg=card_bg, relief=tk.FLAT, bd=0)
        info_box.pack(padx=40, pady=30)
        msg_label = tk.Label(
            info_box,
            text=truncate_text(message, 80),
            font=self.body_font,
            fg=self.palette["muted"],
            bg=card_bg,
            wraplength=800,
            justify=tk.LEFT
        )
        msg_label.pack(pady=20, padx=20)
        self._current_content = "empty"
    
    def _truncate_for_display(self, text: str, max_chars: int) -> str:
        """Truncate text to fit display, handling emojis and special chars."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."
    
    def _create_progress_bar(self, parent: tk.Widget, percentage: float, color: str, height: int = 6) -> tk.Frame:
        """Create a visual progress bar indicator."""
        bar_frame = tk.Frame(parent, bg=self.palette["divider"], height=height, relief=tk.FLAT)
        bar_frame.pack(fill=tk.X, pady=(8, 0))
        bar_frame.pack_propagate(False)
        
        # Calculate width based on percentage (0-100)
        width_px = int((percentage / 100.0) * 100)  # Max 100px width for visual indicator
        
        if width_px > 0:
            progress = tk.Frame(bar_frame, bg=color, height=height, width=width_px)
            progress.pack(side=tk.LEFT, fill=tk.Y)
            progress.pack_propagate(False)
        
        return bar_frame
    
    def _create_enhanced_stat_card(
        self,
        parent: tk.Widget,
        label: str,
        value: str,
        icon: str = "",
        icon_color: str = "#00d4ff",
        description: str = "",
        progress_value: Optional[float] = None,
        trend: Optional[str] = None
    ) -> tk.Frame:
        """
        Create a premium stat card with modern design, gradients, and visual indicators.
        
        Args:
            parent: Parent widget
            label: Label text (eyebrow style)
            value: Value to display
            icon: Optional icon/emoji
            icon_color: Color for the icon/accents
            description: Optional description text below the label
            progress_value: Optional progress percentage (0-100) for visual indicator
            trend: Optional trend indicator ("up", "down", or None)
            
        Returns:
            Frame containing the stat card
        """
        max_label_chars = 25
        max_value_chars = 15
        max_desc_chars = 30
        
        truncated_label = self._truncate_for_display(label, max_label_chars)
        truncated_value = self._truncate_for_display(value, max_value_chars)
        truncated_desc = self._truncate_for_display(description, max_desc_chars) if description else ""
        
        card_bg = self.palette["card_bg"]
        border_color = self.palette["card_border"]
        
        # Create outer frame with subtle border
        outer_frame = tk.Frame(parent, bg=border_color)
        
        # Main card with increased size for better visual impact
        card = tk.Frame(
            outer_frame,
            bg=card_bg,
            relief=tk.FLAT,
            bd=0,
            width=420,
            height=280
        )
        card.pack(padx=2, pady=2)
        card.pack_propagate(False)
        
        # Content frame with better padding
        content = tk.Frame(card, bg=card_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
        
        # Icon and value frame with better alignment
        value_frame = tk.Frame(content, bg=card_bg)
        value_frame.pack(pady=(0, 12), anchor=tk.W)
        
        # Icon with larger size and better spacing
        if icon:
            icon_label = tk.Label(
                value_frame,
                text=icon,
                font=font.Font(family=self.title_font.cget("family"), size=int(int(self.title_font.cget("size")) * 0.5), weight="normal"),
                fg=icon_color,
                bg=card_bg
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 14))
        
        # Value with larger, bolder font
        value_label = tk.Label(
            value_frame,
            text=truncated_value,
            font=font.Font(family=self.title_font.cget("family"), size=int(self.body_font.cget("size")) + 8, weight="bold"),
            fg=self.accent_color,
            bg=card_bg
        )
        value_label.pack(side=tk.LEFT)
        
        # Trend indicator if provided
        if trend:
            trend_icon = "▲" if trend == "up" else "▼" if trend == "down" else ""
            trend_color = "#51cf66" if trend == "up" else "#ff6b6b" if trend == "down" else self.palette["muted"]
            if trend_icon:
                trend_label = tk.Label(
                    value_frame,
                    text=trend_icon,
                    font=self.small_font,
                    fg=trend_color,
                    bg=card_bg
                )
                trend_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # Label with better typography
        label_widget = tk.Label(
            content,
            text=truncated_label.upper(),
            font=font.Font(family=self.eyebrow_font.cget("family"), size=int(self.eyebrow_font.cget("size")), weight="bold"),
            fg=self.text_color,
            bg=card_bg,
            anchor=tk.W
        )
        label_widget.pack(anchor=tk.W, pady=(0, 4))
        
        # Description with muted color
        if truncated_desc:
            desc_widget = tk.Label(
                content,
                text=truncated_desc,
                font=self.small_font,
                fg=self.palette["muted"],
                bg=card_bg,
                anchor=tk.W
            )
            desc_widget.pack(anchor=tk.W, pady=(0, 8))
        
        # Progress bar indicator if provided
        if progress_value is not None:
            self._create_progress_bar(content, min(100, max(0, progress_value)), icon_color)
        
        return outer_frame
    
    
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
