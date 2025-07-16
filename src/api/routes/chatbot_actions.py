"""
Chatbot操作API端点
支持通过对话形式执行文档处理任务
"""

import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...models.document import Document
from ...models.processing_pipeline import ProcessingPipeline, PipelineStage, StageStatus, ProcessingStage
from ...services.summary_service import SummaryService
from ...services.index_service import IndexService
from ...services.pipeline_executor import PipelineExecutor
from ...utils.logger import get_logger
from ..middleware.auth import get_current_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])


class ChatbotActionRequest(BaseModel):
    """Chatbot操作请求"""
    action: str = Field(..., description="操作类型：summary, index, analyze, status")
    document_id: str = Field(..., description="文档ID")
    message: str = Field(..., description="用户消息")
    project_id: Optional[str] = Field(None, description="项目ID")


class ChatbotActionResponse(BaseModel):
    """Chatbot操作响应"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    pipeline_id: Optional[str] = None


@router.post("/action", response_model=ChatbotActionResponse)
async def execute_chatbot_action(
    request: ChatbotActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    current_user: str = Depends(get_current_user)
):
    """
    执行chatbot操作
    
    支持的操作：
    - summary: 生成文档摘要
    - index: 创建文档索引
    - analyze: 深度分析文档
    - status: 查看文档状态
    """
    try:
        # 获取文档
        document = db.query(Document).filter(
            Document.id == UUID(request.document_id)
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail="文档不存在"
            )
        
        # 处理用户ID格式
        user_uuid = None
        if current_user == "u1":
            user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        else:
            try:
                user_uuid = UUID(current_user)
            except ValueError:
                user_uuid = UUID("243588ff-459d-45b8-b77b-09aec3946a64")
        
        # 根据操作类型执行不同的处理
        if request.action == "status":
            return await handle_status_request(document, db)
        
        elif request.action == "summary":
            return await handle_summary_request(document, user_uuid, background_tasks, db)
        
        elif request.action == "index":
            return await handle_index_request(document, user_uuid, background_tasks, db)
        
        elif request.action == "analyze":
            return await handle_analyze_request(document, user_uuid, background_tasks, db)
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的操作类型: {request.action}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chatbot操作失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"操作失败: {str(e)}"
        )


async def handle_status_request(document: Document, db: Session) -> ChatbotActionResponse:
    """处理状态查询请求"""
    try:
        # 查看是否有正在进行的处理管道
        active_pipeline = db.query(ProcessingPipeline).filter(
            ProcessingPipeline.document_id == document.id,
            ProcessingPipeline.completed == False
        ).first()
        
        status_info = {
            "document_id": str(document.id),
            "filename": document.filename,
            "current_status": document.processing_status,
            "file_size": document.file_size,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "has_active_pipeline": active_pipeline is not None
        }
        
        if active_pipeline:
            stages = db.query(PipelineStage).filter(
                PipelineStage.pipeline_id == active_pipeline.id
            ).all()
            
            stage_info = []
            for stage in stages:
                stage_info.append({
                    "name": stage.stage_name,
                    "status": stage.status,
                    "progress": stage.progress,
                    "message": stage.message
                })
            
            status_info["pipeline_progress"] = {
                "pipeline_id": str(active_pipeline.id),
                "overall_progress": active_pipeline.overall_progress,
                "current_stage": active_pipeline.current_stage,
                "stages": stage_info
            }
        
        message = f"文档 '{document.filename}' 状态：{document.processing_status}"
        if active_pipeline:
            message += f"，处理进度：{active_pipeline.overall_progress:.1f}%"
        
        return ChatbotActionResponse(
            success=True,
            message=message,
            data=status_info
        )
        
    except Exception as e:
        logger.error(f"状态查询失败: {e}")
        return ChatbotActionResponse(
            success=False,
            message=f"状态查询失败: {str(e)}"
        )


async def handle_summary_request(
    document: Document, 
    user_uuid: UUID, 
    background_tasks: BackgroundTasks,
    db: Session
) -> ChatbotActionResponse:
    """处理摘要生成请求"""
    try:
        # 创建处理管道
        pipeline = ProcessingPipeline(
            document_id=document.id,
            user_id=user_uuid,
            processing_options={"generate_summary": True}
        )
        db.add(pipeline)
        db.flush()
        
        # 创建摘要阶段
        summary_stage = PipelineStage(
            pipeline_id=pipeline.id,
            stage_type=ProcessingStage.SUMMARY,
            stage_name="生成摘要",
            status=StageStatus.PENDING,
            estimated_time=30
        )
        db.add(summary_stage)
        db.commit()
        
        # 启动后台处理
        background_tasks.add_task(
            execute_summary_task,
            pipeline_id=str(pipeline.id),
            db_session=db
        )
        
        return ChatbotActionResponse(
            success=True,
            message=f"正在为文档 '{document.filename}' 生成摘要，请稍候...",
            pipeline_id=str(pipeline.id)
        )
        
    except Exception as e:
        logger.error(f"摘要生成请求失败: {e}")
        return ChatbotActionResponse(
            success=False,
            message=f"摘要生成请求失败: {str(e)}"
        )


async def handle_index_request(
    document: Document,
    user_uuid: UUID,
    background_tasks: BackgroundTasks,
    db: Session
) -> ChatbotActionResponse:
    """处理索引创建请求"""
    try:
        # 创建处理管道
        pipeline = ProcessingPipeline(
            document_id=document.id,
            user_id=user_uuid,
            processing_options={"create_index": True}
        )
        db.add(pipeline)
        db.flush()
        
        # 创建索引阶段
        index_stage = PipelineStage(
            pipeline_id=pipeline.id,
            stage_type=ProcessingStage.INDEX,
            stage_name="创建索引",
            status=StageStatus.PENDING,
            estimated_time=120
        )
        db.add(index_stage)
        db.commit()
        
        # 启动后台处理
        background_tasks.add_task(
            execute_index_task,
            pipeline_id=str(pipeline.id),
            db_session=db
        )
        
        return ChatbotActionResponse(
            success=True,
            message=f"正在为文档 '{document.filename}' 创建索引，请稍候...",
            pipeline_id=str(pipeline.id)
        )
        
    except Exception as e:
        logger.error(f"索引创建请求失败: {e}")
        return ChatbotActionResponse(
            success=False,
            message=f"索引创建请求失败: {str(e)}"
        )


async def handle_analyze_request(
    document: Document,
    user_uuid: UUID,
    background_tasks: BackgroundTasks,
    db: Session
) -> ChatbotActionResponse:
    """处理深度分析请求"""
    try:
        # 创建处理管道
        pipeline = ProcessingPipeline(
            document_id=document.id,
            user_id=user_uuid,
            processing_options={"deep_analysis": True}
        )
        db.add(pipeline)
        db.flush()
        
        # 创建分析阶段
        analysis_stage = PipelineStage(
            pipeline_id=pipeline.id,
            stage_type=ProcessingStage.ANALYSIS,
            stage_name="深度分析",
            status=StageStatus.PENDING,
            estimated_time=300
        )
        db.add(analysis_stage)
        db.commit()
        
        # 启动后台处理
        background_tasks.add_task(
            execute_analysis_task,
            pipeline_id=str(pipeline.id),
            db_session=db
        )
        
        return ChatbotActionResponse(
            success=True,
            message=f"正在对文档 '{document.filename}' 进行深度分析，请稍候...",
            pipeline_id=str(pipeline.id)
        )
        
    except Exception as e:
        logger.error(f"深度分析请求失败: {e}")
        return ChatbotActionResponse(
            success=False,
            message=f"深度分析请求失败: {str(e)}"
        )


async def execute_summary_task(pipeline_id: str, db_session: Session):
    """执行摘要生成任务"""
    try:
        executor = PipelineExecutor()
        await executor.execute(pipeline_id, db_session)
    except Exception as e:
        logger.error(f"摘要生成任务失败: {pipeline_id} - {e}")


async def execute_index_task(pipeline_id: str, db_session: Session):
    """执行索引创建任务"""
    try:
        executor = PipelineExecutor()
        await executor.execute(pipeline_id, db_session)
    except Exception as e:
        logger.error(f"索引创建任务失败: {pipeline_id} - {e}")


async def execute_analysis_task(pipeline_id: str, db_session: Session):
    """执行深度分析任务"""
    try:
        executor = PipelineExecutor()
        await executor.execute(pipeline_id, db_session)
    except Exception as e:
        logger.error(f"深度分析任务失败: {pipeline_id} - {e}")


@router.get("/actions")
async def get_available_actions():
    """获取可用的操作列表"""
    return {
        "actions": [
            {
                "name": "status",
                "description": "查看文档处理状态",
                "examples": ["查看文档状态", "这个文档处理得怎么样了？"]
            },
            {
                "name": "summary", 
                "description": "生成文档摘要",
                "examples": ["生成摘要", "帮我总结这个文档", "这个文档讲了什么？"]
            },
            {
                "name": "index",
                "description": "创建文档索引",
                "examples": ["创建索引", "建立索引", "让我可以搜索这个文档"]
            },
            {
                "name": "analyze",
                "description": "深度分析文档",
                "examples": ["深度分析", "详细分析这个文档", "帮我分析文档内容"]
            }
        ]
    }