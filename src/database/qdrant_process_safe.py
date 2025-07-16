"""
进程安全的Qdrant客户端实现
解决多进程环境下的httpx.RemoteProtocolError问题
"""

import os
import multiprocessing
import threading
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import time
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    MatchValue, SearchRequest, UpdateStatus, CollectionInfo
)
from qdrant_client.http.exceptions import UnexpectedResponse, ResponseHandlingException

from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# 线程本地存储，确保每个线程/进程有自己的客户端实例
_thread_local = threading.local()


def get_process_safe_client() -> QdrantClient:
    """
    获取进程安全的Qdrant客户端
    每个进程/线程将拥有自己的客户端实例
    """
    # 检查当前线程是否已有客户端
    if not hasattr(_thread_local, 'client') or _thread_local.client is None:
        process_id = os.getpid()
        thread_id = threading.get_ident()
        
        logger.info(f"初始化Qdrant客户端 - 进程ID: {process_id}, 线程ID: {thread_id}")
        
        # 禁用代理，避免连接问题
        os.environ['NO_PROXY'] = 'rtx4080,localhost,127.0.0.1'
        os.environ['no_proxy'] = 'rtx4080,localhost,127.0.0.1'
        os.environ['HTTPX_TRUST_ENV'] = '0'  # 禁用 httpx 的环境变量信任
        
        try:
            # 优先使用REST API（更稳定）
            # 设置环境变量来优化 httpx 连接
            os.environ['HTTPX_TIMEOUT'] = '30.0'
            
            # 使用 host 和 port 分开的方式，避免 URL 解析问题
            _thread_local.client = QdrantClient(
                host=settings.qdrant.host,
                port=settings.qdrant.port,
                timeout=30,
                prefer_grpc=False,  # 使用REST避免gRPC的多进程问题
                https=False,
                force_disable_check_same_thread=True  # 禁用线程检查
            )
            
            # 测试连接
            _thread_local.client.get_collections()
            logger.info(f"进程 {process_id} 成功连接到Qdrant (REST模式)")
            
        except Exception as e:
            logger.error(f"进程 {process_id} 连接Qdrant失败: {e}")
            # 使用模拟客户端作为后备
            from .qdrant_mock import MockQdrantClient
            _thread_local.client = MockQdrantClient()
            logger.info(f"进程 {process_id} 使用模拟客户端")
    
    return _thread_local.client


def ensure_client(func):
    """装饰器：确保函数执行前有可用的客户端"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 确保客户端已初始化
        get_process_safe_client()
        return await func(*args, **kwargs)
    return wrapper


class ProcessSafeQdrantManager:
    """进程安全的Qdrant管理器"""
    
    def __init__(self):
        """初始化管理器（不创建客户端）"""
        self.collection_cache = {}
        logger.info("初始化进程安全的Qdrant管理器")
    
    @property
    def client(self) -> QdrantClient:
        """获取当前进程的客户端实例"""
        return get_process_safe_client()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """创建向量集合"""
        try:
            # 使用缓存避免重复检查
            if collection_name in self.collection_cache:
                return True
            
            # 检查集合是否已存在
            collections = self.client.get_collections()
            exists = any(col.name == collection_name for col in collections.collections)
            
            if exists:
                logger.info(f"集合 {collection_name} 已存在")
                self.collection_cache[collection_name] = True
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
            self.collection_cache[collection_name] = True
            return True
            
        except Exception as e:
            logger.error(f"创建向量集合失败: {collection_name}, 错误: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def upsert_points_batch(
        self,
        collection_name: str,
        points: List[PointStruct],
        batch_size: int = 100
    ) -> bool:
        """批量插入向量点（进程安全）"""
        process_id = os.getpid()
        
        try:
            total_points = len(points)
            logger.info(f"进程 {process_id}: 开始上传 {total_points} 个点到 {collection_name}")
            
            # 分批处理
            for i in range(0, total_points, batch_size):
                batch = points[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_points - 1) // batch_size + 1
                
                try:
                    result = self.client.upsert(
                        collection_name=collection_name,
                        points=batch,
                        wait=True  # 等待操作完成
                    )
                    
                    if result.status == UpdateStatus.COMPLETED:
                        logger.debug(f"进程 {process_id}: 批次 {batch_num}/{total_batches} 上传成功")
                    else:
                        logger.warning(f"进程 {process_id}: 批次 {batch_num} 状态: {result.status}")
                    
                    # 避免请求过快
                    if i + batch_size < total_points:
                        time.sleep(0.1)
                        
                except ResponseHandlingException as e:
                    if "RemoteProtocolError" in str(e) or "Server disconnected" in str(e):
                        logger.error(f"进程 {process_id}: 遇到连接错误，重试批次 {batch_num}")
                        # 重新创建客户端
                        _thread_local.client = None
                        # 重试当前批次
                        raise
                    else:
                        raise
            
            logger.info(f"进程 {process_id}: 成功上传所有 {total_points} 个点")
            return True
            
        except Exception as e:
            logger.error(f"进程 {process_id}: 上传失败 - {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        query_filter: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """搜索向量（进程安全）"""
        process_id = os.getpid()
        
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
            
            logger.debug(f"进程 {process_id}: 搜索返回 {len(search_result)} 个结果")
            return search_result
            
        except ResponseHandlingException as e:
            if "RemoteProtocolError" in str(e) or "Server disconnected" in str(e):
                logger.error(f"进程 {process_id}: 搜索时遇到连接错误，重试")
                # 重新创建客户端
                _thread_local.client = None
                raise
            else:
                logger.error(f"进程 {process_id}: 搜索失败 - {e}")
                return []
        except Exception as e:
            logger.error(f"进程 {process_id}: 搜索失败 - {e}")
            return []
    
    def cleanup(self):
        """清理当前进程的客户端连接"""
        if hasattr(_thread_local, 'client') and _thread_local.client is not None:
            try:
                if hasattr(_thread_local.client, 'close'):
                    _thread_local.client.close()
                logger.info(f"进程 {os.getpid()}: 客户端连接已关闭")
            except Exception as e:
                logger.error(f"进程 {os.getpid()}: 关闭客户端失败 - {e}")
            finally:
                _thread_local.client = None


# 用于多进程池的初始化函数
def init_worker():
    """
    多进程池的worker初始化函数
    在每个工作进程启动时调用
    """
    process_id = os.getpid()
    logger.info(f"初始化工作进程 {process_id}")
    
    # 预先创建客户端，确保连接正常
    try:
        client = get_process_safe_client()
        # 测试连接
        client.get_collections()
        logger.info(f"工作进程 {process_id} 初始化成功")
    except Exception as e:
        logger.error(f"工作进程 {process_id} 初始化失败: {e}")


# 单例管理器
_process_safe_manager: Optional[ProcessSafeQdrantManager] = None


def get_process_safe_qdrant_manager() -> ProcessSafeQdrantManager:
    """获取进程安全的Qdrant管理器"""
    global _process_safe_manager
    if _process_safe_manager is None:
        _process_safe_manager = ProcessSafeQdrantManager()
    return _process_safe_manager