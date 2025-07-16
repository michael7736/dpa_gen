"""
增强的认证中间件 - 提供更强的安全性和错误处理
"""
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config.settings import get_settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer认证
security = HTTPBearer(auto_error=False)

# 用户会话缓存（生产环境应使用Redis）
_user_sessions: Dict[str, Dict[str, Any]] = {}

# 失败尝试跟踪（生产环境应使用Redis）
_failed_attempts: Dict[str, list] = {}


class AuthError(HTTPException):
    """认证错误"""
    def __init__(self, detail: str, status_code: int = 401):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.security.jwt_secret_key, 
        algorithm=settings.security.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """解码令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret_key,
            algorithms=[settings.security.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise AuthError("无效的认证令牌")


def check_rate_limit(client_ip: str, user_id: str) -> bool:
    """检查失败尝试率限制"""
    now = datetime.now()
    window_start = now - timedelta(minutes=15)
    
    # 清理过期记录
    key = f"{client_ip}:{user_id}"
    if key in _failed_attempts:
        _failed_attempts[key] = [
            attempt for attempt in _failed_attempts[key]
            if attempt > window_start
        ]
    
    # 检查失败次数
    attempts = _failed_attempts.get(key, [])
    if len(attempts) >= 5:  # 15分钟内最多5次失败
        logger.warning(f"认证失败次数过多: {key}")
        return False
    
    return True


def record_failed_attempt(client_ip: str, user_id: str):
    """记录失败尝试"""
    key = f"{client_ip}:{user_id}"
    if key not in _failed_attempts:
        _failed_attempts[key] = []
    _failed_attempts[key].append(datetime.now())


async def get_current_user_enhanced(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    增强的获取当前用户
    支持多种认证方式和更好的错误处理
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # 1. 优先使用Bearer Token
    if credentials and credentials.credentials:
        try:
            payload = decode_token(credentials.credentials)
            user_id = payload.get("sub")
            if user_id:
                # 验证会话
                session_key = f"{user_id}:{credentials.credentials[-8:]}"
                if session_key in _user_sessions:
                    _user_sessions[session_key]["last_activity"] = datetime.now()
                    return user_id
                else:
                    logger.warning(f"无效的会话: {session_key}")
                    raise AuthError("会话已过期，请重新登录")
            
        except Exception as e:
            logger.error(f"Token验证失败: {e}")
            raise AuthError("认证失败")
    
    # 2. 使用Header中的用户ID（向后兼容）
    user_id = request.headers.get("X-USER-ID")
    if user_id:
        # 检查率限制
        if not check_rate_limit(client_ip, user_id):
            raise AuthError("认证失败次数过多，请稍后重试", status_code=429)
        
        # 验证用户ID格式
        if not user_id.startswith("u") or not user_id[1:].isdigit():
            record_failed_attempt(client_ip, user_id)
            raise AuthError("无效的用户ID格式")
        
        # 这里应该验证用户是否存在于数据库
        # 暂时接受所有格式正确的用户ID
        return user_id
    
    # 3. 无认证信息
    raise AuthError("需要认证信息")


async def require_admin(current_user: str = Depends(get_current_user_enhanced)) -> str:
    """需要管理员权限"""
    # 这里应该从数据库检查用户角色
    # 暂时硬编码管理员用户
    if current_user not in ["u1", "admin"]:
        raise AuthError("需要管理员权限", status_code=403)
    
    return current_user


async def require_project_access(
    project_id: str,
    current_user: str = Depends(get_current_user_enhanced)
) -> str:
    """检查项目访问权限"""
    # 这里应该检查用户是否有访问该项目的权限
    # 暂时允许所有已认证用户访问所有项目
    return current_user


class EnhancedAuthMiddleware:
    """增强的认证中间件"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, request: Request, call_next):
        # 记录请求信息
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        # 白名单路径（不需要认证）
        white_list = [
            "/health", "/docs", "/redoc", "/openapi.json",
            "/api/v1/auth/login", "/api/v1/auth/register"
        ]
        
        if request.url.path in white_list:
            response = await call_next(request)
        else:
            try:
                # 验证认证
                await get_current_user_enhanced(request, await security(request))
                response = await call_next(request)
                
            except AuthError as e:
                # 记录认证失败
                process_time = time.time() - start_time
                logger.warning(
                    f"认证失败: {request.method} {request.url.path} | "
                    f"客户端: {client_ip} | 原因: {e.detail} | "
                    f"耗时: {process_time:.3f}s"
                )
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
            except Exception as e:
                # 记录其他错误
                process_time = time.time() - start_time
                logger.error(
                    f"认证异常: {request.method} {request.url.path} | "
                    f"客户端: {client_ip} | 错误: {e} | "
                    f"耗时: {process_time:.3f}s"
                )
                return JSONResponse(
                    status_code=500,
                    content={"detail": "内部服务器错误"}
                )
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# 工具函数
def login_user(user_id: str, password: str) -> dict:
    """
    用户登录
    返回访问令牌和刷新令牌
    """
    # 这里应该从数据库验证用户密码
    # 暂时硬编码演示
    fake_users = {
        "u1": get_password_hash("password123"),
        "admin": get_password_hash("admin123")
    }
    
    if user_id not in fake_users:
        raise AuthError("用户不存在")
    
    if not verify_password(password, fake_users[user_id]):
        raise AuthError("密码错误")
    
    # 创建令牌
    access_token_expires = timedelta(
        minutes=settings.security.jwt_access_token_expire_minutes
    )
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(
        days=settings.security.jwt_refresh_token_expire_days
    )
    refresh_token = create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=refresh_token_expires
    )
    
    # 保存会话
    session_key = f"{user_id}:{access_token[-8:]}"
    _user_sessions[session_key] = {
        "user_id": user_id,
        "created_at": datetime.now(),
        "last_activity": datetime.now()
    }
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


from fastapi.responses import JSONResponse