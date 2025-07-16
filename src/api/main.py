"""
DPA智能知识引擎 - FastAPI主应用
整合文档处理、研究规划、知识索引等核心功能
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from ..config.settings import get_settings
from ..database.postgresql import get_db_session
from ..database.qdrant import get_qdrant_manager
from ..database.neo4j_client import get_neo4j_manager
from ..graphs.document_processing_agent_simple import get_document_processing_agent
# from ..graphs.research_planning_agent import get_research_planning_agent
from ..utils.logger import get_logger

# 确保所有模型都被导入
from ..models import *

# 导入路由
from .routes import documents, projects, health, qa, metadata, memory, analysis, enhanced_qa, conversations, qa_with_history
from .routes import documents_simple  # 简化的文档路由，用于测试
from .routes import documents_v2  # V2文档路由，支持用户选择处理选项
from .routes import document_processing  # 文档二次处理路由
from .routes import demo  # 演示路由，展示限流和版本控制
from .routes import memory_workflow  # 记忆工作流路由
from .routes import memory_bank  # Memory Bank路由
from .routes import document_processor  # 文档处理路由
from .routes import hybrid_retrieval  # 混合检索路由
from .routes import mvp_qa  # MVP问答路由
from .routes import fast_qa  # 快速问答路由 - 优化响应时间
from .routes import ultra_fast_qa  # 超快速问答路由 - <1秒响应
from .routes import cognitive  # V3认知系统API桥接层
from .routes import websocket_routes  # WebSocket路由
from .routes import aag  # AAG分析增强生成路由
from .routes import document_operations  # 文档操作路由
# from .routes import auth_demo  # 认证演示路由 - 暂时禁用，缺少jose依赖

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动DPA智能知识引擎...")
    
    try:
        # 初始化数据库连接
        qdrant_manager = get_qdrant_manager()
        neo4j_manager = get_neo4j_manager()
        
        # 创建必要的集合和索引
        await initialize_databases()
        
        logger.info("✅ 数据库初始化完成")
        
        # 初始化智能体
        doc_agent = get_document_processing_agent()
        # research_agent = get_research_planning_agent()
        
        logger.info("✅ 智能体初始化完成")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise
    finally:
        # 清理资源
        logger.info("🔄 正在关闭应用...")
        try:
            await neo4j_manager.close()
            logger.info("✅ 应用关闭完成")
        except Exception as e:
            logger.error(f"❌ 应用关闭异常: {e}")


async def initialize_databases():
    """初始化数据库"""
    try:
        # 初始化Qdrant集合
        qdrant_manager = get_qdrant_manager()
        
        collections = [
            ("documents", settings.ai_model.embedding_dimension),
            ("chunks", settings.ai_model.embedding_dimension),
            ("entities", settings.ai_model.embedding_dimension),
        ]
        
        for collection_name, vector_size in collections:
            await qdrant_manager.create_collection(collection_name, vector_size)
        
        # 初始化Neo4j索引
        try:
            neo4j_manager = get_neo4j_manager()
            await neo4j_manager.create_indexes()
        except Exception as e:
            logger.warning(f"Neo4j初始化失败，继续启动: {e}")
            # 继续启动，不因为Neo4j失败而阻塞
        
        logger.info("✅ 数据库初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise


# 创建FastAPI应用
app = FastAPI(
    title="DPA智能知识引擎",
    description="基于大语言模型的智能知识引擎系统，支持文档处理、研究规划、知识图谱构建等功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8230",
        "http://localhost:8031",  # Next.js 前端
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8230",
        "http://127.0.0.1:8031",
        "http://cnllm:3000",
        "http://cnllm:8230",
        "http://120.26.11.30:3000",
        "http://120.26.11.30:8230"
    ],  # 具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 添加限流中间件
from .middleware import RateLimitMiddleware, VersioningMiddleware
from .middleware.auth import UserAuthMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000
)

# 添加版本控制中间件
app.add_middleware(VersioningMiddleware)

# 添加用户认证中间件（为多用户预埋）
app.add_middleware(UserAuthMiddleware)


# 导入增强的错误处理器 - 暂时禁用，需要先安装依赖
# from .middleware.error_handler import (
#     APIError,
#     api_error_handler,
#     http_exception_handler as enhanced_http_handler,
#     validation_error_handler,
#     generic_exception_handler
# )

# 注册错误处理器 - 暂时使用默认处理器
# app.add_exception_handler(APIError, api_error_handler)
# app.add_exception_handler(RequestValidationError, validation_error_handler)
# app.add_exception_handler(HTTPException, enhanced_http_handler)
# app.add_exception_handler(Exception, generic_exception_handler)

# 恢复原有的异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "内部服务器错误",
            "message": str(exc) if settings.debug else "系统出现异常，请稍后重试",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# 中间件：请求日志
@app.middleware("http")
async def log_requests(request, call_next):
    """请求日志中间件"""
    import time
    import uuid
    
    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    logger.info(
        f"请求开始: {request.method} {request.url} | Request ID: {request_id}"
    )
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        logger.info(
            f"请求完成: {request.method} {request.url} | "
            f"状态码: {response.status_code} | "
            f"耗时: {process_time:.3f}s | "
            f"Request ID: {request_id}"
        )
        
        # 添加响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        logger.error(
            f"请求异常: {request.method} {request.url} | "
            f"错误: {e} | "
            f"耗时: {process_time:.3f}s | "
            f"Request ID: {request_id}"
        )
        
        raise


# 全局OPTIONS处理器，解决CORS预检请求问题
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """处理所有OPTIONS请求，解决CORS预检问题"""
    return {"message": "OK"}


# 根路径
@app.get("/", tags=["根目录"])
async def root():
    """根路径 - 系统信息"""
    return {
        "name": "DPA智能知识引擎",
        "version": "1.0.0",
        "description": "基于大语言模型的智能知识引擎系统",
        "status": "运行中",
        "docs_url": "/docs",
        "health_check": "/health"
    }


# 系统状态检查
@app.get("/health", tags=["系统状态"])
async def health_check():
    """系统健康检查"""
    try:
        # 检查数据库连接
        qdrant_manager = get_qdrant_manager()
        neo4j_manager = get_neo4j_manager()
        
        # 简单的连接测试
        qdrant_status = "healthy"
        neo4j_status = "healthy"
        
        try:
            await qdrant_manager.collection_exists("test")
        except:
            qdrant_status = "unhealthy"
        
        try:
            await neo4j_manager.execute_query("RETURN 1")
        except:
            neo4j_status = "unhealthy"
        
        overall_status = "healthy" if all([
            qdrant_status == "healthy",
            neo4j_status == "healthy"
        ]) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": asyncio.get_event_loop().time(),
            "services": {
                "qdrant": qdrant_status,
                "neo4j": neo4j_status,
                "api": "healthy"
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["健康检查"])
app.include_router(projects.router, prefix="/api/v1", tags=["项目管理"])
app.include_router(documents.router, prefix="/api/v1", tags=["文档管理"])
app.include_router(documents_v2.router, tags=["文档管理V2"])  # V2版本，支持处理选项
app.include_router(document_processing.router, tags=["文档处理"])  # 文档二次处理
app.include_router(conversations.router, tags=["对话管理"])
app.include_router(documents_simple.router, tags=["文档管理"])  # 使用简化版本进行测试
app.include_router(document_operations.router, tags=["文档操作"])  # 文档操作API
# app.include_router(research.router, prefix="/api/v1", tags=["研究规划"])  # 尚未实现
# app.include_router(knowledge.router, prefix="/api/v1", tags=["知识管理"])  # 尚未实现
app.include_router(qa.router, tags=["知识问答"])  # 已包含/api/v1前缀
app.include_router(enhanced_qa.router, tags=["增强问答"])  # 已包含/api/v1前缀
app.include_router(qa_with_history.router, tags=["对话问答"])  # 带对话历史的问答
app.include_router(metadata.router, tags=["元数据管理"])  # 已包含/api/v1前缀
app.include_router(memory.router, tags=["记忆系统"])  # 已包含/api/v1前缀
app.include_router(memory_workflow.router, tags=["记忆工作流"])  # 认知工作流API
app.include_router(memory_bank.router, tags=["Memory Bank"])  # Memory Bank管理
app.include_router(document_processor.router, tags=["文档处理"])  # MVP文档处理
app.include_router(hybrid_retrieval.router, tags=["混合检索"])  # 三阶段混合检索
app.include_router(mvp_qa.router, tags=["MVP问答"])  # MVP问答系统
app.include_router(fast_qa.router, tags=["快速问答"])  # 优化问答系统 - 响应时间<1秒
app.include_router(ultra_fast_qa.router, tags=["超快问答"])  # 超快问答系统 - 极速响应
app.include_router(analysis.router, tags=["文档分析"])  # 已包含/api/v1前缀
app.include_router(cognitive.router, prefix="/api/v1", tags=["V3认知系统"])  # V3认知系统API桥接层
app.include_router(demo.router, prefix="/api/v1", tags=["演示"])  # 演示限流和版本控制
app.include_router(websocket_routes.router, prefix="/api/v1", tags=["WebSocket通信"])  # WebSocket路由
app.include_router(aag.router, tags=["AAG分析"])  # AAG分析增强生成路由
# app.include_router(auth_demo.router, tags=["认证演示"])  # 增强认证和错误处理演示 - 暂时禁用


if __name__ == "__main__":
    # 开发环境启动
    uvicorn.run(
        "src.api.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
        access_log=True
    ) 