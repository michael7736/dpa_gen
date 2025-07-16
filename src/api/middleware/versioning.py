"""
API版本控制中间件
支持URL路径版本和请求头版本
"""

from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...config.settings import get_settings
from ...utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class APIVersion:
    """API版本定义"""
    
    def __init__(self, version: str, deprecated: bool = False, sunset_date: Optional[str] = None):
        self.version = version
        self.deprecated = deprecated
        self.sunset_date = sunset_date
        self.features = {}
        
    def add_feature(self, name: str, enabled: bool = True):
        """添加版本特性"""
        self.features[name] = enabled
        
    def has_feature(self, name: str) -> bool:
        """检查是否有某个特性"""
        return self.features.get(name, False)


class APIVersionManager:
    """API版本管理器"""
    
    def __init__(self):
        self.versions = {}
        self.current_version = "v1"
        self.minimum_version = "v1"
        self._setup_versions()
        
    def _setup_versions(self):
        """设置版本信息"""
        # V1版本 - 基础版本
        v1 = APIVersion("v1")
        v1.add_feature("basic_auth", True)
        v1.add_feature("document_processing", True)
        v1.add_feature("vector_search", True)
        self.versions["v1"] = v1
        
        # V2版本 - 增强版本（规划中）
        v2 = APIVersion("v2", deprecated=False)
        v2.add_feature("basic_auth", True)
        v2.add_feature("document_processing", True)
        v2.add_feature("vector_search", True)
        v2.add_feature("knowledge_graph", True)
        v2.add_feature("advanced_rag", True)
        v2.add_feature("streaming_response", True)
        self.versions["v2"] = v2
        
    def get_version(self, version_string: str) -> Optional[APIVersion]:
        """获取版本信息"""
        return self.versions.get(version_string)
        
    def is_version_supported(self, version_string: str) -> bool:
        """检查版本是否支持"""
        version = self.get_version(version_string)
        if not version:
            return False
            
        # 检查是否已经日落
        if version.sunset_date:
            sunset = datetime.fromisoformat(version.sunset_date)
            if datetime.now() > sunset:
                return False
                
        return True
        
    def extract_version_from_request(self, request: Request) -> str:
        """从请求中提取版本号"""
        try:
            # 1. 从URL路径提取
            path_parts = request.url.path.split("/")
            if len(path_parts) > 2 and path_parts[2].startswith("v"):
                version = path_parts[2]
                return version
                
            # 2. 从请求头提取
            api_version = request.headers.get("X-API-Version")
            if api_version:
                return api_version
                
            # 3. 从查询参数提取
            api_version = request.query_params.get("api_version")
            if api_version:
                return api_version
                
            # 4. 返回当前版本
            return self.current_version
            
        except Exception as e:
            logger.error(f"版本提取异常: {e}, 路径: {request.url.path}, 使用默认版本: {self.current_version}")
            return self.current_version


class VersioningMiddleware(BaseHTTPMiddleware):
    """版本控制中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.version_manager = APIVersionManager()
        
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        try:
            # 提取版本
            version_string = self.version_manager.extract_version_from_request(request)
            
            # 检查版本是否支持
            if not self.version_manager.is_version_supported(version_string):
                logger.error(f"不支持的API版本: {version_string}, 请求路径: {request.url.path}, 方法: {request.method}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Unsupported API version",
                        "message": f"API版本 '{version_string}' 不支持",
                        "supported_versions": list(self.version_manager.versions.keys()),
                        "current_version": self.version_manager.current_version,
                        "request_path": str(request.url.path),
                        "extracted_version": version_string
                    }
                )
        except Exception as e:
            logger.error(f"版本中间件异常: {e}, 请求: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Version middleware error",
                    "message": str(e),
                    "request_path": str(request.url.path)
                }
            )
            
        # 获取版本信息
        version = self.version_manager.get_version(version_string)
        
        # 将版本信息添加到请求状态
        request.state.api_version = version_string
        request.state.api_features = version.features
        
        # 处理请求
        response = await call_next(request)
        
        # 添加版本相关头部
        response.headers["X-API-Version"] = version_string
        
        # 如果版本已弃用，添加警告
        if version.deprecated:
            response.headers["X-API-Deprecated"] = "true"
            if version.sunset_date:
                response.headers["X-API-Sunset"] = version.sunset_date
                
        return response


def require_api_version(min_version: str = "v1", features: Optional[list] = None):
    """要求特定API版本的装饰器"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # 检查版本
            api_version = getattr(request.state, "api_version", "v1")
            if api_version < min_version:
                raise HTTPException(
                    status_code=400,
                    detail=f"此功能需要API版本 {min_version} 或更高"
                )
                
            # 检查特性
            if features:
                api_features = getattr(request.state, "api_features", {})
                for feature in features:
                    if not api_features.get(feature, False):
                        raise HTTPException(
                            status_code=400,
                            detail=f"此功能需要特性: {feature}"
                        )
                        
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def deprecated_endpoint(sunset_date: Optional[str] = None, alternative: Optional[str] = None):
    """标记端点为已弃用"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 记录警告
            logger.warning(f"调用了已弃用的端点: {func.__name__}")
            
            # 执行原函数
            result = await func(*args, **kwargs)
            
            # 如果是Response对象，添加弃用头部
            if hasattr(result, "headers"):
                result.headers["X-API-Deprecated"] = "true"
                if sunset_date:
                    result.headers["X-API-Sunset"] = sunset_date
                if alternative:
                    result.headers["X-API-Alternative"] = alternative
                    
            return result
        return wrapper
    return decorator