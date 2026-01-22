"""Main application entry point for GitHub stats display."""

import sys
import time
import signal
import shutil
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from github_fetcher import GitHubFetcher
from cache_manager import CacheManager
from metrics_calculator import MetricsCalculator
from display import DisplayDriver, TerminalDisplay, CharacterLCDDisplay, GUIDisplay
from github_packages_fetcher import GitHubPackagesFetcher
from donations_fetcher import DonationsFetcher
from utils import truncate_text
import threading


def _resolve_paths() -> Tuple[Path, Path]:
    """Return (exe_dir, example_path) for config resolution."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        example_path = Path(sys._MEIPASS) / "config.yaml.example"
    else:
        exe_dir = Path(__file__).resolve().parent
        example_path = exe_dir / "config.yaml.example"
        if not example_path.exists():
            example_path = Path.cwd() / "config.yaml.example"
    return exe_dir, example_path


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
        
        # Rotation state
        self.processed_repos = {}
        self.aggregated_data = None
        self.current_repo_index = 0
        self.rotation_enabled = self.config.get("rotation_enabled", True)
        self.rotation_interval_seconds = self.config.get("rotation_interval_seconds", 10)
        self.show_summary_first = self.config.get("show_summary_first", True)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            exe_dir, example_path = _resolve_paths()
            if example_path.exists():
                shutil.copy(example_path, self.config_path)
                print(
                    f"Config not found; created {self.config_path} from example. "
                    "Please edit with your GitHub token and repositories."
                )
            else:
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
                bg_color=display_settings.get("bg_color", "#0a0e27"),
                text_color=display_settings.get("text_color", "#ffffff"),
                accent_color=display_settings.get("accent_color", "#00d4ff"),
                font_family=display_settings.get("font_family", "Segoe UI"),
                title_font_size=display_settings.get("title_font_size", 64),
                body_font_size=display_settings.get("body_font_size", 32),
                small_font_size=display_settings.get("small_font_size", 20),
                card_border_color=display_settings.get("card_border_color"),
                divider_color=display_settings.get("divider_color"),
                show_rotation_indicator=display_settings.get("show_rotation_indicator", True),
                transition_type=display_settings.get("transition_type", "fade"),
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
    
    def _fetch_data(self):
        """Fetch and process repository data."""
        repositories = self.config.get("repositories", [])
        
        if not repositories:
            return None, None
        
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
                # Only use latest release downloads, not cumulative
                repo_release_downloads = 0
                for repo_name, repo_stats in processed_repos.items():
                    repo_downloads = repo_stats.get("release_downloads", 0)
                    # Only add if downloads > 0 (latest release has downloads)
                    if repo_downloads > 0:
                        repo_release_downloads += repo_downloads
                        print(f"Repo {repo_name}: {repo_downloads} downloads from latest release")
                
                # Prefer release downloads if package downloads are 0
                # (GitHub Container Registry doesn't always expose download counts)
                if total_downloads == 0:
                    if repo_release_downloads > 0:
                        total_downloads = repo_release_downloads
                        print(f"Using release downloads: {total_downloads}")
                    else:
                        print("No package or release downloads found")
                elif total_downloads > 0 and repo_release_downloads > 0:
                    # If both are available, prefer package downloads but log both
                    print(f"Package downloads: {total_downloads}, Release downloads: {repo_release_downloads}")
                    # Don't combine - use package downloads as primary source
                
                if total_downloads > 0:
                    package_downloads = total_downloads
            
            # Fetch donations if configured
            donations = None
            if self.donations_fetcher:
                try:
                    donations = self.donations_fetcher.get_all_donations()
                except Exception as e:
                    print(f"Error fetching donations: {e}")
            
            # Store processed data for rotation
            self.processed_repos = processed_repos
            
            # Calculate aggregated metrics
            aggregated = self.calculator.aggregate_metrics(
                processed_repos,
                package_downloads=package_downloads,
                donations=donations
            )
            self.aggregated_data = aggregated
            
            return processed_repos, aggregated
        
        except Exception as e:
            print(f"Error fetching data: {e}", file=sys.stderr)
            return None, None
    
    def _display_repo(self, repo_data: Dict[str, Any]) -> None:
        """Display a single repository."""
        if self.is_gui:
            self.display.update_repo(repo_data)
        else:
            lines = self.calculator.prepare_display_lines(
                repo_data,
                self.display.width
            )
            self.display.update(lines)
    
    def _display_summary(self, aggregated: Dict[str, Any]) -> None:
        """Display aggregated summary."""
        if self.is_gui:
            self.display.update_summary(aggregated)
        else:
            lines = self.calculator.prepare_summary_lines(
                aggregated,
                self.display.width
            )
            self.display.update(lines)
    
    def _rotate_display(self):
        """Rotate through repositories and summary view."""
        if not self.processed_repos and not self.aggregated_data:
            if self.is_gui:
                self.display.show_empty("No repository data available.")
            else:
                self.display.update([
                    "No repository",
                    "data available.",
                    "",
                    ""
                ])
            return
        
        repos_list = list(self.processed_repos.values())
        
        # Determine what to show based on rotation
        if self.show_summary_first and self.current_repo_index == 0:
            if self.aggregated_data:
                self._display_summary(self.aggregated_data)
                print("Displaying summary view")
        elif repos_list:
            repo_index = (self.current_repo_index - (1 if self.show_summary_first else 0)) % len(repos_list)
            repo_data = repos_list[repo_index]
            repo_name = list(self.processed_repos.keys())[repo_index]
            self._display_repo(repo_data)
            print(f"Displaying repository: {repo_name}")
        
        total_items = len(repos_list) + (1 if self.show_summary_first else 0)
        if self.is_gui and total_items > 1 and hasattr(self.display, "update_rotation_index"):
            self.display.update_rotation_index(self.current_repo_index, total_items)
        self.current_repo_index = (self.current_repo_index + 1) % total_items
    
    def _fetch_and_display(self):
        """Fetch repository data and update display."""
        repositories = self.config.get("repositories", [])
        
        if not repositories:
            if self.is_gui:
                self.display.show_empty("No repositories configured. Check config.yaml")
            else:
                self.display.update([
                    "No repositories",
                    "configured.",
                    "Check config.yaml",
                    ""
                ])
            return
        
        # Fetch fresh data
        processed_repos, aggregated = self._fetch_data()
        
        if processed_repos is None:
            error_msg = "Failed to fetch repository data"
            if self.is_gui:
                self.display.show_error("Error", error_msg)
            else:
                self.display.update([
                    "Error occurred:",
                    error_msg,
                    "Check logs",
                    ""
                ])
            return
        
        # Update rotation display
        self._rotate_display()
    
    def run(self):
        """Run the main application loop."""
        refresh_interval = self.config.get("refresh_interval_minutes", 15)
        refresh_seconds = refresh_interval * 60
        
        print(f"GitHub Stats Display starting...")
        print(f"Refresh interval: {refresh_interval} minutes")
        print(f"Repositories: {len(self.config.get('repositories', []))}")
        if self.rotation_enabled:
            print(f"Rotation enabled: {self.rotation_interval_seconds} seconds per item")
        print("Press Ctrl+C to stop (or Escape in fullscreen mode)")
        
        # Initial data fetch
        self._fetch_and_display()
        
        if self.is_gui:
            # For GUI, run update loops in separate threads
            def data_refresh_loop():
                """Periodically refresh data from API."""
                while self.running:
                    time.sleep(refresh_seconds)
                    if self.running:
                        try:
                            self._fetch_data()
                        except Exception as e:
                            print(f"Error in data refresh loop: {e}")
            
            def rotation_loop():
                """Rotate through repositories and summary."""
                while self.running:
                    time.sleep(self.rotation_interval_seconds)
                    if self.running:
                        try:
                            self._rotate_display()
                        except Exception as e:
                            print(f"Error in rotation loop: {e}")
            
            # Start background threads
            if self.rotation_enabled:
                rotation_thread = threading.Thread(target=rotation_loop, daemon=True)
                rotation_thread.start()
            
            data_refresh_thread = threading.Thread(target=data_refresh_loop, daemon=True)
            data_refresh_thread.start()
            
            # Run GUI main loop
            try:
                self.display.run()
            except KeyboardInterrupt:
                pass
        else:
            # Main loop for non-GUI displays
            last_rotation_time = time.time()
            last_refresh_time = time.time()
            
            while self.running:
                try:
                    current_time = time.time()
                    
                    # Check if it's time to refresh data
                    if current_time - last_refresh_time >= refresh_seconds:
                        self._fetch_and_display()
                        last_refresh_time = current_time
                        last_rotation_time = current_time  # Reset rotation timer
                    
                    # Check if it's time to rotate
                    elif self.rotation_enabled and current_time - last_rotation_time >= self.rotation_interval_seconds:
                        self._rotate_display()
                        last_rotation_time = current_time
                    
                    # Sleep for a short time to avoid busy waiting
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    break
        
        # Cleanup
        self.display.close()
        print("Application stopped.")


def main():
    """Main entry point."""
    import argparse

    exe_dir, _ = _resolve_paths()
    default_config = str(exe_dir / "config.yaml") if getattr(sys, "frozen", False) else "config.yaml"

    parser = argparse.ArgumentParser(description="GitHub Repository Statistics Display")
    parser.add_argument(
        "--config",
        default=default_config,
        help="Path to configuration file (default: config.yaml, or next to exe when frozen)"
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
