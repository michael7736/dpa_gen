"""
API限流中间件
基于Redis实现分布式限流
"""

import time
from typing import Callable, Optional, Dict, Any
from datetime import timedelta

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...database.redis_client import get_redis_client
from ...config.settings import get_settings
from ...utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RateLimitExceeded(HTTPException):
    """限流异常"""
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "请求过于频繁，请稍后再试",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )


class RateLimiter:
    """
    限流器
    支持多种限流策略：
    - 固定窗口
    - 滑动窗口
    - 令牌桶
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        by_ip: bool = True,
        by_user: bool = True
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.by_ip = by_ip
        self.by_user = by_user
        self.redis = None
        
    async def __call__(self, request: Request) -> bool:
        """检查是否超过限流"""
        if not self.redis:
            self.redis = get_redis_client()
            
        # 获取限流键
        keys = self._get_rate_limit_keys(request)
        
        # 检查所有限流规则
        for key, limit, window in [
            (f"{k}:minute", self.requests_per_minute, 60),
            (f"{k}:hour", self.requests_per_hour, 3600),
            (f"{k}:day", self.requests_per_day, 86400)
        ]:
            for base_key in keys:
                full_key = f"{base_key}:{key}"
                
                # 使用Lua脚本原子性地检查和增加计数
                lua_script = """
                local key = KEYS[1]
                local limit = tonumber(ARGV[1])
                local window = tonumber(ARGV[2])
                local current = tonumber(redis.call('GET', key) or 0)
                
                if current >= limit then
                    local ttl = redis.call('TTL', key)
                    return {1, ttl > 0 and ttl or window}
                else
                    redis.call('INCR', key)
                    if current == 0 then
                        redis.call('EXPIRE', key, window)
                    end
                    return {0, 0}
                end
                """
                
                result = await self.redis.eval(lua_script, 1, full_key, limit, window)
                
                if result[0] == 1:
                    raise RateLimitExceeded(retry_after=result[1])
                    
        return True
        
    def _get_rate_limit_keys(self, request: Request) -> list:
        """获取限流键"""
        keys = []
        
        # 基于IP的限流
        if self.by_ip:
            client_ip = request.client.host if request.client else "unknown"
            keys.append(f"rate_limit:ip:{client_ip}")
            
        # 基于用户的限流
        if self.by_user and hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
            if user_id:
                keys.append(f"rate_limit:user:{user_id}")
                
        # 如果没有任何键，使用全局限流
        if not keys:
            keys.append("rate_limit:global")
            
        return keys


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            requests_per_day=requests_per_day
        )
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 检查是否需要限流
        if request.url.path in self.exclude_paths:
            return await call_next(request)
            
        try:
            # 检查限流
            await self.rate_limiter(request)
            
            # 处理请求
            response = await call_next(request)
            
            # 添加限流相关头部
            response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
            response.headers["X-RateLimit-Window"] = "60"
            
            return response
            
        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=e.headers
            )
        except Exception as e:
            logger.error(f"限流中间件错误: {e}")
            return await call_next(request)


def create_rate_limiter(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    requests_per_day: int = 10000
) -> Callable:
    """创建路由级别的限流装饰器"""
    rate_limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        requests_per_day=requests_per_day
    )
    
    async def rate_limit_decorator(request: Request):
        await rate_limiter(request)
        
    return rate_limit_decorator


# 预定义的限流策略
RATE_LIMITS = {
    "strict": create_rate_limiter(10, 100, 1000),      # 严格限制
    "normal": create_rate_limiter(60, 1000, 10000),    # 正常限制
    "relaxed": create_rate_limiter(120, 2000, 20000),  # 宽松限制
    "unlimited": lambda request: True                    # 无限制
}