#!/usr/bin/env python3
"""
修复数据库enum类型的脚本
将小写的enum值改为大写，以匹配SQLAlchemy的枚举名称
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.postgresql import get_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_enum_types():
    """修复enum类型"""
    engine = get_engine()
    
    with engine.connect() as conn:
        # 修复projecttype枚举
        fix_statements = [
            # 1. 创建临时列
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS type_temp VARCHAR(50)",
            
            # 2. 复制数据到临时列
            "UPDATE projects SET type_temp = type::text WHERE type IS NOT NULL",
            
            # 3. 删除原始列
            "ALTER TABLE projects DROP COLUMN IF EXISTS type",
            
            # 4. 删除旧的enum类型
            "DROP TYPE IF EXISTS projecttype CASCADE",
            
            # 5. 创建新的enum类型（大写）
            "CREATE TYPE projecttype AS ENUM ('RESEARCH', 'ANALYSIS', 'REPORT', 'DOCUMENTATION', 'CUSTOM')",
            
            # 6. 添加新列
            "ALTER TABLE projects ADD COLUMN type projecttype",
            
            # 7. 将数据转换回来（小写转大写）
            """
            UPDATE projects SET type = 
                CASE 
                    WHEN type_temp = 'research' THEN 'RESEARCH'::projecttype
                    WHEN type_temp = 'analysis' THEN 'ANALYSIS'::projecttype
                    WHEN type_temp = 'report' THEN 'REPORT'::projecttype
                    WHEN type_temp = 'documentation' THEN 'DOCUMENTATION'::projecttype
                    WHEN type_temp = 'custom' THEN 'CUSTOM'::projecttype
                    ELSE 'RESEARCH'::projecttype
                END
            WHERE type_temp IS NOT NULL
            """,
            
            # 8. 设置默认值
            "ALTER TABLE projects ALTER COLUMN type SET DEFAULT 'RESEARCH'",
            
            # 9. 删除临时列
            "ALTER TABLE projects DROP COLUMN IF EXISTS type_temp",
            
            # 同样处理projectstatus
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS status_temp VARCHAR(50)",
            "UPDATE projects SET status_temp = status::text WHERE status IS NOT NULL",
            "ALTER TABLE projects DROP COLUMN IF EXISTS status",
            "DROP TYPE IF EXISTS projectstatus CASCADE",
            "CREATE TYPE projectstatus AS ENUM ('DRAFT', 'PLANNING', 'EXECUTING', 'PAUSED', 'COMPLETED', 'ARCHIVED', 'CANCELLED')",
            "ALTER TABLE projects ADD COLUMN status projectstatus",
            """
            UPDATE projects SET status = 
                CASE 
                    WHEN status_temp = 'draft' THEN 'DRAFT'::projectstatus
                    WHEN status_temp = 'planning' THEN 'PLANNING'::projectstatus
                    WHEN status_temp = 'executing' THEN 'EXECUTING'::projectstatus
                    WHEN status_temp = 'paused' THEN 'PAUSED'::projectstatus
                    WHEN status_temp = 'completed' THEN 'COMPLETED'::projectstatus
                    WHEN status_temp = 'archived' THEN 'ARCHIVED'::projectstatus
                    WHEN status_temp = 'cancelled' THEN 'CANCELLED'::projectstatus
                    ELSE 'DRAFT'::projectstatus
                END
            WHERE status_temp IS NOT NULL
            """,
            "ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'DRAFT'",
            "ALTER TABLE projects DROP COLUMN IF EXISTS status_temp",
        ]
        
        for stmt in fix_statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
                logger.info(f"✅ 执行成功: {stmt[:50]}...")
            except Exception as e:
                logger.error(f"❌ 执行失败: {stmt[:50]}... - {str(e)}")
                conn.rollback()
        
        # 检查enum类型
        result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'projecttype')
            ORDER BY enumsortorder
        """))
        
        logger.info("\n当前projecttype枚举值：")
        for row in result:
            logger.info(f"  - {row[0]}")

if __name__ == "__main__":
    logger.info("🚀 开始修复enum类型...")
    
    try:
        fix_enum_types()
        logger.info("\n✅ Enum类型修复完成！")
    except Exception as e:
        logger.error(f"\n❌ 修复失败: {str(e)}")
        sys.exit(1)