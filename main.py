"""Main application entry point for GitHub stats display."""

import sys
import time
import signal
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from github_fetcher import GitHubFetcher
from cache_manager import CacheManager
from metrics_calculator import MetricsCalculator
from display import DisplayDriver, TerminalDisplay, CharacterLCDDisplay, GUIDisplay
from github_packages_fetcher import GitHubPackagesFetcher
from donations_fetcher import DonationsFetcher
from utils import truncate_text
import threading


class GitHubStatsApp:
    """Main application class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.running = True
        
        # Initialize components
        self.cache_manager = CacheManager(
            cache_dir=self.config.get("cache_dir", ".cache"),
            enabled=self.config.get("cache_enabled", True),
            ttl_minutes=self.config.get("cache_duration_minutes", 10)
        )
        
        github_token = self.config.get("github_token")
        if not github_token:
            raise ValueError("github_token is required in config.yaml")
        
        self.fetcher = GitHubFetcher(github_token, self.cache_manager)
        self.calculator = MetricsCalculator()
        
        # Initialize GitHub Packages fetcher if packages are configured
        self.packages_fetcher = None
        if self.config.get("github_packages"):
            self.packages_fetcher = GitHubPackagesFetcher(github_token, self.cache_manager)
        
        # Initialize donations fetcher if configured
        self.donations_fetcher = None
        donations_config = self.config.get("donations", {})
        if donations_config.get("enabled", False):
            self.donations_fetcher = DonationsFetcher(
                paypal_client_id=donations_config.get("paypal", {}).get("client_id"),
                paypal_client_secret=donations_config.get("paypal", {}).get("client_secret"),
                buymeacoffee_username=donations_config.get("buymeacoffee", {}).get("username"),
                cache_manager=self.cache_manager
            )
        
        # Initialize display
        self.display = self._init_display()
        self.is_gui = isinstance(self.display, GUIDisplay)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                "Please create config.yaml (see config.yaml.example)"
            )
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # Set defaults
        defaults = {
            "refresh_interval_minutes": 15,
            "display_type": "terminal",
            "cache_enabled": True,
            "cache_duration_minutes": 10,
            "view_mode": "summary",
            "repositories": [],
        }
        
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
        
        return config
    
    def _init_display(self):
        """Initialize display driver based on config."""
        display_type = self.config.get("display_type", "terminal")
        display_settings = self.config.get("display_settings", {})
        
        if display_type == "gui" or display_type == "fullscreen":
            return GUIDisplay(
                fullscreen=display_settings.get("fullscreen", True),
                bg_color=display_settings.get("bg_color", "#1a1a1a"),
                text_color=display_settings.get("text_color", "#ffffff"),
                accent_color=display_settings.get("accent_color", "#4a9eff"),
                font_family=display_settings.get("font_family", "Arial"),
                title_font_size=display_settings.get("title_font_size", 48),
                body_font_size=display_settings.get("body_font_size", 24),
                small_font_size=display_settings.get("small_font_size", 18)
            )
        elif display_type == "character_lcd":
            width = display_settings.get("width", 20)
            height = display_settings.get("height", 4)
            return CharacterLCDDisplay(width, height, display_settings)
        elif display_type == "terminal":
            width = display_settings.get("width", 80)
            height = display_settings.get("height", 4)
            return TerminalDisplay(width, height)
        else:
            raise ValueError(f"Unknown display type: {display_type}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\nShutting down...")
        self.running = False
    
    def _fetch_and_display(self):
        """Fetch repository data and update display."""
        repositories = self.config.get("repositories", [])
        
        if not repositories:
            if self.is_gui:
                self.display.update(["No repositories configured. Check config.yaml"])
            else:
                self.display.update([
                    "No repositories",
                    "configured.",
                    "Check config.yaml",
                    ""
                ])
            return
        
        try:
            # Fetch repository statistics
            print("Fetching repository statistics...")
            all_repos = self.fetcher.get_multiple_repos(repositories)
            
            # Calculate metrics
            processed_repos = {}
            for repo_name, repo_stats in all_repos.items():
                if "error" not in repo_stats:
                    processed_repos[repo_name] = self.calculator.calculate_repo_metrics(repo_stats)
            
            # Fetch GitHub Container Registry package stats if configured
            package_downloads = None
            if self.packages_fetcher:
                github_packages = self.config.get("github_packages", [])
                total_downloads = 0
                
                # Get package download stats
                packages_list = []
                for pkg in github_packages:
                    if isinstance(pkg, dict):
                        packages_list.append(pkg)
                    elif isinstance(pkg, str):
                        # Simple format: "owner/package-name"
                        parts = pkg.split("/")
                        if len(parts) == 2:
                            packages_list.append({
                                "owner": parts[0],
                                "name": parts[1],
                                "type": "container"
                            })
                
                if packages_list:
                    try:
                        package_stats = self.packages_fetcher.get_multiple_packages(packages_list)
                        for pkg_key, stats in package_stats.items():
                            if "error" not in stats:
                                pkg_downloads = stats.get("total_downloads", 0)
                                if pkg_downloads > 0:
                                    total_downloads += pkg_downloads
                                    print(f"Package {pkg_key}: {pkg_downloads} downloads")
                    except Exception as e:
                        print(f"Error fetching GitHub package stats: {e}")
                
                # Also sum release downloads from GitHub repos (these are more reliable)
                repo_release_downloads = 0
                for repo_stats in processed_repos.values():
                    repo_downloads = repo_stats.get("release_downloads", 0)
                    if repo_downloads > 0:
                        repo_release_downloads += repo_downloads
                
                # Prefer release downloads if package downloads are 0
                # (GitHub Container Registry doesn't always expose download counts)
                if total_downloads == 0 and repo_release_downloads > 0:
                    total_downloads = repo_release_downloads
                    print(f"Using release downloads: {total_downloads}")
                elif total_downloads > 0:
                    # Combine both if available
                    total_downloads += repo_release_downloads
                
                if total_downloads > 0:
                    package_downloads = total_downloads
            
            # Fetch donations if configured
            donations = None
            if self.donations_fetcher:
                try:
                    donations = self.donations_fetcher.get_all_donations()
                except Exception as e:
                    print(f"Error fetching donations: {e}")
            
            # Determine view mode
            view_mode = self.config.get("view_mode", "summary")
            
            if view_mode == "summary":
                # Show aggregated summary
                aggregated = self.calculator.aggregate_metrics(
                    processed_repos,
                    package_downloads=package_downloads,
                    donations=donations
                )
                
                if self.is_gui:
                    self.display.update_summary(aggregated)
                else:
                    lines = self.calculator.prepare_summary_lines(
                        aggregated,
                        self.display.width
                    )
                    self.display.update(lines)
            
            elif view_mode == "per_repo":
                # Rotate through repositories
                if processed_repos:
                    # Show first repo (could be enhanced to rotate)
                    first_repo = next(iter(processed_repos.values()))
                    
                    if self.is_gui:
                        self.display.update_repo(first_repo)
                    else:
                        lines = self.calculator.prepare_display_lines(
                            first_repo,
                            self.display.width
                        )
                        self.display.update(lines)
                else:
                    if self.is_gui:
                        self.display.update(["No repository data available."])
                    else:
                        self.display.update([
                            "No repository",
                            "data available.",
                            "",
                            ""
                        ])
            
            print("Display updated successfully.")
        
        except Exception as e:
            error_msg = str(e)
            if self.is_gui:
                self.display.update([f"Error: {error_msg}"])
            else:
                error_msg = error_msg[:self.display.width] if hasattr(self.display, 'width') else error_msg
                self.display.update([
                    "Error occurred:",
                    truncate_text(error_msg, self.display.width if hasattr(self.display, 'width') else 80),
                    "Check logs",
                    ""
                ])
            print(f"Error: {e}", file=sys.stderr)
    
    def run(self):
        """Run the main application loop."""
        refresh_interval = self.config.get("refresh_interval_minutes", 15)
        refresh_seconds = refresh_interval * 60
        
        print(f"GitHub Stats Display starting...")
        print(f"Refresh interval: {refresh_interval} minutes")
        print(f"Repositories: {len(self.config.get('repositories', []))}")
        print("Press Ctrl+C to stop (or Escape in fullscreen mode)")
        
        # Initial display
        self._fetch_and_display()
        
        if self.is_gui:
            # For GUI, run update loop in a separate thread
            def update_loop():
                while self.running:
                    time.sleep(refresh_seconds)
                    if self.running:
                        try:
                            self._fetch_and_display()
                        except Exception as e:
                            print(f"Error in update loop: {e}")
            
            update_thread = threading.Thread(target=update_loop, daemon=True)
            update_thread.start()
            
            # Run GUI main loop
            try:
                self.display.run()
            except KeyboardInterrupt:
                pass
        else:
            # Main loop for non-GUI displays
            while self.running:
                try:
                    time.sleep(refresh_seconds)
                    if self.running:
                        self._fetch_and_display()
                except KeyboardInterrupt:
                    break
        
        # Cleanup
        self.display.close()
        print("Application stopped.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub Repository Statistics Display")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    args = parser.parse_args()
    
    try:
        app = GitHubStatsApp(args.config)
        app.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
