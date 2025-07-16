#!/usr/bin/env python3
"""
更新数据库表结构脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.postgresql import get_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_projects_table():
    """更新projects表结构"""
    engine = get_engine()
    
    with engine.connect() as conn:
        # 添加缺失的列
        alter_statements = [
            # 基础枚举类型
            """
            DO $$ BEGIN
                CREATE TYPE projecttype AS ENUM ('research', 'analysis', 'report', 'documentation', 'custom');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """,
            """
            DO $$ BEGIN
                CREATE TYPE projectstatus AS ENUM ('draft', 'planning', 'executing', 'paused', 'completed', 'archived', 'cancelled');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """,
            
            # 添加缺失的列
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS type projecttype DEFAULT 'research'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS status projectstatus DEFAULT 'draft'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS template_id UUID",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS quality_gates JSONB DEFAULT '{\"accuracy\": 0.8, \"completeness\": 0.9, \"relevance\": 0.85}'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS objectives TEXT[] DEFAULT '{}'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS constraints TEXT[] DEFAULT '{}'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS execution_plan JSONB DEFAULT '{}'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS estimated_duration INTEGER",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS actual_duration INTEGER",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS progress FLOAT DEFAULT 0.0",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS quality_score FLOAT DEFAULT 0.0",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS success_rate FLOAT DEFAULT 0.0",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS started_at TIMESTAMP",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP",
        ]
        
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
                logger.info(f"✅ 执行成功: {stmt[:50]}...")
            except Exception as e:
                logger.error(f"❌ 执行失败: {stmt[:50]}... - {str(e)}")
                conn.rollback()
        
        # 检查表结构
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            ORDER BY ordinal_position
        """))
        
        logger.info("\n当前projects表结构：")
        for row in result:
            logger.info(f"  - {row[0]}: {row[1]}")

def update_users_table():
    """确保users表存在"""
    engine = get_engine()
    
    with engine.connect() as conn:
        # 检查users表是否存在
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """))
        
        if not result.scalar():
            # 创建users表
            conn.execute(text("""
                CREATE TABLE users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    full_name VARCHAR(200),
                    hashed_password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
                    preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            logger.info("✅ 创建users表成功")
            
            # 创建默认用户
            conn.execute(text("""
                INSERT INTO users (id, email, username, hashed_password, is_active, is_superuser)
                VALUES ('u1'::UUID, 'default@dpa.ai', 'default', 'hashed_password', true, true)
                ON CONFLICT (id) DO NOTHING
            """))
            conn.commit()
            logger.info("✅ 创建默认用户成功")

if __name__ == "__main__":
    logger.info("🚀 开始更新数据库表结构...")
    
    try:
        update_users_table()
        update_projects_table()
        logger.info("\n✅ 数据库表结构更新完成！")
    except Exception as e:
        logger.error(f"\n❌ 更新失败: {str(e)}")
        sys.exit(1)