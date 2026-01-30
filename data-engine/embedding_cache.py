"""
NEXUS AI - Embedding Cache
Caches embeddings to reduce API costs and improve performance
"""
import os
import json
import hashlib
from typing import List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv('.env.local')

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("   [CACHE] Redis not available, using in-memory cache")

class EmbeddingCache:
    """Cache for embeddings to reduce API calls"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.ttl = 86400 * 7  # 7 days
        self.memory_cache = {}  # Fallback in-memory cache
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=False  # We'll handle encoding
                )
                self.redis_client.ping()
                self.use_redis = True
                print("   [CACHE] Redis connected")
            except Exception as e:
                print(f"   [CACHE] Redis connection failed: {e}")
                self.use_redis = False
        else:
            self.use_redis = False
    
    def _generate_key(self, text: str, model: str = "text-embedding-3-large") -> str:
        """Generate cache key from text"""
        # Hash the text to create a unique key
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"emb:{model}:{text_hash}"
    
    def get(self, text: str, model: str = "text-embedding-3-large") -> Optional[List[float]]:
        """Get embedding from cache"""
        key = self._generate_key(text, model)
        
        if self.use_redis:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached.decode())
            except Exception as e:
                print(f"   [CACHE] Redis get error: {e}")
        
        # Fallback to memory cache
        return self.memory_cache.get(key)
    
    def set(
        self,
        text: str,
        embedding: List[float],
        model: str = "text-embedding-3-large"
    ):
        """Store embedding in cache"""
        key = self._generate_key(text, model)
        value = json.dumps(embedding)
        
        if self.use_redis:
            try:
                self.redis_client.setex(key, self.ttl, value)
                return
            except Exception as e:
                print(f"   [CACHE] Redis set error: {e}")
        
        # Fallback to memory cache
        self.memory_cache[key] = embedding
        
        # Limit memory cache size
        if len(self.memory_cache) > 1000:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self.memory_cache.keys())[:100]
            for k in keys_to_remove:
                del self.memory_cache[k]
    
    def exists(self, text: str, model: str = "text-embedding-3-large") -> bool:
        """Check if embedding exists in cache"""
        key = self._generate_key(text, model)
        
        if self.use_redis:
            try:
                return self.redis_client.exists(key) > 0
            except:
                pass
        
        return key in self.memory_cache
    
    def delete(self, text: str, model: str = "text-embedding-3-large"):
        """Delete embedding from cache"""
        key = self._generate_key(text, model)
        
        if self.use_redis:
            try:
                self.redis_client.delete(key)
            except:
                pass
        
        if key in self.memory_cache:
            del self.memory_cache[key]
    
    def clear_all(self):
        """Clear all cached embeddings"""
        if self.use_redis:
            try:
                # Delete all keys matching pattern
                for key in self.redis_client.scan_iter("emb:*"):
                    self.redis_client.delete(key)
                print("   [CACHE] Redis cache cleared")
            except Exception as e:
                print(f"   [CACHE] Clear error: {e}")
        
        self.memory_cache.clear()
        print("   [CACHE] Memory cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            'backend': 'redis' if self.use_redis else 'memory',
            'memory_cache_size': len(self.memory_cache)
        }
        
        if self.use_redis:
            try:
                # Count keys
                count = 0
                for _ in self.redis_client.scan_iter("emb:*"):
                    count += 1
                stats['redis_cache_size'] = count
                
                # Memory usage
                info = self.redis_client.info('memory')
                stats['redis_memory_mb'] = info.get('used_memory', 0) / 1024 / 1024
            except Exception as e:
                stats['redis_error'] = str(e)
        
        return stats

# Singleton instance
embedding_cache = EmbeddingCache()

if __name__ == "__main__":
    # Test cache
    print("Testing Embedding Cache...")
    
    # Test data
    test_text = "This is a test embedding"
    test_embedding = [0.1] * 1536
    
    # Set
    embedding_cache.set(test_text, test_embedding)
    print(f"✅ Cached embedding")
    
    # Get
    cached = embedding_cache.get(test_text)
    if cached:
        print(f"✅ Retrieved from cache: {len(cached)} dimensions")
    else:
        print(f"❌ Cache miss")
    
    # Stats
    stats = embedding_cache.get_stats()
    print(f"\nCache Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
