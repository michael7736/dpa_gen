"""
Qdrant模拟器 - 用于本地测试
"""
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
import uuid
import json


@dataclass
class MockPoint:
    """模拟的向量点"""
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    score: float = 0.0


class MockQdrantClient:
    """模拟的Qdrant客户端"""
    
    def __init__(self, **kwargs):
        self.collections = {}
        
    def get_collections(self):
        """获取所有集合"""
        from types import SimpleNamespace
        collections = [
            SimpleNamespace(name=name) 
            for name in self.collections.keys()
        ]
        return SimpleNamespace(collections=collections)
        
    def create_collection(self, collection_name: str, vectors_config: Any):
        """创建集合"""
        if collection_name not in self.collections:
            self.collections[collection_name] = {
                "vectors_config": vectors_config,
                "points": []
            }
            
    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        return collection_name in self.collections
        
    def upsert(self, collection_name: str, points: List[Any]):
        """插入或更新点"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
            
        collection = self.collections[collection_name]
        
        # 转换并存储点
        for point in points:
            mock_point = MockPoint(
                id=str(point.id),
                vector=point.vector,
                payload=point.payload
            )
            collection["points"].append(mock_point)
            
        from types import SimpleNamespace
        return SimpleNamespace(status="COMPLETED")
        
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        query_filter: Optional[Any] = None
    ):
        """搜索向量"""
        if collection_name not in self.collections:
            return []
            
        collection = self.collections[collection_name]
        points = collection["points"]
        
        if not points:
            return []
            
        # 计算相似度
        query_vec = np.array(query_vector)
        results = []
        
        for point in points:
            # 计算余弦相似度
            point_vec = np.array(point.vector)
            similarity = np.dot(query_vec, point_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(point_vec)
            )
            
            if score_threshold is None or similarity >= score_threshold:
                point.score = similarity
                results.append(point)
                
        # 排序并返回前N个
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
        
    def retrieve(
        self,
        collection_name: str,
        ids: List[str],
        with_payload: bool = True,
        with_vectors: bool = False
    ):
        """根据ID检索点"""
        if collection_name not in self.collections:
            return []
            
        collection = self.collections[collection_name]
        points = collection["points"]
        
        results = []
        for point in points:
            if point.id in ids:
                results.append(point)
                
        return results
        
    def delete_collection(self, collection_name: str):
        """删除集合"""
        if collection_name in self.collections:
            del self.collections[collection_name]
            
    def count(self, collection_name: str, count_filter: Optional[Any] = None):
        """统计点数量"""
        if collection_name not in self.collections:
            return SimpleNamespace(count=0)
            
        collection = self.collections[collection_name]
        from types import SimpleNamespace
        return SimpleNamespace(count=len(collection["points"]))
        
    def close(self):
        """关闭连接"""
        pass


class MockQdrantManager:
    """模拟的Qdrant管理器"""
    
    def __init__(self):
        self.client = MockQdrantClient()
        print("📦 使用Qdrant模拟器（本地测试）")
        
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "COSINE"
    ) -> bool:
        """创建向量集合"""
        try:
            from types import SimpleNamespace
            vectors_config = SimpleNamespace(size=vector_size, distance=distance)
            self.client.create_collection(collection_name, vectors_config)
            return True
        except Exception as e:
            print(f"创建集合失败: {e}")
            return False
            
    async def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        return self.client.collection_exists(collection_name)
        
    async def upsert_points(
        self,
        collection_name: str,
        points: List[Any]
    ) -> bool:
        """插入或更新向量点"""
        try:
            result = self.client.upsert(collection_name, points)
            return result.status == "COMPLETED"
        except Exception as e:
            print(f"Upsert失败: {e}")
            return False
            
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """搜索相似向量"""
        try:
            return self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter
            )
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
            
    async def retrieve(self, collection_name: str, ids: List[str]):
        """根据ID检索"""
        return self.client.retrieve(collection_name, ids)
        
    async def list_collections(self) -> List[str]:
        """列出所有集合"""
        result = self.client.get_collections()
        return [c.name for c in result.collections]
        
    async def count_points(
        self,
        collection_name: str,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计点的数量"""
        result = self.client.count(collection_name, filter_conditions)
        return result.count
        
    def close(self):
        """关闭客户端连接"""
        self.client.close()