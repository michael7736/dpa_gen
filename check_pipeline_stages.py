#!/usr/bin/env python3
"""
检查管道阶段详情
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

PIPELINE_ID = "90e411d2-6131-4688-8bce-935afd4d2336"  # 最新的管道

async def check_pipeline():
    # 连接数据库
    DATABASE_URL = os.getenv("DATABASE_URL")
    # 转换URL格式以适配asyncpg
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # 检查管道阶段
        print("检查管道阶段详情...")
        stage_query = """
        SELECT id, stage_type, status, progress, started_at, completed_at, duration, 
               message, error, result
        FROM pipeline_stages
        WHERE pipeline_id = $1
        ORDER BY id
        """
        stages = await conn.fetch(stage_query, PIPELINE_ID)
        
        if stages:
            print(f"找到 {len(stages)} 个阶段:")
            for stage in stages:
                print(f"\n阶段: {stage['stage_type']}")
                print(f"  状态: {stage['status']}")
                print(f"  进度: {stage['progress']}%")
                print(f"  开始时间: {stage['started_at']}")
                print(f"  完成时间: {stage['completed_at']}")
                print(f"  耗时: {stage['duration']}秒")
                print(f"  消息: {stage['message']}")
                if stage['error']:
                    print(f"  错误: {stage['error']}")
                if stage['result']:
                    print(f"  结果摘要: {str(stage['result'])[:200]}...")
        else:
            print("没有找到阶段记录")
            
    finally:
        await conn.close()

async def main():
    print("🔍 管道阶段检查")
    print("=" * 50)
    print(f"管道ID: {PIPELINE_ID}")
    await check_pipeline()

if __name__ == "__main__":
    asyncio.run(main())