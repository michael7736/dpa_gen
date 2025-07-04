"""
Redis缓存客户端管理器
支持缓存操作和会话管理
"""

import json
from typing import Any, Optional, Union
import redis.asyncio as redis
from datetime import timedelta

from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 全局实例
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """获取Redis客户端实例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password,
            db=settings.redis.db,
            decode_responses=True
        )
    return _redis_client


def get_cache() -> 'CacheManager':
    """获取缓存管理器"""
    return CacheManager()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.client = get_redis_client()
        self.default_ttl = 3600  # 默认1小时
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"缓存读取失败: {key} - {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"缓存写入失败: {key} - {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"缓存删除失败: {key} - {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return await self.client.exists(key)
        except Exception as e:
            logger.error(f"检查缓存失败: {key} - {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有键"""
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"清除了 {deleted} 个缓存键")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"清除缓存模式失败: {pattern} - {e}")
            return 0
    
    async def get_ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        try:
            ttl = await self.client.ttl(key)
            return ttl
        except Exception as e:
            logger.error(f"获取TTL失败: {key} - {e}")
            return -1
    
    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """延长键的生存时间"""
        try:
            await self.client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"延长TTL失败: {key} - {e}")
            return False