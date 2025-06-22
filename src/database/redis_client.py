"""
Redis连接管理
用于缓存和消息队列
"""

import json
import pickle
import logging
from typing import Any, Optional, Union, Dict, List
from redis import Redis
from redis.connection import ConnectionPool
import asyncio

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 全局Redis客户端
_redis_client: Optional[Redis] = None
_connection_pool: Optional[ConnectionPool] = None


def get_redis_client() -> Redis:
    """获取Redis客户端"""
    global _redis_client, _connection_pool
    
    if _redis_client is None:
        try:
            # 解析Redis URL
            redis_url = settings.redis.url
            
            # 创建连接池
            _connection_pool = ConnectionPool.from_url(
                redis_url,
                password=settings.redis.password,
                db=settings.redis.db,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=30,
                socket_connect_timeout=30,
            )
            
            # 创建Redis客户端
            _redis_client = Redis(
                connection_pool=_connection_pool,
                decode_responses=True,
            )
            
            # 测试连接
            _redis_client.ping()
            logger.info(f"✅ Redis客户端连接成功: {redis_url}")
            
        except Exception as e:
            logger.error(f"❌ Redis客户端连接失败: {e}")
            raise
    
    return _redis_client


async def test_connection() -> bool:
    """测试Redis连接"""
    try:
        client = get_redis_client()
        result = client.ping()
        if result:
            logger.info("✅ Redis连接测试成功")
            return True
        else:
            logger.error("❌ Redis连接测试失败: ping返回False")
            return False
            
    except Exception as e:
        logger.error(f"❌ Redis连接测试失败: {e}")
        return False


class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self, prefix: str = "dpa"):
        self.client = get_redis_client()
        self.prefix = prefix
        self.default_ttl = settings.redis.cache_ttl
    
    def _make_key(self, key: str) -> str:
        """生成带前缀的键名"""
        return f"{self.prefix}:{key}"
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """设置缓存"""
        try:
            cache_key = self._make_key(key)
            
            if serialize:
                if isinstance(value, (dict, list, tuple)):
                    value = json.dumps(value, ensure_ascii=False)
                elif not isinstance(value, (str, int, float, bool)):
                    value = pickle.dumps(value)
            
            ttl = ttl or self.default_ttl
            result = self.client.setex(cache_key, ttl, value)
            
            if result:
                logger.debug(f"✅ 缓存设置成功: {cache_key}")
                return True
            else:
                logger.error(f"❌ 缓存设置失败: {cache_key}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 缓存设置异常: {e}")
            return False
    
    def get(
        self, 
        key: str, 
        default: Any = None,
        deserialize: bool = True
    ) -> Any:
        """获取缓存"""
        try:
            cache_key = self._make_key(key)
            value = self.client.get(cache_key)
            
            if value is None:
                return default
            
            if deserialize and isinstance(value, str):
                try:
                    # 尝试JSON反序列化
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        # 尝试pickle反序列化
                        return pickle.loads(value.encode() if isinstance(value, str) else value)
                    except (pickle.PickleError, TypeError):
                        # 返回原始字符串
                        return value
            
            return value
            
        except Exception as e:
            logger.error(f"❌ 缓存获取异常: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_key = self._make_key(key)
            result = self.client.delete(cache_key)
            
            if result:
                logger.debug(f"✅ 缓存删除成功: {cache_key}")
                return True
            else:
                logger.warning(f"⚠️ 缓存键不存在: {cache_key}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 缓存删除异常: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            cache_key = self._make_key(key)
            return bool(self.client.exists(cache_key))
            
        except Exception as e:
            logger.error(f"❌ 缓存检查异常: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        try:
            cache_key = self._make_key(key)
            result = self.client.expire(cache_key, ttl)
            
            if result:
                logger.debug(f"✅ 缓存过期时间设置成功: {cache_key}")
                return True
            else:
                logger.warning(f"⚠️ 缓存键不存在或设置失败: {cache_key}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 缓存过期时间设置异常: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            pattern_key = self._make_key(pattern)
            keys = self.client.keys(pattern_key)
            
            if keys:
                count = self.client.delete(*keys)
                logger.info(f"✅ 清除缓存成功: {count} 个键")
                return count
            else:
                logger.info("没有找到匹配的缓存键")
                return 0
                
        except Exception as e:
            logger.error(f"❌ 清除缓存异常: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            info = self.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
            
        except Exception as e:
            logger.error(f"❌ 获取缓存统计异常: {e}")
            return {}


# 全局缓存实例
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """获取缓存实例"""
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = RedisCache()
    
    return _cache_instance


async def init_redis():
    """初始化Redis"""
    logger.info("开始初始化Redis...")
    
    # 测试连接
    if not await test_connection():
        return False
    
    # 初始化缓存实例
    cache = get_cache()
    
    # 测试缓存功能
    test_key = "test_connection"
    test_value = {"status": "ok", "timestamp": "2024-01-01"}
    
    if cache.set(test_key, test_value, ttl=60):
        retrieved_value = cache.get(test_key)
        if retrieved_value == test_value:
            cache.delete(test_key)
            logger.info("✅ Redis缓存功能测试成功")
        else:
            logger.error("❌ Redis缓存功能测试失败: 数据不匹配")
            return False
    else:
        logger.error("❌ Redis缓存功能测试失败: 无法设置缓存")
        return False
    
    logger.info("✅ Redis初始化完成")
    return True


def close_connection():
    """关闭Redis连接"""
    global _redis_client, _connection_pool, _cache_instance
    
    if _redis_client:
        _redis_client.close()
        _redis_client = None
    
    if _connection_pool:
        _connection_pool.disconnect()
        _connection_pool = None
    
    _cache_instance = None
    logger.info("Redis连接已关闭") 