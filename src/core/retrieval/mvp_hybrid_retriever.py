"""
MVP混合检索器 - 三阶段检索系统
1. 向量搜索 (Qdrant)
2. 图谱扩展 (Neo4j 1-hop)
3. Memory Bank增强
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict

from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

from src.database.qdrant import get_qdrant_manager
from src.database.neo4j_client import get_neo4j_manager
from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 默认配置
DEFAULT_USER_ID = "u1"
DEFAULT_TOP_K = 10
DEFAULT_SCORE_THRESHOLD = 0.3  # 降低阈值以提高召回率
DEFAULT_GRAPH_HOPS = 1  # MVP限制为1跳


@dataclass
class RetrievalResult:
    """检索结果"""
    doc_id: str
    content: str
    score: float
    source: str  # "vector", "graph", "memory"
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class HybridRetrievalResult:
    """混合检索结果"""
    query: str
    total_results: int
    vector_results: List[RetrievalResult]
    graph_results: List[RetrievalResult]
    memory_results: List[RetrievalResult]
    fused_results: List[RetrievalResult]
    retrieval_time: float
    metadata: Dict[str, Any]


class MVPHybridRetriever:
    """
    MVP混合检索器
    实现三阶段检索：向量搜索 → 图谱扩展 → Memory Bank增强
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        self.qdrant_manager = get_qdrant_manager()
        self.neo4j_manager = get_neo4j_manager()
        self.memory_bank_manager = create_memory_bank_manager(user_id=user_id)
        
        # 嵌入模型 - 使用与系统一致的模型
        self.embeddings = OpenAIEmbeddings(
            model=settings.ai_model.default_embedding_model,  # text-embedding-3-large
            api_key=settings.ai_model.openai_api_key
        )
        
    async def retrieve(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        filters: Optional[Dict[str, Any]] = None
    ) -> HybridRetrievalResult:
        """
        执行三阶段混合检索
        
        Args:
            query: 查询文本
            project_id: 项目ID
            top_k: 返回结果数量
            score_threshold: 分数阈值
            filters: 额外过滤条件
            
        Returns:
            HybridRetrievalResult: 混合检索结果
        """
        start_time = datetime.now()
        
        # 生成查询向量
        query_embedding = await self.embeddings.aembed_query(query)
        
        # 并行执行三种检索
        vector_task = self._vector_search(
            query_embedding, project_id, top_k * 2, score_threshold, filters
        )
        graph_task = self._graph_search(
            query, project_id, top_k
        )
        memory_task = self._memory_bank_search(
            query, project_id
        )
        
        # 等待所有检索完成
        vector_results, graph_results, memory_results = await asyncio.gather(
            vector_task, graph_task, memory_task
        )
        
        # 结果融合
        fused_results = await self._fuse_results(
            vector_results, graph_results, memory_results, top_k
        )
        
        # 计算检索时间
        retrieval_time = (datetime.now() - start_time).total_seconds()
        
        return HybridRetrievalResult(
            query=query,
            total_results=len(fused_results),
            vector_results=vector_results,
            graph_results=graph_results,
            memory_results=memory_results,
            fused_results=fused_results,
            retrieval_time=retrieval_time,
            metadata={
                "project_id": project_id,
                "top_k": top_k,
                "score_threshold": score_threshold,
                "user_id": self.user_id
            }
        )
        
    async def _vector_search(
        self,
        query_embedding: List[float],
        project_id: Optional[str],
        top_k: int,
        score_threshold: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[RetrievalResult]:
        """向量搜索阶段"""
        try:
            # 构建过滤条件
            search_filters = {
                "user_id": self.user_id
            }
            if project_id:
                search_filters["project_id"] = project_id
            if filters:
                search_filters.update(filters)
                
            # 搜索向量数据库
            # 使用与存储时一致的集合名
            collection_name = f"project_{project_id or 'default'}"
            results = await self.qdrant_manager.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=search_filters
            )
            
            # 转换为统一格式
            retrieval_results = []
            for hit in results:
                retrieval_results.append(RetrievalResult(
                    doc_id=hit.id,
                    content=hit.payload.get("content", ""),
                    score=hit.score,
                    source="vector",
                    metadata=hit.payload,
                    embedding=hit.vector
                ))
                
            logger.info(f"Vector search found {len(retrieval_results)} results")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
            
    async def _graph_search(
        self,
        query: str,
        project_id: Optional[str],
        top_k: int
    ) -> List[RetrievalResult]:
        """图谱搜索阶段（1跳扩展）"""
        try:
            # 简单的实体提取（MVP版本）
            entities = self._extract_entities_simple(query)
            
            if not entities:
                return []
                
            # 构建Neo4j查询（1跳邻居）
            cypher_query = """
            MATCH (e:Entity)-[r]-(related:Entity)
            WHERE e.name IN $entities
            AND e.user_id = $user_id
            """
            
            params = {
                "entities": entities,
                "user_id": self.user_id
            }
            
            if project_id:
                cypher_query += " AND e.project_id = $project_id"
                params["project_id"] = project_id
                
            cypher_query += """
            WITH related, COUNT(DISTINCT e) as relevance
            ORDER BY relevance DESC
            LIMIT $limit
            RETURN related.name as name, 
                   related.description as description,
                   related.id as id,
                   relevance
            """
            
            params["limit"] = top_k
            
            # 执行查询
            results = await self.neo4j_manager.execute_query(cypher_query, params)
            
            # 转换结果
            retrieval_results = []
            for record in results:
                content = f"{record['name']}: {record.get('description', '')}"
                score = min(record['relevance'] / len(entities), 1.0)
                
                retrieval_results.append(RetrievalResult(
                    doc_id=record['id'],
                    content=content,
                    score=score,
                    source="graph",
                    metadata={
                        "entity_name": record['name'],
                        "relevance": record['relevance']
                    }
                ))
                
            logger.info(f"Graph search found {len(retrieval_results)} results")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Graph search error: {e}")
            return []
            
    async def _memory_bank_search(
        self,
        query: str,
        project_id: Optional[str]
    ) -> List[RetrievalResult]:
        """Memory Bank搜索阶段"""
        try:
            if not project_id:
                return []
                
            # 获取Memory Bank快照
            snapshot = await self.memory_bank_manager.get_snapshot(project_id)
            
            if not snapshot:
                return []
                
            results = []
            
            # 处理字典格式的快照
            if isinstance(snapshot, dict):
                # 搜索动态摘要
                dynamic_summary = snapshot.get('dynamic_summary', '')
                if dynamic_summary and query.lower() in dynamic_summary.lower():
                    results.append(RetrievalResult(
                        doc_id=f"memory_bank_summary_{project_id}",
                        content=dynamic_summary,
                        score=0.8,  # 固定高分
                        source="memory",
                        metadata={
                            "type": "dynamic_summary",
                            "project_id": project_id
                        }
                    ))
                    
                # 搜索核心概念
                core_concepts = snapshot.get('core_concepts', [])
                for concept in core_concepts:
                    if query.lower() in concept.get("name", "").lower():
                        results.append(RetrievalResult(
                            doc_id=f"memory_bank_concept_{concept.get('name')}",
                            content=f"{concept.get('name')}: {concept.get('description', '')}",
                            score=concept.get("confidence", 0.7),
                            source="memory",
                            metadata={
                                "type": "concept",
                                "concept": concept
                            }
                        ))
                        
                # 搜索学习日志
                learning_journals = snapshot.get('learning_journals', [])
                for entry in learning_journals[-5:]:  # 最近5条
                    if query.lower() in entry.get("content", "").lower():
                        results.append(RetrievalResult(
                            doc_id=f"memory_bank_journal_{entry.get('timestamp')}",
                            content=entry.get("content", ""),
                            score=0.6,
                            source="memory",
                            metadata={
                                "type": "learning_journal",
                                "timestamp": entry.get("timestamp")
                            }
                        ))
            else:
                # 处理对象格式的快照
                # 搜索动态摘要
                if snapshot.dynamic_summary and query.lower() in snapshot.dynamic_summary.lower():
                    results.append(RetrievalResult(
                        doc_id=f"memory_bank_summary_{project_id}",
                        content=snapshot.dynamic_summary,
                        score=0.8,  # 固定高分
                        source="memory",
                        metadata={
                            "type": "dynamic_summary",
                            "project_id": project_id
                        }
                    ))
                    
                # 搜索核心概念
                for concept in snapshot.core_concepts:
                    if query.lower() in concept.get("name", "").lower():
                        results.append(RetrievalResult(
                            doc_id=f"memory_bank_concept_{concept.get('name')}",
                            content=f"{concept.get('name')}: {concept.get('description', '')}",
                            score=concept.get("confidence", 0.7),
                            source="memory",
                            metadata={
                                "type": "concept",
                                "concept": concept
                            }
                        ))
                        
                # 搜索学习日志
                for entry in snapshot.learning_journals[-5:]:  # 最近5条
                    if query.lower() in entry.get("content", "").lower():
                        results.append(RetrievalResult(
                            doc_id=f"memory_bank_journal_{entry.get('timestamp')}",
                            content=entry.get("content", ""),
                            score=0.6,
                            source="memory",
                            metadata={
                                "type": "learning_journal",
                                "timestamp": entry.get("timestamp")
                            }
                        ))
                    
            logger.info(f"Memory Bank search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Memory Bank search error: {e}")
            return []
            
    async def _fuse_results(
        self,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        memory_results: List[RetrievalResult],
        top_k: int
    ) -> List[RetrievalResult]:
        """
        结果融合算法
        使用加权排名融合(Weighted Rank Fusion)
        """
        # 权重配置
        weights = {
            "vector": 0.5,
            "graph": 0.3,
            "memory": 0.2
        }
        
        # 收集所有唯一结果
        all_results = {}
        
        # 处理向量搜索结果
        for i, result in enumerate(vector_results):
            key = result.doc_id
            if key not in all_results:
                all_results[key] = {
                    "result": result,
                    "ranks": {},
                    "scores": {}
                }
            all_results[key]["ranks"]["vector"] = i + 1
            all_results[key]["scores"]["vector"] = result.score
            
        # 处理图谱搜索结果
        for i, result in enumerate(graph_results):
            key = result.doc_id
            if key not in all_results:
                all_results[key] = {
                    "result": result,
                    "ranks": {},
                    "scores": {}
                }
            all_results[key]["ranks"]["graph"] = i + 1
            all_results[key]["scores"]["graph"] = result.score
            
        # 处理Memory Bank结果
        for i, result in enumerate(memory_results):
            key = result.doc_id
            if key not in all_results:
                all_results[key] = {
                    "result": result,
                    "ranks": {},
                    "scores": {}
                }
            all_results[key]["ranks"]["memory"] = i + 1
            all_results[key]["scores"]["memory"] = result.score
            
        # 计算融合分数
        for key, data in all_results.items():
            fusion_score = 0.0
            
            # 基于排名的融合
            for source, weight in weights.items():
                if source in data["ranks"]:
                    rank = data["ranks"][source]
                    # 倒数排名分数
                    rank_score = 1.0 / (rank + 1)
                    fusion_score += weight * rank_score
                    
            # 基于原始分数的加权
            for source, weight in weights.items():
                if source in data["scores"]:
                    fusion_score += weight * data["scores"][source] * 0.5
                    
            data["fusion_score"] = fusion_score
            
        # 排序并返回Top-K
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x["fusion_score"],
            reverse=True
        )[:top_k]
        
        # 更新融合后的分数
        fused_results = []
        for item in sorted_results:
            result = item["result"]
            result.score = item["fusion_score"]
            fused_results.append(result)
            
        logger.info(f"Fused {len(all_results)} results into top {len(fused_results)}")
        return fused_results
        
    def _extract_entities_simple(self, text: str) -> List[str]:
        """简单的实体提取（MVP版本）"""
        # 基于关键词的简单提取
        entities = []
        
        # 预定义的实体关键词（示例）
        keywords = [
            "深度学习", "机器学习", "神经网络", "CNN", "RNN", "Transformer",
            "NLP", "计算机视觉", "自然语言处理", "强化学习", "监督学习"
        ]
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                entities.append(keyword)
                
        return entities[:5]  # 限制最多5个实体
        
    async def get_context_documents(
        self,
        doc_ids: List[str],
        include_embeddings: bool = False
    ) -> List[Document]:
        """
        获取文档的完整内容
        
        Args:
            doc_ids: 文档ID列表
            include_embeddings: 是否包含嵌入向量
            
        Returns:
            List[Document]: LangChain文档列表
        """
        documents = []
        
        for doc_id in doc_ids:
            try:
                # 从向量数据库获取
                point = await self.qdrant_manager.retrieve(
                    collection_name="chunks",
                    ids=[doc_id]
                )
                
                if point:
                    doc = Document(
                        page_content=point[0].payload.get("content", ""),
                        metadata=point[0].payload
                    )
                    
                    if include_embeddings:
                        doc.metadata["embedding"] = point[0].vector
                        
                    documents.append(doc)
                    
            except Exception as e:
                logger.error(f"Failed to retrieve document {doc_id}: {e}")
                
        return documents


# 工厂函数
def create_mvp_hybrid_retriever(user_id: str = DEFAULT_USER_ID) -> MVPHybridRetriever:
    """创建MVP混合检索器实例"""
    return MVPHybridRetriever(user_id=user_id)