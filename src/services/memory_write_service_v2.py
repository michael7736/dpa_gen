"""
统一的内存写入服务 V2 - 一致性中间层（支持多用户隔离预埋）
负责协调向量数据库、知识图谱和Memory Bank的数据写入
实现队列机制和补偿事务，确保数据一致性

单用户阶段：使用默认user_id="u1"
多用户阶段：通过user_id实现完全隔离
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import uuid
from collections import deque
import aiofiles
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.config.settings import settings
from src.database.qdrant import get_qdrant_manager
from src.database.neo4j_manager import get_neo4j_manager
from src.database.postgres import get_async_session
from src.models.memory import Memory, MemoryType, MemoryStatus
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 默认用户ID（单用户阶段）
DEFAULT_USER_ID = "u1"


class WriteOperationType(Enum):
    """写操作类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_CREATE = "batch_create"


class WriteStatus(Enum):
    """写入状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class WriteOperation:
    """写操作定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: WriteOperationType = WriteOperationType.CREATE
    target_stores: List[str] = field(default_factory=lambda: ["postgres", "vector", "graph", "memory_bank"])
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: WriteStatus = WriteStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    attempts: int = 0
    max_attempts: int = 3
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    completed_stores: List[str] = field(default_factory=list)
    compensation_data: Dict[str, Any] = field(default_factory=dict)
    # 用户和项目标识（为多用户预埋）
    user_id: str = DEFAULT_USER_ID
    project_id: Optional[str] = None


@dataclass
class WriteResult:
    """写入结果"""
    success: bool
    operation_id: str
    completed_stores: List[str]
    failed_stores: List[str]
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class MemoryBankStore(ABC):
    """Memory Bank存储抽象基类（为并发预埋）"""
    
    @abstractmethod
    async def lock(self, key: str, timeout: int = 30) -> bool:
        """获取锁（单用户阶段返回True）"""
        pass
        
    @abstractmethod
    async def unlock(self, key: str):
        """释放锁（单用户阶段空实现）"""
        pass
        
    @abstractmethod
    async def read(self, path: Path) -> str:
        """读取文件"""
        pass
        
    @abstractmethod
    async def write(self, path: Path, content: str):
        """写入文件"""
        pass
        
    @abstractmethod
    async def append(self, path: Path, content: str):
        """追加内容"""
        pass


class LocalMemoryBankStore(MemoryBankStore):
    """本地文件系统Memory Bank存储（单用户实现）"""
    
    async def lock(self, key: str, timeout: int = 30) -> bool:
        """单用户场景，始终返回True"""
        return True
        
    async def unlock(self, key: str):
        """单用户场景，空实现"""
        pass
        
    async def read(self, path: Path) -> str:
        """读取文件"""
        if not path.exists():
            return ""
        async with aiofiles.open(path, "r") as f:
            return await f.read()
            
    async def write(self, path: Path, content: str):
        """写入文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
            
    async def append(self, path: Path, content: str):
        """追加内容"""
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "a") as f:
            await f.write(content)


class MemoryWriteService:
    """
    统一的内存写入服务
    实现向量、图谱、Memory Bank的一致性写入
    支持多用户隔离预埋
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id  # 当前服务实例的用户ID
        self.qdrant_manager = get_qdrant_manager()
        self.neo4j_manager = get_neo4j_manager()
        self.memory_bank_store = LocalMemoryBankStore()
        
        # 操作队列（未来可按用户分离）
        self.write_queue: deque[WriteOperation] = deque(maxlen=1000)
        self.compensation_queue: deque[WriteOperation] = deque(maxlen=500)
        
        # Memory Bank基础路径（支持用户隔离）
        self.memory_bank_base = Path(settings.paths.memory_bank)
        self.memory_bank_base.mkdir(parents=True, exist_ok=True)
        
        # 处理器状态
        self._running = False
        self._processor_task = None
        self._compensation_task = None
        
    def _get_user_memory_bank_path(self, user_id: str, project_id: Optional[str] = None) -> Path:
        """
        获取用户的Memory Bank路径
        单用户阶段：memory_bank/project_{id}/
        多用户阶段：memory_bank/{user_id}/project_{id}/
        """
        if user_id == DEFAULT_USER_ID:
            # 单用户阶段，简化路径
            if project_id:
                return self.memory_bank_base / f"project_{project_id}"
            return self.memory_bank_base / "default"
        else:
            # 多用户阶段，包含用户ID
            base = self.memory_bank_base / user_id
            if project_id:
                return base / f"project_{project_id}"
            return base / "default"
            
    def _get_collection_name(self, user_id: str, project_id: Optional[str] = None) -> str:
        """
        获取向量集合名称
        单用户阶段：project_{id}
        多用户阶段：u_{user_id}_p_{project_id}
        """
        if user_id == DEFAULT_USER_ID:
            # 单用户阶段
            return f"project_{project_id or 'default'}"
        else:
            # 多用户阶段
            return f"u_{user_id}_p_{project_id or 'default'}"
        
    async def start(self):
        """启动写入服务"""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_write_queue())
        self._compensation_task = asyncio.create_task(self._process_compensation_queue())
        logger.info(f"MemoryWriteService started for user: {self.user_id}")
        
    async def stop(self):
        """停止写入服务"""
        self._running = False
        if self._processor_task:
            await self._processor_task
        if self._compensation_task:
            await self._compensation_task
        logger.info(f"MemoryWriteService stopped for user: {self.user_id}")
        
    async def write_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,  # 为多用户预埋
        embedding: Optional[List[float]] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None
    ) -> WriteResult:
        """
        写入记忆到所有存储系统
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            metadata: 元数据
            project_id: 项目ID
            user_id: 用户ID（默认使用实例的user_id）
            embedding: 向量嵌入（如果已有）
            entities: 实体列表
            relationships: 关系列表
            
        Returns:
            WriteResult: 写入结果
        """
        # 使用传入的user_id或默认值
        effective_user_id = user_id or self.user_id
        
        operation = WriteOperation(
            type=WriteOperationType.CREATE,
            user_id=effective_user_id,
            project_id=project_id,
            data={
                "content": content,
                "memory_type": memory_type.value,
                "metadata": metadata or {},
                "user_id": effective_user_id,
                "project_id": project_id,
                "embedding": embedding,
                "entities": entities or [],
                "relationships": relationships or []
            }
        )
        
        # 加入队列
        self.write_queue.append(operation)
        
        # 如果是关键操作，立即处理
        if memory_type in [MemoryType.SEMANTIC, MemoryType.EPISODIC]:
            return await self._execute_write_operation(operation)
        
        # 否则返回队列状态
        return WriteResult(
            success=True,
            operation_id=operation.id,
            completed_stores=[],
            failed_stores=[],
            data={"status": "queued", "queue_position": len(self.write_queue)}
        )
        
    async def _process_write_queue(self):
        """处理写入队列"""
        while self._running:
            if not self.write_queue:
                await asyncio.sleep(0.1)
                continue
                
            operation = self.write_queue.popleft()
            
            try:
                await self._execute_write_operation(operation)
            except Exception as e:
                logger.error(f"Failed to process write operation {operation.id}: {e}")
                # 加入补偿队列
                if operation.attempts < operation.max_attempts:
                    operation.attempts += 1
                    self.compensation_queue.append(operation)
                    
    async def _execute_write_operation(self, operation: WriteOperation) -> WriteResult:
        """执行写操作"""
        operation.status = WriteStatus.IN_PROGRESS
        await self._log_operation(operation)
        
        completed_stores = []
        failed_stores = []
        errors = []
        
        try:
            # 1. 写入PostgreSQL（主存储）
            if "postgres" in operation.target_stores:
                try:
                    await self._write_to_postgres(operation)
                    completed_stores.append("postgres")
                except Exception as e:
                    failed_stores.append("postgres")
                    errors.append(f"PostgreSQL: {str(e)}")
                    
            # 2. 写入向量数据库
            if "vector" in operation.target_stores:
                try:
                    await self._write_to_vector_store(operation)
                    completed_stores.append("vector")
                except Exception as e:
                    failed_stores.append("vector")
                    errors.append(f"Vector: {str(e)}")
                    
            # 3. 写入知识图谱
            if "graph" in operation.target_stores:
                try:
                    await self._write_to_graph(operation)
                    completed_stores.append("graph")
                except Exception as e:
                    failed_stores.append("graph")
                    errors.append(f"Graph: {str(e)}")
                    
            # 4. 写入Memory Bank
            if "memory_bank" in operation.target_stores:
                try:
                    await self._write_to_memory_bank(operation)
                    completed_stores.append("memory_bank")
                except Exception as e:
                    failed_stores.append("memory_bank")
                    errors.append(f"MemoryBank: {str(e)}")
                    
            # 更新操作状态
            operation.completed_stores = completed_stores
            operation.status = WriteStatus.COMPLETED if not failed_stores else WriteStatus.FAILED
            
            # 记录操作结果
            await self._log_operation(operation)
            
            # 如果有失败，触发补偿
            if failed_stores:
                await self._compensate_operation(operation)
                
            return WriteResult(
                success=len(failed_stores) == 0,
                operation_id=operation.id,
                completed_stores=completed_stores,
                failed_stores=failed_stores,
                error="; ".join(errors) if errors else None
            )
            
        except Exception as e:
            logger.error(f"Critical error in write operation {operation.id}: {e}")
            operation.status = WriteStatus.FAILED
            await self._log_operation(operation)
            
            return WriteResult(
                success=False,
                operation_id=operation.id,
                completed_stores=completed_stores,
                failed_stores=operation.target_stores,
                error=str(e)
            )
            
    async def _write_to_postgres(self, operation: WriteOperation):
        """写入PostgreSQL（支持user_id）"""
        async for session in get_async_session():
            if operation.type == WriteOperationType.CREATE:
                memory = Memory(
                    content=operation.data["content"],
                    memory_type=operation.data["memory_type"],
                    meta_data=operation.data["metadata"],  # 修正字段名
                    user_id=operation.data["user_id"],  # 包含user_id
                    project_id=operation.data.get("project_id"),
                    status=MemoryStatus.ACTIVE
                )
                session.add(memory)
                await session.commit()
                operation.data["memory_id"] = str(memory.id)
                
    async def _write_to_vector_store(self, operation: WriteOperation):
        """写入向量数据库（支持用户隔离）"""
        if operation.type == WriteOperationType.CREATE:
            # 获取或生成嵌入
            embedding = operation.data.get("embedding")
            if not embedding:
                # 这里应该调用嵌入服务
                # embedding = await self.embedding_service.embed(operation.data["content"])
                pass
                
            if embedding:
                # 使用支持用户隔离的集合名
                collection_name = self._get_collection_name(
                    operation.data["user_id"],
                    operation.data.get("project_id")
                )
                
                # 确保集合存在
                if not await self.qdrant_manager.collection_exists(collection_name):
                    await self.qdrant_manager.create_collection(
                        collection_name=collection_name,
                        vector_size=len(embedding)
                    )
                
                from qdrant_client.models import PointStruct
                import uuid
                
                points = [PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "content": operation.data["content"],
                        "memory_type": operation.data["memory_type"],
                        "metadata": operation.data["metadata"],
                        "memory_id": operation.data.get("memory_id"),
                        "user_id": operation.data["user_id"],  # payload中包含user_id
                        "project_id": operation.data.get("project_id")
                    }
                )]
                
                await self.qdrant_manager.upsert_points(
                    collection_name=collection_name,
                    points=points
                )
                
    async def _write_to_graph(self, operation: WriteOperation):
        """写入知识图谱（支持用户隔离）"""
        if operation.type == WriteOperationType.CREATE:
            # 创建记忆节点（包含user_id）
            # 将metadata转换为JSON字符串，避免Neo4j Map类型问题
            import json
            metadata = operation.data.get("metadata", {})
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata)
                
            await self.neo4j_manager.create_memory_node(
                memory_id=operation.data.get("memory_id"),
                content=operation.data["content"],
                memory_type=operation.data["memory_type"],
                user_id=operation.data["user_id"],
                project_id=operation.data.get("project_id"),
                metadata=metadata
            )
            
            # 创建实体和关系
            for entity in operation.data.get("entities", []):
                entity["user_id"] = operation.data["user_id"]
                await self.neo4j_manager.create_entity_node(entity)
                
            for relationship in operation.data.get("relationships", []):
                relationship["user_id"] = operation.data["user_id"]
                await self.neo4j_manager.create_relationship(relationship)
                
    async def _write_to_memory_bank(self, operation: WriteOperation):
        """写入Memory Bank文件系统（支持用户隔离）"""
        user_id = operation.data["user_id"]
        project_id = operation.data.get("project_id")
        
        # 获取用户的Memory Bank路径
        project_path = self._get_user_memory_bank_path(user_id, project_id)
        project_path.mkdir(parents=True, exist_ok=True)
        
        if operation.type == WriteOperationType.CREATE:
            # 获取文件锁（单用户阶段返回True）
            lock_key = f"{user_id}:{project_id}:context"
            if await self.memory_bank_store.lock(lock_key):
                try:
                    # 更新当前上下文
                    context_file = project_path / "context.md"
                    await self.memory_bank_store.append(
                        context_file,
                        f"\n\n## {datetime.now().isoformat()}\n{operation.data['content']}\n"
                    )
                    
                    # 更新概念列表
                    concepts_file = project_path / "concepts.json"
                    concepts_content = await self.memory_bank_store.read(concepts_file)
                    concepts = json.loads(concepts_content) if concepts_content else []
                    
                    # 添加新概念（从实体中提取）
                    for entity in operation.data.get("entities", []):
                        if entity not in concepts:
                            concepts.append(entity)
                            
                    await self.memory_bank_store.write(
                        concepts_file,
                        json.dumps(concepts, ensure_ascii=False, indent=2)
                    )
                finally:
                    await self.memory_bank_store.unlock(lock_key)
                    
    async def _log_operation(self, operation: WriteOperation):
        """记录操作日志（按用户分离）"""
        # 日志路径包含用户ID
        user_log_path = self.memory_bank_base / "operation_logs" / operation.user_id
        user_log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = user_log_path / f"{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        log_entry = {
            "id": operation.id,
            "type": operation.type.value,
            "status": operation.status.value,
            "timestamp": datetime.now().isoformat(),
            "user_id": operation.user_id,
            "project_id": operation.project_id,
            "target_stores": operation.target_stores,
            "completed_stores": operation.completed_stores,
            "attempts": operation.attempts,
            "error_log": operation.error_log
        }
        
        await self.memory_bank_store.append(log_file, json.dumps(log_entry) + "\n")
        
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索记忆（支持用户隔离）"""
        effective_user_id = user_id or self.user_id
        
        # 构建过滤条件
        filters = {
            "user_id": effective_user_id
        }
        if project_id:
            filters["project_id"] = project_id
        if memory_types:
            filters["memory_type"] = {"$in": [t.value for t in memory_types]}
            
        # 从向量数据库搜索
        collection_name = self._get_collection_name(effective_user_id, project_id)
        results = await self.qdrant_manager.search(
            collection_name=collection_name,
            query_text=query,
            filters=filters,
            limit=limit
        )
        
        return results
        
    async def _compensate_operation(self, operation: WriteOperation):
        """补偿操作 - 回滚或重试"""
        operation.status = WriteStatus.COMPENSATING
        await self._log_operation(operation)
        
        try:
            if operation.type == WriteOperationType.CREATE:
                # 删除已创建的数据
                for store in operation.completed_stores:
                    if store == "vector":
                        await self._delete_from_vector_store(operation)
                    elif store == "graph":
                        await self._delete_from_graph(operation)
                    elif store == "memory_bank":
                        await self._delete_from_memory_bank(operation)
                        
            elif operation.type == WriteOperationType.UPDATE:
                # 恢复原始数据
                if operation.compensation_data:
                    for store in operation.completed_stores:
                        if store == "vector":
                            await self._restore_vector_data(operation)
                        elif store == "graph":
                            await self._restore_graph_data(operation)
                        elif store == "memory_bank":
                            await self._restore_memory_bank_data(operation)
                            
            operation.status = WriteStatus.COMPENSATED
            await self._log_operation(operation)
            
        except Exception as e:
            logger.error(f"Compensation failed for operation {operation.id}: {e}")
            operation.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "phase": "compensation"
            })
            
    async def _process_compensation_queue(self):
        """处理补偿队列"""
        while self._running:
            if not self.compensation_queue:
                await asyncio.sleep(1)
                continue
                
            operation = self.compensation_queue.popleft()
            
            try:
                await self._compensate_operation(operation)
            except Exception as e:
                logger.error(f"Failed to compensate operation {operation.id}: {e}")
                
    # 补偿相关方法的占位实现
    async def _delete_from_vector_store(self, operation: WriteOperation):
        """从向量存储删除"""
        pass
        
    async def _delete_from_graph(self, operation: WriteOperation):
        """从图谱删除"""
        pass
        
    async def _delete_from_memory_bank(self, operation: WriteOperation):
        """从Memory Bank删除"""
        pass
        
    async def _restore_vector_data(self, operation: WriteOperation):
        """恢复向量数据"""
        pass
        
    async def _restore_graph_data(self, operation: WriteOperation):
        """恢复图谱数据"""
        pass
        
    async def _restore_memory_bank_data(self, operation: WriteOperation):
        """恢复Memory Bank数据"""
        pass


# 单例实例（单用户阶段）
memory_write_service = MemoryWriteService(user_id=DEFAULT_USER_ID)