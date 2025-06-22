"""
文档管理API路由
支持文档上传、处理、查询、删除等功能
"""

import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...graphs.document_processing_agent import get_document_processing_agent
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str
    filename: str
    size: int
    status: str
    message: str


class DocumentProcessingConfig(BaseModel):
    """文档处理配置"""
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200
    use_semantic_chunking: Optional[bool] = True
    extract_entities: Optional[bool] = True
    build_knowledge_graph: Optional[bool] = True


class DocumentQuery(BaseModel):
    """文档查询请求"""
    query: str
    document_ids: Optional[List[str]] = None
    limit: Optional[int] = 10
    include_chunks: Optional[bool] = True


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    processing_config: Optional[DocumentProcessingConfig] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    上传文档并开始处理
    
    Args:
        project_id: 项目ID
        file: 上传的文件
        processing_config: 处理配置
        background_tasks: 后台任务
    
    Returns:
        文档上传响应
    """
    try:
        # 验证文件类型
        allowed_types = ['.pdf', '.docx', '.doc', '.txt', '.md']
        file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_extension}. 支持的类型: {', '.join(allowed_types)}"
            )
        
        # 生成文档ID
        document_id = str(uuid4())
        
        # 保存文件
        import os
        import tempfile
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 获取文件信息
        file_size = len(content)
        
        logger.info(f"文档上传成功: {file.filename} ({file_size} bytes)")
        
        # 后台处理文档
        background_tasks.add_task(
            process_document_background,
            project_id=project_id,
            document_id=document_id,
            document_path=temp_file_path,
            document_type=file_extension[1:],  # 去掉点号
            processing_config=processing_config.dict() if processing_config else {}
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            size=file_size,
            status="processing",
            message="文档上传成功，正在后台处理"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档上传失败: {str(e)}"
        )


async def process_document_background(
    project_id: str,
    document_id: str,
    document_path: str,
    document_type: str,
    processing_config: Dict[str, Any]
):
    """后台处理文档"""
    try:
        logger.info(f"开始后台处理文档: {document_id}")
        
        # 获取文档处理智能体
        doc_agent = get_document_processing_agent()
        
        # 处理文档
        result = await doc_agent.process_document(
            project_id=project_id,
            document_id=document_id,
            document_path=document_path,
            document_type=document_type,
            processing_config=processing_config
        )
        
        logger.info(f"文档处理完成: {document_id}, 状态: {result.get('processing_status')}")
        
        # 清理临时文件
        import os
        if os.path.exists(document_path):
            os.unlink(document_path)
        
    except Exception as e:
        logger.error(f"后台文档处理失败: {document_id}, 错误: {e}")
        
        # 清理临时文件
        import os
        if os.path.exists(document_path):
            os.unlink(document_path)


@router.get("/documents/{document_id}/status")
async def get_document_status(document_id: str):
    """
    获取文档处理状态
    
    Args:
        document_id: 文档ID
    
    Returns:
        文档状态信息
    """
    try:
        # 这里应该从数据库查询实际状态
        # 目前返回模拟数据
        return {
            "document_id": document_id,
            "status": "completed",
            "processing_progress": 100,
            "total_chunks": 25,
            "total_entities": 15,
            "processing_time": 45.2,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:45Z"
        }
        
    except Exception as e:
        logger.error(f"获取文档状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档状态失败: {str(e)}"
        )


@router.get("/documents/{document_id}/outline")
async def get_document_outline(document_id: str):
    """
    获取文档大纲结构
    
    Args:
        document_id: 文档ID
    
    Returns:
        文档大纲信息
    """
    try:
        # 这里应该从数据库查询实际大纲
        # 目前返回模拟数据
        return {
            "document_id": document_id,
            "title": "示例文档标题",
            "sections": [
                {
                    "id": "section_1",
                    "title": "第一章 概述",
                    "level": 1,
                    "order_index": 1,
                    "subsections": [
                        {
                            "id": "section_1_1",
                            "title": "1.1 背景介绍",
                            "level": 2,
                            "order_index": 1
                        },
                        {
                            "id": "section_1_2", 
                            "title": "1.2 研究目标",
                            "level": 2,
                            "order_index": 2
                        }
                    ]
                },
                {
                    "id": "section_2",
                    "title": "第二章 相关工作",
                    "level": 1,
                    "order_index": 2,
                    "subsections": []
                }
            ],
            "total_sections": 2,
            "total_pages": 10
        }
        
    except Exception as e:
        logger.error(f"获取文档大纲失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档大纲失败: {str(e)}"
        )


@router.post("/documents/search")
async def search_documents(query: DocumentQuery):
    """
    搜索文档内容
    
    Args:
        query: 搜索查询
    
    Returns:
        搜索结果
    """
    try:
        # 这里应该实现实际的搜索逻辑
        # 目前返回模拟数据
        return {
            "query": query.query,
            "total_results": 3,
            "results": [
                {
                    "document_id": "doc_1",
                    "title": "相关文档1",
                    "relevance_score": 0.95,
                    "chunks": [
                        {
                            "chunk_id": "chunk_1",
                            "content": f"这是关于{query.query}的相关内容片段...",
                            "relevance_score": 0.92,
                            "page_number": 1
                        }
                    ] if query.include_chunks else []
                },
                {
                    "document_id": "doc_2",
                    "title": "相关文档2", 
                    "relevance_score": 0.87,
                    "chunks": [
                        {
                            "chunk_id": "chunk_2",
                            "content": f"另一个关于{query.query}的内容片段...",
                            "relevance_score": 0.85,
                            "page_number": 3
                        }
                    ] if query.include_chunks else []
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"文档搜索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档搜索失败: {str(e)}"
        )


@router.get("/documents")
async def list_documents(
    project_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    列出文档
    
    Args:
        project_id: 项目ID（可选）
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        文档列表
    """
    try:
        # 这里应该从数据库查询实际文档
        # 目前返回模拟数据
        documents = [
            {
                "document_id": f"doc_{i+1}",
                "filename": f"文档{i+1}.pdf",
                "title": f"示例文档{i+1}",
                "project_id": project_id or "default_project",
                "status": "completed",
                "file_size": 1024 * (i + 1),
                "total_chunks": 20 + i * 5,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:01:00Z"
            }
            for i in range(min(limit, 5))  # 最多返回5个模拟文档
        ]
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
        
    except Exception as e:
        logger.error(f"列出文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出文档失败: {str(e)}"
        )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    
    Args:
        document_id: 文档ID
    
    Returns:
        删除结果
    """
    try:
        # 这里应该实现实际的删除逻辑
        # 包括从向量数据库、图数据库、文件存储中删除
        
        logger.info(f"删除文档: {document_id}")
        
        return {
            "document_id": document_id,
            "message": "文档删除成功",
            "deleted_at": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    获取文档的分块信息
    
    Args:
        document_id: 文档ID
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        文档分块列表
    """
    try:
        # 这里应该从数据库查询实际分块
        # 目前返回模拟数据
        chunks = [
            {
                "chunk_id": f"chunk_{i+1}",
                "content": f"这是文档{document_id}的第{i+1}个分块内容...",
                "chunk_index": i,
                "word_count": 150 + i * 10,
                "page_number": (i // 3) + 1,
                "section_id": f"section_{(i // 5) + 1}",
                "entities": [
                    {"text": "实体1", "type": "PERSON"},
                    {"text": "实体2", "type": "ORGANIZATION"}
                ],
                "keywords": ["关键词1", "关键词2"]
            }
            for i in range(min(limit, 10))  # 最多返回10个模拟分块
        ]
        
        return {
            "document_id": document_id,
            "chunks": chunks,
            "total": len(chunks),
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
        
    except Exception as e:
        logger.error(f"获取文档分块失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档分块失败: {str(e)}"
        )


@router.get("/documents/{document_id}/entities")
async def get_document_entities(document_id: str):
    """
    获取文档中提取的实体
    
    Args:
        document_id: 文档ID
    
    Returns:
        实体列表
    """
    try:
        # 这里应该从数据库查询实际实体
        # 目前返回模拟数据
        entities = [
            {
                "entity_id": "entity_1",
                "text": "张三",
                "type": "PERSON",
                "confidence": 0.95,
                "mentions": [
                    {"chunk_id": "chunk_1", "position": 10},
                    {"chunk_id": "chunk_3", "position": 25}
                ]
            },
            {
                "entity_id": "entity_2",
                "text": "北京大学",
                "type": "ORGANIZATION",
                "confidence": 0.92,
                "mentions": [
                    {"chunk_id": "chunk_2", "position": 5}
                ]
            }
        ]
        
        return {
            "document_id": document_id,
            "entities": entities,
            "total_entities": len(entities),
            "entity_types": ["PERSON", "ORGANIZATION", "LOCATION", "MISC"]
        }
        
    except Exception as e:
        logger.error(f"获取文档实体失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档实体失败: {str(e)}"
        ) 