"""In-memory cache manager for frequently accessed data."""

import time
from typing import Dict, Any, Optional, List
from collections import OrderedDict
from app.config import settings


class CacheManager:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, ttl: Optional[int] = None):
        """Initialize cache with TTL in seconds."""
        self.ttl = ttl or settings.cache_ttl
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_size = 1000  # Maximum number of cached items
    
    def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, value in self.cache.items()
            if current_time - value['timestamp'] > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_oldest(self) -> None:
        """Evict oldest cache entries if cache is full."""
        while len(self.cache) >= self.max_size:
            # Remove oldest item (first in OrderedDict)
            self.cache.popitem(last=False)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        self._cleanup_expired()
        
        if key in self.cache:
            item = self.cache[key]
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return item['value']
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        self._cleanup_expired()
        
        # Evict old items if needed
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        # Set new value
        self.cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl or self.ttl
        }
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        self._cleanup_expired()
        return key in self.cache
    
    def get_keys(self) -> List[str]:
        """Get all non-expired cache keys."""
        self._cleanup_expired()
        return list(self.cache.keys())
    
    def size(self) -> int:
        """Get current cache size (excluding expired items)."""
        self._cleanup_expired()
        return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._cleanup_expired()
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl,
            'keys': list(self.cache.keys())
        }


# Global cache instance
cache = CacheManager()
