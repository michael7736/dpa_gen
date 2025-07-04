"""
记忆增强的问答API
集成记忆系统提供个性化问答体验
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...graphs.memory_enhanced_qa import MemoryEnhancedQA, MemoryBasedRecommender
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/enhanced-qa", tags=["enhanced-qa"])


class EnhancedQuestionRequest(BaseModel):
    """增强问答请求"""
    question: str = Field(..., description="用户问题")
    project_id: str = Field(..., description="项目ID")
    user_id: str = Field(..., description="用户ID")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    use_memory: bool = Field(True, description="是否使用记忆增强")
    include_context: bool = Field(False, description="是否返回使用的上下文")


class EnhancedQuestionResponse(BaseModel):
    """增强问答响应"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    memory_context: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    response_time: float


@router.post("/answer", response_model=EnhancedQuestionResponse)
async def enhanced_answer(
    request: EnhancedQuestionRequest,
    db: Session = Depends(get_db_session)
):
    """
    记忆增强的问答
    
    特性：
    - 使用项目记忆提供上下文
    - 根据用户偏好个性化回答
    - 记录对话历史
    - 推荐相关查询
    """
    try:
        qa_system = MemoryEnhancedQA(db)
        
        if request.use_memory:
            # 使用记忆增强
            result = await qa_system.answer_with_memory(
                question=request.question,
                project_id=request.project_id,
                user_id=request.user_id,
                conversation_id=request.conversation_id
            )
        else:
            # 使用基础问答
            result = await qa_system.answer_question(
                question=request.question,
                project_id=request.project_id
            )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        response = EnhancedQuestionResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result["sources"],
            response_time=result["response_time"]
        )
        
        # 获取记忆上下文
        if request.include_context and request.use_memory:
            memory_context = await qa_system.get_memory_enhanced_context(
                project_id=request.project_id,
                user_id=request.user_id,
                query=request.question
            )
            response.memory_context = memory_context
        
        # 获取推荐
        if result["confidence"] > 0.5:
            recommender = MemoryBasedRecommender(db)
            recommendations = await recommender.recommend_next_queries(
                project_id=request.project_id,
                user_id=request.user_id,
                current_query=request.question
            )
            response.recommendations = recommendations
        
        return response
        
    except Exception as e:
        logger.error(f"Enhanced QA error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/queries")
async def get_query_recommendations(
    project_id: str,
    user_id: str,
    current_query: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """
    获取查询推荐
    
    基于：
    - 项目常见查询
    - 用户兴趣
    - 当前查询上下文
    """
    try:
        recommender = MemoryBasedRecommender(db)
        
        if current_query:
            recommendations = await recommender.recommend_next_queries(
                project_id=project_id,
                user_id=user_id,
                current_query=current_query
            )
        else:
            # 获取通用推荐
            from ...services.memory_service import ProjectMemoryService
            service = ProjectMemoryService(db)
            memory = await service.get_or_create_project_memory(project_id)
            
            recommendations = [
                fq["query"] for fq in (memory.frequent_queries or [])[:5]
            ]
        
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/documents")
async def get_document_recommendations(
    project_id: str,
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """
    获取文档推荐
    
    基于：
    - 项目重要文档
    - 用户浏览历史
    - 相关性评分
    """
    try:
        recommender = MemoryBasedRecommender(db)
        recommendations = await recommender.recommend_documents(
            project_id=project_id,
            user_id=user_id
        )
        
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Document recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversation/summary")
async def generate_conversation_summary(
    conversation_id: str,
    db: Session = Depends(get_db_session)
):
    """
    生成对话摘要
    
    分析对话历史，提取：
    - 主要主题
    - 关键决定
    - 重要信息
    """
    try:
        from ...services.memory_service import ConversationMemoryService
        service = ConversationMemoryService(db)
        
        # 获取对话历史
        context = await service.get_conversation_context(conversation_id, last_n_turns=20)
        
        if not context:
            raise HTTPException(status_code=404, detail="No conversation history found")
        
        # 提取关键信息
        topics = set()
        important_turns = []
        
        for turn in context:
            if turn.get("topics"):
                topics.update(turn["topics"])
            if turn.get("important"):
                important_turns.append({
                    "turn": turn["turn"],
                    "summary": turn["user"][:100] + "..."
                })
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "turn_count": len(context),
            "main_topics": list(topics),
            "important_turns": important_turns,
            "summary": f"对话包含{len(context)}轮交互，主要讨论了{', '.join(list(topics)[:3])}"
        }
        
    except Exception as e:
        logger.error(f"Conversation summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/qa-profile")
async def get_user_qa_profile(
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """
    获取用户问答画像
    
    包括：
    - 偏好设置
    - 查询习惯
    - 兴趣领域
    - 活跃时段
    """
    try:
        from ...services.memory_service import UserMemoryService
        service = UserMemoryService(db)
        
        memory = await service.get_or_create_user_memory(user_id)
        context = await service.get_user_context(user_id)
        
        # 分析查询模式
        query_patterns = memory.query_patterns or []
        pattern_stats = {}
        for pattern in query_patterns:
            p_type = pattern.get("pattern", "unknown")
            pattern_stats[p_type] = pattern_stats.get(p_type, 0) + 1
        
        # 分析活跃时段
        active_hours = memory.active_hours or {}
        peak_hours = sorted(active_hours.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "user_id": user_id,
            "preferences": context["preferences"],
            "interests": memory.interests or [],
            "expertise_areas": memory.expertise_areas or [],
            "query_patterns": pattern_stats,
            "peak_hours": [int(h[0]) for h in peak_hours],
            "total_queries": sum(pattern_stats.values()),
            "favorite_projects": memory.favorite_projects or []
        }
        
    except Exception as e:
        logger.error(f"User profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))