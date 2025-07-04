"""
知识问答API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...graphs.basic_knowledge_qa import BasicKnowledgeQA, QAEnhancer
from ...services.cache_service import CacheManager
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/qa", tags=["qa"])


class QuestionRequest(BaseModel):
    """问题请求模型"""
    question: str = Field(..., description="用户问题")
    project_id: str = Field(..., description="项目ID")
    include_sources: bool = Field(True, description="是否返回来源信息")
    include_follow_ups: bool = Field(False, description="是否生成后续问题建议")


class QuestionResponse(BaseModel):
    """问题响应模型"""
    answer: str
    confidence: float
    sources: Optional[List[dict]] = None
    follow_up_questions: Optional[List[str]] = None
    response_time: float
    from_cache: bool


class BatchQuestionRequest(BaseModel):
    """批量问题请求"""
    questions: List[dict] = Field(..., description="问题列表")
    project_id: str = Field(..., description="项目ID")


# 创建全局实例
qa_system = BasicKnowledgeQA()
cache_manager = CacheManager()


@router.post("/answer", response_model=QuestionResponse)
async def answer_question(request: QuestionRequest):
    """
    回答单个问题
    
    - 使用RAG技术从项目知识库中检索相关信息
    - 基于检索到的上下文生成答案
    - 返回答案、置信度和来源信息
    """
    try:
        # 回答问题
        result = await qa_system.answer_question(
            question=request.question,
            project_id=request.project_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        response = QuestionResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result["sources"] if request.include_sources else None,
            response_time=result["response_time"],
            from_cache=result.get("from_cache", False),
            follow_up_questions=None
        )
        
        # 生成后续问题（如果需要）
        if request.include_follow_ups and result["confidence"] > 0.5:
            follow_ups = await QAEnhancer.suggest_follow_ups(
                question=request.question,
                answer=result["answer"],
                llm=qa_system.llm
            )
            response.follow_up_questions = follow_ups
        
        return response
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-answer")
async def batch_answer_questions(request: BatchQuestionRequest):
    """
    批量回答问题
    
    - 支持一次性提交多个问题
    - 并行处理提高效率
    - 适用于FAQ或批量测试场景
    """
    try:
        # 准备问题列表
        questions = [
            {
                "id": q.get("id", i),
                "question": q["question"],
                "project_id": request.project_id
            }
            for i, q in enumerate(request.questions)
        ]
        
        # 批量回答
        results = await qa_system.batch_answer(questions)
        
        return {
            "success": True,
            "total": len(questions),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-stats")
async def get_cache_statistics():
    """
    获取缓存统计信息
    
    - 缓存命中率
    - 缓存大小
    - Redis连接状态
    """
    try:
        stats = qa_system.cache_service.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-cache")
async def clear_project_cache(project_id: str):
    """
    清除项目缓存
    
    - 清除指定项目的所有问答缓存
    - 用于数据更新后刷新缓存
    """
    try:
        cleared = await cache_manager.invalidate_project_cache(project_id)
        return {
            "success": True,
            "message": f"Cleared {cleared} cache entries for project {project_id}"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-answer")
async def evaluate_answer_quality(
    question: str,
    answer: str,
    sources: List[dict]
):
    """
    评估答案质量
    
    - 分析答案的完整性和准确性
    - 评估来源的相关性
    - 提供改进建议
    """
    try:
        quality = QAEnhancer.calculate_answer_quality(answer, sources)
        
        # 生成改进建议
        suggestions = []
        if quality["metrics"]["answer_length"] < 50:
            suggestions.append("答案过于简短，可能需要提供更多细节")
        if quality["metrics"]["avg_source_score"] < 0.7:
            suggestions.append("检索到的内容相关性较低，可能需要优化问题表述")
        if quality["metrics"]["source_diversity"] < 2:
            suggestions.append("答案来源单一，可能需要更多样化的信息源")
        
        return {
            "success": True,
            "quality_score": quality["quality_score"],
            "metrics": quality["metrics"],
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error evaluating answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 健康检查端点
@router.get("/health")
async def health_check():
    """QA系统健康检查"""
    try:
        # 检查各组件状态
        cache_connected = qa_system.cache_service._redis_client is not None
        
        return {
            "status": "healthy",
            "components": {
                "qa_system": "ready",
                "cache": "connected" if cache_connected else "local_only",
                "vector_store": "ready"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }