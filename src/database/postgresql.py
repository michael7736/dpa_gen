"""
PostgreSQL数据库连接管理
"""

import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import logging

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 创建基础模型类
Base = declarative_base()

# 异步引擎
async_engine = None
async_session_factory = None

# 同步引擎（用于迁移等）
sync_engine = None
sync_session_factory = None


def get_engine():
    """获取同步数据库引擎"""
    global sync_engine
    if sync_engine is None:
        # 将异步URL转换为同步URL
        sync_url = settings.database.url.replace("postgresql+asyncpg://", "postgresql://")
        sync_engine = create_engine(
            sync_url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            echo=settings.app.debug_sql,
        )
    return sync_engine


def get_async_engine():
    """获取异步数据库引擎"""
    global async_engine
    if async_engine is None:
        # 确保URL使用asyncpg驱动
        async_url = settings.database.url
        if not async_url.startswith("postgresql+asyncpg://"):
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")
        
        async_engine = create_async_engine(
            async_url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            echo=settings.app.debug_sql,
        )
    return async_engine


def get_session_factory():
    """获取同步会话工厂"""
    global sync_session_factory
    if sync_session_factory is None:
        sync_session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return sync_session_factory


def get_async_session_factory():
    """获取异步会话工厂"""
    global async_session_factory
    if async_session_factory is None:
        async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return async_session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话"""
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables(engine=None):
    """创建数据库表"""
    if engine is None:
        engine = get_async_engine()
    
    try:
        # 导入所有模型以确保表被创建
        from ..models import User, Project, Document, Chunk, Conversation, Message
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ 数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库表创建失败: {e}")
        return False


async def test_connection():
    """测试数据库连接"""
    try:
        engine = get_async_engine()
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("✅ PostgreSQL连接测试成功")
                return True
            else:
                logger.error("❌ PostgreSQL连接测试失败: 查询结果异常")
                return False
                
    except Exception as e:
        logger.error(f"❌ PostgreSQL连接测试失败: {e}")
        return False


async def init_database():
    """初始化数据库"""
    logger.info("开始初始化PostgreSQL数据库...")
    
    # 测试连接
    if not await test_connection():
        return False
    
    # 创建表
    if not await create_tables():
        return False
    
    logger.info("✅ PostgreSQL数据库初始化完成")
    return True


async def close_connections():
    """关闭数据库连接"""
    global async_engine, sync_engine
    
    if async_engine:
        await async_engine.dispose()
        async_engine = None
        
    if sync_engine:
        sync_engine.dispose()
        sync_engine = None
        
    logger.info("数据库连接已关闭") 