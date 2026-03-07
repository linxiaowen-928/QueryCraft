"""
缓存服务 - 为性能优化提供高效缓存机制
"""
import hashlib
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import pickle
import logging


logger = logging.getLogger(__name__)


class LRUCache:
    """简单的LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple] = {}  # {key: (value, timestamp)}
        self.access_order = {}  # {key: access_time}
    
    def _cleanup_expired(self):
        """清理过期条目"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp > timedelta(seconds=self.ttl_seconds)
        ]
        for key in expired_keys:
            self._remove_key(key)
    
    def _remove_key(self, key: str):
        """移除键值对"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            del self.access_order[key]
    
    def _evict_if_needed(self):
        """如果达到最大大小则驱逐最少使用的项"""
        if len(self.cache) >= self.max_size:
            # 按访问时间排序并移除最久未使用的项
            sorted_keys = sorted(
                self.access_order.items(),
                key=lambda x: x[1]
            )
            if sorted_keys:
                oldest_key = sorted_keys[0][0]
                self._remove_key(oldest_key)
    
    def get(self, key: str) -> Optional[Any]:
        """获取值"""
        self._cleanup_expired()
        
        if key not in self.cache:
            return None
        
        value, _ = self.cache[key]
        # 更新访问时间
        self.access_order[key] = datetime.now()
        return value
    
    def put(self, key: str, value: Any):
        """放入值"""
        self._cleanup_expired()
        self._evict_if_needed()
        
        self.cache[key] = (value, datetime.now())
        self.access_order[key] = datetime.now()


# 全局缓存实例
llm_cache = LRUCache(max_size=1000, ttl_seconds=7200)  # 2小时TTL，1000项最大
schema_cache = LRUCache(max_size=100, ttl_seconds=1800)  # 30分钟TTL，100项


class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    def generate_cache_key(operation: str, **kwargs) -> str:
        """生成缓存键"""
        # 将kwargs排序以确保相同参数产生相同的键
        sorted_items = sorted(kwargs.items(), key=lambda x: str(x[0]))
        key_string = f"{operation}:{str(sorted_items)}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @staticmethod
    def cache_llm_call(query: str, dialect: str, schema_info: Optional[Dict] = None) -> Optional[str]:
        """缓存LLM调用"""
        cache_key = CacheManager.generate_cache_key(
            "llm_call",
            query=query,
            dialect=dialect,
            schema_info=str(sorted(schema_info.items())) if schema_info else ""
        )
        
        return llm_cache.get(cache_key)
    
    @staticmethod
    def store_llm_result(query: str, dialect: str, result: str, schema_info: Optional[Dict] = None):
        """存储LLM结果"""
        cache_key = CacheManager.generate_cache_key(
            "llm_call",
            query=query,
            dialect=dialect,
            schema_info=str(sorted(schema_info.items())) if schema_info else ""
        )
        
        llm_cache.put(cache_key, result)
    @staticmethod
    def cache_schema_result(datasource_name: str, schema_result: Any):
        """缓存schema结果"""
        cache_key = CacheManager.generate_cache_key("schema", datasource=datasource_name)
        schema_cache.put(cache_key, schema_result)
    
    @staticmethod
    def get_cached_schema(datasource_name: str) -> Optional[Any]:
        """获取缓存的schema"""
        cache_key = CacheManager.generate_cache_key("schema", datasource=datasource_name)
        return schema_cache.get(cache_key)


cache_manager = CacheManager()