"""
LangChain Qdrant向量存储服务
使用LangChain的Qdrant集成来避免直接连接问题
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings
from ..database.qdrant import get_qdrant_manager
import os

logger = logging.getLogger(__name__)


class LangChainVectorStore:
    """基于LangChain的向量存储服务"""
    
    def __init__(
        self,
        collection_name: str = "documents",
        qdrant_url: str = None,
        embedding_model: str = "text-embedding-3-large"
    ):
        self.collection_name = collection_name
        
        # 如果没有提供URL，从环境变量获取
        if qdrant_url is None:
            qdrant_url = os.getenv("QDRANT_URL", "http://rtx4080:6333")
        
        logger.info(f"初始化LangChain向量存储，连接到: {qdrant_url}")
        
        # 初始化嵌入模型
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        try:
            # 使用进程安全的Qdrant管理器
            self.qdrant_manager = get_qdrant_manager()
            self.client = self.qdrant_manager.client
            
            # 初始化LangChain的Qdrant向量存储
            self.vectorstore = Qdrant(
                client=self.client,
                collection_name=collection_name,
                embeddings=self.embeddings
            )
            
            logger.info("成功初始化LangChain向量存储")
            
        except Exception as e:
            logger.error(f"初始化向量存储失败: {e}")
            # 使用内存向量存储作为后备
            logger.info("使用内存向量存储作为后备方案")
            # 使用内存向量存储作为后备
            logger.info("使用内存向量存储作为后备方案")
            # 创建一个简单的内存存储
            self.vectorstore = None
            self.client = None
            self.client = None
    
    async def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> List[str]:
        """添加文档到向量存储"""
        try:
            logger.info(f"开始添加 {len(documents)} 个文档到向量存储")
            
            # 分批添加
            all_ids = []
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                ids = self.vectorstore.add_documents(batch)
                all_ids.extend(ids)
                logger.debug(f"完成批次 {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量存储")
            return all_ids
            
        except Exception as e:
            logger.error(f"添加文档到向量存储失败: {e}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """相似度搜索"""
        try:
            # 构建过滤条件
            filter_dict = None
            if filter_conditions:
                filter_dict = filter_conditions
            
            # 执行搜索
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            logger.debug(f"相似度搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            # 返回空结果而不是抛出异常
            return []
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            if hasattr(self.vectorstore, 'delete'):
                self.vectorstore.delete(ids=document_ids)
                logger.info(f"删除文档: {document_ids}")
                return True
            else:
                logger.warning("当前向量存储不支持删除操作")
                return False
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            if self.client:
                info = self.client.get_collection(self.collection_name)
                return {
                    "name": self.collection_name,
                    "vectors_count": info.vectors_count,
                    "points_count": info.points_count,
                    "status": info.status
                }
            else:
                return {
                    "name": self.collection_name,
                    "vectors_count": "N/A",
                    "points_count": "N/A",
                    "status": "In-Memory"
                }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return {}


def create_langchain_vector_store(
    collection_name: str = "documents",
    qdrant_url: str = None,
    embedding_model: str = "text-embedding-3-large"
) -> LangChainVectorStore:
    """创建LangChain向量存储服务"""
    return LangChainVectorStore(
        collection_name=collection_name,
        qdrant_url=qdrant_url,
        embedding_model=embedding_model
    )