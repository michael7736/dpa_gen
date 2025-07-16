#!/usr/bin/env python3
"""创建AAG相关数据库表"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.postgresql import get_session
from sqlalchemy import text
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def create_aag_tables():
    """创建AAG相关的数据库表"""
    try:
        # 获取数据库连接
        async with get_session() as session:
            # 读取SQL文件
            sql_file = Path(__file__).parent / 'create_aag_tables_simple.sql'
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 将SQL内容分割成独立的语句
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            # 执行每个SQL语句
            for statement in sql_statements:
                if statement:
                    logger.info(f"执行SQL: {statement[:50]}...")
                    await session.execute(text(statement))
            
            # 提交事务
            await session.commit()
            logger.info("AAG数据库表创建成功！")
            
            # 验证表是否创建成功
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('document_metadata_v2', 'analysis_artifacts', 'analysis_tasks')
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            logger.info(f"已创建的AAG表: {[table[0] for table in tables]}")
            
    except Exception as e:
        logger.error(f"创建AAG表失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(create_aag_tables())