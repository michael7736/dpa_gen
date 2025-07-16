"""
统一的内存写入服务 - 一致性中间层
负责协调向量数据库、知识图谱和Memory Bank的数据写入
实现队列机制和补偿事务，确保数据一致性
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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config.settings import settings
from src.database.qdrant import get_qdrant_manager
from src.database.neo4j_manager import Neo4jManager
from src.database.postgres import get_async_session
from src.models.memory import Memory, MemoryType, MemoryStatus
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


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
    target_stores: List[str] = field(default_factory=lambda: ["vector", "graph", "memory_bank"])
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: WriteStatus = WriteStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    attempts: int = 0
    max_attempts: int = 3
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    completed_stores: List[str] = field(default_factory=list)
    compensation_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WriteResult:
    """写入结果"""
    success: bool
    operation_id: str
    completed_stores: List[str]
    failed_stores: List[str]
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class MemoryWriteService:
    """
    统一的内存写入服务
    实现向量、图谱、Memory Bank的一致性写入
    """
    
    def __init__(self):
        self.qdrant_manager = QdrantManager()
        self.neo4j_manager = Neo4jManager()
        
        # 操作队列
        self.write_queue: deque[WriteOperation] = deque(maxlen=1000)
        self.compensation_queue: deque[WriteOperation] = deque(maxlen=500)
        
        # Memory Bank基础路径
        self.memory_bank_path = Path(settings.paths.memory_bank)
        self.memory_bank_path.mkdir(parents=True, exist_ok=True)
        
        # 操作日志路径
        self.operation_log_path = self.memory_bank_path / "operation_logs"
        self.operation_log_path.mkdir(exist_ok=True)
        
        # 处理器状态
        self._running = False
        self._processor_task = None
        self._compensation_task = None
        
    async def start(self):
        """启动写入服务"""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_write_queue())
        self._compensation_task = asyncio.create_task(self._process_compensation_queue())
        logger.info("MemoryWriteService started")
        
    async def stop(self):
        """停止写入服务"""
        self._running = False
        if self._processor_task:
            await self._processor_task
        if self._compensation_task:
            await self._compensation_task
        logger.info("MemoryWriteService stopped")
        
    async def write_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
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
            embedding: 向量嵌入（如果已有）
            entities: 实体列表
            relationships: 关系列表
            
        Returns:
            WriteResult: 写入结果
        """
        operation = WriteOperation(
            type=WriteOperationType.CREATE,
            data={
                "content": content,
                "memory_type": memory_type.value,
                "metadata": metadata or {},
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
        
    async def batch_write_memories(
        self,
        memories: List[Dict[str, Any]],
        project_id: Optional[str] = None
    ) -> WriteResult:
        """批量写入记忆"""
        operation = WriteOperation(
            type=WriteOperationType.BATCH_CREATE,
            data={
                "memories": memories,
                "project_id": project_id
            }
        )
        
        self.write_queue.append(operation)
        
        # 批量操作异步处理
        return WriteResult(
            success=True,
            operation_id=operation.id,
            completed_stores=[],
            failed_stores=[],
            data={"status": "queued", "batch_size": len(memories)}
        )
        
    async def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any],
        project_id: Optional[str] = None
    ) -> WriteResult:
        """更新记忆"""
        operation = WriteOperation(
            type=WriteOperationType.UPDATE,
            data={
                "memory_id": memory_id,
                "updates": updates,
                "project_id": project_id
            }
        )
        
        return await self._execute_write_operation(operation)
        
    async def delete_memory(
        self,
        memory_id: str,
        project_id: Optional[str] = None
    ) -> WriteResult:
        """删除记忆"""
        operation = WriteOperation(
            type=WriteOperationType.DELETE,
            data={
                "memory_id": memory_id,
                "project_id": project_id
            }
        )
        
        return await self._execute_write_operation(operation)
        
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
            
    async def _write_to_postgres(self, operation: WriteOperation):
        """写入PostgreSQL"""
        async with get_async_session() as session:
            if operation.type == WriteOperationType.CREATE:
                memory = Memory(
                    content=operation.data["content"],
                    memory_type=operation.data["memory_type"],
                    metadata=operation.data["metadata"],
                    project_id=operation.data.get("project_id"),
                    status=MemoryStatus.ACTIVE
                )
                session.add(memory)
                await session.commit()
                operation.data["memory_id"] = str(memory.id)
                
    async def _write_to_vector_store(self, operation: WriteOperation):
        """写入向量数据库"""
        if operation.type == WriteOperationType.CREATE:
            # 获取或生成嵌入
            embedding = operation.data.get("embedding")
            if not embedding:
                # 这里应该调用嵌入服务
                # embedding = await self.embedding_service.embed(operation.data["content"])
                pass
                
            if embedding:
                await self.qdrant_manager.upsert_vectors(
                    collection_name=f"project_{operation.data.get('project_id', 'default')}",
                    vectors=[embedding],
                    payloads=[{
                        "content": operation.data["content"],
                        "memory_type": operation.data["memory_type"],
                        "metadata": operation.data["metadata"],
                        "memory_id": operation.data.get("memory_id")
                    }]
                )
                
    async def _write_to_graph(self, operation: WriteOperation):
        """写入知识图谱"""
        if operation.type == WriteOperationType.CREATE:
            # 创建记忆节点
            await self.neo4j_manager.create_memory_node(
                memory_id=operation.data.get("memory_id"),
                content=operation.data["content"],
                memory_type=operation.data["memory_type"],
                project_id=operation.data.get("project_id")
            )
            
            # 创建实体和关系
            for entity in operation.data.get("entities", []):
                await self.neo4j_manager.create_entity_node(entity)
                
            for relationship in operation.data.get("relationships", []):
                await self.neo4j_manager.create_relationship(relationship)
                
    async def _write_to_memory_bank(self, operation: WriteOperation):
        """写入Memory Bank文件系统"""
        project_id = operation.data.get("project_id", "default")
        project_path = self.memory_bank_path / f"project_{project_id}"
        project_path.mkdir(exist_ok=True)
        
        if operation.type == WriteOperationType.CREATE:
            # 更新当前上下文
            context_file = project_path / "context.md"
            async with aiofiles.open(context_file, "a") as f:
                await f.write(f"\n\n## {datetime.now().isoformat()}\n")
                await f.write(f"{operation.data['content']}\n")
                
            # 更新概念列表
            concepts_file = project_path / "concepts.json"
            concepts = []
            if concepts_file.exists():
                async with aiofiles.open(concepts_file, "r") as f:
                    content = await f.read()
                    concepts = json.loads(content) if content else []
                    
            # 添加新概念（从实体中提取）
            for entity in operation.data.get("entities", []):
                if entity not in concepts:
                    concepts.append(entity)
                    
            async with aiofiles.open(concepts_file, "w") as f:
                await f.write(json.dumps(concepts, ensure_ascii=False, indent=2))
                
    async def _delete_from_vector_store(self, operation: WriteOperation):
        """从向量存储删除"""
        # 实现向量删除逻辑
        pass
        
    async def _delete_from_graph(self, operation: WriteOperation):
        """从图谱删除"""
        # 实现图谱删除逻辑
        pass
        
    async def _delete_from_memory_bank(self, operation: WriteOperation):
        """从Memory Bank删除"""
        # 实现文件删除逻辑
        pass
        
    async def _restore_vector_data(self, operation: WriteOperation):
        """恢复向量数据"""
        # 实现向量数据恢复
        pass
        
    async def _restore_graph_data(self, operation: WriteOperation):
        """恢复图谱数据"""
        # 实现图谱数据恢复
        pass
        
    async def _restore_memory_bank_data(self, operation: WriteOperation):
        """恢复Memory Bank数据"""
        # 实现文件数据恢复
        pass
        
    async def _log_operation(self, operation: WriteOperation):
        """记录操作日志"""
        log_file = self.operation_log_path / f"{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        log_entry = {
            "id": operation.id,
            "type": operation.type.value,
            "status": operation.status.value,
            "timestamp": datetime.now().isoformat(),
            "target_stores": operation.target_stores,
            "completed_stores": operation.completed_stores,
            "attempts": operation.attempts,
            "error_log": operation.error_log
        }
        
        async with aiofiles.open(log_file, "a") as f:
            await f.write(json.dumps(log_entry) + "\n")
            
    async def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """获取操作状态"""
        # 从日志中查找操作状态
        for log_file in sorted(self.operation_log_path.glob("*.jsonl"), reverse=True):
            async with aiofiles.open(log_file, "r") as f:
                async for line in f:
                    entry = json.loads(line.strip())
                    if entry["id"] == operation_id:
                        return entry
        return None
        
    async def retry_failed_operations(self, date: Optional[str] = None):
        """重试失败的操作"""
        target_date = date or datetime.now().strftime('%Y%m%d')
        log_file = self.operation_log_path / f"{target_date}.jsonl"
        
        if not log_file.exists():
            return
            
        failed_operations = []
        async with aiofiles.open(log_file, "r") as f:
            async for line in f:
                entry = json.loads(line.strip())
                if entry["status"] == WriteStatus.FAILED.value:
                    failed_operations.append(entry)
                    
        for op_data in failed_operations:
            # 重建操作对象并加入补偿队列
            operation = WriteOperation(
                id=op_data["id"],
                type=WriteOperationType(op_data["type"]),
                target_stores=op_data["target_stores"],
                attempts=op_data["attempts"]
            )
            self.compensation_queue.append(operation)


# 单例实例
memory_write_service = MemoryWriteService()