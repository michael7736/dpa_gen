#!/usr/bin/env python3
"""
添加AAG相关的数据库列
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.postgresql import get_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_aag_columns():
    """为documents表添加AAG相关列"""
    engine = get_engine()
    
    with engine.connect() as conn:
        # 添加AAG相关列
        alter_statements = [
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_skim_summary BOOLEAN DEFAULT FALSE",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_progressive_summary BOOLEAN DEFAULT FALSE", 
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_knowledge_graph BOOLEAN DEFAULT FALSE",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_outline BOOLEAN DEFAULT FALSE",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS has_deep_analysis BOOLEAN DEFAULT FALSE",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS aag_metadata JSONB DEFAULT '{}'",
        ]
        
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
                logger.info(f"✅ 执行成功: {stmt}")
            except Exception as e:
                logger.error(f"❌ 执行失败: {stmt} - {str(e)}")
                conn.rollback()
        
        # 检查documents表结构
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documents'
            AND column_name LIKE '%aag%' OR column_name LIKE 'has_%'
            ORDER BY ordinal_position
        """))
        
        logger.info("\n当前documents表AAG相关列：")
        for row in result:
            logger.info(f"  - {row[0]}: {row[1]}")

if __name__ == "__main__":
    logger.info("🚀 开始添加AAG相关列...")
    
    try:
        add_aag_columns()
        logger.info("\n✅ AAG列添加完成！")
    except Exception as e:
        logger.error(f"\n❌ 添加失败: {str(e)}")
        sys.exit(1)