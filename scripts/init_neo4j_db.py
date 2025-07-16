#!/usr/bin/env python3
"""
初始化Neo4j数据库
创建DPA项目所需的数据库和索引
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from neo4j import AsyncGraphDatabase
from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def create_database():
    """创建Neo4j数据库"""
    logger.info("开始初始化Neo4j数据库...")
    
    # 使用系统数据库连接来创建新数据库
    driver = AsyncGraphDatabase.driver(
        settings.neo4j.url,
        auth=(settings.neo4j.username, settings.neo4j.password),
        database="system"  # 使用系统数据库
    )
    
    try:
        async with driver.session() as session:
            # 检查数据库是否存在
            check_query = "SHOW DATABASES"
            result = await session.run(check_query)
            databases = await result.data()
            
            db_names = [db['name'] for db in databases]
            logger.info(f"现有数据库: {db_names}")
            
            if settings.neo4j.database not in db_names:
                # 创建数据库
                create_query = f"CREATE DATABASE {settings.neo4j.database}"
                logger.info(f"创建数据库: {settings.neo4j.database}")
                await session.run(create_query)
                logger.info(f"✅ 数据库 {settings.neo4j.database} 创建成功")
                
                # 等待数据库启动
                await asyncio.sleep(3)
            else:
                logger.info(f"数据库 {settings.neo4j.database} 已存在")
                
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        logger.info("提示：请确保Neo4j Enterprise版本支持多数据库，或修改配置使用默认的'neo4j'数据库")
        raise
    finally:
        await driver.close()


async def create_indexes():
    """创建索引和约束"""
    logger.info("创建索引和约束...")
    
    # 使用目标数据库连接
    driver = AsyncGraphDatabase.driver(
        settings.neo4j.url,
        auth=(settings.neo4j.username, settings.neo4j.password),
        database=settings.neo4j.database
    )
    
    try:
        async with driver.session() as session:
            # 创建索引
            indexes = [
                # Document节点索引
                "CREATE INDEX doc_id IF NOT EXISTS FOR (d:Document) ON (d.id)",
                "CREATE INDEX doc_project IF NOT EXISTS FOR (d:Document) ON (d.project_id)",
                
                # Chunk节点索引
                "CREATE INDEX chunk_id IF NOT EXISTS FOR (c:Chunk) ON (c.id)",
                "CREATE INDEX chunk_doc IF NOT EXISTS FOR (c:Chunk) ON (c.document_id)",
                
                # Entity节点索引
                "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                
                # Concept节点索引
                "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
                
                # Project节点索引
                "CREATE INDEX project_id IF NOT EXISTS FOR (p:Project) ON (p.id)",
                
                # User节点索引
                "CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)"
            ]
            
            for index_query in indexes:
                try:
                    await session.run(index_query)
                    logger.info(f"✅ 索引创建成功: {index_query.split(' ')[2]}")
                except Exception as e:
                    logger.warning(f"索引创建失败或已存在: {e}")
            
            # 创建约束
            constraints = [
                # 唯一性约束
                "CREATE CONSTRAINT doc_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT chunk_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT project_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT user_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE"
            ]
            
            for constraint_query in constraints:
                try:
                    await session.run(constraint_query)
                    logger.info(f"✅ 约束创建成功: {constraint_query.split(' ')[2]}")
                except Exception as e:
                    logger.warning(f"约束创建失败或已存在: {e}")
                    
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        raise
    finally:
        await driver.close()


async def verify_connection():
    """验证连接"""
    logger.info("验证Neo4j连接...")
    
    driver = AsyncGraphDatabase.driver(
        settings.neo4j.url,
        auth=(settings.neo4j.username, settings.neo4j.password),
        database=settings.neo4j.database
    )
    
    try:
        async with driver.session() as session:
            # 简单查询测试
            result = await session.run("RETURN 1 as test")
            data = await result.single()
            
            if data['test'] == 1:
                logger.info("✅ Neo4j连接验证成功")
                return True
            else:
                logger.error("❌ Neo4j连接验证失败")
                return False
                
    except Exception as e:
        logger.error(f"Neo4j连接失败: {e}")
        return False
    finally:
        await driver.close()


async def main():
    """主函数"""
    logger.info("开始Neo4j数据库初始化")
    logger.info(f"Neo4j URL: {settings.neo4j.url}")
    logger.info(f"目标数据库: {settings.neo4j.database}")
    
    try:
        # 1. 创建数据库（如果需要）
        try:
            await create_database()
        except Exception as e:
            logger.warning(f"数据库创建失败（可能是Community版本）: {e}")
            logger.info("将使用默认的'neo4j'数据库")
            
            # 如果是Community版本，修改设置使用默认数据库
            if "enterprise" not in str(e).lower():
                settings.neo4j.database = "neo4j"
                logger.info("已切换到默认数据库'neo4j'")
        
        # 2. 创建索引
        await create_indexes()
        
        # 3. 验证连接
        success = await verify_connection()
        
        if success:
            logger.info("🎉 Neo4j数据库初始化完成！")
        else:
            logger.error("❌ Neo4j数据库初始化失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"初始化过程发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())