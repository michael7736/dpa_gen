"""
身份认证中间件 - 为多用户隔离预埋
单用户阶段：接受固定值 user_id="u1"
多用户阶段：可接入 OIDC/Token
"""
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 默认用户ID（单用户阶段）
DEFAULT_USER_ID = "243588ff-459d-45b8-b77b-09aec3946a64"  # default_user的UUID

# 允许的固定用户ID列表（单用户阶段）
ALLOWED_USER_IDS = {"u1", "test_user", "demo_user", "243588ff-459d-45b8-b77b-09aec3946a64"}


class UserAuthMiddleware(BaseHTTPMiddleware):
    """
    用户认证中间件
    单用户阶段：从 X-USER-ID header 读取固定值
    多用户阶段：可扩展为 JWT/OIDC 验证
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过健康检查等公开端点和OPTIONS请求
        if (request.url.path in ["/health", "/docs", "/openapi.json", "/redoc", "/"] or 
            request.method == "OPTIONS"):
            response = await call_next(request)
            return response
            
        # 获取用户ID
        user_id = request.headers.get("X-USER-ID", DEFAULT_USER_ID)
        
        # 单用户阶段：仅验证是否在允许列表中
        if user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Invalid user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid user ID. Allowed values: {', '.join(ALLOWED_USER_IDS)}"
            )
            
        # 映射简化的用户ID到UUID
        if user_id in ["u1", "test_user", "demo_user"]:
            mapped_user_id = DEFAULT_USER_ID
        else:
            mapped_user_id = user_id
            
        # 将用户信息注入请求状态
        request.state.user_id = mapped_user_id
        request.state.auth_type = "header"  # 预留字段，未来可能是 "jwt", "oidc" 等
        
        # 记录请求
        logger.info(f"Request from user {user_id}: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # 在响应头中返回用户ID（方便调试）
        response.headers["X-USER-ID"] = user_id
        
        return response


class ProjectAuthMiddleware(BaseHTTPMiddleware):
    """
    项目访问权限中间件
    单用户阶段：所有项目对所有用户开放
    多用户阶段：验证用户是否有权访问特定项目
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 单用户阶段：直接通过
        response = await call_next(request)
        return response
        
        # 多用户阶段的实现示例：
        # if hasattr(request.state, "user_id"):
        #     project_id = extract_project_id_from_path(request.url.path)
        #     if project_id:
        #         if not await check_project_access(request.state.user_id, project_id):
        #             raise HTTPException(
        #                 status_code=status.HTTP_403_FORBIDDEN,
        #                 detail="Access to this project is denied"
        #             )


# Bearer Token 验证器（为未来预留）
security = HTTPBearer(auto_error=False)


async def get_current_user(request: Request) -> str:
    """
    获取当前用户ID
    单用户阶段：从header或默认值
    多用户阶段：从JWT token解析
    """
    # 优先从请求状态获取（由中间件注入）
    if hasattr(request.state, "user_id"):
        user_id = request.state.user_id
    else:
        # 从header获取
        user_id = request.headers.get("X-USER-ID", DEFAULT_USER_ID)
    
    # 单用户阶段验证
    if user_id not in ALLOWED_USER_IDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID"
        )
    
    # 映射简化的用户ID到UUID
    if user_id in ["u1", "test_user", "demo_user"]:
        return DEFAULT_USER_ID
        
    return user_id
    
    # 多用户阶段的JWT验证示例：
    # if credentials:
    #     token = credentials.credentials
    #     try:
    #         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #         return payload.get("user_id")
    #     except jwt.JWTError:
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid authentication credentials"
    #         )


def extract_project_id_from_path(path: str) -> Optional[str]:
    """从URL路径提取项目ID"""
    # 示例：/api/v1/projects/{project_id}/...
    parts = path.strip("/").split("/")
    if "projects" in parts:
        idx = parts.index("projects")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return None


async def check_project_access(user_id: str, project_id: str) -> bool:
    """
    检查用户是否有权访问项目
    单用户阶段：始终返回True
    多用户阶段：查询数据库验证权限
    """
    # 单用户阶段
    return True
    
    # 多用户阶段示例：
    # async with get_async_session() as session:
    #     result = await session.execute(
    #         select(ProjectMember).where(
    #             and_(
    #                 ProjectMember.user_id == user_id,
    #                 ProjectMember.project_id == project_id,
    #                 ProjectMember.status == "active"
    #             )
    #         )
    #     )
    #     return result.scalar_one_or_none() is not None