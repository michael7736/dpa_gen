"""
Neo4j图数据库客户端管理器
支持知识图谱的创建、查询和管理功能
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, TransientError

from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Neo4jManager:
    """Neo4j图数据库管理器"""
    
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j.url,
            auth=(settings.neo4j.username, settings.neo4j.password),
            database=settings.neo4j.database
        )
        
    async def close(self):
        """关闭数据库连接"""
        await self.driver.close()
        logger.info("Neo4j连接已关闭")
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行Cypher查询"""
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                logger.debug(f"查询执行成功，返回 {len(records)} 条记录")
                return records
                
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise
    
    async def execute_write_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行写入查询"""
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters or {})
                summary = await result.consume()
                
                return {
                    "nodes_created": summary.counters.nodes_created,
                    "relationships_created": summary.counters.relationships_created,
                    "properties_set": summary.counters.properties_set,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_deleted": summary.counters.relationships_deleted
                }
                
        except Exception as e:
            logger.error(f"写入查询执行失败: {e}")
            raise
    
    async def create_nodes(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量创建节点"""
        try:
            query = """
            UNWIND $nodes AS node
            CALL apoc.create.node([node.type], node.properties) YIELD node AS created_node
            RETURN count(created_node) AS nodes_created
            """
            
            result = await self.execute_write_query(query, {"nodes": nodes})
            logger.info(f"成功创建 {len(nodes)} 个节点")
            return result
            
        except Exception as e:
            logger.error(f"批量创建节点失败: {e}")
            raise
    
    async def create_relationships(
        self, 
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量创建关系"""
        try:
            query = """
            UNWIND $relationships AS rel
            MATCH (from_node {id: rel.from_id})
            MATCH (to_node {id: rel.to_id})
            CALL apoc.create.relationship(from_node, rel.type, rel.properties, to_node) 
            YIELD rel AS created_rel
            RETURN count(created_rel) AS relationships_created
            """
            
            result = await self.execute_write_query(query, {"relationships": relationships})
            logger.info(f"成功创建 {len(relationships)} 个关系")
            return result
            
        except Exception as e:
            logger.error(f"批量创建关系失败: {e}")
            raise
    
    async def find_nodes(
        self,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找节点"""
        try:
            where_clause = ""
            params = {"limit": limit}
            
            if properties:
                conditions = []
                for key, value in properties.items():
                    conditions.append(f"n.{key} = ${key}")
                    params[key] = value
                where_clause = f"WHERE {' AND '.join(conditions)}"
            
            query = f"""
            MATCH (n:{node_type})
            {where_clause}
            RETURN n
            LIMIT $limit
            """
            
            result = await self.execute_query(query, params)
            nodes = [record["n"] for record in result]
            logger.info(f"找到 {len(nodes)} 个 {node_type} 节点")
            return nodes
            
        except Exception as e:
            logger.error(f"查找节点失败: {e}")
            return []
    
    async def find_relationships(
        self,
        from_node_id: str,
        relationship_type: Optional[str] = None,
        to_node_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查找关系"""
        try:
            rel_pattern = f":{relationship_type}" if relationship_type else ""
            to_pattern = f"(to {{id: $to_node_id}})" if to_node_id else "(to)"
            
            params = {"from_node_id": from_node_id, "limit": limit}
            if to_node_id:
                params["to_node_id"] = to_node_id
            
            query = f"""
            MATCH (from {{id: $from_node_id}})-[r{rel_pattern}]->{to_pattern}
            RETURN from, r, to
            LIMIT $limit
            """
            
            result = await self.execute_query(query, params)
            logger.info(f"找到 {len(result)} 个关系")
            return result
            
        except Exception as e:
            logger.error(f"查找关系失败: {e}")
            return []
    
    async def get_node_neighbors(
        self,
        node_id: str,
        max_depth: int = 2,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取节点的邻居"""
        try:
            rel_types = "|".join(relationship_types) if relationship_types else ""
            rel_pattern = f":{rel_types}" if rel_types else ""
            
            query = f"""
            MATCH (start {{id: $node_id}})-[r{rel_pattern}*1..{max_depth}]-(neighbor)
            RETURN DISTINCT neighbor, length(r) as distance
            ORDER BY distance
            """
            
            result = await self.execute_query(query, {"node_id": node_id})
            logger.info(f"找到 {len(result)} 个邻居节点")
            return result
            
        except Exception as e:
            logger.error(f"获取邻居节点失败: {e}")
            return []
    
    async def get_shortest_path(
        self,
        from_node_id: str,
        to_node_id: str,
        max_length: int = 5
    ) -> Optional[Dict[str, Any]]:
        """获取两个节点之间的最短路径"""
        try:
            query = f"""
            MATCH (from {{id: $from_node_id}}), (to {{id: $to_node_id}})
            MATCH path = shortestPath((from)-[*..{max_length}]-(to))
            RETURN path, length(path) as path_length
            """
            
            result = await self.execute_query(
                query, 
                {"from_node_id": from_node_id, "to_node_id": to_node_id}
            )
            
            if result:
                logger.info(f"找到最短路径，长度: {result[0]['path_length']}")
                return result[0]
            else:
                logger.info("未找到路径")
                return None
                
        except Exception as e:
            logger.error(f"获取最短路径失败: {e}")
            return None
    
    async def delete_nodes(
        self,
        node_ids: List[str],
        delete_relationships: bool = True
    ) -> Dict[str, Any]:
        """删除节点"""
        try:
            if delete_relationships:
                query = """
                UNWIND $node_ids AS node_id
                MATCH (n {id: node_id})
                DETACH DELETE n
                """
            else:
                query = """
                UNWIND $node_ids AS node_id
                MATCH (n {id: node_id})
                DELETE n
                """
            
            result = await self.execute_write_query(query, {"node_ids": node_ids})
            logger.info(f"成功删除 {len(node_ids)} 个节点")
            return result
            
        except Exception as e:
            logger.error(f"删除节点失败: {e}")
            raise
    
    async def delete_relationships(
        self,
        relationship_ids: List[str]
    ) -> Dict[str, Any]:
        """删除关系"""
        try:
            query = """
            UNWIND $relationship_ids AS rel_id
            MATCH ()-[r]-()
            WHERE id(r) = rel_id
            DELETE r
            """
            
            result = await self.execute_write_query(query, {"relationship_ids": relationship_ids})
            logger.info(f"成功删除 {len(relationship_ids)} 个关系")
            return result
            
        except Exception as e:
            logger.error(f"删除关系失败: {e}")
            raise
    
    async def update_node_properties(
        self,
        node_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新节点属性"""
        try:
            set_clauses = []
            params = {"node_id": node_id}
            
            for key, value in properties.items():
                set_clauses.append(f"n.{key} = ${key}")
                params[key] = value
            
            query = f"""
            MATCH (n {{id: $node_id}})
            SET {', '.join(set_clauses)}
            RETURN n
            """
            
            result = await self.execute_write_query(query, params)
            logger.info(f"成功更新节点属性: {node_id}")
            return result
            
        except Exception as e:
            logger.error(f"更新节点属性失败: {e}")
            raise
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """获取图数据库统计信息"""
        try:
            query = """
            MATCH (n)
            OPTIONAL MATCH ()-[r]->()
            RETURN 
                count(DISTINCT n) as total_nodes,
                count(DISTINCT r) as total_relationships,
                count(DISTINCT labels(n)) as node_types,
                count(DISTINCT type(r)) as relationship_types
            """
            
            result = await self.execute_query(query)
            if result:
                stats = result[0]
                logger.info(f"图统计信息: {stats}")
                return stats
            else:
                return {}
                
        except Exception as e:
            logger.error(f"获取图统计信息失败: {e}")
            return {}
    
    async def create_indexes(self) -> Dict[str, Any]:
        """创建索引以提高查询性能"""
        try:
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (n:Document) ON (n.id)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Section) ON (n.id)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Chunk) ON (n.id)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.text)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Document) ON (n.project_id)",
                "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)"
            ]
            
            results = []
            for index_query in indexes:
                result = await self.execute_write_query(index_query)
                results.append(result)
            
            logger.info(f"成功创建 {len(indexes)} 个索引")
            return {"indexes_created": len(indexes)}
            
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise
    
    async def clear_database(self) -> Dict[str, Any]:
        """清空数据库（谨慎使用）"""
        try:
            query = """
            MATCH (n)
            DETACH DELETE n
            """
            
            result = await self.execute_write_query(query)
            logger.warning("数据库已清空")
            return result
            
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            raise


# 全局Neo4j管理器实例
_neo4j_manager = None

def get_neo4j_manager() -> Neo4jManager:
    """获取Neo4j管理器实例（单例模式）"""
    global _neo4j_manager
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jManager()
    return _neo4j_manager 