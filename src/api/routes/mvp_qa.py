"""
MVP问答系统API路由
集成混合检索的RAG问答服务
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.qa.mvp_qa_system import (
    create_mvp_qa_system,
    QAResult
)
from src.api.middleware.auth import get_current_user
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/qa/mvp", tags=["mvp-qa"])


class QARequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="用户问题")
    project_id: Optional[str] = Field(None, description="项目ID")
    top_k: int = Field(10, ge=1, le=20, description="检索文档数量")
    include_memory: bool = Field(True, description="是否包含记忆库信息")


class BatchQARequest(BaseModel):
    """批量问答请求"""
    questions: List[str] = Field(..., description="问题列表")
    project_id: Optional[str] = Field(None, description="项目ID")
    max_concurrent: int = Field(3, ge=1, le=5, description="最大并发数")


class ContextQARequest(BaseModel):
    """带上下文的问答请求"""
    question: str = Field(..., description="用户问题")
    context: str = Field(..., description="额外上下文")
    project_id: Optional[str] = Field(None, description="项目ID")


class QAResponse(BaseModel):
    """问答响应"""
    question: str
    answer: str
    confidence_score: float
    context_used: List[Dict[str, Any]]
    retrieval_breakdown: Dict[str, int]
    processing_time: float
    metadata: Dict[str, Any]


@router.post("/answer", response_model=QAResponse)
async def answer_question(
    request: QARequest,
    current_user: str = Depends(get_current_user)
):
    """
    回答单个问题
    
    使用三阶段混合检索增强回答质量
    """
    try:
        # 创建问答系统
        qa_system = create_mvp_qa_system(user_id=current_user)
        
        # 回答问题
        result = await qa_system.answer_question(
            question=request.question,
            project_id=request.project_id,
            top_k=request.top_k,
            include_memory=request.include_memory
        )
        
        return QAResponse(
            question=result.question,
            answer=result.answer,
            confidence_score=result.confidence_score,
            context_used=result.context_used,
            retrieval_breakdown=result.retrieval_breakdown,
            processing_time=result.processing_time,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"QA error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post("/batch-answer")
async def batch_answer_questions(
    request: BatchQARequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    批量回答问题
    
    异步处理多个问题
    """
    try:
        qa_system = create_mvp_qa_system(user_id=current_user)
        
        # 异步批量处理
        async def process_batch():
            results = await qa_system.batch_answer(
                questions=request.questions,
                project_id=request.project_id,
                max_concurrent=request.max_concurrent
            )
            # 这里可以保存结果或发送通知
            logger.info(f"Batch QA completed: {len(results)} questions")
            
        background_tasks.add_task(process_batch)
        
        return {
            "message": "Batch processing started",
            "question_count": len(request.questions),
            "project_id": request.project_id
        }
        
    except Exception as e:
        logger.error(f"Batch QA error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch processing: {str(e)}"
        )


@router.post("/answer-with-context", response_model=QAResponse)
async def answer_with_context(
    request: ContextQARequest,
    current_user: str = Depends(get_current_user)
):
    """
    带额外上下文的问答
    
    允许用户提供额外的背景信息
    """
    try:
        qa_system = create_mvp_qa_system(user_id=current_user)
        
        result = await qa_system.answer_with_context(
            question=request.question,
            additional_context=request.context,
            project_id=request.project_id
        )
        
        return QAResponse(
            question=result.question,
            answer=result.answer,
            confidence_score=result.confidence_score,
            context_used=result.context_used,
            retrieval_breakdown=result.retrieval_breakdown,
            processing_time=result.processing_time,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Context QA error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.get("/test")
async def test_qa_system(
    current_user: str = Depends(get_current_user)
):
    """
    测试问答系统
    
    使用预定义的测试问题
    """
    try:
        qa_system = create_mvp_qa_system(user_id=current_user)
        
        # 测试问题
        test_questions = [
            "什么是深度学习？",
            "CNN和RNN有什么区别？",
            "Transformer架构的主要优势是什么？"
        ]
        
        results = []
        for question in test_questions:
            try:
                result = await qa_system.answer_question(
                    question=question,
                    top_k=5
                )
                results.append({
                    "question": question,
                    "answer": result.answer[:200] + "..." if len(result.answer) > 200 else result.answer,
                    "confidence": result.confidence_score,
                    "sources": len(result.context_used)
                })
            except Exception as e:
                results.append({
                    "question": question,
                    "error": str(e)
                })
                
        return {
            "test_results": results,
            "user_id": current_user
        }
        
    except Exception as e:
        logger.error(f"Test QA error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )


@router.get("/stats/{project_id}")
async def get_qa_stats(
    project_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    获取项目的问答统计信息
    """
    try:
        # 这里可以从数据库获取统计信息
        # MVP版本返回模拟数据
        return {
            "project_id": project_id,
            "total_questions": 42,
            "average_confidence": 0.82,
            "average_response_time": 2.3,
            "top_topics": [
                {"topic": "深度学习", "count": 15},
                {"topic": "神经网络", "count": 12},
                {"topic": "机器学习", "count": 10}
            ],
            "retrieval_sources": {
                "vector": 120,
                "graph": 45,
                "memory": 30
            }
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )