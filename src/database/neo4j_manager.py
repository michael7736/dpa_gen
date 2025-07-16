"""
Neo4j数据库管理器 - 支持事务和补偿
"""
import logging
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import Neo4jError

from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class Neo4jManager:
    """Neo4j数据库管理器"""
    
    def __init__(self):
        self.uri = settings.neo4j.url
        self.username = settings.neo4j.username
        self.password = settings.neo4j.password
        self._driver: Optional[AsyncDriver] = None
        
    async def connect(self):
        """连接到Neo4j"""
        if not self._driver:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            logger.info("Connected to Neo4j")
            
    async def disconnect(self):
        """断开连接"""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j")
            
    @asynccontextmanager
    async def session(self):
        """获取会话上下文"""
        if not self._driver:
            await self.connect()
        async with self._driver.session() as session:
            yield session
            
    async def create_memory_node(
        self,
        memory_id: str,
        content: str,
        memory_type: str,
        user_id: str = "u1",  # 为多用户预埋
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建记忆节点（支持用户隔离）"""
        async with self.session() as session:
            query = """
            CREATE (m:Memory {
                id: $memory_id,
                content: $content,
                type: $memory_type,
                user_id: $user_id,
                project_id: $project_id,
                created_at: datetime(),
                metadata: $metadata
            })
            RETURN m
            """
            
            result = await session.run(
                query,
                memory_id=memory_id,
                content=content,
                memory_type=memory_type,
                user_id=user_id,
                project_id=project_id,
                metadata=metadata or {}
            )
            
            record = await result.single()
            return dict(record["m"]) if record else None
            
    async def create_entity_node(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """创建实体节点"""
        async with self.session() as session:
            query = """
            MERGE (e:Entity {name: $name})
            ON CREATE SET
                e.type = $type,
                e.created_at = datetime()
            ON MATCH SET
                e.updated_at = datetime()
            SET e += $properties
            RETURN e
            """
            
            result = await session.run(
                query,
                name=entity.get("name"),
                type=entity.get("type", "Unknown"),
                properties=entity.get("properties", {})
            )
            
            record = await result.single()
            return dict(record["e"]) if record else None
            
    async def create_relationship(
        self,
        relationship: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建关系"""
        async with self.session() as session:
            query = """
            MATCH (a {id: $from_id})
            MATCH (b {id: $to_id})
            CREATE (a)-[r:$rel_type {
                created_at: datetime()
            }]->(b)
            SET r += $properties
            RETURN r
            """
            
            result = await session.run(
                query,
                from_id=relationship.get("from_id"),
                to_id=relationship.get("to_id"),
                rel_type=relationship.get("type", "RELATES_TO"),
                properties=relationship.get("properties", {})
            )
            
            record = await result.single()
            return dict(record["r"]) if record else None
            
    async def delete_memory_node(self, memory_id: str) -> bool:
        """删除记忆节点及其关系"""
        async with self.session() as session:
            query = """
            MATCH (m:Memory {id: $memory_id})
            DETACH DELETE m
            RETURN COUNT(m) as deleted
            """
            
            result = await session.run(query, memory_id=memory_id)
            record = await result.single()
            return record["deleted"] > 0 if record else False
            
    async def update_memory_node(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新记忆节点"""
        async with self.session() as session:
            # 先获取原始数据用于补偿
            backup_query = """
            MATCH (m:Memory {id: $memory_id})
            RETURN m
            """
            backup_result = await session.run(backup_query, memory_id=memory_id)
            backup_record = await backup_result.single()
            original_data = dict(backup_record["m"]) if backup_record else None
            
            # 执行更新
            update_query = """
            MATCH (m:Memory {id: $memory_id})
            SET m += $updates,
                m.updated_at = datetime()
            RETURN m
            """
            
            result = await session.run(
                update_query,
                memory_id=memory_id,
                updates=updates
            )
            
            record = await result.single()
            updated_data = dict(record["m"]) if record else None
            
            return {
                "updated": updated_data,
                "original": original_data
            }
            
    async def search_memories(
        self,
        project_id: str,
        query: str,
        user_id: str = "u1",  # 为多用户预埋
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索记忆节点（支持用户隔离）"""
        async with self.session() as session:
            search_query = """
            MATCH (m:Memory {user_id: $user_id, project_id: $project_id})
            WHERE m.content CONTAINS $query
            RETURN m
            ORDER BY m.created_at DESC
            LIMIT $limit
            """
            
            result = await session.run(
                search_query,
                user_id=user_id,
                project_id=project_id,
                query=query,
                limit=limit
            )
            
            memories = []
            async for record in result:
                memories.append(dict(record["m"]))
                
            return memories
            
    async def get_memory_graph(
        self,
        memory_id: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """获取记忆的关系图谱"""
        async with self.session() as session:
            query = """
            MATCH path = (m:Memory {id: $memory_id})-[*0..$depth]-(connected)
            RETURN 
                m,
                collect(distinct connected) as connected_nodes,
                collect(distinct relationships(path)) as relationships
            """
            
            result = await session.run(
                query,
                memory_id=memory_id,
                depth=depth
            )
            
            record = await result.single()
            if not record:
                return None
                
            return {
                "root": dict(record["m"]),
                "nodes": [dict(n) for n in record["connected_nodes"]],
                "relationships": [
                    {
                        "type": rel.type,
                        "properties": dict(rel),
                        "start": rel.start_node.element_id,
                        "end": rel.end_node.element_id
                    }
                    for rels in record["relationships"]
                    for rel in rels
                ]
            }
            
    async def execute_transaction(
        self,
        queries: List[Dict[str, Any]]
    ) -> List[Any]:
        """执行事务"""
        async with self.session() as session:
            async with session.begin_transaction() as tx:
                results = []
                try:
                    for query_data in queries:
                        result = await tx.run(
                            query_data["query"],
                            **query_data.get("params", {})
                        )
                        results.append(await result.data())
                    await tx.commit()
                    return results
                except Exception as e:
                    await tx.rollback()
                    raise e
                    
    async def check_health(self) -> bool:
        """检查数据库健康状态"""
        try:
            async with self.session() as session:
                result = await session.run("RETURN 1 as health")
                record = await result.single()
                return record["health"] == 1 if record else False
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False


# 单例实例
_neo4j_manager = None

def get_neo4j_manager() -> Neo4jManager:
    """获取Neo4j管理器单例"""
    global _neo4j_manager
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jManager()
    return _neo4j_manager