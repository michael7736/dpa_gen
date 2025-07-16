#!/usr/bin/env python3
"""测试文档处理流程"""

import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(str(Path(__file__).parent))

from src.graphs.simplified_document_processor import SimplifiedDocumentProcessor
from src.database.postgresql import get_db_session
from src.models.project import Project
from src.models.document import Document
import uuid

async def test_document_processing():
    """测试文档处理"""
    
    # 获取数据库会话
    db = next(get_db_session())
    
    try:
        # 获取AI研究项目
        project = db.query(Project).filter(Project.name == "AI研究项目").first()
        if not project:
            print("未找到AI研究项目")
            return
        
        print(f"找到项目: {project.name} (ID: {project.id})")
        
        # 创建文档处理器
        processor = SimplifiedDocumentProcessor()
        
        # 准备处理参数
        file_path = "test_document.txt"
        doc_id = str(uuid.uuid4())
        
        print(f"\n开始处理文档: {file_path}")
        print(f"文档ID: {doc_id}")
        
        # 处理文档
        result = await processor.process_document({
            "document_id": doc_id,
            "project_id": str(project.id),
            "file_path": file_path,
            "file_name": "test_document.txt",
            "file_type": "text",
            "user_id": str(project.user_id)
        })
        
        print("\n处理结果:")
        print(f"返回数据: {result}")
        if result.get('success'):
            print(f"状态: {result.get('status', 'N/A')}")
            print(f"处理时间: {result.get('processing_time', 0):.2f}秒")
            print(f"元数据: {result.get('metadata', {})}")
        
        if result.get('status') == 'completed':
            # 查询保存的文档
            saved_doc = db.query(Document).filter(Document.id == doc_id).first()
            if saved_doc:
                print(f"\n文档已保存到数据库:")
                print(f"  文件名: {saved_doc.file_name}")
                print(f"  状态: {saved_doc.status}")
                print(f"  文件大小: {saved_doc.file_size} bytes")
            else:
                print("\n警告: 文档未保存到数据库")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("开始测试文档处理流程...")
    asyncio.run(test_document_processing())