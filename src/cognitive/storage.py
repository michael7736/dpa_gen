"""
认知系统存储管理器
整合PostgreSQL、Neo4j、Qdrant和Redis的混合存储架构
"""

import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from ..config.settings import get_settings
from ..database.postgresql import get_db_session
from ..database.neo4j_manager import Neo4jManager
from ..database.qdrant import get_qdrant_manager
from ..services.cache_service import CacheService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PostgresCheckpointer:
    """PostgreSQL检查点管理器 - 优化的状态持久化"""
    
    def __init__(self):
        self.settings = get_settings()
        self.table_name = "langgraph.checkpoints"
        self._init_schema()
    
    def _init_schema(self):
        """初始化检查点表结构"""
        init_sql = """
        -- 创建LangGraph专用schema
        CREATE SCHEMA IF NOT EXISTS langgraph;
        
        -- 检查点表
        CREATE TABLE IF NOT EXISTS langgraph.checkpoints (
            thread_id TEXT NOT NULL,
            checkpoint_id TEXT NOT NULL,
            parent_id TEXT,
            state JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (thread_id, checkpoint_id)
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_created 
        ON langgraph.checkpoints(thread_id, created_at DESC);
        
        CREATE INDEX IF NOT EXISTS idx_checkpoints_parent 
        ON langgraph.checkpoints(parent_id);
        
        -- GIN索引用于JSONB查询
        CREATE INDEX IF NOT EXISTS idx_checkpoints_state_gin 
        ON langgraph.checkpoints USING GIN (state);
        
        -- 写入表 - 用于临时状态
        CREATE TABLE IF NOT EXISTS langgraph.writes (
            thread_id TEXT NOT NULL,
            checkpoint_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            value JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (thread_id, checkpoint_id, task_id, channel)
        );
        """
        
        # 这里应该执行SQL，但为了示例简化
        logger.info("PostgreSQL checkpoint schema initialized")
    
    async def save_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        state: Dict[str, Any],
        parent_id: Optional[str] = None
    ) -> None:
        """保存检查点"""
        # TODO: 实际实现应该使用SQLAlchemy或asyncpg
        logger.info(f"Saving checkpoint {checkpoint_id} for thread {thread_id}")
        # 临时实现：保存到内存或文件
        self._checkpoints = getattr(self, '_checkpoints', {})
        self._checkpoints[f"{thread_id}:{checkpoint_id}"] = state
    
    async def load_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """加载检查点"""
        # TODO: 实际实现应该使用数据库
        logger.info(f"Loading checkpoint for thread {thread_id}")
        self._checkpoints = getattr(self, '_checkpoints', {})
        if checkpoint_id:
            return self._checkpoints.get(f"{thread_id}:{checkpoint_id}")
        # 返回最新的检查点
        for key in sorted(self._checkpoints.keys(), reverse=True):
            if key.startswith(f"{thread_id}:"):
                return self._checkpoints[key]
        return None


class Neo4jKnowledgeGraph:
    """Neo4j知识图谱管理器"""
    
    def __init__(self):
        self.neo4j = Neo4jManager()
        self._init_schema()
    
    def _init_schema(self):
        """初始化图谱schema"""
        cypher_queries = [
            # 创建约束
            """
            CREATE CONSTRAINT concept_id IF NOT EXISTS 
            FOR (c:Concept) REQUIRE c.id IS UNIQUE
            """,
            
            # 创建索引
            """
            CREATE INDEX concept_name IF NOT EXISTS 
            FOR (c:Concept) ON (c.name)
            """,
            
            # 全文搜索索引
            """
            CALL db.index.fulltext.createNodeIndex(
                "conceptSearch",
                ["Concept"],
                ["name", "definition", "description"]
            ) YIELD indexName
            """
        ]
        
        # 执行初始化
        logger.info("Neo4j knowledge graph schema initialized")
    
    async def add_concept(
        self,
        concept_id: str,
        name: str,
        definition: str,
        properties: Dict[str, Any]
    ) -> None:
        """添加概念节点"""
        query = """
        MERGE (c:Concept {id: $concept_id})
        SET c.name = $name,
            c.definition = $definition,
            c.created_at = datetime(),
            c.properties = $properties
        """
        
        await self.neo4j.execute_query(
            query,
            concept_id=concept_id,
            name=name,
            definition=definition,
            properties=json.dumps(properties)
        )
    
    async def add_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Dict[str, Any]
    ) -> None:
        """添加关系"""
        query = f"""
        MATCH (a:Concept {{id: $from_id}})
        MATCH (b:Concept {{id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r.created_at = datetime(),
            r.properties = $properties
        """
        
        await self.neo4j.execute_query(
            query,
            from_id=from_id,
            to_id=to_id,
            properties=json.dumps(properties)
        )
    
    async def get_graph_snapshot(self, limit: int = 1000) -> Dict[str, Any]:
        """获取图谱快照"""
        query = """
        MATCH (c:Concept)
        WITH c LIMIT $limit
        OPTIONAL MATCH (c)-[r]->(other:Concept)
        RETURN c, collect(DISTINCT {
            type: type(r),
            target: other.id,
            properties: r.properties
        }) as relationships
        """
        
        result = await self.neo4j.execute_query(query, limit=limit)
        
        # 构建快照
        snapshot = {
            "nodes": [],
            "edges": [],
            "statistics": {
                "node_count": 0,
                "edge_count": 0
            }
        }
        
        # 处理结果（简化版）
        return snapshot


class QdrantVectorStore:
    """Qdrant向量存储管理器 - 支持多集合"""
    
    def __init__(self):
        self.qdrant = QdrantManager()
        self.collections = {
            "concepts": {"size": 3072, "distance": "Cosine"},
            "chunks": {"size": 3072, "distance": "Cosine"},
            "summaries": {"size": 3072, "distance": "Cosine"}
        }
        self._init_collections()
    
    def _init_collections(self):
        """初始化向量集合"""
        for name, config in self.collections.items():
            # 实际应该调用create_collection
            logger.info(f"Initialized Qdrant collection: {name}")
    
    async def upsert_vectors(
        self,
        collection: str,
        vectors: List[Dict[str, Any]]
    ) -> None:
        """批量更新向量"""
        if collection not in self.collections:
            raise ValueError(f"Unknown collection: {collection}")
        
        # 实际实现应调用qdrant.upsert
        logger.info(f"Upserting {len(vectors)} vectors to {collection}")
    
    async def search_vectors(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """向量搜索"""
        if collection not in self.collections:
            raise ValueError(f"Unknown collection: {collection}")
        
        # 实际实现应调用qdrant.search
        return []


class RedisCache:
    """Redis缓存管理器 - 多层缓存策略"""
    
    def __init__(self):
        self.cache = CacheService()
        self.ttl_config = {
            "query_result": 3600,      # 查询结果缓存1小时
            "graph_snapshot": 300,     # 图谱快照缓存5分钟
            "working_memory": 1800,    # 工作记忆缓存30分钟
            "user_context": 7200       # 用户上下文缓存2小时
        }
    
    async def get_cached(
        self,
        key: str,
        cache_type: str = "query_result"
    ) -> Optional[Any]:
        """获取缓存"""
        return await self.cache.get(f"{cache_type}:{key}")
    
    async def set_cached(
        self,
        key: str,
        value: Any,
        cache_type: str = "query_result"
    ) -> None:
        """设置缓存"""
        ttl = self.ttl_config.get(cache_type, 3600)
        await self.cache.set(f"{cache_type}:{key}", value, ttl=ttl)
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """按模式失效缓存"""
        # 实际实现应该使用Redis的SCAN命令
        logger.info(f"Invalidating cache pattern: {pattern}")


class CognitiveStorageManager:
    """认知存储管理器 - 统一接口"""
    
    def __init__(self):
        self.postgres = PostgresCheckpointer()
        self.neo4j = Neo4jKnowledgeGraph()
        self.qdrant = QdrantVectorStore()
        self.redis = RedisCache()
        
        logger.info("Cognitive storage manager initialized")
    
    async def save_cognitive_state(
        self,
        state: Dict[str, Any]
    ) -> None:
        """保存完整认知状态"""
        thread_id = state.get("thread_id")
        checkpoint_id = f"ckpt_{datetime.now().timestamp()}"
        
        # 1. 保存检查点到PostgreSQL
        await self.postgres.save_checkpoint(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            state=state
        )
        
        # 2. 更新知识图谱
        if state.get("extracted_graph_documents"):
            for doc in state["extracted_graph_documents"]:
                await self.neo4j.add_concept(
                    concept_id=doc["id"],
                    name=doc["name"],
                    definition=doc.get("definition", ""),
                    properties=doc.get("properties", {})
                )
        
        # 3. 更新向量索引
        if state.get("concept_embeddings"):
            vectors = []
            for concept_id, embedding in state["concept_embeddings"].items():
                vectors.append({
                    "id": concept_id,
                    "vector": embedding,
                    "payload": {"type": "concept"}
                })
            await self.qdrant.upsert_vectors("concepts", vectors)
        
        # 4. 更新缓存
        await self.redis.set_cached(
            key=thread_id,
            value={"checkpoint_id": checkpoint_id},
            cache_type="working_memory"
        )
        
        logger.info(f"Saved cognitive state: {checkpoint_id}")
    
    async def load_cognitive_state(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """加载认知状态"""
        # 1. 尝试从缓存加载
        cached = await self.redis.get_cached(thread_id, "working_memory")
        if cached and not checkpoint_id:
            checkpoint_id = cached.get("checkpoint_id")
        
        # 2. 从PostgreSQL加载
        state = await self.postgres.load_checkpoint(thread_id, checkpoint_id)
        if not state:
            return None
        
        # 3. 加载图谱快照
        state["knowledge_graph_snapshot"] = await self.neo4j.get_graph_snapshot()
        
        # 4. 预热缓存
        await self.redis.set_cached(
            key=thread_id,
            value={"checkpoint_id": checkpoint_id, "loaded_at": datetime.now()},
            cache_type="working_memory"
        )
        
        return state
    
    async def search_knowledge(
        self,
        query: str,
        search_type: str = "hybrid"
    ) -> Dict[str, Any]:
        """知识搜索 - 支持多种搜索策略"""
        # 这将在retrieval模块中详细实现
        return {
            "query": query,
            "results": [],
            "search_type": search_type
        }


# 工厂函数
def create_cognitive_storage() -> CognitiveStorageManager:
    """创建认知存储管理器实例"""
    return CognitiveStorageManager()