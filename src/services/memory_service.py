"""
记忆服务
管理项目和用户记忆的存储、检索和更新
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from ..models.memory import (
    Memory, ProjectMemory, UserMemory, ConversationMemory
)
from ..models.memory_schemas import (
    MemoryType, MemoryScope,
    MemoryCreate, MemoryUpdate, MemoryQuery,
    ProjectMemoryUpdate, UserPreferenceUpdate
)
from ..services.cache_service import CacheService, CacheKeys
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MemoryService:
    """记忆服务"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.cache = CacheService()
        self.logger = get_logger(__name__)
    
    async def create_memory(self, memory_data: MemoryCreate) -> Memory:
        """创建新记忆"""
        try:
            # 计算过期时间
            expires_at = None
            if memory_data.expires_in_hours:
                expires_at = datetime.now() + timedelta(hours=memory_data.expires_in_hours)
            
            # 创建记忆实体
            memory = Memory(
                memory_type=memory_data.memory_type,
                scope=memory_data.scope,
                key=memory_data.key,
                content=memory_data.content,
                summary=memory_data.summary,
                importance=memory_data.importance,
                expires_at=expires_at,
                user_id=memory_data.user_id,
                project_id=memory_data.project_id,
                session_id=memory_data.session_id,
                last_accessed_at=datetime.now()
            )
            
            self.session.add(memory)
            await self.session.commit()
            
            # 清除相关缓存
            await self._invalidate_memory_cache(memory_data.scope, memory_data.user_id, memory_data.project_id)
            
            self.logger.info(f"Created memory: {memory.memory_type}/{memory.key}")
            return memory
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create memory: {e}")
            raise
    
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取单个记忆"""
        memory = self.session.query(Memory).filter_by(id=memory_id).first()
        
        if memory:
            # 更新访问计数和时间
            memory.access_count += 1
            memory.last_accessed_at = datetime.now()
            await self.session.commit()
        
        return memory
    
    async def query_memories(self, query: MemoryQuery) -> List[Memory]:
        """查询记忆"""
        # 生成缓存键
        cache_key = f"memories:query:{json.dumps(query.dict(), sort_keys=True)}"
        
        # 尝试从缓存获取
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # 构建查询
        q = self.session.query(Memory)
        
        # 应用过滤条件
        conditions = []
        
        if query.memory_types:
            conditions.append(Memory.memory_type.in_(query.memory_types))
        
        if query.scope:
            conditions.append(Memory.scope == query.scope)
        
        if query.user_id:
            conditions.append(Memory.user_id == query.user_id)
        
        if query.project_id:
            conditions.append(Memory.project_id == query.project_id)
        
        if query.key_pattern:
            conditions.append(Memory.key.like(f"%{query.key_pattern}%"))
        
        if query.min_importance:
            conditions.append(Memory.importance >= query.min_importance)
        
        if not query.include_expired:
            conditions.append(
                or_(Memory.expires_at.is_(None), Memory.expires_at > datetime.now())
            )
        
        if conditions:
            q = q.filter(and_(*conditions))
        
        # 排序和限制
        memories = q.order_by(
            Memory.importance.desc(),
            Memory.last_accessed_at.desc()
        ).limit(query.limit).all()
        
        # 缓存结果
        await self.cache.set(cache_key, memories, ttl=300)  # 5分钟
        
        return memories
    
    async def update_memory(self, memory_id: str, update_data: MemoryUpdate) -> Optional[Memory]:
        """更新记忆"""
        memory = self.session.query(Memory).filter_by(id=memory_id).first()
        
        if not memory:
            return None
        
        # 更新字段
        if update_data.content is not None:
            memory.content = update_data.content
        
        if update_data.summary is not None:
            memory.summary = update_data.summary
        
        if update_data.importance is not None:
            memory.importance = update_data.importance
        
        if update_data.extend_expiry_hours:
            if memory.expires_at:
                memory.expires_at += timedelta(hours=update_data.extend_expiry_hours)
            else:
                memory.expires_at = datetime.now() + timedelta(hours=update_data.extend_expiry_hours)
        
        memory.updated_at = datetime.now()
        
        await self.session.commit()
        
        # 清除缓存
        await self._invalidate_memory_cache(memory.scope, memory.user_id, memory.project_id)
        
        return memory
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        memory = self.session.query(Memory).filter_by(id=memory_id).first()
        
        if not memory:
            return False
        
        self.session.delete(memory)
        await self.session.commit()
        
        # 清除缓存
        await self._invalidate_memory_cache(memory.scope, memory.user_id, memory.project_id)
        
        return True
    
    async def _invalidate_memory_cache(self, scope: MemoryScope, user_id: str = None, project_id: str = None):
        """清除记忆相关缓存"""
        patterns = [f"memories:query:*"]
        
        if scope == MemoryScope.USER and user_id:
            patterns.append(f"user:memory:{user_id}:*")
        elif scope == MemoryScope.PROJECT and project_id:
            patterns.append(f"project:memory:{project_id}:*")
        
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)


class ProjectMemoryService:
    """项目记忆服务"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.cache = CacheService()
        self.memory_service = MemoryService(db_session)
    
    async def get_or_create_project_memory(self, project_id: str) -> ProjectMemory:
        """获取或创建项目记忆"""
        memory = self.session.query(ProjectMemory).filter_by(project_id=project_id).first()
        
        if not memory:
            memory = ProjectMemory(project_id=project_id)
            self.session.add(memory)
            await self.session.commit()
        
        return memory
    
    async def update_project_memory(self, project_id: str, update_data: ProjectMemoryUpdate) -> ProjectMemory:
        """更新项目记忆"""
        memory = await self.get_or_create_project_memory(project_id)
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                # 对于列表字段，追加而不是替换
                if field in ['key_concepts', 'learned_facts', 'important_documents'] and isinstance(value, list):
                    current = getattr(memory, field) or []
                    # 去重追加
                    for item in value:
                        if item not in current:
                            current.append(item)
                    setattr(memory, field, current)
                else:
                    setattr(memory, field, value)
        
        memory.last_activity_at = datetime.now()
        memory.memory_version += 1
        
        await self.session.commit()
        
        # 同时创建通用记忆记录
        await self.memory_service.create_memory(MemoryCreate(
            memory_type=MemoryType.PROJECT_CONTEXT,
            scope=MemoryScope.PROJECT,
            project_id=project_id,
            key=f"update_{datetime.now().isoformat()}",
            content=update_dict,
            summary=f"Project memory updated: {', '.join(update_dict.keys())}",
            importance=0.7
        ))
        
        return memory
    
    async def add_learned_fact(self, project_id: str, fact: str, confidence: float = 0.8, source: str = None):
        """添加学习到的事实"""
        memory = await self.get_or_create_project_memory(project_id)
        
        learned_fact = {
            "fact": fact,
            "confidence": confidence,
            "source": source,
            "learned_at": datetime.now().isoformat()
        }
        
        if memory.learned_facts is None:
            memory.learned_facts = []
        
        memory.learned_facts.append(learned_fact)
        memory.last_activity_at = datetime.now()
        
        await self.session.commit()
        
        logger.info(f"Added learned fact to project {project_id}: {fact}")
    
    async def record_query(self, project_id: str, query: str, success: bool = True):
        """记录查询"""
        memory = await self.get_or_create_project_memory(project_id)
        
        # 更新统计
        memory.total_queries += 1
        
        # 记录常见查询
        if memory.frequent_queries is None:
            memory.frequent_queries = []
        
        # 查找是否已存在
        found = False
        for fq in memory.frequent_queries:
            if fq['query'] == query:
                fq['count'] += 1
                fq['last_used'] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            memory.frequent_queries.append({
                "query": query,
                "count": 1,
                "success_rate": 1.0 if success else 0.0,
                "last_used": datetime.now().isoformat()
            })
        
        # 只保留前20个常见查询
        memory.frequent_queries = sorted(
            memory.frequent_queries,
            key=lambda x: x['count'],
            reverse=True
        )[:20]
        
        await self.session.commit()


class UserMemoryService:
    """用户记忆服务"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.cache = CacheService()
        self.memory_service = MemoryService(db_session)
    
    async def get_or_create_user_memory(self, user_id: str) -> UserMemory:
        """获取或创建用户记忆"""
        memory = self.session.query(UserMemory).filter_by(user_id=user_id).first()
        
        if not memory:
            memory = UserMemory(user_id=user_id)
            self.session.add(memory)
            await self.session.commit()
        
        return memory
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferenceUpdate) -> UserMemory:
        """更新用户偏好"""
        memory = await self.get_or_create_user_memory(user_id)
        
        # 更新字段
        update_dict = preferences.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(memory, field, value)
        
        memory.updated_at = datetime.now()
        await self.session.commit()
        
        # 创建通用记忆记录
        await self.memory_service.create_memory(MemoryCreate(
            memory_type=MemoryType.USER_PREFERENCE,
            scope=MemoryScope.USER,
            user_id=user_id,
            key="preferences_update",
            content=update_dict,
            summary=f"User preferences updated: {', '.join(update_dict.keys())}",
            importance=0.6
        ))
        
        return memory
    
    async def record_user_activity(self, user_id: str, activity_type: str, details: Dict[str, Any]):
        """记录用户活动"""
        # 获取当前小时
        current_hour = datetime.now().hour
        
        memory = await self.get_or_create_user_memory(user_id)
        
        # 更新活跃时段
        if memory.active_hours is None:
            memory.active_hours = {}
        
        hour_key = str(current_hour)
        memory.active_hours[hour_key] = memory.active_hours.get(hour_key, 0) + 1
        
        # 记录查询模式
        if activity_type == "query" and "query" in details:
            if memory.query_patterns is None:
                memory.query_patterns = []
            
            # 简单的模式识别（可以更复杂）
            query = details["query"]
            pattern = "question" if "?" in query else "statement"
            
            memory.query_patterns.append({
                "pattern": pattern,
                "timestamp": datetime.now().isoformat(),
                "project_id": details.get("project_id")
            })
            
            # 只保留最近100个模式
            memory.query_patterns = memory.query_patterns[-100:]
        
        await self.session.commit()
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """获取用户上下文（用于个性化）"""
        memory = await self.get_or_create_user_memory(user_id)
        
        return {
            "language": memory.language_preference,
            "style": memory.response_style,
            "expertise": memory.expertise_level,
            "interests": memory.interests or [],
            "custom_prompts": memory.custom_prompts or {},
            "preferences": {
                "chunk_size": memory.preferred_chunk_size,
                "detail_level": memory.detail_level,
                "include_sources": memory.include_sources
            }
        }


class ConversationMemoryService:
    """对话记忆服务"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.memory_service = MemoryService(db_session)
    
    async def record_conversation_turn(
        self,
        conversation_id: str,
        turn_number: int,
        user_message: str,
        assistant_response: str,
        metadata: Dict[str, Any] = None
    ):
        """记录对话轮次"""
        memory = ConversationMemory(
            conversation_id=conversation_id,
            turn_number=turn_number,
            user_message=user_message,
            assistant_response=assistant_response,
            entities_mentioned=metadata.get("entities", []) if metadata else [],
            topics_discussed=metadata.get("topics", []) if metadata else [],
            referenced_documents=metadata.get("documents", []) if metadata else []
        )
        
        # 判断重要性
        if metadata and metadata.get("importance_score", 0) > 0.7:
            memory.is_important = True
            memory.importance_reason = metadata.get("importance_reason")
        
        self.session.add(memory)
        await self.session.commit()
        
        return memory
    
    async def get_conversation_context(self, conversation_id: str, last_n_turns: int = 5) -> List[Dict[str, Any]]:
        """获取对话上下文"""
        memories = self.session.query(ConversationMemory).filter_by(
            conversation_id=conversation_id
        ).order_by(
            ConversationMemory.turn_number.desc()
        ).limit(last_n_turns).all()
        
        return [
            {
                "turn": m.turn_number,
                "user": m.user_message,
                "assistant": m.assistant_response,
                "topics": m.topics_discussed,
                "important": m.is_important
            }
            for m in reversed(memories)
        ]