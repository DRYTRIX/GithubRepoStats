"""Cache manager for GitHub API responses."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class CacheManager:
    """Manages caching of GitHub API responses with TTL support."""
    
    def __init__(self, cache_dir: str = ".cache", enabled: bool = True, ttl_minutes: int = 10):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled
            ttl_minutes: Time-to-live for cached data in minutes
        """
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.ttl_minutes = ttl_minutes
        
        if self.enabled:
            self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a given key."""
        # Sanitize key for filename
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data if available and not expired.
        
        Args:
            key: Cache key (e.g., 'repo_owner_name')
            
        Returns:
            Cached data dictionary or None if not found/expired
        """
        if not self.enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # Check expiration
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            age = datetime.now() - cached_time
            
            if age > timedelta(minutes=self.ttl_minutes):
                # Cache expired
                cache_path.unlink()
                return None
            
            return cache_data["data"]
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Invalid cache file, remove it
            if cache_path.exists():
                cache_path.unlink()
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """
        Store data in cache.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        if not self.enabled:
            return
        
        cache_path = self._get_cache_path(key)
        
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            # Silently fail if cache write fails
            pass
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache for a specific key or all cache.
        
        Args:
            key: Cache key to clear, or None to clear all
        """
        if not self.enabled:
            return
        
        if key:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
        else:
            # Clear all cache files
            if self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
