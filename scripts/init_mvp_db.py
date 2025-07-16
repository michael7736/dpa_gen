#!/usr/bin/env python3
"""
初始化MVP数据库
设置PostgreSQL表、Neo4j索引、Qdrant集合等
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.database.postgres import engine, Base, get_async_session
from src.database.qdrant_manager import QdrantManager
from src.database.neo4j_manager import neo4j_manager
from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def init_postgres():
    """初始化PostgreSQL数据库"""
    logger.info("Initializing PostgreSQL...")
    
    try:
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # 创建LangGraph所需的表
        async with get_async_session() as session:
            # 检查点表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    parent_id TEXT,
                    checkpoint JSONB NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (thread_id, checkpoint_id)
                );
            """))
            
            # 写入日志表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS langgraph_writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    value JSONB,
                    PRIMARY KEY (thread_id, checkpoint_id, task_id, idx)
                );
            """))
            
            # 添加索引
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id 
                ON langgraph_checkpoints(thread_id);
            """))
            
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_writes_thread_checkpoint 
                ON langgraph_writes(thread_id, checkpoint_id);
            """))
            
            # 为多用户预埋 - 所有表添加user_id索引
            tables_to_index = ['memories', 'documents', 'projects', 'conversations']
            for table in tables_to_index:
                try:
                    await session.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table}_user_id 
                        ON {table}(user_id);
                    """))
                    
                    await session.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table}_user_project 
                        ON {table}(user_id, project_id);
                    """))
                except Exception as e:
                    logger.warning(f"Index creation for {table} failed (might not exist): {e}")
                    
            await session.commit()
            
        logger.info("✓ PostgreSQL initialized successfully")
        
    except Exception as e:
        logger.error(f"PostgreSQL initialization failed: {e}")
        raise


async def init_qdrant():
    """初始化Qdrant向量数据库"""
    logger.info("Initializing Qdrant...")
    
    try:
        qdrant = QdrantManager()
        
        # 创建默认集合
        collections = [
            "project_default",  # 默认项目集合
            "project_test",     # 测试项目集合
        ]
        
        for collection_name in collections:
            exists = await qdrant.collection_exists(collection_name)
            if not exists:
                await qdrant.create_collection(
                    collection_name=collection_name,
                    vector_size=1536  # OpenAI embedding size
                )
                logger.info(f"✓ Created collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")
                
        logger.info("✓ Qdrant initialized successfully")
        
    except Exception as e:
        logger.error(f"Qdrant initialization failed: {e}")
        raise


async def init_neo4j():
    """初始化Neo4j图数据库"""
    logger.info("Initializing Neo4j...")
    
    try:
        # 连接Neo4j
        await neo4j_manager.connect()
        
        # 创建约束和索引
        async with neo4j_manager.session() as session:
            # 唯一约束
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"✓ Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint creation failed (might exist): {e}")
                    
            # 索引（为多用户预埋）
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.user_id)",
                "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.project_id)",
                "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.user_id, m.project_id)",
                "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.user_id)",
                "CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.user_id)",
            ]
            
            for index in indexes:
                try:
                    await session.run(index)
                    logger.info(f"✓ Created index: {index}")
                except Exception as e:
                    logger.warning(f"Index creation failed (might exist): {e}")
                    
        logger.info("✓ Neo4j initialized successfully")
        
    except Exception as e:
        logger.error(f"Neo4j initialization failed: {e}")
        raise
    finally:
        await neo4j_manager.disconnect()


async def init_memory_bank():
    """初始化Memory Bank目录结构"""
    logger.info("Initializing Memory Bank...")
    
    try:
        # 创建基础目录
        base_path = Path(settings.paths.memory_bank)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # 创建操作日志目录
        (base_path / "operation_logs").mkdir(exist_ok=True)
        (base_path / "operation_logs" / "u1").mkdir(exist_ok=True)  # 默认用户
        
        # 创建默认项目目录
        default_project = base_path / "project_default"
        default_project.mkdir(exist_ok=True)
        
        # 创建初始文件
        files = {
            "metadata.json": '{"created_at": "2024-01-01T00:00:00", "version": "1.0.0"}',
            "context.md": "# Project Context\n\n",
            "concepts.json": "[]",
            "summary.md": "# Project Summary\n\n",
        }
        
        for filename, content in files.items():
            filepath = default_project / filename
            if not filepath.exists():
                filepath.write_text(content)
                logger.info(f"✓ Created file: {filepath}")
                
        logger.info("✓ Memory Bank initialized successfully")
        
    except Exception as e:
        logger.error(f"Memory Bank initialization failed: {e}")
        raise


async def verify_initialization():
    """验证初始化结果"""
    logger.info("\nVerifying initialization...")
    
    results = {
        "PostgreSQL": False,
        "Qdrant": False,
        "Neo4j": False,
        "Memory Bank": False
    }
    
    # 检查PostgreSQL
    try:
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            results["PostgreSQL"] = True
    except Exception as e:
        logger.error(f"PostgreSQL check failed: {e}")
        
    # 检查Qdrant
    try:
        qdrant = QdrantManager()
        exists = await qdrant.collection_exists("project_default")
        results["Qdrant"] = exists
    except Exception as e:
        logger.error(f"Qdrant check failed: {e}")
        
    # 检查Neo4j
    try:
        results["Neo4j"] = await neo4j_manager.check_health()
    except Exception as e:
        logger.error(f"Neo4j check failed: {e}")
        
    # 检查Memory Bank
    memory_bank_path = Path(settings.paths.memory_bank) / "project_default" / "metadata.json"
    results["Memory Bank"] = memory_bank_path.exists()
    
    # 打印结果
    logger.info("\n=== Initialization Results ===")
    for component, status in results.items():
        status_str = "✓ OK" if status else "✗ FAILED"
        logger.info(f"{component}: {status_str}")
        
    all_ok = all(results.values())
    if all_ok:
        logger.info("\n✅ All components initialized successfully!")
    else:
        logger.error("\n❌ Some components failed to initialize!")
        
    return all_ok


async def main():
    """主函数"""
    logger.info("=== DPA MVP Database Initialization ===\n")
    
    try:
        # 初始化各组件
        await init_postgres()
        await init_qdrant()
        await init_neo4j()
        await init_memory_bank()
        
        # 验证结果
        success = await verify_initialization()
        
        if success:
            logger.info("\n🎉 MVP database initialization completed successfully!")
            logger.info("\nYou can now start the API server with:")
            logger.info("  uvicorn src.api.main:app --reload")
        else:
            logger.error("\n💥 Initialization failed! Please check the logs.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n💥 Fatal error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())