"""GitHub API client for fetching repository statistics."""

import time
from typing import Dict, Any, Optional, List
import requests
from cache_manager import CacheManager


class GitHubFetcher:
    """Fetches repository statistics from GitHub API."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, cache_manager: Optional[CacheManager] = None):
        """
        Initialize GitHub API fetcher.
        
        Args:
            token: GitHub personal access token
            cache_manager: Optional cache manager instance
        """
        self.token = token
        self.cache = cache_manager
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Repo-Stats/1.0"
        })
        self._rate_limit_remaining = 5000
        self._rate_limit_reset = 0
    
    def _check_rate_limit(self) -> None:
        """Check and wait if rate limit is exceeded."""
        if self._rate_limit_remaining <= 10:
            # Wait until rate limit resets
            reset_time = self._rate_limit_reset
            current_time = time.time()
            if reset_time > current_time:
                wait_time = reset_time - current_time + 1
                time.sleep(wait_time)
    
    def _make_request(self, endpoint: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Make a GitHub API request with rate limit handling.
        
        Args:
            endpoint: API endpoint (e.g., '/repos/owner/name')
            use_cache: Whether to use cache if available
            
        Returns:
            JSON response as dictionary
        """
        cache_key = f"api_{endpoint.replace('/', '_')}"
        
        # Check cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        self._check_rate_limit()
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, timeout=10)
            
            # Update rate limit info
            if "X-RateLimit-Remaining" in response.headers:
                self._rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
            if "X-RateLimit-Reset" in response.headers:
                self._rate_limit_reset = int(response.headers["X-RateLimit-Reset"])
            
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            if use_cache and self.cache:
                self.cache.set(cache_key, data)
            
            return data
        
        except requests.exceptions.RequestException as e:
            # Try to return cached data if request fails
            if use_cache and self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    return cached_data
            
            raise
    
    def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get basic repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information dictionary
        """
        endpoint = f"/repos/{owner}/{repo}"
        return self._make_request(endpoint)
    
    def get_repo_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get comprehensive repository statistics.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with repository statistics
        """
        repo_info = self.get_repo_info(owner, repo)
        
        # Extract key stats
        stats = {
            "name": repo_info.get("name", ""),
            "full_name": repo_info.get("full_name", ""),
            "description": repo_info.get("description", ""),
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "watchers": repo_info.get("watchers_count", 0),
            "open_issues": repo_info.get("open_issues_count", 0),
            "language": repo_info.get("language", "N/A"),
            "created_at": repo_info.get("created_at", ""),
            "updated_at": repo_info.get("updated_at", ""),
            "pushed_at": repo_info.get("pushed_at", ""),
            "default_branch": repo_info.get("default_branch", "main"),
            "size": repo_info.get("size", 0),
            "archived": repo_info.get("archived", False),
            "private": repo_info.get("private", False),
        }
        
        # Get contributors count
        try:
            contributors = self._make_request(f"/repos/{owner}/{repo}/contributors", use_cache=True)
            stats["contributors_count"] = len(contributors) if isinstance(contributors, list) else 0
        except Exception:
            stats["contributors_count"] = 0
        
        # Get latest commit
        try:
            commits = self._make_request(
                f"/repos/{owner}/{repo}/commits?per_page=1",
                use_cache=True
            )
            if isinstance(commits, list) and len(commits) > 0:
                latest_commit = commits[0]
                stats["last_commit"] = {
                    "sha": latest_commit.get("sha", "")[:7],
                    "message": latest_commit.get("commit", {}).get("message", "").split("\n")[0],
                    "date": latest_commit.get("commit", {}).get("author", {}).get("date", ""),
                    "author": latest_commit.get("commit", {}).get("author", {}).get("name", ""),
                }
            else:
                stats["last_commit"] = None
        except Exception:
            stats["last_commit"] = None
        
        # Get latest release and downloads
        try:
            # Use shorter cache for releases to get fresh download counts
            release = self._make_request(
                f"/repos/{owner}/{repo}/releases/latest",
                use_cache=False  # Don't cache to get fresh download counts
            )
            if release:
                stats["latest_version"] = release.get("tag_name", "")
                stats["release_name"] = release.get("name", "")
                stats["release_date"] = release.get("published_at", "")
                
                # Sum download counts from all assets in the latest release only
                assets = release.get("assets", [])
                total_downloads = sum(asset.get("download_count", 0) for asset in assets)
                stats["release_downloads"] = total_downloads
                
                # Debug info
                if assets:
                    asset_info = ", ".join([f"{a.get('name', 'unknown')}: {a.get('download_count', 0)}" for a in assets])
                    print(f"Latest release '{stats['latest_version']}' assets: {asset_info}")
            else:
                stats["latest_version"] = None
                stats["release_downloads"] = 0
        except Exception as e:
            stats["latest_version"] = None
            stats["release_downloads"] = 0
            print(f"Error fetching release for {owner}/{repo}: {e}")
        
        return stats
    
    def get_multiple_repos(self, repositories: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for multiple repositories.
        
        Args:
            repositories: List of repositories in format 'owner/repo'
            
        Returns:
            Dictionary mapping repo names to their stats
        """
        results = {}
        
        for repo_path in repositories:
            try:
                parts = repo_path.split("/")
                if len(parts) != 2:
                    continue
                
                owner, repo = parts
                stats = self.get_repo_stats(owner, repo)
                results[repo_path] = stats
                
                # Small delay to avoid hitting rate limits
                time.sleep(0.1)
            
            except Exception as e:
                # Log error but continue with other repos
                results[repo_path] = {"error": str(e)}
        
        return results
