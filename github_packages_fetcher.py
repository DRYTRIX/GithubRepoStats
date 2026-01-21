"""GitHub Packages API client for fetching container registry package statistics."""

import time
from typing import Dict, Any, Optional, List
import requests
from cache_manager import CacheManager


class GitHubPackagesFetcher:
    """Fetches package statistics from GitHub Container Registry."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, cache_manager: Optional[CacheManager] = None):
        """
        Initialize GitHub Packages API fetcher.
        
        Args:
            token: GitHub personal access token (needs read:packages permission)
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
            reset_time = self._rate_limit_reset
            current_time = time.time()
            if reset_time > current_time:
                wait_time = reset_time - current_time + 1
                time.sleep(wait_time)
    
    def _make_request(self, endpoint: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Make a GitHub API request with rate limit handling.
        
        Args:
            endpoint: API endpoint
            use_cache: Whether to use cache if available
            
        Returns:
            JSON response as dictionary
        """
        cache_key = f"gh_packages_{endpoint.replace('/', '_')}"
        
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
    
    def get_package_versions(
        self,
        owner: str,
        package_name: str,
        package_type: str = "container"
    ) -> List[Dict[str, Any]]:
        """
        Get all versions of a package.
        
        Args:
            owner: Package owner (user or org)
            package_name: Package name
            package_type: Package type (container, npm, maven, nuget, rubygems)
            
        Returns:
            List of package versions
        """
        try:
            endpoint = f"/users/{owner}/packages/{package_type}/{package_name}/versions"
            versions = self._make_request(endpoint, use_cache=True)
            return versions if isinstance(versions, list) else []
        except Exception:
            return []
    
    def get_package_downloads(
        self,
        owner: str,
        package_name: str,
        package_type: str = "container"
    ) -> Dict[str, Any]:
        """
        Get download statistics for a package.
        
        IMPORTANT: GitHub Container Registry (ghcr.io) does NOT expose download/pull
        counts via the API. This method will return 0 for container packages.
        
        For accurate download counts, use GitHub Releases API which tracks
        release asset downloads. The main.py will automatically fall back to
        release downloads if package downloads are 0.
        
        Args:
            owner: Package owner
            package_name: Package name
            package_type: Package type
            
        Returns:
            Dictionary with package download statistics
        """
        try:
            # First, try to get package info
            package_info_endpoint = f"/users/{owner}/packages/{package_type}/{package_name}"
            package_info = self._make_request(package_info_endpoint, use_cache=True)
            
            versions = self.get_package_versions(owner, package_name, package_type)
            
            total_downloads = 0
            latest_version = None
            latest_version_downloads = 0
            
            # Try to get download counts from versions
            for version in versions:
                version_id = version.get("id")
                if version_id:
                    try:
                        version_endpoint = f"/users/{owner}/packages/{package_type}/{package_name}/versions/{version_id}"
                        version_data = self._make_request(version_endpoint, use_cache=True)
                        
                        # Check various possible fields for download count
                        downloads = (
                            version_data.get("download_count") or
                            version_data.get("package_file", {}).get("download_count") or
                            0
                        )
                        
                        if downloads and downloads > 0:
                            total_downloads += downloads
                            
                            # Track latest version
                            version_created = version.get("created_at", "")
                            if not latest_version or (latest_version and version_created > latest_version.get("created_at", "")):
                                latest_version = version_data
                                latest_version_downloads = downloads
                    except Exception:
                        continue
            
            # If no downloads found from package versions, try to get from releases
            # This works if the package is also published as release assets
            if total_downloads == 0:
                try:
                    # Try to find associated repository and get release downloads
                    repo_name = package_info.get("repository", {}).get("full_name")
                    if repo_name:
                        # Use the GitHub fetcher to get release downloads
                        # This will be handled in main.py by combining repo release downloads
                        pass
                except Exception:
                    pass
            
            return {
                "total_downloads": total_downloads,
                "latest_version": latest_version.get("name", "") if latest_version else None,
                "latest_version_downloads": latest_version_downloads,
                "version_count": len(versions),
                "package_info": package_info
            }
        
        except Exception as e:
            return {
                "total_downloads": 0,
                "latest_version": None,
                "latest_version_downloads": 0,
                "version_count": 0,
                "error": str(e)
            }
    
    def get_multiple_packages(
        self,
        packages: List[Dict[str, str]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for multiple packages.
        
        Args:
            packages: List of dicts with 'owner', 'name', and optionally 'type'
            
        Returns:
            Dictionary mapping package identifiers to their stats
        """
        results = {}
        
        for package in packages:
            owner = package.get("owner")
            name = package.get("name")
            pkg_type = package.get("type", "container")
            
            if not owner or not name:
                continue
            
            key = f"{owner}/{name}"
            try:
                stats = self.get_package_downloads(owner, name, pkg_type)
                results[key] = stats
                
                # Small delay to avoid hitting rate limits
                time.sleep(0.1)
            
            except Exception as e:
                results[key] = {"error": str(e), "total_downloads": 0}
        
        return results
