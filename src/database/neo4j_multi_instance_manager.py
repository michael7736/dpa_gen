"""
多实例Neo4j管理器 - 支持每用户独立Docker实例
单用户阶段：使用默认实例
多用户阶段：动态管理用户专属Neo4j实例
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass
import docker
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import Neo4jError

from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 默认用户和实例配置
DEFAULT_USER_ID = "u1"
DEFAULT_NEO4J_PORT = 7687
DEFAULT_NEO4J_HTTP_PORT = 7474


@dataclass
class Neo4jInstanceConfig:
    """Neo4j实例配置"""
    user_id: str
    container_name: str
    bolt_port: int
    http_port: int
    password: str
    memory_heap_size: str = "512M"
    page_cache_size: str = "256M"
    

class Neo4jMultiInstanceManager:
    """
    多实例Neo4j管理器
    单用户阶段：连接到默认配置的Neo4j实例
    多用户阶段：为每个用户创建和管理独立的Neo4j容器
    """
    
    def __init__(self):
        # Docker客户端（多用户阶段使用）
        self._docker_client = None
        
        # 驱动缓存：user_id -> driver
        self._drivers: Dict[str, AsyncDriver] = {}
        
        # 实例配置缓存
        self._instance_configs: Dict[str, Neo4jInstanceConfig] = {}
        
        # 默认实例配置（单用户阶段）
        self._default_config = Neo4jInstanceConfig(
            user_id=DEFAULT_USER_ID,
            container_name="dpa_neo4j_default",
            bolt_port=settings.neo4j.port or DEFAULT_NEO4J_PORT,
            http_port=DEFAULT_NEO4J_HTTP_PORT,
            password=settings.neo4j.password
        )
        
    def _get_docker_client(self):
        """获取Docker客户端（延迟初始化）"""
        if not self._docker_client:
            self._docker_client = docker.from_env()
        return self._docker_client
        
    def _get_instance_config(self, user_id: str) -> Neo4jInstanceConfig:
        """
        获取用户的Neo4j实例配置
        单用户阶段：返回默认配置
        多用户阶段：返回用户专属配置
        """
        if user_id == DEFAULT_USER_ID:
            return self._default_config
            
        # 多用户阶段：生成用户专属配置
        if user_id not in self._instance_configs:
            # 分配端口（简单策略：基于用户ID哈希）
            user_hash = hash(user_id) % 1000
            bolt_port = 7687 + user_hash * 2
            http_port = 7474 + user_hash * 2
            
            self._instance_configs[user_id] = Neo4jInstanceConfig(
                user_id=user_id,
                container_name=f"dpa_neo4j_{user_id}",
                bolt_port=bolt_port,
                http_port=http_port,
                password=f"{settings.neo4j.password}_{user_id}"  # 用户专属密码
            )
            
        return self._instance_configs[user_id]
        
    async def ensure_instance_running(self, user_id: str) -> Neo4jInstanceConfig:
        """
        确保用户的Neo4j实例正在运行
        单用户阶段：检查默认实例
        多用户阶段：创建或启动用户专属容器
        """
        config = self._get_instance_config(user_id)
        
        if user_id == DEFAULT_USER_ID:
            # 单用户阶段：假设默认实例已经在运行
            logger.info(f"Using default Neo4j instance for user {user_id}")
            return config
            
        # 多用户阶段：检查和创建Docker容器
        client = self._get_docker_client()
        
        try:
            container = client.containers.get(config.container_name)
            if container.status != "running":
                container.start()
                await asyncio.sleep(5)  # 等待Neo4j启动
                logger.info(f"Started Neo4j container for user {user_id}")
        except docker.errors.NotFound:
            # 创建新容器
            logger.info(f"Creating Neo4j container for user {user_id}")
            container = client.containers.run(
                "neo4j:5-community",
                name=config.container_name,
                detach=True,
                ports={
                    "7687/tcp": config.bolt_port,
                    "7474/tcp": config.http_port
                },
                environment={
                    "NEO4J_AUTH": f"neo4j/{config.password}",
                    "NEO4J_server_memory_heap_max__size": config.memory_heap_size,
                    "NEO4J_server_memory_pagecache_size": config.page_cache_size,
                },
                volumes={
                    f"dpa_neo4j_data_{user_id}": {"bind": "/data", "mode": "rw"},
                    f"dpa_neo4j_logs_{user_id}": {"bind": "/logs", "mode": "rw"}
                },
                restart_policy={"Name": "unless-stopped"}
            )
            await asyncio.sleep(10)  # 等待Neo4j完全启动
            
        return config
        
    async def get_driver(self, user_id: str = DEFAULT_USER_ID) -> AsyncDriver:
        """获取用户的Neo4j驱动"""
        if user_id in self._drivers:
            return self._drivers[user_id]
            
        # 确保实例运行
        config = await self.ensure_instance_running(user_id)
        
        # 创建驱动
        uri = f"bolt://localhost:{config.bolt_port}"
        driver = AsyncGraphDatabase.driver(
            uri,
            auth=("neo4j", config.password)
        )
        
        # 验证连接
        try:
            async with driver.session() as session:
                await session.run("RETURN 1")
            logger.info(f"Connected to Neo4j instance for user {user_id}")
        except Exception as e:
            await driver.close()
            raise Exception(f"Failed to connect to Neo4j for user {user_id}: {e}")
            
        self._drivers[user_id] = driver
        return driver
        
    @asynccontextmanager
    async def session(self, user_id: str = DEFAULT_USER_ID):
        """获取用户的Neo4j会话"""
        driver = await self.get_driver(user_id)
        async with driver.session() as session:
            yield session
            
    async def stop_instance(self, user_id: str):
        """
        停止用户的Neo4j实例
        单用户阶段：不停止默认实例
        多用户阶段：停止用户容器
        """
        if user_id == DEFAULT_USER_ID:
            logger.info("Default instance will not be stopped")
            return
            
        # 关闭驱动
        if user_id in self._drivers:
            await self._drivers[user_id].close()
            del self._drivers[user_id]
            
        # 停止容器
        try:
            client = self._get_docker_client()
            container = client.containers.get(f"dpa_neo4j_{user_id}")
            container.stop()
            logger.info(f"Stopped Neo4j container for user {user_id}")
        except docker.errors.NotFound:
            pass
            
    async def remove_instance(self, user_id: str, remove_volumes: bool = False):
        """
        删除用户的Neo4j实例
        单用户阶段：不删除默认实例
        多用户阶段：删除用户容器和数据
        """
        if user_id == DEFAULT_USER_ID:
            logger.warning("Cannot remove default instance")
            return
            
        # 先停止
        await self.stop_instance(user_id)
        
        # 删除容器
        try:
            client = self._get_docker_client()
            container = client.containers.get(f"dpa_neo4j_{user_id}")
            container.remove()
            logger.info(f"Removed Neo4j container for user {user_id}")
            
            # 删除数据卷
            if remove_volumes:
                for volume_name in [f"dpa_neo4j_data_{user_id}", f"dpa_neo4j_logs_{user_id}"]:
                    try:
                        volume = client.volumes.get(volume_name)
                        volume.remove()
                        logger.info(f"Removed volume {volume_name}")
                    except docker.errors.NotFound:
                        pass
        except docker.errors.NotFound:
            pass
            
    async def list_user_instances(self) -> List[Dict[str, Any]]:
        """列出所有用户实例"""
        instances = []
        
        # 默认实例
        instances.append({
            "user_id": DEFAULT_USER_ID,
            "container_name": self._default_config.container_name,
            "bolt_port": self._default_config.bolt_port,
            "status": "assumed_running",
            "is_default": True
        })
        
        # Docker容器
        try:
            client = self._get_docker_client()
            containers = client.containers.list(all=True, filters={"name": "dpa_neo4j_"})
            
            for container in containers:
                if container.name != self._default_config.container_name:
                    user_id = container.name.replace("dpa_neo4j_", "")
                    instances.append({
                        "user_id": user_id,
                        "container_name": container.name,
                        "status": container.status,
                        "is_default": False
                    })
        except Exception as e:
            logger.error(f"Failed to list Docker containers: {e}")
            
        return instances
        
    async def cleanup_idle_instances(self, idle_hours: int = 24):
        """清理闲置的实例（仅限多用户实例）"""
        # TODO: 实现基于最后访问时间的清理逻辑
        pass
        
    async def close_all(self):
        """关闭所有驱动连接"""
        for driver in self._drivers.values():
            await driver.close()
        self._drivers.clear()
        logger.info("Closed all Neo4j drivers")


# 全局实例管理器
neo4j_multi_manager = Neo4jMultiInstanceManager()


# 兼容性包装器 - 保持与原Neo4jManager相同的接口
class Neo4jManager:
    """
    Neo4j管理器包装器 - 兼容原有接口
    自动使用当前请求的user_id
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        self.multi_manager = neo4j_multi_manager
        
    @asynccontextmanager
    async def session(self):
        """获取会话"""
        async with self.multi_manager.session(self.user_id) as session:
            yield session
            
    async def create_memory_node(
        self,
        memory_id: str,
        content: str,
        memory_type: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建记忆节点"""
        # 使用传入的user_id或实例的user_id
        effective_user_id = user_id or self.user_id
        
        async with self.multi_manager.session(effective_user_id) as session:
            query = """
            CREATE (m:Memory {
                id: $memory_id,
                content: $content,
                type: $memory_type,
                user_id: $user_id,
                project_id: $project_id,
                created_at: datetime(),
                metadata: $metadata
            })
            RETURN m
            """
            
            result = await session.run(
                query,
                memory_id=memory_id,
                content=content,
                memory_type=memory_type,
                user_id=effective_user_id,
                project_id=project_id,
                metadata=metadata or {}
            )
            
            record = await result.single()
            return dict(record["m"]) if record else None
            
    # ... 其他方法类似，都通过multi_manager代理


# 工厂函数 - 根据请求上下文创建管理器
def get_neo4j_manager(user_id: str = DEFAULT_USER_ID) -> Neo4jManager:
    """获取用户专属的Neo4j管理器"""
    return Neo4jManager(user_id=user_id)