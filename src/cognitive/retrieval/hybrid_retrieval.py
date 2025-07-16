"""
三阶段混合检索系统 - Vector → Graph → Memory Bank
基于V3设计的完整检索增强生成（RAG）实现
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from pathlib import Path
import json

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ..storage import create_cognitive_storage
from ..memory.memory_bank import create_memory_bank_manager
from ...utils.logger import get_logger
from ...config.settings import get_settings

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """检索结果数据结构"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    stage: str = "unknown"  # vector/graph/memory
    type: str = "chunk"  # chunk/concept/relationship/memory
    
    def __post_init__(self):
        self.metadata["retrieved_at"] = datetime.now().isoformat()


@dataclass
class HybridQuery:
    """混合查询请求"""
    query: str
    query_type: str = "semantic"  # semantic/factual/exploratory
    max_results: int = 20
    filters: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, Any] = field(default_factory=dict)
    
    # 阶段权重配置
    vector_weight: float = 0.4
    graph_weight: float = 0.35
    memory_weight: float = 0.25
    
    # 检索配置
    vector_top_k: int = 50
    graph_depth: int = 2
    memory_similarity_threshold: float = 0.7


class VectorRetriever:
    """第一阶段：向量检索器"""
    
    def __init__(self, storage_manager, mock_mode: bool = False):
        self.storage = storage_manager
        self.mock_mode = mock_mode
        
        # 尝试初始化OpenAI嵌入，如果失败则使用模拟模式
        if not mock_mode:
            try:
                settings = get_settings()
                if settings.ai_model.openai_api_key:
                    self.embeddings = OpenAIEmbeddings(
                        model=settings.ai_model.default_embedding_model,
                        openai_api_key=settings.ai_model.openai_api_key,
                        openai_api_base=settings.ai_model.openai_base_url
                    )
                    logger.info("OpenAI embeddings initialized successfully")
                else:
                    logger.warning("OpenAI API key not found, using mock mode")
                    self.mock_mode = True
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}, using mock mode")
                self.mock_mode = True
        
        self.collections = {
            "chunks": "document_chunks",
            "concepts": "semantic_concepts", 
            "summaries": "document_summaries"
        }
    
    async def retrieve(
        self,
        query: HybridQuery,
        embedding_cache: Dict[str, List[float]] = None
    ) -> List[RetrievalResult]:
        """执行向量检索"""
        logger.info(f"开始向量检索，查询: {query.query[:50]}...")
        
        # 生成查询向量
        if embedding_cache and query.query in embedding_cache:
            query_vector = embedding_cache[query.query]
        else:
            if self.mock_mode:
                # 模拟向量
                query_vector = [0.1] * 3072
            else:
                query_vector = await self.embeddings.aembed_query(query.query)
            if embedding_cache is not None:
                embedding_cache[query.query] = query_vector
        
        results = []
        
        # 1. 文档块检索
        chunk_results = await self._search_chunks(query, query_vector)
        results.extend(chunk_results)
        
        # 2. 概念检索
        concept_results = await self._search_concepts(query, query_vector)
        results.extend(concept_results)
        
        # 3. 摘要检索
        summary_results = await self._search_summaries(query, query_vector)
        results.extend(summary_results)
        
        # 去重和重排序
        results = self._deduplicate_results(results)
        results = sorted(results, key=lambda x: x.score, reverse=True)
        
        logger.info(f"向量检索完成，获得 {len(results)} 个结果")
        return results[:query.vector_top_k]
    
    async def _search_chunks(
        self,
        query: HybridQuery,
        query_vector: List[float]
    ) -> List[RetrievalResult]:
        """搜索文档块"""
        # 实际实现应该调用Qdrant
        # 这里提供模拟实现
        results = []
        
        # 模拟向量搜索结果
        for i in range(10):
            result = RetrievalResult(
                content=f"模拟文档块 {i}: 与查询'{query.query}'相关的内容...",
                score=0.9 - i * 0.05,
                source=f"chunk_{i}",
                stage="vector",
                type="chunk",
                metadata={
                    "collection": "chunks",
                    "document_id": f"doc_{i // 3}",
                    "chunk_index": i
                }
            )
            results.append(result)
        
        return results
    
    async def _search_concepts(
        self,
        query: HybridQuery,
        query_vector: List[float]
    ) -> List[RetrievalResult]:
        """搜索语义概念"""
        results = []
        
        # 模拟概念搜索
        for i in range(5):
            result = RetrievalResult(
                content=f"概念 {i}: 与查询相关的语义概念定义...",
                score=0.85 - i * 0.08,
                source=f"concept_{i}",
                stage="vector",
                type="concept",
                metadata={
                    "collection": "concepts",
                    "concept_type": "semantic",
                    "definition_length": 200 + i * 50
                }
            )
            results.append(result)
        
        return results
    
    async def _search_summaries(
        self,
        query: HybridQuery,
        query_vector: List[float]
    ) -> List[RetrievalResult]:
        """搜索文档摘要"""
        results = []
        
        # 模拟摘要搜索
        for i in range(3):
            result = RetrievalResult(
                content=f"摘要 {i}: 相关文档的高级摘要...",
                score=0.8 - i * 0.1,
                source=f"summary_{i}",
                stage="vector",
                type="summary",
                metadata={
                    "collection": "summaries",
                    "document_count": 5 + i * 2,
                    "summary_level": "high"
                }
            )
            results.append(result)
        
        return results
    
    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """去重结果"""
        seen = set()
        unique_results = []
        
        for result in results:
            # 使用内容hash作为去重键
            content_hash = hash(result.content)
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(result)
        
        return unique_results


class GraphEnhancer:
    """第二阶段：图谱增强器"""
    
    def __init__(self, storage_manager, mock_mode: bool = False):
        self.storage = storage_manager
        self.mock_mode = mock_mode
        
        # 尝试初始化LLM
        if not mock_mode:
            try:
                settings = get_settings()
                if settings.ai_model.openai_api_key:
                    self.llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=0,
                        openai_api_key=settings.ai_model.openai_api_key,
                        openai_api_base=settings.ai_model.openai_base_url
                    )
                    logger.info("LLM initialized successfully")
                else:
                    logger.warning("OpenAI API key not found for LLM, using mock mode")
                    self.mock_mode = True
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}, using mock mode")
                self.mock_mode = True
    
    async def enhance(
        self,
        query: HybridQuery,
        vector_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """图谱增强检索"""
        logger.info("开始图谱增强...")
        
        enhanced_results = []
        
        # 1. 提取关键实体
        entities = await self._extract_entities(query, vector_results)
        
        # 2. 图谱扩展
        graph_results = await self._expand_graph_context(entities, query)
        enhanced_results.extend(graph_results)
        
        # 3. 关系推理
        relation_results = await self._infer_relationships(entities, query)
        enhanced_results.extend(relation_results)
        
        # 4. 上下文增强
        context_results = await self._enhance_context(vector_results, graph_results)
        enhanced_results.extend(context_results)
        
        logger.info(f"图谱增强完成，新增 {len(enhanced_results)} 个结果")
        return enhanced_results
    
    async def _extract_entities(
        self,
        query: HybridQuery,
        vector_results: List[RetrievalResult]
    ) -> List[str]:
        """提取关键实体"""
        # 构建实体提取上下文
        context = "\n".join([r.content[:200] for r in vector_results[:5]])
        
        extraction_prompt = f"""
        从以下查询和上下文中提取关键实体：
        
        查询: {query.query}
        
        上下文:
        {context}
        
        请提取最重要的3-5个实体，返回JSON格式的列表。
        """
        
        if self.mock_mode:
            # 模拟实体提取
            return ["认知架构", "人工智能", "工作记忆"]
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            entities = json.loads(response.content)
            return entities if isinstance(entities, list) else []
        except Exception as e:
            logger.warning(f"实体提取失败: {e}")
            return []
    
    async def _expand_graph_context(
        self,
        entities: List[str],
        query: HybridQuery
    ) -> List[RetrievalResult]:
        """扩展图谱上下文"""
        results = []
        
        # 模拟图谱查询
        for i, entity in enumerate(entities[:3]):
            # 邻居节点
            neighbor_result = RetrievalResult(
                content=f"与 {entity} 相关的邻居概念和关系...",
                score=0.8 - i * 0.1,
                source=f"graph_neighbors_{entity}",
                stage="graph",
                type="relationship",
                metadata={
                    "entity": entity,
                    "relation_type": "neighbors",
                    "depth": 1
                }
            )
            results.append(neighbor_result)
            
            # 路径查询
            if i < 2:  # 限制路径查询数量
                path_result = RetrievalResult(
                    content=f"从 {entity} 到其他概念的推理路径...",
                    score=0.75 - i * 0.1,
                    source=f"graph_path_{entity}",
                    stage="graph",
                    type="path",
                    metadata={
                        "entity": entity,
                        "path_length": 2 + i,
                        "confidence": 0.8
                    }
                )
                results.append(path_result)
        
        return results
    
    async def _infer_relationships(
        self,
        entities: List[str],
        query: HybridQuery
    ) -> List[RetrievalResult]:
        """推理实体关系"""
        results = []
        
        # 实体对关系推理
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                relation_result = RetrievalResult(
                    content=f"{entity1} 与 {entity2} 之间的隐含关系...",
                    score=0.7 - (i+j) * 0.05,
                    source=f"relation_{entity1}_{entity2}",
                    stage="graph",
                    type="inferred_relation",
                    metadata={
                        "entity1": entity1,
                        "entity2": entity2,
                        "relation_strength": 0.7,
                        "inference_method": "graph_reasoning"
                    }
                )
                results.append(relation_result)
        
        return results[:5]  # 限制推理关系数量
    
    async def _enhance_context(
        self,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """增强上下文"""
        enhanced = []
        
        # 为向量结果添加图谱上下文
        for vector_result in vector_results[:3]:
            # 找到相关的图谱结果
            relevant_graph = [
                gr for gr in graph_results 
                if any(entity in vector_result.content.lower() 
                      for entity in gr.metadata.get("entity", "").split())
            ]
            
            if relevant_graph:
                enhanced_content = vector_result.content + "\n\n[图谱上下文]\n" + \
                                 "\n".join(gr.content for gr in relevant_graph[:2])
                
                enhanced_result = RetrievalResult(
                    content=enhanced_content,
                    score=vector_result.score * 1.1,  # 增强分数
                    source=f"enhanced_{vector_result.source}",
                    stage="graph",
                    type="enhanced_chunk",
                    metadata={
                        **vector_result.metadata,
                        "enhancement_type": "graph_context",
                        "graph_sources": [gr.source for gr in relevant_graph]
                    }
                )
                enhanced.append(enhanced_result)
        
        return enhanced


class MemoryBankRetriever:
    """第三阶段：记忆库检索器"""
    
    def __init__(self, storage_manager, mock_mode: bool = False):
        self.storage = storage_manager
        self.memory_bank = create_memory_bank_manager()
        self.mock_mode = mock_mode
        
        # 尝试初始化嵌入模型
        if not mock_mode:
            try:
                settings = get_settings()
                if settings.ai_model.openai_api_key:
                    self.embeddings = OpenAIEmbeddings(
                        model=settings.ai_model.default_embedding_model,
                        openai_api_key=settings.ai_model.openai_api_key,
                        openai_api_base=settings.ai_model.openai_base_url
                    )
                    logger.info("Memory embeddings initialized successfully")
                else:
                    logger.warning("OpenAI API key not found for Memory embeddings, using mock mode")
                    self.mock_mode = True
            except Exception as e:
                logger.warning(f"Failed to initialize Memory embeddings: {e}, using mock mode")
                self.mock_mode = True
    
    async def retrieve(
        self,
        query: HybridQuery,
        previous_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """从记忆库检索"""
        logger.info("开始记忆库检索...")
        
        results = []
        
        # 1. 检索相关记忆
        memory_results = await self._search_memories(query)
        results.extend(memory_results)
        
        # 2. 检索学习假设
        hypothesis_results = await self._search_hypotheses(query)
        results.extend(hypothesis_results)
        
        # 3. 检索研究计划
        plan_results = await self._search_research_plans(query)
        results.extend(plan_results)
        
        # 4. 动态摘要匹配
        summary_results = await self._match_dynamic_summaries(query, previous_results)
        results.extend(summary_results)
        
        logger.info(f"记忆库检索完成，获得 {len(results)} 个结果")
        return results
    
    async def _search_memories(self, query: HybridQuery) -> List[RetrievalResult]:
        """搜索记忆"""
        results = []
        
        # 读取记忆库
        memories = await self.memory_bank.read_all_memories()
        
        # 计算查询向量
        if self.mock_mode:
            query_vector = [0.1] * 3072  # 模拟向量
        else:
            query_vector = await self.embeddings.aembed_query(query.query)
        
        # 搜索各类记忆
        for memory_type, memory_data in memories.items():
            if memory_type == "learning_journal":
                # 学习日志搜索
                for i, entry in enumerate(memory_data.get("entries", [])[:5]):
                    result = RetrievalResult(
                        content=f"学习记录: {entry.get('insight', 'No insight')}",
                        score=0.7 - i * 0.05,
                        source=f"memory_journal_{i}",
                        stage="memory",
                        type="learning_record",
                        metadata={
                            "memory_type": "learning_journal",
                            "timestamp": entry.get("timestamp"),
                            "confidence": entry.get("confidence", 0.5)
                        }
                    )
                    results.append(result)
            
            elif memory_type == "knowledge_graph":
                # 知识图谱记忆
                concepts = memory_data.get("concepts", {})
                for concept_id, concept_data in list(concepts.items())[:3]:
                    result = RetrievalResult(
                        content=f"概念记忆: {concept_data.get('definition', 'No definition')}",
                        score=0.75,
                        source=f"memory_concept_{concept_id}",
                        stage="memory",
                        type="concept_memory",
                        metadata={
                            "memory_type": "knowledge_graph",
                            "concept_id": concept_id,
                            "connections": len(concept_data.get("connections", []))
                        }
                    )
                    results.append(result)
        
        return results
    
    async def _search_hypotheses(self, query: HybridQuery) -> List[RetrievalResult]:
        """搜索假设"""
        results = []
        
        # 模拟假设搜索
        for i in range(3):
            result = RetrievalResult(
                content=f"假设 {i}: 关于查询主题的学习假设...",
                score=0.6 - i * 0.1,
                source=f"hypothesis_{i}",
                stage="memory",
                type="hypothesis",
                metadata={
                    "memory_type": "hypothesis",
                    "status": "active",
                    "confidence": 0.7 - i * 0.1
                }
            )
            results.append(result)
        
        return results
    
    async def _search_research_plans(self, query: HybridQuery) -> List[RetrievalResult]:
        """搜索研究计划"""
        results = []
        
        # 模拟研究计划搜索
        for i in range(2):
            result = RetrievalResult(
                content=f"研究计划 {i}: 相关的研究方向和计划...",
                score=0.65 - i * 0.1,
                source=f"research_plan_{i}",
                stage="memory",
                type="research_plan",
                metadata={
                    "memory_type": "research_plan",
                    "status": "active",
                    "progress": 0.3 + i * 0.2
                }
            )
            results.append(result)
        
        return results
    
    async def _match_dynamic_summaries(
        self,
        query: HybridQuery,
        previous_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """匹配动态摘要"""
        results = []
        
        # 读取动态摘要
        try:
            summary_path = Path(self.memory_bank.base_path) / "dynamic_summary.json"
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
                
                # 匹配核心洞察
                for i, insight in enumerate(summary_data.get("core_insights", [])[:3]):
                    result = RetrievalResult(
                        content=f"核心洞察: {insight.get('content', 'No content')}",
                        score=0.8 - i * 0.05,
                        source=f"dynamic_summary_insight_{i}",
                        stage="memory",
                        type="dynamic_insight",
                        metadata={
                            "memory_type": "dynamic_summary",
                            "insight_type": "core",
                            "confidence": insight.get("confidence", 0.5)
                        }
                    )
                    results.append(result)
        except Exception as e:
            logger.warning(f"动态摘要匹配失败: {e}")
        
        return results


class HybridRetrievalSystem:
    """三阶段混合检索系统主控制器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.storage = create_cognitive_storage()
        
        # 检查是否需要模拟模式
        mock_mode = self.config.get("mock_mode", False)
        
        # 初始化三个阶段的检索器
        self.vector_retriever = VectorRetriever(self.storage, mock_mode)
        self.graph_enhancer = GraphEnhancer(self.storage, mock_mode)
        self.memory_retriever = MemoryBankRetriever(self.storage, mock_mode)
        
        # 缓存
        self.embedding_cache = {}
        self.result_cache = {}
        
        logger.info("混合检索系统初始化完成")
    
    async def retrieve(
        self,
        query: HybridQuery,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """执行完整的三阶段检索"""
        logger.info(f"开始三阶段混合检索: {query.query}")
        
        # 检查缓存
        if use_cache:
            cache_key = f"{query.query}_{query.query_type}"
            if cache_key in self.result_cache:
                logger.info("使用缓存结果")
                return self.result_cache[cache_key]
        
        start_time = datetime.now()
        
        # 第一阶段：向量检索
        vector_results = await self.vector_retriever.retrieve(
            query, self.embedding_cache
        )
        
        # 第二阶段：图谱增强
        graph_results = await self.graph_enhancer.enhance(
            query, vector_results
        )
        
        # 第三阶段：记忆库检索
        memory_results = await self.memory_retriever.retrieve(
            query, vector_results + graph_results
        )
        
        # 融合和重排序
        final_results = await self._fuse_and_rerank(
            query, vector_results, graph_results, memory_results
        )
        
        # 构建完整响应
        response = {
            "query": query.query,
            "query_type": query.query_type,
            "total_results": len(final_results),
            "results": final_results[:query.max_results],
            "stage_statistics": {
                "vector_results": len(vector_results),
                "graph_results": len(graph_results),
                "memory_results": len(memory_results)
            },
            "retrieval_time": (datetime.now() - start_time).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }
        
        # 缓存结果
        if use_cache:
            self.result_cache[cache_key] = response
        
        logger.info(f"三阶段检索完成，返回 {len(final_results)} 个结果")
        return response
    
    async def _fuse_and_rerank(
        self,
        query: HybridQuery,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        memory_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """融合和重排序"""
        all_results = []
        
        # 加权融合
        for result in vector_results:
            result.score *= query.vector_weight
            all_results.append(result)
        
        for result in graph_results:
            result.score *= query.graph_weight
            all_results.append(result)
        
        for result in memory_results:
            result.score *= query.memory_weight
            all_results.append(result)
        
        # 去重
        unique_results = self._deduplicate_by_content(all_results)
        
        # 多样性重排序
        diverse_results = self._diversify_results(unique_results)
        
        # 按分数排序
        final_results = sorted(diverse_results, key=lambda x: x.score, reverse=True)
        
        return final_results
    
    def _deduplicate_by_content(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """基于内容去重"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            content_signature = result.content[:100].lower().strip()
            if content_signature not in seen_content:
                seen_content.add(content_signature)
                unique_results.append(result)
        
        return unique_results
    
    def _diversify_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """多样性重排序"""
        if len(results) <= 5:
            return results
        
        # 简单的多样性算法：确保不同类型的结果分布均匀
        type_buckets = {}
        for result in results:
            result_type = result.type
            if result_type not in type_buckets:
                type_buckets[result_type] = []
            type_buckets[result_type].append(result)
        
        # 轮询选择
        diverse_results = []
        max_per_type = max(3, len(results) // len(type_buckets))
        
        for result_type, bucket in type_buckets.items():
            # 按分数排序并选择前N个
            bucket_sorted = sorted(bucket, key=lambda x: x.score, reverse=True)
            diverse_results.extend(bucket_sorted[:max_per_type])
        
        return diverse_results
    
    async def clear_cache(self):
        """清除缓存"""
        self.embedding_cache.clear()
        self.result_cache.clear()
        logger.info("检索缓存已清除")


# 工厂函数
def create_hybrid_retrieval_system(config: Optional[Dict[str, Any]] = None) -> HybridRetrievalSystem:
    """创建混合检索系统实例"""
    return HybridRetrievalSystem(config)


# 便捷查询函数
async def hybrid_search(
    query: str,
    query_type: str = "semantic",
    max_results: int = 20,
    **kwargs
) -> Dict[str, Any]:
    """便捷的混合检索函数"""
    retrieval_system = create_hybrid_retrieval_system()
    
    hybrid_query = HybridQuery(
        query=query,
        query_type=query_type,
        max_results=max_results,
        **kwargs
    )
    
    return await retrieval_system.retrieve(hybrid_query)