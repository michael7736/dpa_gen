"""
记忆系统API端点
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...models.memory import (
    MemoryCreate, MemoryUpdate, MemoryQuery,
    ProjectMemoryUpdate, UserPreferenceUpdate,
    MemoryType, MemoryScope
)
from ...services.memory_service import (
    MemoryService, ProjectMemoryService, 
    UserMemoryService, ConversationMemoryService
)
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


# 通用记忆管理
@router.post("/")
async def create_memory(
    memory_data: MemoryCreate,
    db: Session = Depends(get_db_session)
):
    """
    创建新的记忆记录
    
    支持多种记忆类型和作用域：
    - 项目级记忆
    - 用户级记忆
    - 会话级记忆
    """
    try:
        service = MemoryService(db)
        memory = await service.create_memory(memory_data)
        
        return {
            "success": True,
            "memory_id": memory.id,
            "message": f"Memory created: {memory.memory_type}/{memory.key}"
        }
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}")
async def get_memory(
    memory_id: str,
    db: Session = Depends(get_db_session)
):
    """获取特定记忆"""
    service = MemoryService(db)
    memory = await service.get_memory(memory_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return memory


@router.post("/query")
async def query_memories(
    query: MemoryQuery,
    db: Session = Depends(get_db_session)
):
    """
    查询记忆
    
    支持多种过滤条件：
    - 记忆类型
    - 作用域
    - 用户/项目ID
    - 重要性阈值
    """
    try:
        service = MemoryService(db)
        memories = await service.query_memories(query)
        
        return {
            "success": True,
            "count": len(memories),
            "memories": memories
        }
    except Exception as e:
        logger.error(f"Failed to query memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{memory_id}")
async def update_memory(
    memory_id: str,
    update_data: MemoryUpdate,
    db: Session = Depends(get_db_session)
):
    """更新记忆"""
    service = MemoryService(db)
    memory = await service.update_memory(memory_id, update_data)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {
        "success": True,
        "message": "Memory updated",
        "memory": memory
    }


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    db: Session = Depends(get_db_session)
):
    """删除记忆"""
    service = MemoryService(db)
    success = await service.delete_memory(memory_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {
        "success": True,
        "message": "Memory deleted"
    }


# 项目记忆管理
@router.get("/project/{project_id}")
async def get_project_memory(
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """获取项目记忆"""
    service = ProjectMemoryService(db)
    memory = await service.get_or_create_project_memory(project_id)
    
    return {
        "project_id": project_id,
        "context_summary": memory.context_summary,
        "key_concepts": memory.key_concepts,
        "research_goals": memory.research_goals,
        "learned_facts": memory.learned_facts,
        "important_documents": memory.important_documents,
        "statistics": {
            "total_documents": memory.total_documents,
            "total_queries": memory.total_queries,
            "avg_confidence": memory.avg_confidence
        },
        "last_activity": memory.last_activity_at,
        "version": memory.memory_version
    }


@router.put("/project/{project_id}")
async def update_project_memory(
    project_id: str,
    update_data: ProjectMemoryUpdate,
    db: Session = Depends(get_db_session)
):
    """更新项目记忆"""
    try:
        service = ProjectMemoryService(db)
        memory = await service.update_project_memory(project_id, update_data)
        
        return {
            "success": True,
            "message": "Project memory updated",
            "version": memory.memory_version
        }
    except Exception as e:
        logger.error(f"Failed to update project memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/project/{project_id}/learn")
async def add_learned_fact(
    project_id: str,
    fact: str,
    confidence: float = Query(0.8, ge=0, le=1),
    source: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """添加学习到的事实"""
    try:
        service = ProjectMemoryService(db)
        await service.add_learned_fact(project_id, fact, confidence, source)
        
        return {
            "success": True,
            "message": "Learned fact added to project memory"
        }
    except Exception as e:
        logger.error(f"Failed to add learned fact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/project/{project_id}/query-record")
async def record_project_query(
    project_id: str,
    query: str,
    success: bool = True,
    db: Session = Depends(get_db_session)
):
    """记录项目查询"""
    try:
        service = ProjectMemoryService(db)
        await service.record_query(project_id, query, success)
        
        return {
            "success": True,
            "message": "Query recorded"
        }
    except Exception as e:
        logger.error(f"Failed to record query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 用户记忆管理
@router.get("/user/{user_id}")
async def get_user_memory(
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """获取用户记忆和偏好"""
    service = UserMemoryService(db)
    memory = await service.get_or_create_user_memory(user_id)
    context = await service.get_user_context(user_id)
    
    return {
        "user_id": user_id,
        "preferences": {
            "language": memory.language_preference,
            "response_style": memory.response_style,
            "expertise_level": memory.expertise_level,
            "detail_level": memory.detail_level,
            "preferred_chunk_size": memory.preferred_chunk_size,
            "include_sources": memory.include_sources
        },
        "interests": memory.interests,
        "expertise_areas": memory.expertise_areas,
        "custom_prompts": memory.custom_prompts,
        "context": context
    }


@router.put("/user/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: UserPreferenceUpdate,
    db: Session = Depends(get_db_session)
):
    """更新用户偏好"""
    try:
        service = UserMemoryService(db)
        memory = await service.update_user_preferences(user_id, preferences)
        
        return {
            "success": True,
            "message": "User preferences updated",
            "preferences": {
                "language": memory.language_preference,
                "response_style": memory.response_style,
                "expertise_level": memory.expertise_level
            }
        }
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/activity")
async def record_user_activity(
    user_id: str,
    activity_type: str,
    details: Dict[str, Any],
    db: Session = Depends(get_db_session)
):
    """记录用户活动"""
    try:
        service = UserMemoryService(db)
        await service.record_user_activity(user_id, activity_type, details)
        
        return {
            "success": True,
            "message": "User activity recorded"
        }
    except Exception as e:
        logger.error(f"Failed to record user activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 对话记忆管理
@router.post("/conversation/{conversation_id}/turn")
async def record_conversation_turn(
    conversation_id: str,
    turn_number: int,
    user_message: str,
    assistant_response: str,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db_session)
):
    """记录对话轮次"""
    try:
        service = ConversationMemoryService(db)
        memory = await service.record_conversation_turn(
            conversation_id,
            turn_number,
            user_message,
            assistant_response,
            metadata
        )
        
        return {
            "success": True,
            "message": "Conversation turn recorded",
            "turn_id": memory.id
        }
    except Exception as e:
        logger.error(f"Failed to record conversation turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    last_n_turns: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db_session)
):
    """获取对话上下文"""
    try:
        service = ConversationMemoryService(db)
        context = await service.get_conversation_context(conversation_id, last_n_turns)
        
        return {
            "conversation_id": conversation_id,
            "turn_count": len(context),
            "context": context
        }
    except Exception as e:
        logger.error(f"Failed to get conversation context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 记忆系统统计
@router.get("/stats/overview")
async def get_memory_stats(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """获取记忆系统统计信息"""
    from sqlalchemy import func
    from ...models.memory import Memory
    
    try:
        query = db.query(
            Memory.memory_type,
            func.count(Memory.id).label("count"),
            func.avg(Memory.importance).label("avg_importance"),
            func.sum(Memory.access_count).label("total_accesses")
        )
        
        if user_id:
            query = query.filter(Memory.user_id == user_id)
        if project_id:
            query = query.filter(Memory.project_id == project_id)
        
        stats = query.group_by(Memory.memory_type).all()
        
        return {
            "success": True,
            "stats": [
                {
                    "type": stat.memory_type,
                    "count": stat.count,
                    "avg_importance": float(stat.avg_importance or 0),
                    "total_accesses": stat.total_accesses or 0
                }
                for stat in stats
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired_memories(
    db: Session = Depends(get_db_session)
):
    """清理过期的记忆"""
    from datetime import datetime
    from ...models.memory import Memory
    
    try:
        # 删除过期记忆
        expired_count = db.query(Memory).filter(
            Memory.expires_at < datetime.now()
        ).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Cleaned up {expired_count} expired memories"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))