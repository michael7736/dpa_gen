"""
向量化服务模块
实现文档向量化、相似度计算和向量存储
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

logger = logging.getLogger(__name__)

@dataclass
class VectorConfig:
    """向量配置"""
    model_name: str = "text-embedding-ada-002"
    dimension: int = 1536
    distance_metric: str = "cosine"
    batch_size: int = 100
    
class EmbeddingService:
    """嵌入向量服务"""
    
    def __init__(
        self,
        config: VectorConfig,
        provider: str = "openai",
        api_key: Optional[str] = None
    ):
        self.config = config
        self.provider = provider
        
        # 初始化嵌入模型
        if provider == "openai":
            self.embeddings = OpenAIEmbeddings(
                model=config.model_name,
                openai_api_key=api_key
            )
        elif provider == "huggingface":
            self.embeddings = HuggingFaceEmbeddings(
                model_name=config.model_name
            )
        else:
            raise ValueError(f"不支持的嵌入提供商: {provider}")
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文档"""
        try:
            logger.info(f"开始嵌入 {len(texts)} 个文档")
            
            # 分批处理
            all_embeddings = []
            for i in range(0, len(texts), self.config.batch_size):
                batch = texts[i:i + self.config.batch_size]
                batch_embeddings = await self._embed_batch(batch)
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(f"完成批次 {i//self.config.batch_size + 1}/{(len(texts)-1)//self.config.batch_size + 1}")
            
            logger.info(f"完成 {len(texts)} 个文档的嵌入")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"文档嵌入失败: {e}")
            raise
    
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """嵌入单个批次"""
        if self.provider == "openai":
            # OpenAI API支持异步
            return await self.embeddings.aembed_documents(texts)
        else:
            # 其他提供商使用同步方法
            return self.embeddings.embed_documents(texts)
    
    async def embed_query(self, text: str) -> List[float]:
        """嵌入查询文本"""
        try:
            if self.provider == "openai":
                return await self.embeddings.aembed_query(text)
            else:
                return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"查询嵌入失败: {e}")
            raise

class VectorStore:
    """向量存储服务"""
    
    def __init__(
        self,
        config: VectorConfig,
        qdrant_url: str = "localhost:6333",
        collection_name: str = "documents"
    ):
        self.config = config
        self.collection_name = collection_name
        
        # 初始化Qdrant客户端
        self.client = QdrantClient(url=qdrant_url)
        
        # 创建集合
        self._create_collection()
    
    def _create_collection(self):
        """创建向量集合"""
        try:
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                # 创建新集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.config.dimension,
                        distance=Distance.COSINE if self.config.distance_metric == "cosine" else Distance.EUCLIDEAN
                    )
                )
                logger.info(f"创建向量集合: {self.collection_name}")
            else:
                logger.info(f"向量集合已存在: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"创建向量集合失败: {e}")
            raise
    
    async def add_documents(
        self,
        documents: List[Document],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> List[str]:
        """添加文档到向量存储"""
        try:
            logger.info(f"开始添加 {len(documents)} 个文档到向量存储")
            
            if len(documents) != len(embeddings):
                raise ValueError("文档数量与嵌入向量数量不匹配")
            
            point_ids = []
            
            # 分批添加
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                
                batch_ids = await self._add_batch(batch_docs, batch_embeddings)
                point_ids.extend(batch_ids)
                
                logger.debug(f"完成批次 {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量存储")
            return point_ids
            
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {e}")
            raise
    
    async def _add_batch(
        self,
        documents: List[Document],
        embeddings: List[List[float]]
    ) -> List[str]:
        """添加单个批次"""
        points = []
        point_ids = []
        
        for doc, embedding in zip(documents, embeddings):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            
            # 准备元数据
            payload = {
                "content": doc.page_content,
                **doc.metadata
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        # 批量插入
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return point_ids
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """相似度搜索"""
        try:
            # 构建过滤条件
            query_filter = None
            if filter_conditions:
                query_filter = self._build_filter(filter_conditions)
            
            # 执行搜索
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False
            )
            
            # 转换结果
            results = []
            for point in search_result:
                payload = point.payload
                content = payload.pop("content", "")
                
                doc = Document(
                    page_content=content,
                    metadata=payload
                )
                
                results.append((doc, point.score))
            
            logger.debug(f"相似度搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            raise
    
    def _build_filter(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """构建查询过滤条件"""
        # TODO: 实现复杂的过滤条件构建
        return {
            "must": [
                {"key": key, "match": {"value": value}}
                for key, value in conditions.items()
            ]
        }
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            # 根据document_id删除
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"any": document_ids}
                            }
                        ]
                    }
                }
            )
            
            logger.info(f"删除文档: {document_ids}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {}

class VectorSearchService:
    """向量搜索服务"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
    
    async def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = False
    ) -> List[Tuple[Document, float]]:
        """执行向量搜索"""
        try:
            logger.info(f"执行向量搜索: {query[:50]}...")
            
            # 1. 嵌入查询
            query_embedding = await self.embedding_service.embed_query(query)
            
            # 2. 向量搜索
            results = await self.vector_store.similarity_search(
                query_embedding=query_embedding,
                k=k * 2 if rerank else k,  # 如果需要重排序，先获取更多结果
                filter_conditions=filters
            )
            
            # 3. 重排序（可选）
            if rerank:
                results = await self._rerank_results(query, results, k)
            
            logger.info(f"搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Tuple[Document, float]],
        k: int
    ) -> List[Tuple[Document, float]]:
        """重排序搜索结果"""
        # TODO: 实现基于交叉编码器的重排序
        # 目前简单返回前k个结果
        return results[:k]
    
    async def hybrid_search(
        self,
        query: str,
        k: int = 10,
        alpha: float = 0.7,  # 向量搜索权重
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """混合搜索（向量+关键词）"""
        try:
            logger.info(f"执行混合搜索: {query[:50]}...")
            
            # 1. 向量搜索
            vector_results = await self.search(query, k=k*2, filters=filters)
            
            # 2. 关键词搜索（简化实现）
            keyword_results = await self._keyword_search(query, k=k*2, filters=filters)
            
            # 3. 融合结果
            fused_results = self._fuse_results(vector_results, keyword_results, alpha)
            
            logger.info(f"混合搜索完成，返回 {len(fused_results[:k])} 个结果")
            return fused_results[:k]
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            raise
    
    async def _keyword_search(
        self,
        query: str,
        k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """关键词搜索（简化实现）"""
        # TODO: 实现基于BM25的关键词搜索
        # 目前返回空结果
        return []
    
    def _fuse_results(
        self,
        vector_results: List[Tuple[Document, float]],
        keyword_results: List[Tuple[Document, float]],
        alpha: float
    ) -> List[Tuple[Document, float]]:
        """融合搜索结果"""
        # TODO: 实现RRF（Reciprocal Rank Fusion）算法
        # 目前简单返回向量搜索结果
        return vector_results

def create_vector_service(
    config: VectorConfig,
    embedding_provider: str = "openai",
    qdrant_url: str = "localhost:6333",
    collection_name: str = "documents"
) -> VectorSearchService:
    """创建向量搜索服务"""
    embedding_service = EmbeddingService(config, embedding_provider)
    vector_store = VectorStore(config, qdrant_url, collection_name)
    return VectorSearchService(embedding_service, vector_store) 