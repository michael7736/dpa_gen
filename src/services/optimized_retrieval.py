"""
优化的向量检索服务
实现查询优化、多策略检索和性能提升
"""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime
import hashlib
import json
from collections import defaultdict

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage
from ..database.qdrant import get_qdrant_manager
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, Range, MatchValue,
    SearchParams, QuantizationSearchParams
)

from ..config.settings import get_settings
from ..services.cache_service import CacheService, CacheKeys
from ..services.reranker import RerankerService
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OptimizedVectorRetrieval:
    """优化的向量检索服务"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 初始化组件
        import os
        if settings.ai_model.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.ai_model.openai_api_key
            
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Qdrant客户端
        self.qdrant_manager = get_qdrant_manager()
        self.qdrant = self.qdrant_manager.client
        
        # 缓存和重排序
        self.cache = CacheService()
        self.reranker = RerankerService()
        
        # 检索配置
        self.search_params = SearchParams(
            hnsw_ef=128,  # HNSW搜索参数
            exact=False,  # 使用近似搜索以提高速度
            quantization=QuantizationSearchParams(
                ignore=False,
                rescore=True,
                oversampling=2.0
            )
        )
    
    async def optimized_search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        search_strategy: str = "hybrid"  # hybrid, dense, sparse
    ) -> List[Dict[str, Any]]:
        """
        优化的向量搜索
        
        Args:
            collection_name: 集合名称
            query: 查询文本
            top_k: 返回结果数
            filters: 过滤条件
            search_strategy: 搜索策略
            
        Returns:
            搜索结果列表
        """
        # 生成查询指纹用于缓存
        query_hash = self._generate_query_hash(query, filters)
        cache_key = f"optimized_search:{collection_name}:{query_hash}"
        
        # 检查缓存
        cached_results = await self.cache.get(cache_key)
        if cached_results:
            self.logger.info("Using cached optimized search results")
            return cached_results
        
        try:
            # 根据策略执行搜索
            if search_strategy == "hybrid":
                results = await self._hybrid_search(collection_name, query, top_k, filters)
            elif search_strategy == "sparse":
                results = await self._sparse_search(collection_name, query, top_k, filters)
            else:
                results = await self._dense_search(collection_name, query, top_k, filters)
            
            # 缓存结果
            await self.cache.set(cache_key, results, ttl=1800)  # 30分钟
            
            return results
            
        except Exception as e:
            self.logger.error(f"Optimized search error: {e}")
            # 降级到基础搜索
            return await self._basic_search(collection_name, query, top_k, filters)
    
    async def _dense_search(
        self,
        collection_name: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """密集向量搜索"""
        # 1. 查询扩展
        expanded_queries = await self._expand_query(query)
        
        # 2. 多查询嵌入
        all_embeddings = []
        for q in expanded_queries:
            embedding = await self.embeddings.aembed_query(q)
            all_embeddings.append(embedding)
        
        # 3. 并行搜索
        search_tasks = []
        for embedding in all_embeddings:
            task = self._single_vector_search(
                collection_name, embedding, top_k * 2, filters
            )
            search_tasks.append(task)
        
        all_results = await asyncio.gather(*search_tasks)
        
        # 4. 合并和去重
        merged_results = self._merge_search_results(all_results)
        
        # 5. 重排序
        reranked = await self.reranker.rerank(
            query=query,
            chunks=merged_results,
            strategy="hybrid",
            top_k=top_k
        )
        
        return reranked
    
    async def _sparse_search(
        self,
        collection_name: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """稀疏向量搜索（基于关键词）"""
        # 提取关键词
        keywords = await self._extract_keywords(query)
        
        # 构建关键词过滤器
        keyword_filter = self._build_keyword_filter(keywords, filters)
        
        # 执行搜索
        results = await self._search_with_filter(
            collection_name,
            keyword_filter,
            limit=top_k * 3
        )
        
        # 基于关键词相关性排序
        scored_results = []
        for result in results:
            score = self._calculate_keyword_relevance(
                result["content"], 
                keywords
            )
            result["score"] = score
            scored_results.append(result)
        
        # 排序并返回
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
    
    async def _hybrid_search(
        self,
        collection_name: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """混合搜索（密集+稀疏）"""
        # 并行执行两种搜索
        dense_task = self._dense_search(collection_name, query, top_k, filters)
        sparse_task = self._sparse_search(collection_name, query, top_k, filters)
        
        dense_results, sparse_results = await asyncio.gather(
            dense_task, sparse_task
        )
        
        # 使用RRF算法融合结果
        fused_results = self._reciprocal_rank_fusion(
            [dense_results, sparse_results],
            k=60
        )
        
        return fused_results[:top_k]
    
    async def _single_vector_search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行单次向量搜索"""
        # 构建Qdrant过滤器
        qdrant_filter = self._build_qdrant_filter(filters) if filters else None
        
        # 执行搜索
        search_result = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            search_params=self.search_params,
            with_payload=True,
            with_vectors=False
        )
        
        # 转换结果格式
        results = []
        for point in search_result:
            payload = point.payload
            results.append({
                "id": point.id,
                "content": payload.get("content", ""),
                "metadata": payload,
                "score": point.score,
                "document_id": payload.get("document_id")
            })
        
        return results
    
    async def _search_with_filter(
        self,
        collection_name: str,
        filter_conditions: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """基于过滤器的搜索（无向量）"""
        # 获取随机向量进行搜索
        dummy_vector = [0.0] * 3072  # text-embedding-3-large维度
        
        return await self._single_vector_search(
            collection_name,
            dummy_vector,
            limit,
            filter_conditions
        )
    
    async def _expand_query(self, query: str) -> List[str]:
        """查询扩展"""
        prompt = f"""为以下查询生成2-3个相关的扩展查询，用于提高搜索召回率。
只返回扩展查询，每行一个。

原始查询：{query}

扩展查询："""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            expansions = [
                line.strip() 
                for line in response.content.split('\n') 
                if line.strip()
            ]
            
            # 包含原始查询
            return [query] + expansions[:2]
            
        except Exception as e:
            self.logger.error(f"Query expansion error: {e}")
            return [query]
    
    async def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        import jieba
        import jieba.analyse
        
        # 使用TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(
            query, 
            topK=5,
            withWeight=False
        )
        
        # 添加原始分词
        words = jieba.lcut(query)
        important_words = [
            w for w in words 
            if len(w) > 1 and w not in ['的', '了', '在', '是', '和', '与']
        ]
        
        # 合并并去重
        all_keywords = list(set(keywords + important_words))
        return all_keywords[:8]
    
    def _build_qdrant_filter(self, filters: Dict[str, Any]) -> Filter:
        """构建Qdrant过滤器"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # 范围过滤
                if "gte" in value or "lte" in value:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(
                                gte=value.get("gte"),
                                lte=value.get("lte")
                            )
                        )
                    )
            elif isinstance(value, list):
                # 多值匹配
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(any=value)
                    )
                )
            else:
                # 单值匹配
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
        
        return Filter(must=conditions) if conditions else None
    
    def _build_keyword_filter(
        self, 
        keywords: List[str], 
        existing_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """构建关键词过滤器"""
        filters = existing_filters or {}
        
        # 添加关键词过滤（简化版，实际应使用全文搜索）
        # 这里假设content字段支持文本搜索
        filters["$text"] = {"$search": " ".join(keywords)}
        
        return filters
    
    def _calculate_keyword_relevance(
        self, 
        content: str, 
        keywords: List[str]
    ) -> float:
        """计算关键词相关性分数"""
        import jieba
        
        content_words = set(jieba.lcut(content.lower()))
        keyword_set = set(k.lower() for k in keywords)
        
        # 计算匹配度
        matches = len(keyword_set.intersection(content_words))
        if not keywords:
            return 0.0
        
        return matches / len(keywords)
    
    def _merge_search_results(
        self, 
        results_list: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """合并多个搜索结果"""
        # 使用字典去重
        merged = {}
        
        for results in results_list:
            for result in results:
                doc_id = result.get("document_id") or result.get("id")
                if doc_id not in merged:
                    merged[doc_id] = result
                else:
                    # 保留更高分数
                    if result["score"] > merged[doc_id]["score"]:
                        merged[doc_id] = result
        
        # 转换回列表并排序
        merged_list = list(merged.values())
        merged_list.sort(key=lambda x: x["score"], reverse=True)
        
        return merged_list
    
    def _reciprocal_rank_fusion(
        self,
        results_lists: List[List[Dict[str, Any]]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """RRF算法融合多个排序列表"""
        # 计算每个文档的RRF分数
        rrf_scores = defaultdict(float)
        doc_map = {}
        
        for results in results_lists:
            for rank, result in enumerate(results):
                doc_id = result.get("document_id") or result.get("id")
                # RRF公式: 1 / (k + rank)
                rrf_scores[doc_id] += 1.0 / (k + rank + 1)
                
                # 保存文档信息
                if doc_id not in doc_map:
                    doc_map[doc_id] = result
        
        # 按RRF分数排序
        sorted_docs = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 构建最终结果
        final_results = []
        for doc_id, rrf_score in sorted_docs:
            result = doc_map[doc_id].copy()
            result["rrf_score"] = rrf_score
            final_results.append(result)
        
        return final_results
    
    def _generate_query_hash(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """生成查询哈希"""
        query_data = {
            "query": query,
            "filters": filters or {}
        }
        query_str = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(query_str.encode()).hexdigest()
    
    async def _basic_search(
        self,
        collection_name: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """基础搜索（降级方案）"""
        try:
            # 简单嵌入和搜索
            query_embedding = await self.embeddings.aembed_query(query)
            return await self._single_vector_search(
                collection_name,
                query_embedding,
                top_k,
                filters
            )
        except Exception as e:
            self.logger.error(f"Basic search error: {e}")
            return []
    
    async def batch_search(
        self,
        collection_name: str,
        queries: List[str],
        top_k: int = 10,
        max_concurrent: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """批量搜索"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_with_limit(query: str):
            async with semaphore:
                return await self.optimized_search(
                    collection_name,
                    query,
                    top_k
                )
        
        # 并发执行搜索
        results = await asyncio.gather(
            *[search_with_limit(q) for q in queries]
        )
        
        # 构建结果字典
        return {
            query: result 
            for query, result in zip(queries, results)
        }
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        stats = {
            "cache_stats": self.cache.get_stats(),
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取集合信息
        try:
            collections = self.qdrant.get_collections().collections
            stats["collections"] = [
                {
                    "name": col.name,
                    "vectors_count": col.vectors_count,
                    "points_count": col.points_count
                }
                for col in collections
            ]
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            stats["collections"] = []
        
        return stats


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 设置API密钥
        import os
        if settings.ai_model.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.ai_model.openai_api_key
            
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    async def optimize_query(self, query: str) -> Dict[str, Any]:
        """优化查询"""
        # 1. 分析查询意图
        intent = await self._analyze_intent(query)
        
        # 2. 提取实体
        entities = await self._extract_entities(query)
        
        # 3. 生成优化建议
        suggestions = {
            "intent": intent,
            "entities": entities,
            "filters": self._generate_filters(entities),
            "search_strategy": self._recommend_strategy(intent),
            "expanded_queries": await self._generate_expansions(query, intent)
        }
        
        return suggestions
    
    async def _analyze_intent(self, query: str) -> str:
        """分析查询意图"""
        prompt = f"""分析以下查询的意图类型：
查询：{query}

意图类型选择：
- factual: 寻找具体事实信息
- conceptual: 理解概念或原理
- procedural: 了解步骤或流程
- comparative: 比较不同事物
- exploratory: 探索性了解

只返回一个意图类型。"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip().lower()
        except:
            return "factual"
    
    async def _extract_entities(self, query: str) -> List[Dict[str, str]]:
        """提取实体"""
        prompt = f"""从查询中提取关键实体（人名、地点、时间、概念等）。
查询：{query}

返回JSON格式：[{{"entity": "实体名", "type": "类型"}}]"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            import json
            return json.loads(response.content)
        except:
            return []
    
    def _generate_filters(self, entities: List[Dict[str, str]]) -> Dict[str, Any]:
        """根据实体生成过滤器"""
        filters = {}
        
        for entity in entities:
            if entity["type"] == "time":
                # 时间过滤
                filters["created_at"] = {"gte": entity["entity"]}
            elif entity["type"] == "category":
                # 类别过滤
                filters["category"] = entity["entity"]
        
        return filters
    
    def _recommend_strategy(self, intent: str) -> str:
        """推荐搜索策略"""
        strategy_map = {
            "factual": "dense",
            "conceptual": "hybrid",
            "procedural": "hybrid",
            "comparative": "dense",
            "exploratory": "hybrid"
        }
        return strategy_map.get(intent, "hybrid")
    
    async def _generate_expansions(
        self, 
        query: str, 
        intent: str
    ) -> List[str]:
        """生成查询扩展"""
        if intent == "factual":
            template = "具体关于{}"
        elif intent == "conceptual":
            template = "{}的定义和原理"
        elif intent == "procedural":
            template = "如何{}"
        else:
            template = "{}"
        
        return [template.format(query)]