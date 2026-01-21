"""GitHub Packages API client for fetching container registry package statistics."""

import time
import re
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
    
    def _scrape_package_downloads(
        self,
        owner: str,
        package_name: str
    ) -> Dict[str, Any]:
        """
        Scrape download counts from GitHub Container Registry package page.
        
        Since GitHub doesn't expose download counts via API, we scrape the web page.
        Returns both total downloads and latest version downloads.
        
        Args:
            owner: Package owner
            package_name: Package name
            
        Returns:
            Dictionary with scraped download statistics
        """
        try:
            # GitHub package page URL
            url = f"https://github.com/{owner}/{package_name}/pkgs/container/{package_name}"
            
            # Use browser-like headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return {"total_downloads": 0, "latest_version_downloads": 0, "error": f"HTTP {response.status_code}"}
            
            html = response.text
            
            # First, try to find the latest version's download count
            # Look for the first version entry (which should be the latest)
            # Pattern: Look for download icon followed by number, near version tags like "latest", "4.12"
            latest_version_downloads = 0
            
            # Pattern 1: Look for download count near "latest" tag or first version entry
            # The structure is usually: version tags, then "Published X ago", then download count
            latest_patterns = [
                # Match download icon/button followed by number in the latest version section
                r'(?:latest|Published[^<]*Digest[^<]*)(?:[^<]*<[^>]*>)*[^<]*([\d,]+)\s*(?:Version downloads|downloads?)',
                # Match number right after download icon
                r'<[^>]*download[^>]*>[^<]*([\d,]+)',
                # Match in the first version row
                r'Published[^<]*ago[^<]*Digest[^<]*>([^<]*<[^>]*>)*[^<]*([\d,]+)\s*(?:Version downloads|downloads?)',
            ]
            
            for pattern in latest_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    # Take the first match (should be the latest version)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = match[-1]  # Take last element if tuple
                        try:
                            count = int(match.replace(',', '').strip())
                            if count > 0:
                                latest_version_downloads = count
                                print(f"Found latest version downloads: {count}")
                                break
                        except (ValueError, AttributeError):
                            continue
                    if latest_version_downloads > 0:
                        break
            
            # Pattern 2: Look for "Total downloads" text with number (all-time total)
            total_patterns = [
                r'Total downloads[:\s]+([\d,\.]+[KM]?)',
                r'Total downloads[:\s]+([\d,]+)',
                r'"totalDownloads":\s*([\d,]+)',
                r'total[_\s]*downloads[:\s]*([\d,\.]+[KM]?)',
            ]
            
            total_downloads = 0
            
            for pattern in total_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    # Parse the number (handle K, M suffixes)
                    for match in matches:
                        try:
                            match_str = match.replace(',', '').strip()
                            if match_str.upper().endswith('K'):
                                total_downloads = int(float(match_str[:-1]) * 1000)
                            elif match_str.upper().endswith('M'):
                                total_downloads = int(float(match_str[:-1]) * 1000000)
                            else:
                                total_downloads = int(float(match_str))
                            break
                        except ValueError:
                            continue
                    if total_downloads > 0:
                        break
            
            # Pattern 3: Look in JSON data embedded in the page
            if total_downloads == 0 or latest_version_downloads == 0:
                # Try to find JSON data in script tags
                script_pattern = r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>'
                scripts = re.findall(script_pattern, html, re.DOTALL | re.IGNORECASE)
                
                for script in scripts:
                    try:
                        import json
                        data = json.loads(script)
                        # Recursively search for download count
                        def find_downloads(obj, path=""):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    if 'download' in key.lower() and isinstance(value, (int, float)):
                                        return int(value)
                                    result = find_downloads(value, f"{path}.{key}")
                                    if result:
                                        return result
                            elif isinstance(obj, list):
                                for item in obj:
                                    result = find_downloads(item, path)
                                    if result:
                                        return result
                            return None
                        
                        found = find_downloads(data)
                        if found and found > 0:
                            if total_downloads == 0:
                                total_downloads = found
                            if latest_version_downloads == 0:
                                latest_version_downloads = found
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            # If we found latest version downloads but not total, use latest as total
            # (for display purposes, showing latest is more useful than all-time)
            if latest_version_downloads > 0 and total_downloads == 0:
                total_downloads = latest_version_downloads
            elif total_downloads > 0 and latest_version_downloads == 0:
                # If we only have total, use it for latest too
                latest_version_downloads = total_downloads
            
            return {
                "total_downloads": total_downloads,
                "latest_version_downloads": latest_version_downloads,
                "source": "scraped"
            }
        
        except Exception as e:
            return {
                "total_downloads": 0,
                "latest_version_downloads": 0,
                "error": str(e),
                "source": "scraped"
            }
    
    def get_package_downloads(
        self,
        owner: str,
        package_name: str,
        package_type: str = "container"
    ) -> Dict[str, Any]:
        """
        Get download statistics for a package.
        
        For container packages, this will scrape the GitHub package page since
        GitHub Container Registry doesn't expose download counts via API.
        
        Args:
            owner: Package owner
            package_name: Package name
            package_type: Package type
            
        Returns:
            Dictionary with package download statistics
        """
        try:
            # First, try to get package info via API
            package_info_endpoint = f"/users/{owner}/packages/{package_type}/{package_name}"
            package_info = self._make_request(package_info_endpoint, use_cache=True)
            
            versions = self.get_package_versions(owner, package_name, package_type)
            
            total_downloads = 0
            latest_version = None
            latest_version_downloads = 0
            
            # For container packages, scrape the web page for download counts
            if package_type == "container":
                scraped_data = self._scrape_package_downloads(owner, package_name)
                # Prefer latest version downloads over total (more accurate for current state)
                scraped_latest = scraped_data.get("latest_version_downloads", 0)
                scraped_total = scraped_data.get("total_downloads", 0)
                
                if scraped_latest > 0:
                    total_downloads = scraped_latest
                    latest_version_downloads = scraped_latest
                    print(f"Scraped latest version downloads: {scraped_latest} for {owner}/{package_name}")
                elif scraped_total > 0:
                    total_downloads = scraped_total
                    print(f"Scraped total downloads: {scraped_total} for {owner}/{package_name}")
            else:
                # For other package types, try API
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
