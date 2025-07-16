"""
认证演示路由 - 展示增强的认证和错误处理
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from src.api.middleware.enhanced_auth import (
    get_current_user_enhanced,
    require_admin,
    require_project_access,
    login_user
)
from src.api.middleware.error_handler import (
    APIError,
    NotFoundError,
    ValidationError,
    BusinessError,
    RateLimitError
)
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth-demo", tags=["auth-demo"])


class LoginRequest(BaseModel):
    """登录请求"""
    user_id: str = Field(..., description="用户ID")
    password: str = Field(..., description="密码")


class UserInfo(BaseModel):
    """用户信息"""
    user_id: str
    role: str
    permissions: list[str]


@router.post("/login")
async def demo_login(request: LoginRequest):
    """
    演示登录接口
    
    测试账号：
    - 用户: u1 / password123
    - 管理员: admin / admin123
    """
    try:
        result = login_user(request.user_id, request.password)
        logger.info(f"用户登录成功: {request.user_id}")
        return {
            "success": True,
            "data": result,
            "message": "登录成功"
        }
    except Exception as e:
        logger.warning(f"登录失败: {request.user_id} - {e}")
        raise BusinessError("用户名或密码错误", "INVALID_CREDENTIALS")


@router.get("/profile", response_model=UserInfo)
async def get_user_profile(
    current_user: str = Depends(get_current_user_enhanced)
):
    """
    获取当前用户信息 - 需要认证
    """
    # 模拟从数据库获取用户信息
    if current_user == "admin":
        return UserInfo(
            user_id=current_user,
            role="admin",
            permissions=["read", "write", "delete", "admin"]
        )
    else:
        return UserInfo(
            user_id=current_user,
            role="user",
            permissions=["read", "write"]
        )


@router.get("/admin/users")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: str = Depends(require_admin)
):
    """
    获取用户列表 - 需要管理员权限
    """
    # 模拟分页数据
    mock_users = [
        {"id": f"u{i}", "name": f"用户{i}", "role": "user"}
        for i in range(1, 6)
    ]
    
    return {
        "data": mock_users,
        "page": page,
        "size": size,
        "total": len(mock_users),
        "admin": current_user
    }


@router.get("/project/{project_id}/info")
async def get_project_info(
    project_id: str,
    current_user: str = Depends(get_current_user_enhanced)
):
    """
    获取项目信息 - 需要项目访问权限
    """
    # 验证项目访问权限
    await require_project_access(project_id, current_user)
    
    # 模拟项目不存在的情况
    if project_id == "not_exists":
        raise NotFoundError("项目", project_id)
    
    return {
        "project_id": project_id,
        "name": f"项目 {project_id}",
        "owner": current_user,
        "created_at": "2024-01-01T00:00:00Z"
    }


@router.post("/test-errors/{error_type}")
async def test_error_handling(
    error_type: str,
    current_user: str = Depends(get_current_user_enhanced)
):
    """
    测试各种错误处理
    
    错误类型：
    - not_found: 资源未找到
    - validation: 验证错误
    - business: 业务错误
    - rate_limit: 速率限制
    - api_error: 通用API错误
    - exception: 未处理异常
    """
    if error_type == "not_found":
        raise NotFoundError("测试资源", "test_123")
    
    elif error_type == "validation":
        raise ValidationError("字段格式不正确", "email")
    
    elif error_type == "business":
        raise BusinessError("余额不足", "INSUFFICIENT_BALANCE")
    
    elif error_type == "rate_limit":
        raise RateLimitError(retry_after=120)
    
    elif error_type == "api_error":
        raise APIError(
            message="这是一个自定义API错误",
            status_code=418,
            error_code="IM_A_TEAPOT",
            details={"reason": "测试目的"}
        )
    
    elif error_type == "exception":
        # 故意触发异常
        result = 1 / 0
    
    else:
        return {
            "message": f"未知的错误类型: {error_type}",
            "user": current_user
        }


@router.get("/protected-resource")
async def access_protected_resource(
    resource_id: Optional[str] = None,
    current_user: str = Depends(get_current_user_enhanced)
):
    """
    访问受保护资源 - 演示参数验证
    """
    if not resource_id:
        raise ValidationError("resource_id参数是必需的", "resource_id")
    
    if len(resource_id) < 3:
        raise ValidationError("resource_id长度至少为3个字符", "resource_id")
    
    # 模拟权限检查
    if resource_id.startswith("secret_") and current_user != "admin":
        raise BusinessError("权限不足：只有管理员可以访问机密资源", "PERMISSION_DENIED")
    
    return {
        "resource_id": resource_id,
        "data": f"这是资源 {resource_id} 的内容",
        "accessed_by": current_user,
        "access_time": "2024-01-01T12:00:00Z"
    }


@router.get("/health-check")
async def auth_health_check():
    """
    认证系统健康检查 - 不需要认证
    """
    return {
        "status": "healthy",
        "auth_system": "enhanced",
        "features": [
            "JWT认证",
            "速率限制",
            "权限检查",
            "错误处理"
        ]
    }