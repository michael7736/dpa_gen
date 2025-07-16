"""
文档操作API路由
支持对文档执行摘要、索引、分析等操作
"""

import asyncio
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...models.document import Document, ProcessingStatus
from ...models.processing_pipeline import ProcessingPipeline, PipelineStage, StageStatus, ProcessingStage
from ...services.project_service import ProjectService
from ...services.pipeline_executor import PipelineExecutor, get_pipeline_executor
from ...utils.logger import get_logger
from ..middleware.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["document-operations"])


class DocumentOperationRequest(BaseModel):
    """文档操作请求"""
    operation: str = Field(..., description="操作类型: summary, index, analysis")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作参数")


class DocumentOperationResponse(BaseModel):
    """文档操作响应"""
    success: bool
    message: str
    pipeline_id: Optional[str] = None
    operation: str
    estimated_time: Optional[int] = None


class StartProcessingRequest(BaseModel):
    """启动处理请求"""
    upload_only: bool = False
    generate_summary: bool = False
    create_index: bool = False
    deep_analysis: bool = False


@router.post("/{document_id}/operations/start", response_model=DocumentOperationResponse)
async def start_document_operation(
    document_id: str,
    request: StartProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    启动文档处理操作
    """
    try:
        # 获取文档
        document = db.query(Document).filter(
            Document.id == UUID(document_id)
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 处理用户ID
        user_uuid = None
        if current_user == "u1":
            user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        else:
            try:
                user_uuid = UUID(current_user)
            except ValueError:
                user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        
        # 检查是否已有正在进行的处理
        active_pipeline = db.query(ProcessingPipeline).filter(
            ProcessingPipeline.document_id == document.id,
            ProcessingPipeline.completed == False,
            ProcessingPipeline.interrupted == False
        ).first()
        
        if active_pipeline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该文档已有正在进行的处理任务"
            )
        
        # 创建处理管道
        pipeline = ProcessingPipeline(
            document_id=document.id,
            user_id=user_uuid,
            processing_options={
                "generate_summary": request.generate_summary,
                "create_index": request.create_index,
                "deep_analysis": request.deep_analysis
            }
        )
        db.add(pipeline)
        db.flush()
        
        # 创建处理阶段
        stages = []
        total_time = 0
        
        if request.generate_summary:
            summary_stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_type=ProcessingStage.SUMMARY,
                stage_name="生成摘要",
                status=StageStatus.PENDING,
                estimated_time=30,
                can_interrupt=True
            )
            stages.append(summary_stage)
            total_time += 30
        
        if request.create_index:
            index_stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_type=ProcessingStage.INDEX,
                stage_name="创建索引",
                status=StageStatus.PENDING,
                estimated_time=120,
                can_interrupt=True
            )
            stages.append(index_stage)
            total_time += 120
        
        if request.deep_analysis:
            analysis_stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_type=ProcessingStage.ANALYSIS,
                stage_name="深度分析",
                status=StageStatus.PENDING,
                estimated_time=300,
                can_interrupt=True
            )
            stages.append(analysis_stage)
            total_time += 300
        
        # 批量添加阶段
        for stage in stages:
            db.add(stage)
        
        db.commit()
        
        # 启动后台处理
        if stages:
            background_tasks.add_task(
                execute_pipeline_background,
                pipeline_id=str(pipeline.id),
                db_session=db
            )
        
        # 确定操作类型
        operation = "unknown"
        if request.generate_summary:
            operation = "summary"
        elif request.create_index:
            operation = "index"
        elif request.deep_analysis:
            operation = "analysis"
        
        return DocumentOperationResponse(
            success=True,
            message="处理已启动",
            pipeline_id=str(pipeline.id),
            operation=operation,
            estimated_time=total_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动文档操作失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动操作失败: {str(e)}"
        )


@router.get("/{document_id}/operations/status")
async def get_document_operation_status(
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    获取文档操作状态
    """
    try:
        # 获取文档
        document = db.query(Document).filter(
            Document.id == UUID(document_id)
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 获取所有相关管道
        pipelines = db.query(ProcessingPipeline).filter(
            ProcessingPipeline.document_id == document.id
        ).order_by(ProcessingPipeline.created_at.desc()).limit(5).all()
        
        # 构建响应
        pipeline_info = []
        for pipeline in pipelines:
            # 获取阶段信息
            stages = db.query(PipelineStage).filter(
                PipelineStage.pipeline_id == pipeline.id
            ).all()
            
            stage_info = []
            for stage in stages:
                stage_data = {
                    "type": stage.stage_type,
                    "name": stage.stage_name,
                    "status": stage.status,
                    "progress": stage.progress,
                    "message": stage.message,
                    "can_interrupt": stage.can_interrupt
                }
                
                if stage.started_at:
                    stage_data["started_at"] = stage.started_at.isoformat()
                if stage.completed_at:
                    stage_data["completed_at"] = stage.completed_at.isoformat()
                    stage_data["duration"] = stage.duration
                if stage.error:
                    stage_data["error"] = stage.error
                    
                stage_info.append(stage_data)
            
            pipeline_info.append({
                "pipeline_id": str(pipeline.id),
                "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
                "overall_progress": pipeline.overall_progress,
                "current_stage": pipeline.current_stage,
                "completed": pipeline.completed,
                "interrupted": pipeline.interrupted,
                "stages": stage_info
            })
        
        # 获取文档的处理历史摘要
        summary_completed = any(
            stage.stage_type == ProcessingStage.SUMMARY and stage.status == StageStatus.COMPLETED
            for pipeline in pipelines
            for stage in db.query(PipelineStage).filter(PipelineStage.pipeline_id == pipeline.id).all()
        )
        
        index_completed = any(
            stage.stage_type == ProcessingStage.INDEX and stage.status == StageStatus.COMPLETED
            for pipeline in pipelines
            for stage in db.query(PipelineStage).filter(PipelineStage.pipeline_id == pipeline.id).all()
        )
        
        analysis_completed = any(
            stage.stage_type == ProcessingStage.ANALYSIS and stage.status == StageStatus.COMPLETED
            for pipeline in pipelines
            for stage in db.query(PipelineStage).filter(PipelineStage.pipeline_id == pipeline.id).all()
        )
        
        return {
            "document_id": str(document.id),
            "document_status": document.processing_status,
            "operations_summary": {
                "summary_completed": summary_completed,
                "index_completed": index_completed,
                "analysis_completed": analysis_completed
            },
            "pipelines": pipeline_info,
            "has_active_pipeline": any(not p.completed and not p.interrupted for p in pipelines)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取操作状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取操作状态失败"
        )


@router.post("/{document_id}/operations/{operation}/execute")
async def execute_single_operation(
    document_id: str,
    operation: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    执行单个文档操作
    """
    # 映射操作到处理选项
    operation_map = {
        "summary": {"generate_summary": True},
        "index": {"create_index": True},
        "analysis": {"deep_analysis": True}
    }
    
    if operation not in operation_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的操作: {operation}"
        )
    
    # 构建请求
    request = StartProcessingRequest(**operation_map[operation])
    
    # 调用通用处理函数
    return await start_document_operation(
        document_id=document_id,
        request=request,
        background_tasks=background_tasks,
        db=db,
        current_user=current_user
    )


async def execute_pipeline_background(pipeline_id: str, db_session: Session):
    """后台执行处理管道"""
    try:
        executor = get_pipeline_executor()
        await executor.execute(pipeline_id, db_session)
    except Exception as e:
        logger.error(f"管道执行失败: {pipeline_id} - {e}")