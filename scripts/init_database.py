#!/usr/bin/env python3
"""
初始化数据库表结构
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.database.postgres import engine, Base, init_database
from src.models.memory import Memory
from src.config.settings import get_settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def create_tables():
    """创建所有数据库表"""
    try:
        logger.info("开始创建数据库表...")
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # 先删除旧表
            await conn.run_sync(Base.metadata.create_all)  # 创建新表
            
        logger.info("✅ 数据库表创建成功")
        
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {e}")
        raise


async def main():
    """主函数"""
    print("🗄️  初始化DPA数据库...")
    
    try:
        # 创建表
        await create_tables()
        
        # 关闭引擎
        await engine.dispose()
        
        print("✅ 数据库初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())