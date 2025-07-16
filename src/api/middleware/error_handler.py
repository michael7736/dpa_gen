"""
增强的错误处理中间件
提供统一的错误响应格式和详细的错误日志
"""
import time
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """API错误基类"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(APIError):
    """资源未找到错误"""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource}未找到: {resource_id}",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "id": resource_id}
        )


class ValidationError(APIError):
    """验证错误"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class BusinessError(APIError):
    """业务逻辑错误"""
    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code
        )


class RateLimitError(APIError):
    """速率限制错误"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="请求过于频繁，请稍后重试",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )


def create_error_response(
    request: Request,
    status_code: int,
    message: str,
    error_code: str = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """创建统一的错误响应"""
    error_response = {
        "error": {
            "code": error_code or f"ERR_{status_code}",
            "message": message,
            "details": details or {},
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": time.time()
        }
    }
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers={
            "X-Error-Code": error_code or f"ERR_{status_code}",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """处理APIError"""
    request_id = getattr(request.state, "request_id", None)
    
    # 记录错误
    logger.error(
        f"API错误: {exc.error_code} | {exc.message} | "
        f"路径: {request.url.path} | 详情: {exc.details} | "
        f"Request ID: {request_id}"
    )
    
    return create_error_response(
        request=request,
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        request_id=request_id
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理HTTP异常"""
    request_id = getattr(request.state, "request_id", None)
    
    # 记录错误（只记录5xx错误）
    if exc.status_code >= 500:
        logger.error(
            f"HTTP异常: {exc.status_code} | {exc.detail} | "
            f"路径: {request.url.path} | Request ID: {request_id}"
        )
    
    return create_error_response(
        request=request,
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code=f"HTTP_{exc.status_code}",
        request_id=request_id
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理验证错误"""
    request_id = getattr(request.state, "request_id", None)
    
    # 格式化验证错误
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"验证错误: {request.url.path} | "
        f"错误数: {len(errors)} | Request ID: {request_id}"
    )
    
    return create_error_response(
        request=request,
        status_code=422,
        message="请求参数验证失败",
        error_code="VALIDATION_ERROR",
        details={"errors": errors},
        request_id=request_id
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理通用异常"""
    request_id = getattr(request.state, "request_id", None)
    
    # 记录详细错误信息
    logger.error(
        f"未处理异常: {type(exc).__name__} | {str(exc)} | "
        f"路径: {request.url.path} | Request ID: {request_id}\n"
        f"堆栈跟踪:\n{traceback.format_exc()}"
    )
    
    # 生产环境不应该暴露详细错误信息
    message = "服务器内部错误，请稍后重试"
    details = {}
    
    # 开发环境可以显示更多信息
    from src.config.settings import get_settings
    settings = get_settings()
    if settings.debug:
        message = str(exc)
        details = {
            "exception": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n")
        }
    
    return create_error_response(
        request=request,
        status_code=500,
        message=message,
        error_code="INTERNAL_SERVER_ERROR",
        details=details,
        request_id=request_id
    )


class ErrorHandlerMiddleware:
    """错误处理中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            
            # 检查响应状态码
            if hasattr(response, "status_code") and response.status_code >= 400:
                # 记录4xx和5xx错误
                request_id = getattr(request.state, "request_id", None)
                if response.status_code >= 500:
                    logger.error(
                        f"响应错误: {response.status_code} | "
                        f"路径: {request.url.path} | Request ID: {request_id}"
                    )
                elif response.status_code >= 400:
                    logger.warning(
                        f"客户端错误: {response.status_code} | "
                        f"路径: {request.url.path} | Request ID: {request_id}"
                    )
            
            return response
            
        except Exception as exc:
            # 处理未捕获的异常
            request_id = getattr(request.state, "request_id", None)
            logger.error(
                f"中间件异常: {type(exc).__name__} | {str(exc)} | "
                f"路径: {request.url.path} | Request ID: {request_id}\n"
                f"堆栈跟踪:\n{traceback.format_exc()}"
            )
            
            return create_error_response(
                request=request,
                status_code=500,
                message="请求处理失败",
                error_code="MIDDLEWARE_ERROR",
                request_id=request_id
            )