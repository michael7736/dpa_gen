#!/usr/bin/env python3
"""
检查文档在数据库中的状态
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DOCUMENT_ID = "5ec3e004-ab9c-40af-9ed3-0837fddfc628"

async def check_document():
    # 连接数据库
    DATABASE_URL = os.getenv("DATABASE_URL")
    # 转换URL格式以适配asyncpg
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # 1. 检查文档是否存在
        print("1. 检查文档表...")
        doc_query = """
        SELECT id, filename, processing_status, created_at, project_id 
        FROM documents 
        WHERE id = $1
        """
        doc = await conn.fetchrow(doc_query, DOCUMENT_ID)
        
        if doc:
            print(f"   ✅ 文档存在")
            print(f"   文件名: {doc['filename']}")
            print(f"   状态: {doc['processing_status']}")
            print(f"   项目ID: {doc['project_id']}")
            print(f"   创建时间: {doc['created_at']}")
        else:
            print(f"   ❌ 文档不存在")
            
            # 查看最近的文档
            print("\n   最近的文档:")
            recent_query = """
            SELECT id, filename, processing_status, created_at 
            FROM documents 
            ORDER BY created_at DESC 
            LIMIT 5
            """
            recent_docs = await conn.fetch(recent_query)
            for doc in recent_docs:
                print(f"   - {doc['id']}: {doc['filename']} ({doc['processing_status']})")
        
        # 2. 检查处理管道
        print("\n2. 检查处理管道...")
        pipeline_query = """
        SELECT id, document_id, completed, interrupted, overall_progress, current_stage, created_at
        FROM processing_pipelines
        WHERE document_id = $1
        ORDER BY created_at DESC
        LIMIT 3
        """
        pipelines = await conn.fetch(pipeline_query, DOCUMENT_ID)
        
        if pipelines:
            print(f"   找到 {len(pipelines)} 个管道")
            for p in pipelines:
                print(f"   - 管道ID: {p['id']}")
                print(f"     完成: {p['completed']}, 中断: {p['interrupted']}")
                print(f"     进度: {p['overall_progress']}%")
                print(f"     当前阶段: {p['current_stage']}")
                print(f"     创建时间: {p['created_at']}")
        else:
            print("   没有找到管道记录")
            
            # 查看最近的管道
            print("\n   最近的管道:")
            recent_pipeline_query = """
            SELECT id, document_id, completed, current_stage, created_at
            FROM processing_pipelines
            ORDER BY created_at DESC
            LIMIT 5
            """
            recent_pipelines = await conn.fetch(recent_pipeline_query)
            for p in recent_pipelines:
                print(f"   - {p['id']}: 文档 {p['document_id']} ({p['current_stage']})")
        
    finally:
        await conn.close()

async def main():
    print("🔍 数据库文档检查")
    print("=" * 50)
    print(f"目标文档ID: {DOCUMENT_ID}")
    await check_document()

if __name__ == "__main__":
    asyncio.run(main())