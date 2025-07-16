"""
文档管理API路由 V2
支持用户选择处理选项的新版本
"""

import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, status, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...models.document import Document, ProcessingStatus, DocumentType
from ...models.processing_pipeline import ProcessingPipeline, PipelineStage, StageStatus, ProcessingStage
from ...services.project_service import ProjectService
from ...services.minio_service import get_minio_service
from ...services.pipeline_executor import PipelineExecutor, get_pipeline_executor
from ...utils.logger import get_logger
from ..middleware.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v2/documents", tags=["documents-v2"])


def _get_document_type(file_extension: str) -> str:
    """根据文件扩展名获取文档类型"""
    extension_map = {
        '.pdf': DocumentType.PDF,
        '.docx': DocumentType.WORD,
        '.doc': DocumentType.WORD,
        '.txt': DocumentType.TEXT,
        '.md': DocumentType.MARKDOWN
    }
    return extension_map.get(file_extension, DocumentType.TEXT)


class ProcessingOptions(BaseModel):
    """处理选项"""
    upload_only: bool = Field(True, description="仅上传")
    generate_summary: bool = Field(False, description="生成摘要")
    create_index: bool = Field(False, description="创建索引")
    deep_analysis: bool = Field(False, description="深度分析")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str
    filename: str
    size: int
    status: str
    message: str
    processing_pipeline: Optional[Dict[str, Any]] = None


class PipelineProgressResponse(BaseModel):
    """管道进度响应"""
    pipeline_id: str
    overall_progress: float
    current_stage: Optional[str]
    stages: List[Dict[str, Any]]
    can_resume: bool
    interrupted: bool


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document_v2(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    upload_only: bool = Form(True),
    generate_summary: bool = Form(False),
    create_index: bool = Form(False),
    deep_analysis: bool = Form(False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    上传文档并根据用户选择处理
    
    Args:
        file: 上传的文件
        project_id: 项目ID（可选，默认使用默认项目）
        upload_only: 仅上传
        generate_summary: 生成摘要
        create_index: 创建索引
        deep_analysis: 深度分析
        
    Returns:
        文档上传响应，包含处理管道信息
    """
    try:
        # 记录处理选项
        logger.info(f"处理选项: upload_only={upload_only}, generate_summary={generate_summary}, "
                   f"create_index={create_index}, deep_analysis={deep_analysis}")
        
        # 处理用户ID格式 - 单用户阶段兼容性
        user_uuid = None
        if current_user == "u1":
            # 单用户阶段，映射到默认用户UUID
            user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        else:
            try:
                # 尝试解析为UUID
                user_uuid = UUID(current_user)
            except ValueError:
                # 如果不是有效UUID，使用默认用户
                user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        
        # 如果没有提供项目ID或者项目ID是"default"，使用用户的默认项目
        if not project_id or project_id == "default":
            project_service = ProjectService(db)
            default_project = await project_service.get_or_create_default_project(user_uuid)
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
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 计算文件哈希
        import hashlib
        file_hash = hashlib.sha256(content).hexdigest()
        
        # 检查是否已存在相同哈希的文档
        existing_doc = db.query(Document).filter(
            Document.file_hash == file_hash,
            Document.project_id == UUID(project_id)
        ).first()
        
        if existing_doc:
            # 如果文档已存在，返回现有文档信息
            logger.info(f"文档已存在，返回现有文档: {existing_doc.id}")
            return DocumentUploadResponse(
                document_id=str(existing_doc.id),
                filename=existing_doc.filename,
                size=existing_doc.file_size,
                status="exists",
                message=f"文档已存在：{existing_doc.filename}",
                processing_pipeline=None
            )
        
        # 生成文档ID
        document_id = str(uuid4())
        
        # 上传到MinIO
        minio_service = get_minio_service()
        storage_path = await minio_service.upload_document(
            file_content=content,
            file_name=file.filename,
            user_id=current_user,
            project_id=project_id,
            document_id=document_id,
            content_type=file.content_type,
            metadata={
                "file_size": str(file_size),
                "upload_time": datetime.utcnow().isoformat()
            }
        )
        
        # 创建文档记录
        document = Document(
            id=UUID(document_id),
            project_id=UUID(project_id),
            title=file.filename,
            filename=file.filename,
            file_path=storage_path,
            file_size=file_size,
            file_hash=file_hash,
            document_type=_get_document_type(file_extension),
            processing_status=ProcessingStatus.UPLOADED,
            language="zh",  # TODO: 自动检测语言
            metadata_info={
                "storage_path": storage_path,
                "upload_user": current_user,
                "upload_time": datetime.utcnow().isoformat()
            }
        )
        
        db.add(document)
        
        # 创建处理管道（如果需要处理）
        pipeline_data = None
        if not upload_only:
            # 创建管道
            pipeline = ProcessingPipeline(
                document_id=UUID(document_id),
                user_id=user_uuid,
                processing_options={
                    "generate_summary": generate_summary,
                    "create_index": create_index,
                    "deep_analysis": deep_analysis
                }
            )
            db.add(pipeline)
            db.flush()  # 获取pipeline.id
            
            # 创建处理阶段
            stages = []
            
            # 上传阶段（已完成）
            upload_stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_type=ProcessingStage.UPLOAD,
                stage_name="文件上传",
                status=StageStatus.COMPLETED,
                progress=100,
                completed_at=datetime.utcnow(),
                result={
                    "minio_path": storage_path,
                    "file_size": file_size
                }
            )
            stages.append(upload_stage)
            
            # 摘要阶段
            if generate_summary:
                summary_stage = PipelineStage(
                    pipeline_id=pipeline.id,
                    stage_type=ProcessingStage.SUMMARY,
                    stage_name="生成摘要",
                    status=StageStatus.PENDING,
                    estimated_time=30
                )
                stages.append(summary_stage)
            
            # 索引阶段
            if create_index:
                index_stage = PipelineStage(
                    pipeline_id=pipeline.id,
                    stage_type=ProcessingStage.INDEX,
                    stage_name="创建索引",
                    status=StageStatus.PENDING,
                    estimated_time=120
                )
                stages.append(index_stage)
            
            # 分析阶段
            if deep_analysis:
                analysis_stage = PipelineStage(
                    pipeline_id=pipeline.id,
                    stage_type=ProcessingStage.ANALYSIS,
                    stage_name="深度分析",
                    status=StageStatus.PENDING,
                    estimated_time=300
                )
                stages.append(analysis_stage)
            
            # 批量添加阶段
            for stage in stages:
                db.add(stage)
            
            db.commit()
            
            # 准备管道响应数据
            pipeline_data = {
                "pipeline_id": str(pipeline.id),
                "stages": [
                    {
                        "id": stage.stage_type,
                        "name": stage.stage_name,
                        "status": stage.status,
                        "progress": stage.progress,
                        "estimated_time": stage.estimated_time,
                        "result": stage.result
                    }
                    for stage in stages
                ]
            }
            
            # 启动后台处理
            if len(stages) > 1:  # 有除了上传之外的阶段
                background_tasks.add_task(
                    execute_pipeline_background,
                    pipeline_id=str(pipeline.id),
                    db_session=db
                )
        else:
            db.commit()
        
        logger.info(f"文档上传成功: {file.filename} ({file_size} bytes)")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            size=file_size,
            status="uploaded",
            message="文档上传成功" + ("，处理已开始" if not upload_only else ""),
            processing_pipeline=pipeline_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档上传失败: {str(e)}"
        )


async def execute_pipeline_background(pipeline_id: str, db_session: Session):
    """后台执行处理管道 - 改进版本"""
    import asyncio
    from ..websocket import get_progress_notifier
    
    logger.info(f"🚀 开始执行管道: {pipeline_id}")
    
    try:
        # 获取执行器
        executor = get_pipeline_executor()
        
        # 设置超时（10分钟）
        timeout = 600
        
        # 执行管道（带超时控制）
        await asyncio.wait_for(
            executor.execute(pipeline_id, db_session),
            timeout=timeout
        )
        
        logger.info(f"✅ 管道执行完成: {pipeline_id}")
        
        # 发送完成通知
        try:
            notifier = get_progress_notifier()
            await notifier.notify_pipeline_progress(pipeline_id, db_session)
            logger.info(f"📡 WebSocket通知已发送: {pipeline_id}")
        except Exception as ws_error:
            logger.warning(f"WebSocket通知失败: {ws_error}")
            
    except asyncio.TimeoutError:
        logger.error(f"⏰ 管道执行超时: {pipeline_id} (超时: {timeout}秒)")
        
        # 标记管道为中断
        try:
            pipeline = db_session.query(ProcessingPipeline).filter(
                ProcessingPipeline.id == pipeline_id
            ).first()
            if pipeline:
                pipeline.interrupted = True
                pipeline.completed_at = datetime.utcnow()
                db_session.commit()
                logger.info(f"🚫 管道已标记为中断: {pipeline_id}")
        except Exception as db_error:
            logger.error(f"标记管道中断时出错: {db_error}")
            
    except Exception as e:
        logger.error(f"❌ 管道执行异常: {pipeline_id} - {e}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        # 标记管道为失败
        try:
            pipeline = db_session.query(ProcessingPipeline).filter(
                ProcessingPipeline.id == pipeline_id
            ).first()
            if pipeline:
                pipeline.interrupted = True
                pipeline.completed_at = datetime.utcnow()
                db_session.commit()
                logger.info(f"🚫 管道已标记为失败: {pipeline_id}")
        except Exception as db_error:
            logger.error(f"标记管道失败时出错: {db_error}")
    
    finally:
        # 确保数据库会话关闭
        try:
            db_session.close()
        except:
            pass


@router.get("/{document_id}/pipeline/{pipeline_id}/progress", response_model=PipelineProgressResponse)
async def get_pipeline_progress(
    document_id: str,
    pipeline_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """获取处理管道进度"""
    try:
        # 验证文档和管道
        pipeline = db.query(ProcessingPipeline).filter(
            ProcessingPipeline.id == pipeline_id,
            ProcessingPipeline.document_id == document_id,
            ProcessingPipeline.user_id == current_user
        ).first()
        
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="管道不存在"
            )
        
        # 获取所有阶段
        stages = db.query(PipelineStage).filter(
            PipelineStage.pipeline_id == pipeline.id
        ).order_by(PipelineStage.id).all()
        
        # 构建响应
        stage_data = []
        for stage in stages:
            stage_info = {
                "id": stage.stage_type,
                "name": stage.stage_name,
                "status": stage.status,
                "progress": stage.progress,
                "message": stage.message,
                "can_interrupt": stage.can_interrupt
            }
            
            if stage.started_at:
                stage_info["started_at"] = stage.started_at.isoformat()
            if stage.completed_at:
                stage_info["completed_at"] = stage.completed_at.isoformat()
                stage_info["duration"] = stage.duration
            if stage.error:
                stage_info["error"] = stage.error
                
            stage_data.append(stage_info)
        
        return PipelineProgressResponse(
            pipeline_id=str(pipeline.id),
            overall_progress=pipeline.overall_progress,
            current_stage=pipeline.current_stage,
            stages=stage_data,
            can_resume=pipeline.can_resume,
            interrupted=pipeline.interrupted
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取管道进度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取管道进度失败"
        )


@router.post("/{document_id}/pipeline/{pipeline_id}/interrupt")
async def interrupt_pipeline(
    document_id: str,
    pipeline_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """中断处理管道"""
    try:
        # 验证并获取管道
        pipeline = db.query(ProcessingPipeline).filter(
            ProcessingPipeline.id == pipeline_id,
            ProcessingPipeline.document_id == document_id,
            ProcessingPipeline.user_id == current_user
        ).first()
        
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="管道不存在"
            )
        
        if pipeline.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="管道已完成，无法中断"
            )
        
        # 设置中断标志
        pipeline.interrupted = True
        pipeline.can_resume = True
        
        # 更新当前处理中的阶段
        current_stage = db.query(PipelineStage).filter(
            PipelineStage.pipeline_id == pipeline.id,
            PipelineStage.status == StageStatus.PROCESSING
        ).first()
        
        if current_stage:
            current_stage.status = StageStatus.INTERRUPTED
            current_stage.message = "用户中断处理"
        
        db.commit()
        
        # TODO: 通知执行器中断
        
        return {"message": "处理已中断", "pipeline_id": str(pipeline.id)}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"中断管道失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="中断管道失败"
        )


@router.post("/{document_id}/pipeline/{pipeline_id}/resume")
async def resume_pipeline(
    document_id: str,
    pipeline_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """恢复处理管道"""
    try:
        # 验证并获取管道
        pipeline = db.query(ProcessingPipeline).filter(
            ProcessingPipeline.id == pipeline_id,
            ProcessingPipeline.document_id == document_id,
            ProcessingPipeline.user_id == current_user
        ).first()
        
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="管道不存在"
            )
        
        if not pipeline.interrupted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="管道未被中断"
            )
        
        if not pipeline.can_resume:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="管道无法恢复"
            )
        
        # 清除中断标志
        pipeline.interrupted = False
        
        # 重置被中断的阶段
        interrupted_stage = db.query(PipelineStage).filter(
            PipelineStage.pipeline_id == pipeline.id,
            PipelineStage.status == StageStatus.INTERRUPTED
        ).first()
        
        if interrupted_stage:
            interrupted_stage.status = StageStatus.PENDING
            interrupted_stage.message = "等待恢复处理"
        
        db.commit()
        
        # 重新启动后台处理
        background_tasks.add_task(
            execute_pipeline_background,
            pipeline_id=str(pipeline.id),
            db_session=db
        )
        
        return {"message": "处理已恢复", "pipeline_id": str(pipeline.id)}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"恢复管道失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="恢复管道失败"
        )