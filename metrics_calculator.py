"""Calculate and aggregate metrics from repository data."""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from utils import parse_iso_datetime, format_relative_time, format_number


class MetricsCalculator:
    """Calculates derived metrics and aggregates repository statistics."""
    
    def __init__(self):
        """Initialize metrics calculator."""
        pass
    
    def calculate_repo_metrics(self, repo_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate derived metrics for a single repository.
        
        Args:
            repo_stats: Raw repository statistics
            
        Returns:
            Dictionary with calculated metrics
        """
        metrics = repo_stats.copy()
        
        # Parse dates
        if metrics.get("pushed_at"):
            try:
                metrics["last_commit_date"] = parse_iso_datetime(metrics["pushed_at"])
            except Exception:
                metrics["last_commit_date"] = None
        else:
            metrics["last_commit_date"] = None
        
        if metrics.get("updated_at"):
            try:
                metrics["last_updated_date"] = parse_iso_datetime(metrics["updated_at"])
            except Exception:
                metrics["last_updated_date"] = None
        else:
            metrics["last_updated_date"] = None
        
        # Calculate days since last commit
        if metrics["last_commit_date"]:
            days_since = (datetime.now(metrics["last_commit_date"].tzinfo) - metrics["last_commit_date"]).days
            metrics["days_since_last_commit"] = days_since
        else:
            metrics["days_since_last_commit"] = None
        
        # Check if repo is active (commits in last 7 days)
        metrics["is_active"] = (
            metrics["days_since_last_commit"] is not None and
            metrics["days_since_last_commit"] <= 7
        )
        
        # Format relative times
        metrics["last_commit_relative"] = format_relative_time(metrics["last_commit_date"])
        metrics["last_updated_relative"] = format_relative_time(metrics["last_updated_date"])
        
        # Format numbers
        metrics["stars_formatted"] = format_number(metrics.get("stars", 0))
        metrics["forks_formatted"] = format_number(metrics.get("forks", 0))
        
        return metrics
    
    def aggregate_metrics(
        self,
        all_repos: Dict[str, Dict[str, Any]],
        package_downloads: Optional[int] = None,
        donations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate metrics across all repositories.
        
        Args:
            all_repos: Dictionary mapping repo names to their stats
            package_downloads: Total package downloads (optional)
            donations: Donation statistics (optional)
            
        Returns:
            Dictionary with aggregated metrics
        """
        if not all_repos:
            result = {
                "total_repos": 0,
                "total_stars": 0,
                "total_forks": 0,
                "total_open_issues": 0,
                "active_repos": 0,
                "most_starred": None,
            }
        else:
            total_stars = 0
            total_forks = 0
            total_open_issues = 0
            total_release_downloads = 0
            active_repos = 0
            most_starred = None
            most_starred_count = 0
            
            for repo_name, repo_stats in all_repos.items():
                if "error" in repo_stats:
                    continue
                
                total_stars += repo_stats.get("stars", 0)
                total_forks += repo_stats.get("forks", 0)
                total_open_issues += repo_stats.get("open_issues", 0)
                total_release_downloads += repo_stats.get("release_downloads", 0)
                
                # Check if active
                if repo_stats.get("is_active", False):
                    active_repos += 1
                
                # Track most starred
                stars = repo_stats.get("stars", 0)
                if stars > most_starred_count:
                    most_starred_count = stars
                    most_starred = {
                        "name": repo_stats.get("name", repo_name),
                        "stars": stars,
                    }
            
            result = {
                "total_repos": len(all_repos),
                "total_stars": total_stars,
                "total_forks": total_forks,
                "total_open_issues": total_open_issues,
                "active_repos": active_repos,
                "most_starred": most_starred,
                "total_stars_formatted": format_number(total_stars),
                "total_forks_formatted": format_number(total_forks),
                "total_release_downloads": total_release_downloads,
            }
        
        # Add package downloads if provided
        if package_downloads is not None:
            result["total_downloads"] = package_downloads
            result["total_downloads_formatted"] = format_number(package_downloads)
        
        # Add donations if provided
        if donations:
            total_donations = donations.get("total", 0)
            currency = donations.get("currency", "USD")
            result["total_donations"] = total_donations
            result["total_donations_formatted"] = f"${total_donations:,.2f}" if currency == "USD" else f"{total_donations:,.2f} {currency}"
            result["donations_currency"] = currency
        
        return result
    
    def prepare_display_lines(
        self,
        repo_stats: Dict[str, Any],
        display_width: int = 20
    ) -> List[str]:
        """
        Prepare formatted lines for display from repository stats.
        
        Args:
            repo_stats: Repository statistics
            display_width: Width of display in characters
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        # Line 1: Repository name
        repo_name = repo_stats.get("name", "Unknown")
        lines.append(repo_name[:display_width])
        
        # Line 2: Stars and Forks
        stars = repo_stats.get("stars_formatted", "0")
        forks = repo_stats.get("forks_formatted", "0")
        lines.append(f"★{stars} | Fork:{forks}"[:display_width])
        
        # Line 3: Issues and Language
        issues = repo_stats.get("open_issues", 0)
        lang = repo_stats.get("language", "N/A")
        lines.append(f"Issues:{issues} | {lang}"[:display_width])
        
        # Line 4: Last commit
        last_commit = repo_stats.get("last_commit_relative", "Never")
        lines.append(f"Last: {last_commit}"[:display_width])
        
        return lines
    
    def prepare_summary_lines(
        self,
        aggregated: Dict[str, Any],
        display_width: int = 20
    ) -> List[str]:
        """
        Prepare formatted lines for summary view.
        
        Args:
            aggregated: Aggregated metrics
            display_width: Width of display in characters
            
        Returns:
            List of formatted lines
        """
        lines = []
        
        # Line 1: Title
        lines.append("GitHub Stats Summary"[:display_width])
        
        # Line 2: Total stars and forks
        stars = aggregated.get("total_stars_formatted", "0")
        forks = aggregated.get("total_forks_formatted", "0")
        lines.append(f"★{stars} | Forks:{forks}"[:display_width])
        
        # Line 3: Issues and active repos
        issues = aggregated.get("total_open_issues", 0)
        active = aggregated.get("active_repos", 0)
        total = aggregated.get("total_repos", 0)
        lines.append(f"Issues:{issues} | Active:{active}/{total}"[:display_width])
        
        # Line 4: Most starred repo
        most_starred = aggregated.get("most_starred")
        if most_starred:
            name = most_starred["name"][:display_width - 10]
            stars = most_starred["stars"]
            lines.append(f"Top: {name} ★{stars}"[:display_width])
        else:
            lines.append("No repos found"[:display_width])
        
        return lines
