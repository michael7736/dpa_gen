"""
文档管理API路由
支持文档上传、处理、查询、删除等功能
"""

import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...services.project_service import ProjectService
from ...graphs.simplified_document_processor import SimplifiedDocumentProcessor, ProcessingMode
from ...utils.logger import get_logger
from ...config.feature_flags import is_feature_enabled
from ..middleware.auth import get_current_user

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
    mode: Optional[str] = "standard"  # standard or fast
    use_semantic_chunking: Optional[bool] = False  # 默认禁用
    extract_entities: Optional[bool] = False  # 暂时禁用
    build_knowledge_graph: Optional[bool] = False  # 暂时禁用


class DocumentQuery(BaseModel):
    """文档查询请求"""
    query: str
    document_ids: Optional[List[str]] = None
    limit: Optional[int] = 10
    include_chunks: Optional[bool] = True


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    project_id: Optional[str] = None,
    file: UploadFile = File(...),
    processing_config: Optional[DocumentProcessingConfig] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
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
        # 如果没有提供项目ID，使用用户的默认项目
        if not project_id:
            project_service = ProjectService(db)
            default_project = await project_service.get_or_create_default_project(UUID(current_user))
            project_id = str(default_project.id)
            logger.info(f"使用用户 {current_user} 的默认项目: {project_id}")
        
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
            processing_config=processing_config.dict() if processing_config else {"file_size": file_size}
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
        
        # 使用简化版文档处理器
        processor = SimplifiedDocumentProcessor()
        
        # 准备处理参数
        document_info = {
            "document_id": document_id,
            "project_id": project_id,
            "file_path": document_path,
            "file_name": document_path.split("/")[-1],
            "mode": ProcessingMode(processing_config.get("mode", "standard"))
        }
        
        # 处理文档
        result = await processor.process_document(document_info)
        
        logger.info(f"文档处理完成: {document_id}, 成功: {result.get('success')}")
        
        # 如果处理成功，保存文档到数据库
        if result.get('success'):
            from ...models.document import Document
            from ...database.postgresql import get_db_session
            
            db = next(get_db_session())
            try:
                # 创建文档记录
                doc = Document(
                    id=document_id,
                    project_id=project_id,
                    file_name=document_info["file_name"],
                    file_type=document_type,
                    file_path=document_path,  # 临时路径，后续会删除
                    file_size=processing_config.get("file_size", 0),
                    status="completed",
                    chunks_count=result.get("metadata", {}).get("chunk_count", 0)
                )
                
                db.add(doc)
                db.commit()
                logger.info(f"文档记录已保存到数据库: {document_id}")
            except Exception as e:
                logger.error(f"保存文档记录失败: {e}")
                db.rollback()
            finally:
                db.close()
        
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
    offset: int = 0,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
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
        from ...models.document import Document
        from ...services.project_service import ProjectService
        
        # 处理用户ID格式
        user_uuid = None
        if current_user == "u1":
            user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        else:
            try:
                user_uuid = UUID(current_user)
            except ValueError:
                user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        
        # 如果没有提供项目ID或者项目ID是"default"，使用用户的默认项目
        if not project_id or project_id == "default":
            project_service = ProjectService(db)
            default_project = await project_service.get_or_create_default_project(user_uuid)
            project_id = str(default_project.id)
        
        # 从数据库查询实际文档
        query = db.query(Document).filter(Document.project_id == UUID(project_id))
        
        # 分页
        total_count = query.count()
        documents_db = query.offset(offset).limit(limit).all()
        
        # 转换为API格式
        documents = []
        for doc in documents_db:
            documents.append({
                "id": str(doc.id),
                "project_id": str(doc.project_id),
                "filename": doc.filename,
                "file_type": doc.document_type.lower() if doc.document_type else "unknown",
                "file_size": doc.file_size,
                "status": doc.processing_status.lower() if doc.processing_status else "unknown",
                "page_count": doc.metadata_info.get("page_count", 0) if doc.metadata_info else 0,
                "word_count": doc.metadata_info.get("word_count", 0) if doc.metadata_info else 0,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            })
        
        # 计算分页信息
        page = (offset // limit) + 1
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "items": documents,
            "total": total_count,
            "page": page,
            "page_size": limit,
            "total_pages": total_pages
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


@router.get("/documents/{document_id}/summary")
async def get_document_summary(
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    获取文档摘要
    
    Args:
        document_id: 文档ID
    
    Returns:
        文档摘要信息
    """
    try:
        from ...models.document import Document
        from ...models.processing_pipeline import ProcessingPipeline
        from ...models.processing_pipeline import PipelineStage, ProcessingStage
        from uuid import UUID
        
        # 转换文档ID为UUID
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的文档ID格式"
            )
        
        # 查询文档信息
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 查询摘要处理阶段
        summary_stage = db.query(PipelineStage).join(ProcessingPipeline).filter(
            ProcessingPipeline.document_id == doc_uuid,
            PipelineStage.stage_type == ProcessingStage.SUMMARY,
            PipelineStage.status == "completed"
        ).first()
        
        if not summary_stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档摘要尚未生成或生成失败"
            )
        
        # 构建摘要响应
        summary_response = {
            "document_id": document_id,
            "filename": document.filename,
            "summary": summary_stage.result.get("summary", "摘要内容暂不可用") if summary_stage.result else "摘要内容暂不可用",
            "generated_at": summary_stage.completed_at.isoformat() if summary_stage.completed_at else None
        }
        
        return summary_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档摘要失败: {str(e)}"
        )


@router.get("/documents/{document_id}/analysis")
async def get_document_analysis(
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    获取文档分析结果
    
    Args:
        document_id: 文档ID
    
    Returns:
        文档分析结果
    """
    try:
        from ...models.document import Document
        from ...models.processing_pipeline import ProcessingPipeline
        from ...models.processing_pipeline import PipelineStage, ProcessingStage
        from uuid import UUID
        
        # 转换文档ID为UUID
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的文档ID格式"
            )
        
        # 查询文档信息
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 查询深度分析阶段
        analysis_stage = db.query(PipelineStage).join(ProcessingPipeline).filter(
            ProcessingPipeline.document_id == doc_uuid,
            PipelineStage.stage_type == ProcessingStage.ANALYSIS,
            PipelineStage.status == "completed"
        ).first()
        
        if not analysis_stage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档分析尚未完成或分析失败"
            )
        
        # 构建分析响应
        analysis_response = {
            "analysis_id": str(analysis_stage.id),
            "document_id": document_id,
            "analysis_depth": analysis_stage.result.get("analysis_depth", "standard") if analysis_stage.result else "standard",
            "status": "completed",
            "created_at": analysis_stage.started_at.isoformat() if analysis_stage.started_at else None,
            "result": {
                "executive_summary": analysis_stage.result.get("executive_summary", "暂无执行摘要") if analysis_stage.result else "暂无执行摘要",
                "key_insights": analysis_stage.result.get("key_insights", []) if analysis_stage.result else [],
                "action_items": analysis_stage.result.get("action_items", []) if analysis_stage.result else [],
                "detailed_report": analysis_stage.result.get("detailed_report", "暂无详细报告") if analysis_stage.result else "暂无详细报告",
                "visualization_data": analysis_stage.result.get("visualization_data", {}) if analysis_stage.result else {}
            }
        }
        
        return analysis_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档分析失败: {str(e)}"
        )


@router.get("/documents/{document_id}/operations/status")
async def get_document_operations_status(
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    获取文档操作状态
    
    Args:
        document_id: 文档ID
    
    Returns:
        文档操作状态信息
    """
    try:
        from ...models.document import Document
        from ...models.processing_pipeline import ProcessingPipeline
        from ...models.processing_pipeline import PipelineStage, ProcessingStage
        from uuid import UUID
        
        # 转换文档ID为UUID
        try:
            doc_uuid = UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的文档ID格式"
            )
        
        # 查询文档信息
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 查询所有处理管道
        pipelines = db.query(ProcessingPipeline).filter(
            ProcessingPipeline.document_id == doc_uuid
        ).all()
        
        # 构建操作状态响应
        operations_summary = {
            "summary_completed": False,
            "index_completed": False,
            "analysis_completed": False
        }
        
        pipeline_data = []
        for pipeline in pipelines:
            stages = db.query(PipelineStage).filter(
                PipelineStage.pipeline_id == pipeline.id
            ).all()
            
            stage_data = []
            for stage in stages:
                stage_data.append({
                    "type": stage.stage_type,
                    "name": stage.stage_name,
                    "status": stage.status,
                    "progress": stage.progress,
                    "message": stage.message
                })
                
                # 更新操作摘要
                if stage.stage_type == ProcessingStage.SUMMARY and stage.status == "completed":
                    operations_summary["summary_completed"] = True
                elif stage.stage_type == ProcessingStage.INDEX and stage.status == "completed":
                    operations_summary["index_completed"] = True
                elif stage.stage_type == ProcessingStage.ANALYSIS and stage.status == "completed":
                    operations_summary["analysis_completed"] = True
            
            pipeline_data.append({
                "pipeline_id": str(pipeline.id),
                "overall_progress": pipeline.overall_progress,
                "completed": pipeline.completed,
                "stages": stage_data
            })
        
        status_response = {
            "document_id": document_id,
            "document_status": document.processing_status,
            "operations_summary": operations_summary,
            "pipelines": pipeline_data
        }
        
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档操作状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档操作状态失败: {str(e)}"
        ) 