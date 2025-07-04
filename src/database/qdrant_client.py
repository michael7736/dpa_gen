"""
Qdrant向量数据库客户端管理器
支持向量存储、检索和管理功能
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    MatchValue, SearchRequest, UpdateStatus, CollectionInfo
)
from qdrant_client.http.exceptions import UnexpectedResponse

from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 全局实例
_qdrant_manager: Optional['QdrantManager'] = None


def get_qdrant_client() -> 'QdrantManager':
    """获取Qdrant客户端管理器实例"""
    global _qdrant_manager
    if _qdrant_manager is None:
        _qdrant_manager = QdrantManager()
    return _qdrant_manager


def get_qdrant_manager() -> 'QdrantManager':
    """获取Qdrant管理器实例（别名）"""
    return get_qdrant_client()


async def init_qdrant_collection(collection_name: str, vector_size: int):
    """初始化Qdrant集合"""
    manager = get_qdrant_client()
    return await manager.create_collection(collection_name, vector_size)


class QdrantManager:
    """Qdrant向量数据库管理器"""
    
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant.url,
            api_key=settings.qdrant.api_key,
            timeout=30
        )
        
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """创建向量集合"""
        try:
            # 检查集合是否已存在
            if await self.collection_exists(collection_name):
                logger.info(f"集合 {collection_name} 已存在")
                return True
            
            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            logger.info(f"成功创建向量集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建向量集合失败: {collection_name}, 错误: {e}")
            return False
    
    async def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            collections = self.client.get_collections()
            return any(
                collection.name == collection_name 
                for collection in collections.collections
            )
        except Exception as e:
            logger.error(f"检查集合存在性失败: {e}")
            return False
    
    async def get_collection_info(self, collection_name: str) -> Optional[CollectionInfo]:
        """获取集合信息"""
        try:
            return self.client.get_collection(collection_name)
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return None
    
    async def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct]
    ) -> bool:
        """插入或更新向量点"""
        try:
            result = self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            if result.status == UpdateStatus.COMPLETED:
                logger.info(f"成功upsert {len(points)} 个点到集合 {collection_name}")
                return True
            else:
                logger.warning(f"Upsert状态: {result.status}")
                return False
                
        except Exception as e:
            logger.error(f"Upsert点失败: {e}")
            return False
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        query_filter: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """搜索相似向量"""
        try:
            # 构建过滤条件
            filter_condition = None
            if query_filter:
                conditions = []
                for key, value in query_filter.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                filter_condition = Filter(must=conditions)
            
            # 执行搜索
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=filter_condition,
                limit=limit,
                score_threshold=score_threshold
            )
            
            logger.info(f"搜索返回 {len(search_result)} 个结果")
            return search_result
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def delete_points(
        self,
        collection_name: str,
        point_ids: Optional[List[Union[str, int]]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """删除向量点"""
        try:
            if point_ids:
                # 按ID删除
                result = self.client.delete(
                    collection_name=collection_name,
                    points_selector=point_ids
                )
            elif filter_conditions:
                # 按条件删除
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                filter_condition = Filter(must=conditions)
                
                result = self.client.delete(
                    collection_name=collection_name,
                    points_selector=filter_condition
                )
            else:
                logger.error("删除点时必须提供point_ids或filter_conditions")
                return False
            
            if result.status == UpdateStatus.COMPLETED:
                logger.info(f"成功删除点从集合 {collection_name}")
                return True
            else:
                logger.warning(f"删除状态: {result.status}")
                return False
                
        except Exception as e:
            logger.error(f"删除点失败: {e}")
            return False
    
    async def update_payload(
        self,
        collection_name: str,
        point_id: Union[str, int],
        payload: Dict[str, Any]
    ) -> bool:
        """更新点的载荷数据"""
        try:
            result = self.client.set_payload(
                collection_name=collection_name,
                payload=payload,
                points=[point_id]
            )
            
            if result.status == UpdateStatus.COMPLETED:
                logger.info(f"成功更新点载荷: {point_id}")
                return True
            else:
                logger.warning(f"更新载荷状态: {result.status}")
                return False
                
        except Exception as e:
            logger.error(f"更新点载荷失败: {e}")
            return False
    
    async def get_points(
        self,
        collection_name: str,
        point_ids: List[Union[str, int]],
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Any]:
        """获取指定点的信息"""
        try:
            result = self.client.retrieve(
                collection_name=collection_name,
                ids=point_ids,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            
            logger.info(f"获取到 {len(result)} 个点的信息")
            return result
            
        except Exception as e:
            logger.error(f"获取点信息失败: {e}")
            return []
    
    async def count_points(
        self,
        collection_name: str,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计点的数量"""
        try:
            filter_condition = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                filter_condition = Filter(must=conditions)
            
            result = self.client.count(
                collection_name=collection_name,
                count_filter=filter_condition
            )
            
            return result.count
            
        except Exception as e:
            logger.error(f"统计点数量失败: {e}")
            return 0
    
    async def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            result = self.client.delete_collection(collection_name)
            logger.info(f"成功删除集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除集合失败: {collection_name}, 错误: {e}")
            return False
    
    async def scroll_points(
        self,
        collection_name: str,
        limit: int = 100,
        offset: Optional[Union[str, int]] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> tuple[List[Any], Optional[Union[str, int]]]:
        """分页获取点数据"""
        try:
            filter_condition = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                filter_condition = Filter(must=conditions)
            
            result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,
                limit=limit,
                offset=offset,
                with_payload=with_payload,
                with_vectors=with_vectors
            )
            
            points, next_offset = result
            logger.info(f"分页获取到 {len(points)} 个点")
            return points, next_offset
            
        except Exception as e:
            logger.error(f"分页获取点失败: {e}")
            return [], None
    
    async def batch_search(
        self,
        collection_name: str,
        search_requests: List[Dict[str, Any]]
    ) -> List[List[Any]]:
        """批量搜索"""
        try:
            requests = []
            for req in search_requests:
                filter_condition = None
                if req.get("filter"):
                    conditions = []
                    for key, value in req["filter"].items():
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                    filter_condition = Filter(must=conditions)
                
                search_req = SearchRequest(
                    vector=req["query_vector"],
                    filter=filter_condition,
                    limit=req.get("limit", 10),
                    score_threshold=req.get("score_threshold")
                )
                requests.append(search_req)
            
            results = self.client.search_batch(
                collection_name=collection_name,
                requests=requests
            )
            
            logger.info(f"批量搜索完成，处理了 {len(requests)} 个请求")
            return results
            
        except Exception as e:
            logger.error(f"批量搜索失败: {e}")
            return []
    
    def close(self):
        """关闭客户端连接"""
        try:
            self.client.close()
            logger.info("Qdrant客户端连接已关闭")
        except Exception as e:
            logger.error(f"关闭Qdrant客户端失败: {e}")


# 全局Qdrant管理器实例
_qdrant_manager = None

def get_qdrant_manager() -> QdrantManager:
    """获取Qdrant管理器实例（单例模式）"""
    global _qdrant_manager
    if _qdrant_manager is None:
        _qdrant_manager = QdrantManager()
    return _qdrant_manager 