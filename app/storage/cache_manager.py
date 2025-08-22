"""Mock cache manager for view-only mode."""

import logging
import time
from typing import Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)


class MockCache:
    """Simple in-memory cache for view-only mode."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.ttl_data = {}
        logger.info("Initialized mock cache manager for view-only mode")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache with optional TTL."""
        try:
            # Remove old entry if it exists
            if key in self.cache:
                del self.cache[key]
                if key in self.ttl_data:
                    del self.ttl_data[key]
            
            # Add new entry
            self.cache[key] = value
            
            # Set TTL if provided
            if ttl:
                self.ttl_data[key] = time.time() + ttl
            
            # Maintain max size
            if len(self.cache) > self.max_size:
                # Remove oldest entry
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                if oldest_key in self.ttl_data:
                    del self.ttl_data[oldest_key]
            
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache value: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cache."""
        try:
            # Check if key exists
            if key not in self.cache:
                return default
            
            # Check TTL
            if key in self.ttl_data:
                if time.time() > self.ttl_data[key]:
                    # Expired, remove it
                    del self.cache[key]
                    del self.ttl_data[key]
                    return default
            
            # Move to end (LRU behavior)
            value = self.cache.pop(key)
            self.cache[key] = value
            
            logger.debug(f"Cache hit: {key}")
            return value
            
        except Exception as e:
            logger.error(f"Error getting cache value: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        try:
            if key in self.cache:
                del self.cache[key]
                if key in self.ttl_data:
                    del self.ttl_data[key]
                logger.debug(f"Cache delete: {key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting cache value: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        try:
            if key not in self.cache:
                return False
            
            # Check TTL
            if key in self.ttl_data:
                if time.time() > self.ttl_data[key]:
                    # Expired, remove it
                    del self.cache[key]
                    del self.ttl_data[key]
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            self.cache.clear()
            self.ttl_data.clear()
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def keys(self) -> list:
        """Get all cache keys."""
        return list(self.cache.keys())


# Create CacheManager as an alias for MockCache to fix import issues
CacheManager = MockCache

# Global cache instance
cache = MockCache()
