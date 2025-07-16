"""
简单的向量存储实现
临时解决方案，允许服务启动并运行
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class SimpleVectorStore:
    """简单的内存向量存储实现"""
    
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.metadata = []
        logger.info("初始化简单内存向量存储")
    
    async def add_documents(
        self,
        documents: List[Document],
        embeddings: List[List[float]],
        batch_size: int = 100
    ) -> List[str]:
        """添加文档到向量存储"""
        try:
            logger.info(f"添加 {len(documents)} 个文档到内存存储")
            
            # 生成ID
            start_id = len(self.documents)
            ids = [str(start_id + i) for i in range(len(documents))]
            
            # 存储文档和向量
            for doc, emb, doc_id in zip(documents, embeddings, ids):
                self.documents.append(doc)
                self.embeddings.append(emb)
                self.metadata.append({
                    "id": doc_id,
                    **doc.metadata
                })
            
            logger.info(f"成功添加文档，当前总数: {len(self.documents)}")
            return ids
            
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """相似度搜索"""
        try:
            if not self.embeddings:
                logger.warning("向量存储为空")
                return []
            
            # 计算余弦相似度
            query_np = np.array(query_embedding)
            scores = []
            
            for i, emb in enumerate(self.embeddings):
                # 应用过滤条件
                if filter_conditions:
                    match = True
                    for key, value in filter_conditions.items():
                        if self.metadata[i].get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                # 计算余弦相似度
                emb_np = np.array(emb)
                similarity = np.dot(query_np, emb_np) / (np.linalg.norm(query_np) * np.linalg.norm(emb_np))
                scores.append((i, similarity))
            
            # 排序并返回前k个
            scores.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for idx, score in scores[:k]:
                results.append((self.documents[idx], score))
            
            logger.debug(f"搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档（简单实现）"""
        logger.warning("内存存储不支持删除操作")
        return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        return {
            "name": "memory_store",
            "vectors_count": len(self.embeddings),
            "points_count": len(self.documents),
            "status": "active"
        }


# 全局实例
_simple_store = None


def get_simple_vector_store() -> SimpleVectorStore:
    """获取简单向量存储实例"""
    global _simple_store
    if _simple_store is None:
        _simple_store = SimpleVectorStore()
    return _simple_store