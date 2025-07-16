"""
简化的检索器 - 专注于性能优化
去除复杂的多阶段检索，只保留最核心的向量检索
"""
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_openai import OpenAIEmbeddings
from src.database.qdrant import get_qdrant_manager
from src.config.settings import get_settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class SimpleRetrievalResult:
    """简化的检索结果"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class SimpleRetriever:
    """
    简化的检索器 - 性能优化版本
    
    优化策略：
    1. 只使用向量检索，跳过图谱和记忆库
    2. 减少检索数量
    3. 简化后处理逻辑
    4. 使用更小的嵌入模型
    """
    
    def __init__(self, user_id: str = "u1"):
        self.user_id = user_id
        self.qdrant = get_qdrant_manager()
        
        # 使用与系统一致的嵌入模型，确保向量维度匹配
        self.embeddings = OpenAIEmbeddings(
            model=settings.ai_model.embedding_model,  # text-embedding-3-large
            api_key=settings.ai_model.openai_api_key
        )
        
    async def retrieve(
        self,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,  # 默认只返回5个结果
        score_threshold: float = 0.5  # 提高阈值，只返回高质量结果
    ) -> List[SimpleRetrievalResult]:
        """
        执行简化的向量检索
        
        Args:
            query: 查询文本
            project_id: 项目ID
            top_k: 返回结果数量
            score_threshold: 分数阈值
            
        Returns:
            检索结果列表
        """
        start_time = time.time()
        
        try:
            # 生成查询向量
            query_embedding = await self.embeddings.aembed_query(query)
            
            # 确定集合名称
            collection_name = f"project_{project_id}" if project_id else "project_default"
            
            # 构建过滤条件
            filters = {"user_id": self.user_id}
            if project_id:
                filters["project_id"] = project_id
            
            # 执行向量搜索
            results = await self.qdrant.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=filters
            )
            
            # 转换结果
            retrieval_results = []
            for hit in results:
                retrieval_results.append(SimpleRetrievalResult(
                    doc_id=hit.id,
                    content=hit.payload.get("content", ""),
                    score=hit.score,
                    metadata=hit.payload
                ))
            
            retrieval_time = time.time() - start_time
            logger.info(f"简化检索完成: {len(retrieval_results)}个结果, 耗时{retrieval_time:.3f}秒")
            
            return retrieval_results
            
        except Exception as e:
            logger.error(f"简化检索错误: {e}")
            return []
    
    async def batch_retrieve(
        self,
        queries: List[str],
        project_id: Optional[str] = None,
        top_k: int = 3  # 批量时进一步减少结果数
    ) -> Dict[str, List[SimpleRetrievalResult]]:
        """
        批量检索多个查询
        
        优化策略：批量生成嵌入向量，减少API调用
        """
        try:
            # 批量生成查询向量
            query_embeddings = await self.embeddings.aembed_documents(queries)
            
            results = {}
            for query, embedding in zip(queries, query_embeddings):
                # 为每个查询执行检索
                collection_name = f"project_{project_id}" if project_id else "project_default"
                
                filters = {"user_id": self.user_id}
                if project_id:
                    filters["project_id"] = project_id
                
                search_results = await self.qdrant.search(
                    collection_name=collection_name,
                    query_vector=embedding,
                    limit=top_k,
                    score_threshold=0.6,  # 批量时使用更高阈值
                    query_filter=filters
                )
                
                # 转换结果
                retrieval_results = []
                for hit in search_results:
                    retrieval_results.append(SimpleRetrievalResult(
                        doc_id=hit.id,
                        content=hit.payload.get("content", ""),
                        score=hit.score,
                        metadata=hit.payload
                    ))
                
                results[query] = retrieval_results
            
            return results
            
        except Exception as e:
            logger.error(f"批量检索错误: {e}")
            return {query: [] for query in queries}


# 全局实例，避免重复初始化
_simple_retriever_instance = None


def get_simple_retriever(user_id: str = "u1") -> SimpleRetriever:
    """获取简化检索器的单例实例"""
    global _simple_retriever_instance
    if _simple_retriever_instance is None:
        _simple_retriever_instance = SimpleRetriever(user_id)
    return _simple_retriever_instance