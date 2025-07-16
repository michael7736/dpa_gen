"""
文档二次处理API路由
支持对已上传文档进行摘要、索引、分析等处理
"""

import asyncio
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.postgresql import get_db_session
from ...models.document import Document, ProcessingStatus
from ...models.processing_pipeline import ProcessingPipeline, PipelineStage, StageStatus, ProcessingStage
from ...services.pipeline_executor import PipelineExecutor
from ...services.summary_service import SummaryService
from ...services.index_service import IndexService
from ...graphs.advanced_document_analyzer import AdvancedDocumentAnalyzer, AnalysisDepth
from ...utils.logger import get_logger
from ..middleware.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["document-processing"])


class ProcessingRequest(BaseModel):
    """文档处理请求"""
    generate_summary: bool = Field(False, description="生成摘要")
    create_index: bool = Field(False, description="创建索引") 
    deep_analysis: bool = Field(False, description="深度分析")
    analysis_depth: Optional[AnalysisDepth] = Field(AnalysisDepth.STANDARD, description="分析深度")
    analysis_goal: Optional[str] = Field(None, description="分析目标")


class ProcessingResponse(BaseModel):
    """处理响应"""
    document_id: str
    pipeline_id: Optional[str]
    message: str
    processing_tasks: list[str]


@router.post("/{document_id}/process", response_model=ProcessingResponse)
async def process_document(
    document_id: str,
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    对已上传的文档进行二次处理
    
    支持的处理选项：
    - generate_summary: 生成文档摘要
    - create_index: 创建向量索引
    - deep_analysis: 进行深度分析
    """
    try:
        # 查询文档
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 检查文档状态
        if document.processing_status in [ProcessingStatus.PROCESSING, ProcessingStatus.SUMMARIZING, 
                                         ProcessingStatus.INDEXING, ProcessingStatus.ANALYZING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文档正在处理中，请稍后再试"
            )
        
        # 确定需要执行的任务
        tasks = []
        
        # 摘要只能生成一次（除非文档只是上传状态）
        if request.generate_summary and document.processing_status == ProcessingStatus.UPLOADED:
            tasks.append("生成摘要")
        elif request.generate_summary and document.summary:
            logger.info(f"文档 {document_id} 已有摘要，跳过生成")
        
        # 索引只能创建一次（除非还未创建）
        if request.create_index and document.processing_status in [ProcessingStatus.UPLOADED, ProcessingStatus.SUMMARIZED]:
            tasks.append("创建索引")
        elif request.create_index and document.processing_status in [ProcessingStatus.INDEXED, ProcessingStatus.ANALYZED, ProcessingStatus.COMPLETED]:
            logger.info(f"文档 {document_id} 已创建索引，跳过")
            
        # 分析可以多次进行（每次都会保存新的分析结果）
        if request.deep_analysis:
            tasks.append("深度分析")
        
        if not tasks:
            return ProcessingResponse(
                document_id=str(document.id),
                pipeline_id=None,
                message="文档已完成所请求的处理，无需重复处理",
                processing_tasks=[]
            )
        
        # 创建处理管道
        pipeline = ProcessingPipeline(
            document_id=document.id,
            user_id=UUID(current_user) if current_user != 'u1' else UUID("243588ff-459d-45b8-b77b-09aec3946a64"),
            processing_options={
                "generate_summary": request.generate_summary,
                "create_index": request.create_index,
                "deep_analysis": request.deep_analysis,
                "analysis_depth": request.analysis_depth.value if request.analysis_depth else "standard",
                "analysis_goal": request.analysis_goal
            }
        )
        db.add(pipeline)
        db.flush()
        
        # 创建处理阶段
        stages = []
        stage_order = 0
        
        if request.generate_summary:
            summary_stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_type=ProcessingStage.SUMMARY,
                stage_name="生成摘要",
                status=StageStatus.PENDING,
                estimated_time=30,
                order_index=stage_order
            )
            stages.append(summary_stage)
            stage_order += 1
        
        if request.create_index:
            index_stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_type=ProcessingStage.INDEX,
                stage_name="创建索引",
                status=StageStatus.PENDING,
                estimated_time=120,
                order_index=stage_order
            )
            stages.append(index_stage)
            stage_order += 1
        
        if request.deep_analysis:
            analysis_stage = PipelineStage(
                pipeline_id=pipeline.id,
                stage_type=ProcessingStage.ANALYSIS,
                stage_name="深度分析",
                status=StageStatus.PENDING,
                estimated_time=300,
                order_index=stage_order
            )
            stages.append(analysis_stage)
            stage_order += 1
        
        # 批量添加阶段
        for stage in stages:
            db.add(stage)
        
        db.commit()
        
        # 启动后台处理
        background_tasks.add_task(
            execute_document_processing,
            document_id=str(document.id),
            pipeline_id=str(pipeline.id),
            db_session=db
        )
        
        return ProcessingResponse(
            document_id=str(document.id),
            pipeline_id=str(pipeline.id),
            message=f"文档处理已启动，将执行以下任务：{', '.join(tasks)}",
            processing_tasks=tasks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"文档处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}"
        )


@router.get("/{document_id}/summary")
async def get_document_summary(
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """获取文档摘要"""
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    if not document.summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档尚未生成摘要"
        )
    
    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "summary": document.summary,
        "generated_at": document.updated_at
    }


@router.get("/{document_id}/analysis")
async def get_document_analysis(
    document_id: str,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """获取文档分析结果"""
    # 查询最新的分析结果
    from ...models.analysis import DocumentAnalysis
    
    analysis = db.query(DocumentAnalysis).filter(
        DocumentAnalysis.document_id == document_id
    ).order_by(DocumentAnalysis.created_at.desc()).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档尚未进行深度分析"
        )
    
    return {
        "document_id": str(analysis.document_id),
        "analysis_id": str(analysis.id),
        "analysis_type": analysis.analysis_type,
        "depth_level": analysis.depth_level,
        "executive_summary": analysis.executive_summary,
        "key_insights": analysis.key_insights,
        "action_items": analysis.action_items,
        "detailed_report": analysis.detailed_report,
        "visualizations": analysis.visualizations,
        "metadata": analysis.metadata_info,
        "created_at": analysis.created_at
    }


async def execute_document_processing(document_id: str, pipeline_id: str, db_session: Session):
    """后台执行文档处理"""
    try:
        executor = PipelineExecutor()
        await executor.execute(pipeline_id, db_session)
    except Exception as e:
        logger.error(f"文档处理执行失败: {document_id} - {e}")
        
        # 更新文档状态为失败
        document = db_session.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processing_status = ProcessingStatus.FAILED
            db_session.commit()