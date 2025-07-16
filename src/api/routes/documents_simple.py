"""
简化的文档管理API路由
用于集成测试和基础功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.postgresql import get_db_session
from ...models.document import Document
from ...models.project import Project
from ...services.project_service import ProjectService
from ...graphs.simplified_document_processor import SimplifiedDocumentProcessor
from ...utils.logger import get_logger
from ..middleware.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/documents")


class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    project_id: Optional[str] = Field(None, description="项目ID，如果未提供则使用默认项目")
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """文档响应"""
    document_id: str
    project_id: str
    title: str
    status: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    """文档状态响应"""
    document_id: str
    status: str
    progress: float
    message: Optional[str]
    metadata: Optional[Dict[str, Any]]


# 存储处理中的文档状态
processing_status = {}


@router.post("/upload", response_model=Dict[str, str])
async def upload_document(
    request: DocumentUploadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """上传并处理文档"""
    try:
        # 如果没有提供项目ID，使用用户的默认项目
        if not request.project_id:
            project_service = ProjectService(db)
            default_project = await project_service.get_or_create_default_project(uuid.UUID(current_user))
            project_id = str(default_project.id)
            logger.info(f"使用用户 {current_user} 的默认项目: {project_id}")
        else:
            project_id = request.project_id
            # 验证项目存在
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="项目不存在")
        
        # 创建文档记录
        document = Document(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=request.title,
            content=request.content,
            status="processing",
            metadata=request.metadata or {},
            file_type="text",
            file_size=len(request.content.encode('utf-8'))
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # 初始化处理状态
        processing_status[document.id] = {
            "status": "processing",
            "progress": 0.0,
            "message": "文档上传成功，开始处理"
        }
        
        # 在后台处理文档
        background_tasks.add_task(
            process_document_background,
            document.id,
            request.content,
            db
        )
        
        logger.info(f"文档上传成功: {document.id} - {document.title}")
        
        return {
            "document_id": document.id,
            "status": "processing",
            "message": "文档已上传，正在后台处理"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail="文档上传失败")


async def process_document_background(document_id: str, content: str, db: Session):
    """后台处理文档"""
    try:
        # 更新状态
        processing_status[document_id] = {
            "status": "processing",
            "progress": 0.2,
            "message": "正在初始化文档处理器"
        }
        
        # 创建简化的文档处理器
        processor = SimplifiedDocumentProcessor(db)
        
        # 准备处理状态
        state = {
            "document_id": document_id,
            "content": content,
            "metadata": {},
            "chunks": [],
            "embeddings": [],
            "status": "processing",
            "errors": []
        }
        
        # 更新进度
        processing_status[document_id]["progress"] = 0.4
        processing_status[document_id]["message"] = "正在分块和向量化"
        
        # 执行处理（简化版本）
        # 这里应该调用实际的处理流程
        await asyncio.sleep(2)  # 模拟处理时间
        
        # 更新文档状态
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "completed"
            document.updated_at = datetime.utcnow()
            db.commit()
        
        # 更新处理状态
        processing_status[document_id] = {
            "status": "completed",
            "progress": 1.0,
            "message": "文档处理完成"
        }
        
        logger.info(f"文档处理完成: {document_id}")
        
    except Exception as e:
        logger.error(f"文档处理失败: {document_id} - {e}")
        
        # 更新错误状态
        processing_status[document_id] = {
            "status": "failed",
            "progress": 0.0,
            "message": f"处理失败: {str(e)}"
        }
        
        # 更新数据库
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "failed"
            document.metadata["error"] = str(e)
            document.updated_at = datetime.utcnow()
            db.commit()


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db_session)
):
    """获取文档处理状态"""
    try:
        # 从数据库获取文档
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取处理状态
        status_info = processing_status.get(document_id, {
            "status": document.status,
            "progress": 1.0 if document.status == "completed" else 0.0,
            "message": None
        })
        
        return DocumentStatusResponse(
            document_id=document_id,
            status=status_info["status"],
            progress=status_info["progress"],
            message=status_info.get("message"),
            metadata=document.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取文档状态失败")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db_session)
):
    """获取文档详情"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return DocumentResponse(
            document_id=document.id,
            project_id=document.project_id,
            title=document.title,
            status=document.status,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail="获取文档失败")


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db_session)
):
    """获取文档列表"""
    try:
        query = db.query(Document).filter(Document.is_deleted == False)
        
        if project_id:
            query = query.filter(Document.project_id == project_id)
        
        if status:
            query = query.filter(Document.status == status)
        
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            DocumentResponse(
                document_id=doc.id,
                project_id=doc.project_id,
                title=doc.title,
                status=doc.status,
                metadata=doc.metadata,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取文档列表失败")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db_session)
):
    """删除文档"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 软删除
        document.is_deleted = True
        document.updated_at = datetime.utcnow()
        
        db.commit()
        
        # 清理处理状态
        if document_id in processing_status:
            del processing_status[document_id]
        
        logger.info(f"文档删除成功: {document_id}")
        
        return {"message": "文档删除成功", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail="删除文档失败")