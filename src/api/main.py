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

from ..config.settings import get_settings
from ..database.postgresql import get_db_session
from ..database.qdrant_client import get_qdrant_manager
from ..database.neo4j_client import get_neo4j_manager
from ..graphs.document_processing_agent_simple import get_document_processing_agent
# from ..graphs.research_planning_agent import get_research_planning_agent
from ..utils.logger import get_logger

# 导入路由
from .routes import documents, projects, research, knowledge, health, qa, metadata, memory, analysis, enhanced_qa
from .routes import documents_simple  # 简化的文档路由，用于测试
from .routes import demo  # 演示路由，展示限流和版本控制

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
        neo4j_manager = get_neo4j_manager()
        await neo4j_manager.create_indexes()
        
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
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加限流中间件
from .middleware import RateLimitMiddleware, VersioningMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000
)

# 添加版本控制中间件
app.add_middleware(VersioningMiddleware)


# 全局异常处理器
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
# app.include_router(documents.router, prefix="/api/v1", tags=["文档管理"])  # 原始文档路由
app.include_router(documents_simple.router, tags=["文档管理"])  # 使用简化版本进行测试
app.include_router(research.router, prefix="/api/v1", tags=["研究规划"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["知识管理"])
app.include_router(qa.router, tags=["知识问答"])  # 已包含/api/v1前缀
app.include_router(enhanced_qa.router, tags=["增强问答"])  # 已包含/api/v1前缀
app.include_router(metadata.router, tags=["元数据管理"])  # 已包含/api/v1前缀
app.include_router(memory.router, tags=["记忆系统"])  # 已包含/api/v1前缀
app.include_router(analysis.router, tags=["文档分析"])  # 已包含/api/v1前缀
app.include_router(demo.router, prefix="/api/v1", tags=["演示"])  # 演示限流和版本控制


# WebSocket支持（用于实时通信）
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket, client_id: str):
    """WebSocket端点 - 实时通信"""
    await websocket.accept()
    
    logger.info(f"WebSocket连接建立: {client_id}")
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            # 这里可以处理实时消息
            logger.info(f"收到WebSocket消息: {client_id} -> {data}")
            
            # 回复消息
            await websocket.send_text(f"服务器收到: {data}")
            
    except Exception as e:
        logger.error(f"WebSocket连接异常: {client_id} -> {e}")
    finally:
        logger.info(f"WebSocket连接关闭: {client_id}")


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