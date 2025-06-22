"""
数据库初始化脚本
用于创建数据库表结构和初始化向量数据库集合
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.database.postgresql import create_tables, get_engine
from src.database.qdrant_client import init_qdrant_collection
from src.database.neo4j_client import init_neo4j_constraints
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def setup_postgresql():
    """初始化PostgreSQL数据库"""
    try:
        logger.info("开始初始化PostgreSQL数据库...")
        
        # 创建数据库引擎
        engine = get_engine()
        
        # 创建所有表
        await create_tables(engine)
        
        logger.info("✅ PostgreSQL数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL数据库初始化失败: {e}")
        return False


async def setup_qdrant():
    """初始化Qdrant向量数据库"""
    try:
        logger.info("开始初始化Qdrant向量数据库...")
        
        # 初始化集合
        success = await init_qdrant_collection()
        
        if success:
            logger.info("✅ Qdrant向量数据库初始化完成")
            return True
        else:
            logger.error("❌ Qdrant向量数据库初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ Qdrant向量数据库初始化失败: {e}")
        return False


async def setup_neo4j():
    """初始化Neo4j图数据库"""
    try:
        logger.info("开始初始化Neo4j图数据库...")
        
        # 创建约束和索引
        success = await init_neo4j_constraints()
        
        if success:
            logger.info("✅ Neo4j图数据库初始化完成")
            return True
        else:
            logger.error("❌ Neo4j图数据库初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ Neo4j图数据库初始化失败: {e}")
        return False


def check_environment():
    """检查环境配置"""
    logger.info("检查环境配置...")
    
    required_vars = [
        "DATABASE_URL",
        "QDRANT_URL", 
        "NEO4J_URL",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("请检查 .env 文件或环境变量配置")
        return False
    
    logger.info("✅ 环境配置检查通过")
    return True


async def main():
    """主函数"""
    logger.info("🚀 开始数据库初始化...")
    
    # 检查环境配置
    if not check_environment():
        sys.exit(1)
    
    # 初始化各个数据库
    tasks = []
    
    # PostgreSQL初始化
    tasks.append(("PostgreSQL", setup_postgresql()))
    
    # Qdrant初始化
    tasks.append(("Qdrant", setup_qdrant()))
    
    # Neo4j初始化
    tasks.append(("Neo4j", setup_neo4j()))
    
    # 并行执行初始化
    results = []
    for name, task in tasks:
        try:
            result = await task
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ {name} 初始化异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    logger.info(f"\n📊 数据库初始化结果汇总:")
    for name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"  {name}: {status}")
    
    if success_count == total_count:
        logger.info(f"\n🎉 所有数据库初始化完成! ({success_count}/{total_count})")
        logger.info("现在可以启动DPA应用了")
    else:
        logger.error(f"\n⚠️  部分数据库初始化失败 ({success_count}/{total_count})")
        logger.info("请检查失败的数据库配置和连接")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 