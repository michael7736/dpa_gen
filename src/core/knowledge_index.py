"""
知识索引系统
支持层次化索引、语义检索和知识图谱构建
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from uuid import UUID
from datetime import datetime

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from ..config.settings import get_settings
from ..database.qdrant_client import QdrantManager
from ..database.neo4j_client import Neo4jManager
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class KnowledgeIndexer:
    """知识索引器 - 负责构建和管理知识索引"""
    
    def __init__(self):
        self.settings = settings
        self.qdrant_manager = QdrantManager()
        self.neo4j_manager = Neo4jManager()
        self.embeddings = OpenAIEmbeddings(
            model=settings.ai_model.default_embedding_model,
            dimensions=settings.ai_model.embedding_dimension
        )
        
    async def create_project_collection(self, project_id: UUID) -> str:
        """为项目创建专用的向量集合"""
        collection_name = f"project_{project_id}"
        
        try:
            await self.qdrant_manager.create_collection(
                collection_name=collection_name,
                vector_size=settings.ai_model.embedding_dimension,
                distance=Distance.COSINE
            )
            logger.info(f"创建项目向量集合: {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"创建项目向量集合失败: {e}")
            raise
    
    async def index_document_chunks(
        self, 
        project_id: UUID,
        document_id: UUID,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """索引文档块到向量数据库"""
        collection_name = f"project_{project_id}"
        
        try:
            # 准备文档内容
            texts = [chunk["content"] for chunk in chunks]
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                metadata = {
                    "chunk_id": chunk["id"],
                    "document_id": str(document_id),
                    "project_id": str(project_id),
                    "chunk_index": chunk["chunk_index"],
                    "chunk_type": chunk["chunk_type"],
                    "page_number": chunk.get("page_number"),
                    "section_id": chunk.get("section_id"),
                    "keywords": chunk.get("keywords", []),
                    "entities": json.dumps(chunk.get("entities", [])),
                    "created_at": datetime.utcnow().isoformat()
                }
                metadatas.append(metadata)
            
            # 生成嵌入向量
            logger.info(f"为 {len(texts)} 个文档块生成嵌入向量")
            embeddings = await self.embeddings.aembed_documents(texts)
            
            # 构建点数据
            points = []
            for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
                point = PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "content": text,
                        **metadata
                    }
                )
                points.append(point)
            
            # 批量插入向量数据库
            await self.qdrant_manager.upsert_points(collection_name, points)
            
            logger.info(f"成功索引 {len(points)} 个文档块到集合 {collection_name}")
            
            return {
                "collection_name": collection_name,
                "indexed_chunks": len(points),
                "embedding_model": settings.ai_model.default_embedding_model
            }
            
        except Exception as e:
            logger.error(f"索引文档块失败: {e}")
            raise
    
    async def build_knowledge_graph(
        self,
        project_id: UUID,
        document_id: UUID,
        chunks: List[Dict[str, Any]],
        document_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建知识图谱"""
        try:
            # 创建文档节点
            document_node = {
                "id": str(document_id),
                "type": "Document",
                "properties": {
                    "project_id": str(project_id),
                    "title": document_structure.get("title", ""),
                    "document_type": document_structure.get("document_type", ""),
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            
            # 创建章节节点和关系
            section_nodes = []
            section_relationships = []
            
            for section in document_structure.get("sections", []):
                section_node = {
                    "id": str(section["id"]),
                    "type": "Section",
                    "properties": {
                        "title": section["title"],
                        "section_type": section["section_type"],
                        "level": section["level"],
                        "order_index": section["order_index"]
                    }
                }
                section_nodes.append(section_node)
                
                # 文档-章节关系
                doc_section_rel = {
                    "from_id": str(document_id),
                    "to_id": str(section["id"]),
                    "type": "CONTAINS_SECTION",
                    "properties": {}
                }
                section_relationships.append(doc_section_rel)
                
                # 父子章节关系
                if section.get("parent_id"):
                    parent_child_rel = {
                        "from_id": str(section["parent_id"]),
                        "to_id": str(section["id"]),
                        "type": "HAS_SUBSECTION",
                        "properties": {}
                    }
                    section_relationships.append(parent_child_rel)
            
            # 创建块节点和关系
            chunk_nodes = []
            chunk_relationships = []
            
            for chunk in chunks:
                chunk_node = {
                    "id": str(chunk["id"]),
                    "type": "Chunk",
                    "properties": {
                        "chunk_index": chunk["chunk_index"],
                        "chunk_type": chunk["chunk_type"],
                        "word_count": chunk["word_count"],
                        "keywords": chunk.get("keywords", [])
                    }
                }
                chunk_nodes.append(chunk_node)
                
                # 文档-块关系
                doc_chunk_rel = {
                    "from_id": str(document_id),
                    "to_id": str(chunk["id"]),
                    "type": "CONTAINS_CHUNK",
                    "properties": {}
                }
                chunk_relationships.append(doc_chunk_rel)
                
                # 章节-块关系
                if chunk.get("section_id"):
                    section_chunk_rel = {
                        "from_id": str(chunk["section_id"]),
                        "to_id": str(chunk["id"]),
                        "type": "CONTAINS_CHUNK",
                        "properties": {}
                    }
                    chunk_relationships.append(section_chunk_rel)
            
            # 提取实体和概念节点
            entity_nodes = []
            entity_relationships = []
            
            for chunk in chunks:
                for entity in chunk.get("entities", []):
                    entity_id = f"entity_{entity['text'].replace(' ', '_')}"
                    entity_node = {
                        "id": entity_id,
                        "type": "Entity",
                        "properties": {
                            "text": entity["text"],
                            "entity_type": entity.get("type", "UNKNOWN"),
                            "confidence": entity.get("confidence", 0.0)
                        }
                    }
                    entity_nodes.append(entity_node)
                    
                    # 块-实体关系
                    chunk_entity_rel = {
                        "from_id": str(chunk["id"]),
                        "to_id": entity_id,
                        "type": "MENTIONS",
                        "properties": {
                            "confidence": entity.get("confidence", 0.0)
                        }
                    }
                    entity_relationships.append(chunk_entity_rel)
            
            # 批量创建节点和关系
            all_nodes = [document_node] + section_nodes + chunk_nodes + entity_nodes
            all_relationships = section_relationships + chunk_relationships + entity_relationships
            
            await self.neo4j_manager.create_nodes(all_nodes)
            await self.neo4j_manager.create_relationships(all_relationships)
            
            logger.info(f"成功构建知识图谱: {len(all_nodes)} 个节点, {len(all_relationships)} 个关系")
            
            return {
                "nodes_created": len(all_nodes),
                "relationships_created": len(all_relationships),
                "document_node_id": str(document_id)
            }
            
        except Exception as e:
            logger.error(f"构建知识图谱失败: {e}")
            raise
    
    async def search_similar_chunks(
        self,
        project_id: UUID,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.7,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似的文档块"""
        collection_name = f"project_{project_id}"
        
        try:
            # 生成查询向量
            query_embedding = await self.embeddings.aembed_query(query)
            
            # 构建过滤条件
            query_filter = {"project_id": str(project_id)}
            if filter_conditions:
                query_filter.update(filter_conditions)
            
            # 执行向量搜索
            search_results = await self.qdrant_manager.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # 格式化搜索结果
            results = []
            for result in search_results:
                result_data = {
                    "chunk_id": result.payload.get("chunk_id"),
                    "document_id": result.payload.get("document_id"),
                    "content": result.payload.get("content"),
                    "score": result.score,
                    "metadata": {
                        "chunk_index": result.payload.get("chunk_index"),
                        "chunk_type": result.payload.get("chunk_type"),
                        "page_number": result.payload.get("page_number"),
                        "section_id": result.payload.get("section_id"),
                        "keywords": result.payload.get("keywords", [])
                    }
                }
                results.append(result_data)
            
            logger.info(f"搜索到 {len(results)} 个相似文档块")
            return results
            
        except Exception as e:
            logger.error(f"搜索相似文档块失败: {e}")
            raise
    
    async def get_document_structure(
        self,
        project_id: UUID,
        document_id: UUID
    ) -> Dict[str, Any]:
        """获取文档的层次结构"""
        try:
            # 从知识图谱查询文档结构
            query = """
            MATCH (doc:Document {id: $document_id})
            OPTIONAL MATCH (doc)-[:CONTAINS_SECTION]->(section:Section)
            OPTIONAL MATCH (section)-[:HAS_SUBSECTION*]->(subsection:Section)
            OPTIONAL MATCH (doc)-[:CONTAINS_CHUNK]->(chunk:Chunk)
            OPTIONAL MATCH (section)-[:CONTAINS_CHUNK]->(section_chunk:Chunk)
            
            RETURN doc, 
                   collect(DISTINCT section) as sections,
                   collect(DISTINCT subsection) as subsections,
                   collect(DISTINCT chunk) as chunks,
                   collect(DISTINCT section_chunk) as section_chunks
            """
            
            result = await self.neo4j_manager.execute_query(
                query, 
                {"document_id": str(document_id)}
            )
            
            if not result:
                return {}
            
            # 构建层次结构
            structure = {
                "document_id": str(document_id),
                "project_id": str(project_id),
                "sections": [],
                "chunks": [],
                "total_sections": 0,
                "total_chunks": 0
            }
            
            # 处理结果数据
            record = result[0]
            
            # 添加章节信息
            sections = record.get("sections", []) + record.get("subsections", [])
            for section in sections:
                if section:
                    structure["sections"].append({
                        "id": section["id"],
                        "title": section.get("title", ""),
                        "section_type": section.get("section_type", ""),
                        "level": section.get("level", 1),
                        "order_index": section.get("order_index", 0)
                    })
            
            # 添加块信息
            chunks = record.get("chunks", []) + record.get("section_chunks", [])
            for chunk in chunks:
                if chunk:
                    structure["chunks"].append({
                        "id": chunk["id"],
                        "chunk_index": chunk.get("chunk_index", 0),
                        "chunk_type": chunk.get("chunk_type", ""),
                        "word_count": chunk.get("word_count", 0)
                    })
            
            structure["total_sections"] = len(structure["sections"])
            structure["total_chunks"] = len(structure["chunks"])
            
            return structure
            
        except Exception as e:
            logger.error(f"获取文档结构失败: {e}")
            raise
    
    async def get_related_concepts(
        self,
        project_id: UUID,
        entity_text: str,
        relationship_types: List[str] = None,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """获取相关概念和实体"""
        try:
            # 构建查询条件
            rel_types = relationship_types or ["MENTIONS", "RELATED_TO", "SIMILAR_TO"]
            rel_pattern = "|".join(rel_types)
            
            query = f"""
            MATCH (start:Entity {{text: $entity_text}})
            MATCH (start)-[r:{rel_pattern}*1..{max_depth}]-(related)
            WHERE related.project_id = $project_id OR related:Entity
            
            RETURN DISTINCT related, 
                   type(r) as relationship_type,
                   length(r) as distance
            ORDER BY distance, related.confidence DESC
            LIMIT 20
            """
            
            result = await self.neo4j_manager.execute_query(
                query, 
                {
                    "entity_text": entity_text,
                    "project_id": str(project_id)
                }
            )
            
            related_concepts = []
            for record in result:
                related = record["related"]
                related_concepts.append({
                    "id": related["id"],
                    "text": related.get("text", ""),
                    "type": related.get("type", ""),
                    "relationship_type": record["relationship_type"],
                    "distance": record["distance"],
                    "confidence": related.get("confidence", 0.0)
                })
            
            return related_concepts
            
        except Exception as e:
            logger.error(f"获取相关概念失败: {e}")
            raise
    
    async def update_chunk_index(
        self,
        project_id: UUID,
        chunk_id: UUID,
        updated_content: str = None,
        updated_metadata: Dict[str, Any] = None
    ) -> bool:
        """更新块的索引信息"""
        collection_name = f"project_{project_id}"
        
        try:
            if updated_content:
                # 重新生成嵌入向量
                new_embedding = await self.embeddings.aembed_query(updated_content)
                
                # 更新向量数据库
                point = PointStruct(
                    id=str(chunk_id),
                    vector=new_embedding,
                    payload={
                        "content": updated_content,
                        **(updated_metadata or {})
                    }
                )
                
                await self.qdrant_manager.upsert_points(collection_name, [point])
            
            elif updated_metadata:
                # 仅更新元数据
                await self.qdrant_manager.update_payload(
                    collection_name,
                    str(chunk_id),
                    updated_metadata
                )
            
            logger.info(f"成功更新块索引: {chunk_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新块索引失败: {e}")
            return False
    
    async def delete_document_index(
        self,
        project_id: UUID,
        document_id: UUID
    ) -> bool:
        """删除文档的所有索引"""
        collection_name = f"project_{project_id}"
        
        try:
            # 删除向量数据库中的文档块
            await self.qdrant_manager.delete_points(
                collection_name,
                filter_conditions={"document_id": str(document_id)}
            )
            
            # 删除知识图谱中的文档节点及相关关系
            query = """
            MATCH (doc:Document {id: $document_id})
            OPTIONAL MATCH (doc)-[r1]->(related1)
            OPTIONAL MATCH (related1)-[r2]->(related2)
            DELETE r1, r2, doc, related1, related2
            """
            
            await self.neo4j_manager.execute_query(
                query,
                {"document_id": str(document_id)}
            )
            
            logger.info(f"成功删除文档索引: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档索引失败: {e}")
            return False


class HierarchicalIndexBuilder:
    """层次化索引构建器"""
    
    def __init__(self, knowledge_indexer: KnowledgeIndexer):
        self.knowledge_indexer = knowledge_indexer
        
    async def build_hierarchical_index(
        self,
        project_id: UUID,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """构建项目的层次化索引"""
        try:
            total_documents = len(documents)
            total_chunks = 0
            total_sections = 0
            
            # 为项目创建向量集合
            collection_name = await self.knowledge_indexer.create_project_collection(project_id)
            
            # 处理每个文档
            for doc in documents:
                # 索引文档块
                chunk_result = await self.knowledge_indexer.index_document_chunks(
                    project_id=project_id,
                    document_id=doc["id"],
                    chunks=doc["chunks"]
                )
                
                # 构建知识图谱
                graph_result = await self.knowledge_indexer.build_knowledge_graph(
                    project_id=project_id,
                    document_id=doc["id"],
                    chunks=doc["chunks"],
                    document_structure=doc["structure"]
                )
                
                total_chunks += chunk_result["indexed_chunks"]
                total_sections += len(doc["structure"].get("sections", []))
            
            # 构建项目级别的概念关系
            await self._build_cross_document_relationships(project_id, documents)
            
            index_stats = {
                "project_id": str(project_id),
                "collection_name": collection_name,
                "total_documents": total_documents,
                "total_sections": total_sections,
                "total_chunks": total_chunks,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"成功构建项目层次化索引: {index_stats}")
            return index_stats
            
        except Exception as e:
            logger.error(f"构建层次化索引失败: {e}")
            raise
    
    async def _build_cross_document_relationships(
        self,
        project_id: UUID,
        documents: List[Dict[str, Any]]
    ) -> None:
        """构建跨文档的概念关系"""
        try:
            # 收集所有实体
            all_entities = {}
            for doc in documents:
                for chunk in doc["chunks"]:
                    for entity in chunk.get("entities", []):
                        entity_text = entity["text"].lower()
                        if entity_text not in all_entities:
                            all_entities[entity_text] = []
                        all_entities[entity_text].append({
                            "document_id": doc["id"],
                            "chunk_id": chunk["id"],
                            "entity": entity
                        })
            
            # 创建跨文档的实体关系
            cross_doc_relationships = []
            for entity_text, occurrences in all_entities.items():
                if len(occurrences) > 1:  # 实体在多个文档中出现
                    for i in range(len(occurrences)):
                        for j in range(i + 1, len(occurrences)):
                            rel = {
                                "from_id": f"entity_{entity_text.replace(' ', '_')}",
                                "to_id": f"entity_{entity_text.replace(' ', '_')}",
                                "type": "CROSS_DOCUMENT_REFERENCE",
                                "properties": {
                                    "source_doc": str(occurrences[i]["document_id"]),
                                    "target_doc": str(occurrences[j]["document_id"]),
                                    "confidence": min(
                                        occurrences[i]["entity"].get("confidence", 0.0),
                                        occurrences[j]["entity"].get("confidence", 0.0)
                                    )
                                }
                            }
                            cross_doc_relationships.append(rel)
            
            # 批量创建关系
            if cross_doc_relationships:
                await self.knowledge_indexer.neo4j_manager.create_relationships(
                    cross_doc_relationships
                )
                
            logger.info(f"创建了 {len(cross_doc_relationships)} 个跨文档关系")
            
        except Exception as e:
            logger.error(f"构建跨文档关系失败: {e}")
            raise 