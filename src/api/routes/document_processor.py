"""
文档处理API路由
提供文档上传、处理和管理的HTTP接口
"""
import os
import shutil
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import aiofiles

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.core.document.mvp_document_processor import (
    create_mvp_document_processor,
    DocumentMetadata,
    SUPPORTED_EXTENSIONS
)
from src.api.middleware.auth import get_current_user
from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# 上传目录
UPLOAD_DIR = Path(settings.paths.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ProcessDocumentRequest(BaseModel):
    """处理文档请求"""
    file_path: str = Field(..., description="文档文件路径")
    project_id: Optional[str] = Field(None, description="项目ID")
    metadata: Optional[dict] = Field(None, description="额外元数据")


class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    file_paths: List[str] = Field(..., description="文档文件路径列表")
    project_id: Optional[str] = Field(None, description="项目ID")
    max_concurrent: int = Field(3, ge=1, le=10, description="最大并发数")


class DocumentStatusResponse(BaseModel):
    """文档状态响应"""
    document_id: str
    filename: str
    status: str
    chunk_count: int
    processed_at: Optional[str]
    error_message: Optional[str]


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    current_user: str = Depends(get_current_user)
):
    """
    上传文档
    
    将文档保存到服务器，返回文件路径
    """
    try:
        # 验证文件类型
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
            
        # 验证文件大小（最大50MB）
        max_size = 50 * 1024 * 1024
        file_size = 0
        
        # 创建用户上传目录
        user_upload_dir = UPLOAD_DIR / current_user
        user_upload_dir.mkdir(exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = user_upload_dir / safe_filename
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > max_size:
                    # 删除部分写入的文件
                    await aiofiles.os.remove(file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size is 50MB"
                    )
                await f.write(chunk)
                
        logger.info(f"File uploaded: {file_path} (size: {file_size} bytes)")
        
        return {
            "success": True,
            "file_path": str(file_path),
            "filename": file.filename,
            "file_size": file_size,
            "user_id": current_user,
            "project_id": project_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/process")
async def process_document(
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    处理文档
    
    解析文档、分块、生成嵌入并存储到记忆系统
    """
    try:
        # 验证文件路径
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_path}"
            )
            
        # 验证用户权限（简单检查路径）
        if current_user != "u1" and current_user not in str(file_path):
            raise HTTPException(
                status_code=403,
                detail="Access denied to this file"
            )
            
        # 创建处理器
        processor = create_mvp_document_processor(user_id=current_user)
        
        # 异步处理文档
        async def process_task():
            try:
                await processor.process_document(
                    file_path=str(file_path),
                    project_id=request.project_id,
                    metadata=request.metadata
                )
            except Exception as e:
                logger.error(f"Background processing error: {e}")
                
        background_tasks.add_task(process_task)
        
        # 返回初始状态
        return {
            "success": True,
            "message": "Document processing started",
            "file_path": str(file_path),
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process document error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/process-sync")
async def process_document_sync(
    request: ProcessDocumentRequest,
    current_user: str = Depends(get_current_user)
):
    """
    同步处理文档
    
    等待处理完成后返回结果
    """
    try:
        # 验证文件路径
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_path}"
            )
            
        # 创建处理器
        processor = create_mvp_document_processor(user_id=current_user)
        
        # 同步处理文档
        result = await processor.process_document(
            file_path=str(file_path),
            project_id=request.project_id,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "document_id": result.document_id,
            "filename": result.filename,
            "status": result.status,
            "chunk_count": result.chunk_count,
            "processed_at": result.processed_at
        }
        
    except Exception as e:
        logger.error(f"Sync process error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/batch-process")
async def batch_process_documents(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    批量处理文档
    
    并发处理多个文档
    """
    try:
        # 验证所有文件
        for file_path in request.file_paths:
            if not Path(file_path).exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"File not found: {file_path}"
                )
                
        # 创建处理器
        processor = create_mvp_document_processor(user_id=current_user)
        
        # 异步批量处理
        async def batch_task():
            try:
                await processor.process_batch(
                    file_paths=request.file_paths,
                    project_id=request.project_id,
                    max_concurrent=request.max_concurrent
                )
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                
        background_tasks.add_task(batch_task)
        
        return {
            "success": True,
            "message": "Batch processing started",
            "document_count": len(request.file_paths),
            "max_concurrent": request.max_concurrent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch process error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch processing: {str(e)}"
        )


@router.get("/supported-types")
async def get_supported_types():
    """
    获取支持的文件类型
    """
    return {
        "supported_extensions": list(SUPPORTED_EXTENSIONS),
        "max_file_size_mb": 50
    }


@router.get("/uploads")
async def list_uploaded_files(
    current_user: str = Depends(get_current_user)
):
    """
    列出用户上传的文件
    """
    try:
        user_upload_dir = UPLOAD_DIR / current_user
        
        if not user_upload_dir.exists():
            return {
                "files": [],
                "count": 0
            }
            
        files = []
        for file_path in user_upload_dir.glob("*"):
            if file_path.is_file():
                stats = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": stats.st_size,
                    "uploaded_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "file_type": file_path.suffix
                })
                
        # 按上传时间倒序
        files.sort(key=lambda x: x["uploaded_at"], reverse=True)
        
        return {
            "files": files,
            "count": len(files),
            "user_id": current_user
        }
        
    except Exception as e:
        logger.error(f"List uploads error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list uploaded files: {str(e)}"
        )


@router.delete("/uploads/{filename}")
async def delete_uploaded_file(
    filename: str,
    current_user: str = Depends(get_current_user)
):
    """
    删除上传的文件
    """
    try:
        file_path = UPLOAD_DIR / current_user / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {filename}"
            )
            
        # 删除文件
        file_path.unlink()
        
        return {
            "success": True,
            "message": f"File {filename} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.post("/extract-text")
async def extract_text_preview(
    file: UploadFile = File(...),
    max_length: int = 1000
):
    """
    提取文档文本预览
    
    不保存文件，仅返回文本内容预览
    """
    try:
        # 验证文件类型
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}"
            )
            
        # 创建临时文件
        temp_file = UPLOAD_DIR / f"temp_{datetime.now().timestamp()}_{file.filename}"
        
        try:
            # 保存临时文件
            content = await file.read()
            async with aiofiles.open(temp_file, 'wb') as f:
                await f.write(content)
                
            # 创建处理器并加载文档
            processor = create_mvp_document_processor()
            text_content = await processor._load_document(temp_file)
            
            # 截取预览
            preview = text_content[:max_length]
            if len(text_content) > max_length:
                preview += "..."
                
            return {
                "success": True,
                "filename": file.filename,
                "text_length": len(text_content),
                "preview": preview
            }
            
        finally:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract text error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract text: {str(e)}"
        )