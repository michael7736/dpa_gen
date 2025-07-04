"""
演示路由 - 展示限流和版本控制功能
"""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..middleware import RATE_LIMITS, require_api_version, deprecated_endpoint
from ...config.settings import get_settings
from ...utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/demo", tags=["演示"])


class DemoResponse(BaseModel):
    """演示响应模型"""
    message: str
    timestamp: datetime
    version: str
    features: Dict[str, Any]


@router.get("/basic", response_model=DemoResponse)
async def basic_demo(request: Request):
    """基础演示端点（无限流）"""
    return DemoResponse(
        message="这是一个基础演示端点",
        timestamp=datetime.now(),
        version=request.state.api_version,
        features=request.state.api_features
    )


@router.get("/limited", response_model=DemoResponse, dependencies=[Depends(RATE_LIMITS["strict"])])
async def limited_demo(request: Request):
    """限流演示端点（严格限制：10次/分钟）"""
    return DemoResponse(
        message="这是一个严格限流的端点",
        timestamp=datetime.now(),
        version=request.state.api_version,
        features=request.state.api_features
    )


@router.get("/v2-feature", response_model=DemoResponse)
@require_api_version(min_version="v2", features=["advanced_rag"])
async def v2_feature_demo(request: Request):
    """V2版本特性演示（需要v2版本和advanced_rag特性）"""
    return DemoResponse(
        message="这是V2版本的高级特性",
        timestamp=datetime.now(),
        version=request.state.api_version,
        features=request.state.api_features
    )


@router.get("/deprecated", response_model=DemoResponse)
@deprecated_endpoint(sunset_date="2025-12-31", alternative="/api/v2/demo/new-endpoint")
async def deprecated_demo(request: Request):
    """已弃用的端点演示"""
    return DemoResponse(
        message="警告：此端点已弃用，将于2025-12-31停用",
        timestamp=datetime.now(),
        version=request.state.api_version,
        features=request.state.api_features
    )


@router.get("/rate-limit-test")
async def rate_limit_test(request: Request):
    """测试限流功能"""
    return {
        "message": "限流测试端点",
        "headers": {
            "X-RateLimit-Limit": request.headers.get("X-RateLimit-Limit"),
            "X-RateLimit-Window": request.headers.get("X-RateLimit-Window"),
        },
        "client_ip": request.client.host if request.client else "unknown",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/version-test")
async def version_test(request: Request):
    """测试版本控制功能"""
    api_version = getattr(request.state, "api_version", "unknown")
    api_features = getattr(request.state, "api_features", {})
    
    return {
        "message": "版本控制测试端点",
        "current_version": api_version,
        "available_features": api_features,
        "request_headers": {
            "X-API-Version": request.headers.get("X-API-Version"),
        },
        "timestamp": datetime.now().isoformat()
    }