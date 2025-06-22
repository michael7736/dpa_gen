"""
记忆系统服务
实现多层次记忆管理，包括情节记忆、语义记忆、工作记忆和元记忆
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """记忆类型"""
    EPISODIC = "episodic"  # 情节记忆
    SEMANTIC = "semantic"  # 语义记忆
    WORKING = "working"  # 工作记忆
    META = "meta"  # 元记忆

class MemoryImportance(Enum):
    """记忆重要性"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1

@dataclass
class MemoryItem:
    """记忆项"""
    memory_id: str
    content: str
    memory_type: MemoryType
    importance: MemoryImportance
    context: Dict[str, Any]
    embedding: Optional[List[float]] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    decay_factor: float = 1.0  # 遗忘因子
    associations: List[str] = field(default_factory=list)  # 关联的记忆ID
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EpisodicMemory:
    """情节记忆"""
    episode_id: str
    title: str
    description: str
    events: List[Dict[str, Any]]
    participants: List[str]
    location: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    emotional_valence: float = 0.0  # -1到1，负面到正面
    significance: float = 0.5  # 0到1
    related_concepts: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)

@dataclass
class SemanticMemory:
    """语义记忆"""
    concept_id: str
    concept_name: str
    definition: str
    properties: Dict[str, Any]
    relationships: Dict[str, List[str]]  # 关系类型 -> 相关概念列表
    examples: List[str]
    confidence: float = 1.0  # 置信度
    source_episodes: List[str] = field(default_factory=list)  # 来源情节
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class WorkingMemory:
    """工作记忆"""
    session_id: str
    active_items: deque = field(default_factory=lambda: deque(maxlen=7))  # 7±2规则
    focus_item: Optional[str] = None
    context_buffer: Dict[str, Any] = field(default_factory=dict)
    attention_weights: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MetaMemory:
    """元记忆"""
    strategy_id: str
    strategy_name: str
    description: str
    effectiveness: float = 0.5  # 有效性评分
    usage_count: int = 0
    success_rate: float = 0.0
    applicable_contexts: List[str] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)

class MemoryConsolidation:
    """记忆巩固"""
    
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        
    async def consolidate_episodic_to_semantic(
        self,
        episodes: List[EpisodicMemory]
    ) -> List[SemanticMemory]:
        """将情节记忆巩固为语义记忆"""
        try:
            logger.info(f"开始巩固 {len(episodes)} 个情节记忆")
            
            # 1. 提取共同概念
            concept_clusters = await self._extract_concept_clusters(episodes)
            
            # 2. 生成语义记忆
            semantic_memories = []
            for cluster in concept_clusters:
                semantic_memory = await self._create_semantic_memory(cluster, episodes)
                semantic_memories.append(semantic_memory)
            
            logger.info(f"巩固完成，生成 {len(semantic_memories)} 个语义记忆")
            return semantic_memories
            
        except Exception as e:
            logger.error(f"记忆巩固失败: {e}")
            raise
    
    async def _extract_concept_clusters(self, episodes: List[EpisodicMemory]) -> List[Dict[str, Any]]:
        """提取概念聚类"""
        # TODO: 实现基于语义相似度的概念聚类
        # 目前简化实现
        concept_map = defaultdict(list)
        
        for episode in episodes:
            for concept in episode.related_concepts:
                concept_map[concept].append(episode.episode_id)
        
        clusters = []
        for concept, episode_ids in concept_map.items():
            if len(episode_ids) >= 2:  # 至少出现在2个情节中
                clusters.append({
                    "concept": concept,
                    "episodes": episode_ids,
                    "frequency": len(episode_ids)
                })
        
        return clusters
    
    async def _create_semantic_memory(
        self,
        cluster: Dict[str, Any],
        episodes: List[EpisodicMemory]
    ) -> SemanticMemory:
        """创建语义记忆"""
        concept = cluster["concept"]
        episode_ids = cluster["episodes"]
        
        # 从相关情节中提取信息
        related_episodes = [ep for ep in episodes if ep.episode_id in episode_ids]
        
        # 生成定义和属性
        definition = f"从 {len(related_episodes)} 个情节中学习到的概念"
        properties = {
            "frequency": cluster["frequency"],
            "contexts": [ep.title for ep in related_episodes],
            "significance": np.mean([ep.significance for ep in related_episodes])
        }
        
        return SemanticMemory(
            concept_id=str(uuid.uuid4()),
            concept_name=concept,
            definition=definition,
            properties=properties,
            relationships={},
            examples=[ep.description for ep in related_episodes[:3]],
            source_episodes=episode_ids
        )

class MemoryRetrieval:
    """记忆检索"""
    
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
    
    async def retrieve_memories(
        self,
        query: str,
        memory_store: Dict[str, MemoryItem],
        k: int = 10,
        memory_types: Optional[List[MemoryType]] = None,
        time_window: Optional[timedelta] = None
    ) -> List[Tuple[MemoryItem, float]]:
        """检索相关记忆"""
        try:
            logger.debug(f"检索记忆: {query[:50]}...")
            
            # 1. 过滤记忆
            filtered_memories = self._filter_memories(
                memory_store, memory_types, time_window
            )
            
            # 2. 计算相似度
            query_embedding = await self.embedding_service.embed_query(query)
            similarities = []
            
            for memory in filtered_memories:
                if memory.embedding:
                    similarity = self._cosine_similarity(query_embedding, memory.embedding)
                    # 考虑重要性和访问频率
                    score = similarity * memory.importance.value * (1 + np.log(1 + memory.access_count))
                    similarities.append((memory, score))
            
            # 3. 排序并返回top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # 4. 更新访问统计
            for memory, _ in similarities[:k]:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
            
            logger.debug(f"检索到 {len(similarities[:k])} 个相关记忆")
            return similarities[:k]
            
        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            return []
    
    def _filter_memories(
        self,
        memory_store: Dict[str, MemoryItem],
        memory_types: Optional[List[MemoryType]],
        time_window: Optional[timedelta]
    ) -> List[MemoryItem]:
        """过滤记忆"""
        memories = list(memory_store.values())
        
        # 按类型过滤
        if memory_types:
            memories = [m for m in memories if m.memory_type in memory_types]
        
        # 按时间过滤
        if time_window:
            cutoff_time = datetime.now() - time_window
            memories = [m for m in memories if m.created_at >= cutoff_time]
        
        return memories
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        except:
            return 0.0

class MemoryForgetting:
    """记忆遗忘"""
    
    def __init__(self):
        self.forgetting_curve_params = {
            MemoryImportance.CRITICAL: 0.1,
            MemoryImportance.HIGH: 0.2,
            MemoryImportance.MEDIUM: 0.3,
            MemoryImportance.LOW: 0.5,
            MemoryImportance.MINIMAL: 0.8
        }
    
    def update_memory_decay(self, memory: MemoryItem) -> float:
        """更新记忆衰减"""
        # 基于Ebbinghaus遗忘曲线
        time_elapsed = (datetime.now() - memory.last_accessed).total_seconds() / 3600  # 小时
        decay_rate = self.forgetting_curve_params[memory.importance]
        
        # 考虑访问频率的影响
        access_factor = 1 / (1 + memory.access_count * 0.1)
        
        # 计算新的衰减因子
        new_decay = memory.decay_factor * np.exp(-decay_rate * time_elapsed * access_factor)
        memory.decay_factor = max(new_decay, 0.01)  # 最小保留0.01
        
        return memory.decay_factor
    
    def should_forget(self, memory: MemoryItem, threshold: float = 0.1) -> bool:
        """判断是否应该遗忘"""
        self.update_memory_decay(memory)
        return memory.decay_factor < threshold

class MemorySystemService:
    """记忆系统服务"""
    
    def __init__(self, embedding_service, vector_store):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
        # 记忆存储
        self.memory_store: Dict[str, MemoryItem] = {}
        self.episodic_memories: Dict[str, EpisodicMemory] = {}
        self.semantic_memories: Dict[str, SemanticMemory] = {}
        self.working_memories: Dict[str, WorkingMemory] = {}
        self.meta_memories: Dict[str, MetaMemory] = {}
        
        # 记忆管理组件
        self.consolidation = MemoryConsolidation(embedding_service)
        self.retrieval = MemoryRetrieval(embedding_service)
        self.forgetting = MemoryForgetting()
        
        # 统计信息
        self.stats = {
            "total_memories": 0,
            "episodic_count": 0,
            "semantic_count": 0,
            "working_count": 0,
            "meta_count": 0,
            "consolidation_count": 0,
            "forgotten_count": 0
        }
    
    async def store_episodic_memory(
        self,
        title: str,
        description: str,
        events: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """存储情节记忆"""
        try:
            episode = EpisodicMemory(
                episode_id=str(uuid.uuid4()),
                title=title,
                description=description,
                events=events,
                participants=context.get("participants", []),
                location=context.get("location"),
                emotional_valence=context.get("emotional_valence", 0.0),
                significance=context.get("significance", 0.5),
                related_concepts=context.get("concepts", []),
                outcomes=context.get("outcomes", [])
            )
            
            self.episodic_memories[episode.episode_id] = episode
            
            # 创建对应的记忆项
            memory_item = await self._create_memory_item(
                content=f"{title}: {description}",
                memory_type=MemoryType.EPISODIC,
                importance=MemoryImportance.MEDIUM,
                context=context
            )
            
            self.memory_store[memory_item.memory_id] = memory_item
            
            # 更新统计
            self.stats["episodic_count"] += 1
            self.stats["total_memories"] += 1
            
            logger.info(f"存储情节记忆: {episode.episode_id}")
            return episode.episode_id
            
        except Exception as e:
            logger.error(f"存储情节记忆失败: {e}")
            raise
    
    async def store_semantic_memory(
        self,
        concept_name: str,
        definition: str,
        properties: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """存储语义记忆"""
        try:
            semantic = SemanticMemory(
                concept_id=str(uuid.uuid4()),
                concept_name=concept_name,
                definition=definition,
                properties=properties,
                relationships=context.get("relationships", {}),
                examples=context.get("examples", []),
                confidence=context.get("confidence", 1.0)
            )
            
            self.semantic_memories[semantic.concept_id] = semantic
            
            # 创建对应的记忆项
            memory_item = await self._create_memory_item(
                content=f"{concept_name}: {definition}",
                memory_type=MemoryType.SEMANTIC,
                importance=MemoryImportance.HIGH,
                context=context
            )
            
            self.memory_store[memory_item.memory_id] = memory_item
            
            # 更新统计
            self.stats["semantic_count"] += 1
            self.stats["total_memories"] += 1
            
            logger.info(f"存储语义记忆: {semantic.concept_id}")
            return semantic.concept_id
            
        except Exception as e:
            logger.error(f"存储语义记忆失败: {e}")
            raise
    
    async def _create_memory_item(
        self,
        content: str,
        memory_type: MemoryType,
        importance: MemoryImportance,
        context: Dict[str, Any]
    ) -> MemoryItem:
        """创建记忆项"""
        # 生成嵌入向量
        embedding = await self.embedding_service.embed_query(content)
        
        memory_item = MemoryItem(
            memory_id=str(uuid.uuid4()),
            content=content,
            memory_type=memory_type,
            importance=importance,
            context=context,
            embedding=embedding
        )
        
        return memory_item
    
    async def retrieve_relevant_memories(
        self,
        query: str,
        k: int = 10,
        memory_types: Optional[List[MemoryType]] = None,
        time_window: Optional[timedelta] = None
    ) -> List[Tuple[MemoryItem, float]]:
        """检索相关记忆"""
        return await self.retrieval.retrieve_memories(
            query=query,
            memory_store=self.memory_store,
            k=k,
            memory_types=memory_types,
            time_window=time_window
        )
    
    async def consolidate_memories(self) -> Dict[str, Any]:
        """巩固记忆"""
        try:
            logger.info("开始记忆巩固")
            
            # 1. 选择需要巩固的情节记忆
            episodes_to_consolidate = [
                ep for ep in self.episodic_memories.values()
                if ep.significance > 0.7 and len(ep.related_concepts) > 0
            ]
            
            if not episodes_to_consolidate:
                logger.info("没有需要巩固的情节记忆")
                return {"consolidated": 0}
            
            # 2. 执行巩固
            new_semantic_memories = await self.consolidation.consolidate_episodic_to_semantic(
                episodes_to_consolidate
            )
            
            # 3. 存储新的语义记忆
            for semantic in new_semantic_memories:
                self.semantic_memories[semantic.concept_id] = semantic
                
                # 创建对应的记忆项
                memory_item = await self._create_memory_item(
                    content=f"{semantic.concept_name}: {semantic.definition}",
                    memory_type=MemoryType.SEMANTIC,
                    importance=MemoryImportance.HIGH,
                    context={"source": "consolidation"}
                )
                
                self.memory_store[memory_item.memory_id] = memory_item
            
            # 4. 更新统计
            self.stats["semantic_count"] += len(new_semantic_memories)
            self.stats["total_memories"] += len(new_semantic_memories)
            self.stats["consolidation_count"] += 1
            
            result = {
                "consolidated": len(new_semantic_memories),
                "source_episodes": len(episodes_to_consolidate),
                "new_concepts": [sm.concept_name for sm in new_semantic_memories]
            }
            
            logger.info(f"记忆巩固完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"记忆巩固失败: {e}")
            raise
    
    async def forget_old_memories(self, threshold: float = 0.1) -> Dict[str, Any]:
        """遗忘旧记忆"""
        try:
            logger.info("开始记忆遗忘处理")
            
            forgotten_memories = []
            
            for memory_id, memory in list(self.memory_store.items()):
                if self.forgetting.should_forget(memory, threshold):
                    # 从存储中移除
                    del self.memory_store[memory_id]
                    forgotten_memories.append(memory_id)
                    
                    # 从对应的专门存储中移除
                    if memory.memory_type == MemoryType.EPISODIC:
                        # 查找对应的情节记忆
                        for ep_id, episode in list(self.episodic_memories.items()):
                            if episode.title in memory.content:
                                del self.episodic_memories[ep_id]
                                break
                    elif memory.memory_type == MemoryType.SEMANTIC:
                        # 查找对应的语义记忆
                        for sem_id, semantic in list(self.semantic_memories.items()):
                            if semantic.concept_name in memory.content:
                                del self.semantic_memories[sem_id]
                                break
            
            # 更新统计
            self.stats["forgotten_count"] += len(forgotten_memories)
            self.stats["total_memories"] -= len(forgotten_memories)
            
            result = {
                "forgotten_count": len(forgotten_memories),
                "remaining_memories": len(self.memory_store)
            }
            
            logger.info(f"记忆遗忘完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"记忆遗忘失败: {e}")
            raise
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        # 计算记忆类型分布
        type_distribution = defaultdict(int)
        importance_distribution = defaultdict(int)
        
        for memory in self.memory_store.values():
            type_distribution[memory.memory_type.value] += 1
            importance_distribution[memory.importance.value] += 1
        
        return {
            **self.stats,
            "type_distribution": dict(type_distribution),
            "importance_distribution": dict(importance_distribution),
            "average_access_count": np.mean([m.access_count for m in self.memory_store.values()]) if self.memory_store else 0,
            "memory_health": {
                "active_memories": len([m for m in self.memory_store.values() if m.decay_factor > 0.5]),
                "decaying_memories": len([m for m in self.memory_store.values() if 0.1 < m.decay_factor <= 0.5]),
                "critical_memories": len([m for m in self.memory_store.values() if m.decay_factor <= 0.1])
            }
        }
    
    async def create_working_memory_session(self, session_id: str) -> WorkingMemory:
        """创建工作记忆会话"""
        working_memory = WorkingMemory(session_id=session_id)
        self.working_memories[session_id] = working_memory
        self.stats["working_count"] += 1
        
        logger.info(f"创建工作记忆会话: {session_id}")
        return working_memory
    
    def update_working_memory(
        self,
        session_id: str,
        item: str,
        attention_weight: float = 1.0
    ):
        """更新工作记忆"""
        if session_id not in self.working_memories:
            self.create_working_memory_session(session_id)
        
        working_memory = self.working_memories[session_id]
        working_memory.active_items.append(item)
        working_memory.attention_weights[item] = attention_weight
        
        # 设置焦点项
        if attention_weight > 0.8:
            working_memory.focus_item = item

def create_memory_system_service(
    embedding_service,
    vector_store
) -> MemorySystemService:
    """创建记忆系统服务"""
    return MemorySystemService(embedding_service, vector_store) 