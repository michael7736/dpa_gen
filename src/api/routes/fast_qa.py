"""
快速问答API - 优化响应时间
专门用于快速响应的问答端点
"""
from typing import Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.qa.optimized_qa_system import (
    create_optimized_qa_system,
    create_hybrid_qa_system,
    OptimizedQAResult
)
from src.api.middleware.auth import get_current_user
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/qa", tags=["fast-qa"])


class FastQARequest(BaseModel):
    """快速问答请求"""
    question: str = Field(..., description="用户问题")
    project_id: Union[str, None] = Field(None, description="项目ID（可选）")
    mode: str = Field(default="fast", description="回答模式: fast|accurate|auto")


class FastQAResponse(BaseModel):
    """快速问答响应"""
    question: str
    answer: str
    confidence_score: float
    context_used: list
    processing_time: float
    metadata: Dict[str, Any]


@router.post("/answer", response_model=FastQAResponse)
async def fast_answer_question(
    request: FastQARequest,
    current_user: str = Depends(get_current_user)
):
    """
    快速问答 - 优化版本
    
    目标响应时间: <1秒
    使用优化的检索和生成策略
    """
    try:
        # 创建优化的问答系统
        qa_system = create_optimized_qa_system(user_id=current_user)
        
        # 根据模式选择策略
        if request.mode == "fast":
            result = await qa_system.fast_answer_question(
                question=request.question,
                project_id=request.project_id,
                top_k=3,
                use_memory=False
            )
        elif request.mode == "accurate":
            result = await qa_system.fast_answer_question(
                question=request.question,
                project_id=request.project_id,
                top_k=8,
                use_memory=True
            )
        else:  # auto mode
            hybrid_system = create_hybrid_qa_system(user_id=current_user)
            result = await hybrid_system.smart_answer(
                question=request.question,
                project_id=request.project_id,
                priority="auto"
            )
        
        return FastQAResponse(
            question=result.question,
            answer=result.answer,
            confidence_score=result.confidence_score,
            context_used=result.context_used,
            processing_time=result.processing_time,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Fast QA error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to answer question: {str(e)}"
        )


class SimpleQARequest(BaseModel):
    """简单问答请求"""
    question: str
    project_id: Optional[str] = None


@router.post("/answer-simple")
async def simple_answer_question(
    request: SimpleQARequest,
    current_user: str = Depends(get_current_user)
):
    """
    超简单问答接口 - 极速响应
    
    最小化参数，最快响应
    """
    try:
        qa_system = create_optimized_qa_system(user_id=current_user)
        
        result = await qa_system.fast_answer_question(
            question=request.question,
            project_id=request.project_id,
            top_k=3,
            use_memory=False
        )
        
        return {
            "answer": result.answer,
            "confidence": result.confidence_score,
            "time": result.processing_time
        }
        
    except Exception as e:
        logger.error(f"Simple QA error: {e}")
        return {
            "answer": "抱歉，当前系统繁忙，请稍后重试。",
            "confidence": 0.0,
            "error": str(e)
        }


@router.get("/test-speed")
async def test_qa_speed(
    current_user: str = Depends(get_current_user)
):
    """
    测试问答速度
    """
    import time
    
    qa_system = create_optimized_qa_system(user_id=current_user)
    
    test_questions = [
        "什么是人工智能？",
        "深度学习的优势是什么？",
        "机器学习有哪些应用？"
    ]
    
    results = []
    total_start = time.time()
    
    for question in test_questions:
        start = time.time()
        try:
            result = await qa_system.fast_answer_question(
                question=question,
                top_k=3,
                use_memory=False
            )
            duration = time.time() - start
            
            results.append({
                "question": question,
                "answer_length": len(result.answer),
                "response_time": duration,
                "confidence": result.confidence_score,
                "status": "success"
            })
        except Exception as e:
            duration = time.time() - start
            results.append({
                "question": question,
                "response_time": duration,
                "status": "error",
                "error": str(e)
            })
    
    total_time = time.time() - total_start
    avg_time = sum(r["response_time"] for r in results) / len(results)
    
    return {
        "test_results": results,
        "summary": {
            "total_questions": len(test_questions),
            "total_time": total_time,
            "average_time": avg_time,
            "success_rate": sum(1 for r in results if r["status"] == "success") / len(results),
            "target_met": avg_time < 1.0  # 目标是1秒以内
        }
    }


@router.post("/benchmark")
async def benchmark_qa_performance(
    iterations: int = 5,
    current_user: str = Depends(get_current_user)
):
    """
    基准测试问答性能
    """
    import time
    import asyncio
    
    qa_system = create_optimized_qa_system(user_id=current_user)
    test_question = "人工智能技术的发展趋势是什么？"
    
    times = []
    errors = 0
    
    for i in range(iterations):
        start = time.time()
        try:
            result = await qa_system.fast_answer_question(
                question=test_question,
                top_k=3,
                use_memory=False
            )
            duration = time.time() - start
            times.append(duration)
        except Exception as e:
            errors += 1
            logger.error(f"Benchmark iteration {i} failed: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        return {
            "benchmark_results": {
                "iterations": iterations,
                "successful": len(times),
                "errors": errors,
                "average_time": avg_time,
                "min_time": min_time,
                "max_time": max_time,
                "times": times,
                "performance_grade": (
                    "优秀" if avg_time < 0.5 else
                    "良好" if avg_time < 1.0 else
                    "一般" if avg_time < 2.0 else
                    "需要优化"
                ),
                "target_achieved": avg_time < 1.0
            }
        }
    else:
        return {
            "benchmark_results": {
                "status": "failed",
                "errors": errors,
                "message": "所有测试都失败了"
            }
        }