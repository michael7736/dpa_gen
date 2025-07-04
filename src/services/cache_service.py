"""
统一的缓存服务
支持Redis缓存和本地内存缓存
"""

import json
import pickle
from typing import Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
from functools import wraps

import redis.asyncio as redis
from redis.exceptions import RedisError

from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CacheService:
    """统一的缓存服务"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._redis_client = None
        self._local_cache = {}  # 本地内存缓存作为后备
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
    
    async def _get_redis_client(self):
        """获取Redis客户端（懒加载）"""
        if self._redis_client is None:
            try:
                self._redis_client = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False  # 返回字节，支持pickle
                )
                await self._redis_client.ping()
                self.logger.info("Redis cache connected")
            except Exception as e:
                self.logger.warning(f"Failed to connect to Redis: {e}")
                self._redis_client = None
        
        return self._redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            # 尝试从Redis获取
            client = await self._get_redis_client()
            if client:
                value = await client.get(key)
                if value:
                    self._cache_stats["hits"] += 1
                    # 尝试JSON解析，失败则使用pickle
                    try:
                        return json.loads(value)
                    except:
                        return pickle.loads(value)
            
            # Redis不可用或未找到，尝试本地缓存
            if key in self._local_cache:
                entry = self._local_cache[key]
                if entry["expiry"] > datetime.now():
                    self._cache_stats["hits"] += 1
                    return entry["value"]
                else:
                    # 过期，删除
                    del self._local_cache[key]
            
            self._cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            self._cache_stats["errors"] += 1
            self.logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        try:
            # 尝试存储到Redis
            client = await self._get_redis_client()
            if client:
                # 尝试JSON序列化，失败则使用pickle
                try:
                    serialized = json.dumps(value)
                except:
                    serialized = pickle.dumps(value)
                
                await client.setex(key, ttl, serialized)
                self.logger.debug(f"Cached {key} in Redis with TTL {ttl}s")
            
            # 同时存储到本地缓存
            self._local_cache[key] = {
                "value": value,
                "expiry": datetime.now() + timedelta(seconds=ttl)
            }
            
            # 限制本地缓存大小
            if len(self._local_cache) > 1000:
                self._cleanup_local_cache()
            
            return True
            
        except Exception as e:
            self._cache_stats["errors"] += 1
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            # 从Redis删除
            client = await self._get_redis_client()
            if client:
                await client.delete(key)
            
            # 从本地缓存删除
            if key in self._local_cache:
                del self._local_cache[key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        count = 0
        try:
            client = await self._get_redis_client()
            if client:
                # 使用SCAN避免阻塞
                async for key in client.scan_iter(match=pattern):
                    await client.delete(key)
                    count += 1
            
            # 清理本地缓存
            keys_to_delete = [k for k in self._local_cache.keys() if pattern.replace("*", "") in k]
            for key in keys_to_delete:
                del self._local_cache[key]
                count += 1
            
            self.logger.info(f"Cleared {count} cache entries matching pattern: {pattern}")
            return count
            
        except Exception as e:
            self.logger.error(f"Cache clear pattern error: {e}")
            return count
    
    def _cleanup_local_cache(self):
        """清理过期的本地缓存"""
        now = datetime.now()
        expired_keys = [
            k for k, v in self._local_cache.items()
            if v["expiry"] <= now
        ]
        for key in expired_keys:
            del self._local_cache[key]
        
        # 如果还是太大，删除最旧的条目
        if len(self._local_cache) > 800:
            sorted_items = sorted(
                self._local_cache.items(),
                key=lambda x: x[1]["expiry"]
            )
            for key, _ in sorted_items[:200]:
                del self._local_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = self._cache_stats["hits"] / total if total > 0 else 0
        
        return {
            **self._cache_stats,
            "hit_rate": f"{hit_rate * 100:.1f}%",
            "local_cache_size": len(self._local_cache),
            "redis_connected": self._redis_client is not None
        }


def cache_result(key_prefix: str, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{str(args)}:{str(kwargs)}"
            
            # 获取缓存服务
            cache_service = CacheService()
            
            # 尝试从缓存获取
            cached = await cache_service.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存储到缓存
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class CacheManager:
    """缓存管理器 - 提供高级缓存功能"""
    
    def __init__(self):
        self.cache_service = CacheService()
    
    async def get_or_compute(self, key: str, compute_func, ttl: int = 3600) -> Any:
        """获取缓存或计算并缓存"""
        # 尝试从缓存获取
        value = await self.cache_service.get(key)
        if value is not None:
            return value
        
        # 计算值
        if asyncio.iscoroutinefunction(compute_func):
            value = await compute_func()
        else:
            value = compute_func()
        
        # 缓存结果
        await self.cache_service.set(key, value, ttl)
        
        return value
    
    async def invalidate_document_cache(self, document_id: str):
        """使文档相关的缓存失效"""
        patterns = [
            f"embeddings:{document_id}*",
            f"chunks:{document_id}*",
            f"metadata:{document_id}*",
            f"search:*{document_id}*"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            cleared = await self.cache_service.clear_pattern(pattern)
            total_cleared += cleared
        
        logger.info(f"Invalidated {total_cleared} cache entries for document {document_id}")
        return total_cleared
    
    async def invalidate_project_cache(self, project_id: str):
        """使项目相关的缓存失效"""
        patterns = [
            f"project:{project_id}:*",
            f"search:{project_id}:*",
            f"stats:{project_id}:*"
        ]
        
        total_cleared = 0
        for pattern in patterns:
            cleared = await self.cache_service.clear_pattern(pattern)
            total_cleared += cleared
        
        logger.info(f"Invalidated {total_cleared} cache entries for project {project_id}")
        return total_cleared
    
    async def warm_cache(self, project_id: str):
        """预热项目缓存"""
        # 这里可以预加载常用数据到缓存
        # 例如：项目统计信息、最近文档列表等
        pass


# 缓存键生成器
class CacheKeys:
    """标准化的缓存键生成"""
    
    @staticmethod
    def document_embeddings(document_id: str) -> str:
        return f"embeddings:{document_id}"
    
    @staticmethod
    def document_chunks(document_id: str) -> str:
        return f"chunks:{document_id}"
    
    @staticmethod
    def document_metadata(document_id: str) -> str:
        return f"metadata:{document_id}"
    
    @staticmethod
    def search_results(project_id: str, query_hash: str) -> str:
        return f"search:{project_id}:{query_hash}"
    
    @staticmethod
    def project_stats(project_id: str) -> str:
        return f"stats:{project_id}"
    
    @staticmethod
    def user_preferences(user_id: str) -> str:
        return f"user:prefs:{user_id}"