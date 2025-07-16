# DPA多用户隔离设计文档

## 概述

本文档描述了DPA系统从单用户到多用户的演进设计，确保在MVP阶段简单实现的同时，为未来的多用户完全隔离预埋必要的钩子。

## 设计原则

1. **MVP优先**：单用户阶段使用最简实现
2. **预埋钩子**：所有接口保留用户标识参数
3. **平滑升级**：从逻辑隔离到物理隔离的无缝过渡
4. **数据安全**：确保用户数据完全隔离

## 架构对比

| 组件 | 单用户阶段（MVP） | 多用户阶段 | 预埋钩子 |
|------|------------------|------------|----------|
| **命名空间** | `project_id` 或 `default` | `{user_id}/{project_id}` | 所有API保留`user_id`参数 |
| **Memory Bank** | `~/memory_bank/project_x/` | `~/memory_bank/{user_id}/project_x/` | `MemoryBankStore`抽象类 |
| **PostgreSQL** | 单库单表 | 逻辑隔离（user_id列） | 所有表包含`user_id`列和索引 |
| **Neo4j** | 单实例 | 每用户独立Docker实例 | `Neo4jMultiInstanceManager` |
| **Qdrant** | 集合名：`project_x` | 集合名：`u_{user_id}_p_x` | Payload包含`user_id` |
| **Redis** | 键：`cache:query:xxx` | 键：`cache:{user_id}:query:xxx` | 键前缀包含用户ID |

## 核心组件实现

### 1. 一致性中间层（MemoryWriteService）

```python
# 统一的写入服务，确保数据一致性
class MemoryWriteService:
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        
    async def write_memory(
        self,
        content: str,
        memory_type: MemoryType,
        user_id: Optional[str] = None,  # 预埋参数
        project_id: Optional[str] = None,
        # ...
    ) -> WriteResult:
        # 使用队列和补偿事务确保一致性
        pass
```

**特性：**
- 写操作队列化，支持补偿事务
- 所有存储系统的双写保证
- 操作日志按用户分离存储

### 2. Neo4j多实例管理

```python
# 支持每用户独立Neo4j实例
class Neo4jMultiInstanceManager:
    async def get_driver(self, user_id: str = DEFAULT_USER_ID) -> AsyncDriver:
        if user_id == DEFAULT_USER_ID:
            # 单用户：使用默认实例
            return default_driver
        else:
            # 多用户：创建/获取用户专属实例
            return await self.ensure_instance_running(user_id)
```

**Docker管理：**
- 自动创建用户专属容器
- 端口分配：基于user_id哈希
- 数据卷隔离：`neo4j_data_{user_id}`

### 3. Memory Bank存储抽象

```python
class MemoryBankStore(ABC):
    @abstractmethod
    async def lock(self, key: str) -> bool:
        """单用户阶段返回True，多用户阶段实现分布式锁"""
        pass
        
    @abstractmethod
    async def read(self, path: Path) -> str:
        pass
```

**路径规则：**
- 单用户：`memory_bank/project_x/`
- 多用户：`memory_bank/{user_id}/project_x/`

### 4. API身份认证中间件

```python
class UserAuthMiddleware:
    async def dispatch(self, request: Request, call_next):
        # 单用户：接受固定值
        user_id = request.headers.get("X-USER-ID", "u1")
        if user_id not in {"u1", "test_user", "demo_user"}:
            raise HTTPException(401)
            
        request.state.user_id = user_id
        # 多用户阶段可扩展为JWT/OIDC验证
```

### 5. LangGraph状态管理

```python
class MVPCognitiveState(TypedDict):
    # 用户标识（预埋）
    user_id: str  # 默认 "u1"
    project_id: Optional[str]
    
    # 其他状态字段
    messages: List[BaseMessage]
    working_memory: Dict[str, Any]
```

## 数据库设计

### PostgreSQL表结构

```sql
-- 所有表都包含user_id列
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'u1',
    project_id VARCHAR(100),
    content TEXT,
    -- 其他字段
    INDEX idx_user_project (user_id, project_id)
);
```

### Neo4j节点结构

```cypher
// 所有节点包含user_id属性
CREATE (m:Memory {
    id: $id,
    user_id: $user_id,  // 必需字段
    project_id: $project_id,
    content: $content
})

// 索引支持高效查询
CREATE INDEX memory_user_idx FOR (m:Memory) ON (m.user_id)
```

### Qdrant集合命名

```python
def get_collection_name(user_id: str, project_id: str) -> str:
    if user_id == "u1":
        return f"project_{project_id}"  # 单用户
    else:
        return f"u_{user_id}_p_{project_id}"  # 多用户
```

## 升级路径

### 第一阶段：MVP（当前）
1. 所有用户使用 `user_id="u1"`
2. Neo4j使用单个默认实例
3. Memory Bank本地文件存储
4. API通过header传递固定user_id

### 第二阶段：逻辑隔离
1. 支持多个user_id值
2. 数据库查询增加user_id过滤
3. 缓存键包含user_id前缀
4. Memory Bank按用户创建子目录

### 第三阶段：物理隔离
1. Neo4j为每用户创建独立实例
2. PostgreSQL可选schema隔离
3. Qdrant独立集合
4. 分布式锁支持并发写入

## 运维工具

### Neo4j实例管理脚本

```bash
# 创建用户实例
./scripts/manage_user_neo4j.py create user123

# 列出所有实例
./scripts/manage_user_neo4j.py list

# 删除用户实例（含数据）
./scripts/manage_user_neo4j.py remove user123 --volumes
```

### 监控指标

```python
# Prometheus指标（按用户分组）
memory_operations_total{user_id="u1", operation="write"}
neo4j_instance_status{user_id="u1", status="running"}
storage_usage_bytes{user_id="u1", store="memory_bank"}
```

## 安全考虑

1. **数据隔离**：确保查询时总是包含user_id条件
2. **访问控制**：API层验证用户只能访问自己的数据
3. **资源限制**：每用户的存储和计算资源配额
4. **审计日志**：所有操作记录user_id

## 测试策略

### 单用户测试
```python
async def test_single_user_flow():
    service = MemoryWriteService(user_id="u1")
    result = await service.write_memory(
        content="test",
        memory_type=MemoryType.SEMANTIC
    )
    assert result.success
```

### 多用户隔离测试
```python
async def test_user_isolation():
    # 创建两个用户的数据
    service1 = MemoryWriteService(user_id="user1")
    service2 = MemoryWriteService(user_id="user2")
    
    # 验证数据隔离
    memories1 = await service1.search_memories("test")
    memories2 = await service2.search_memories("test")
    
    # 确保互不影响
    assert len(memories1) != len(memories2)
```

## 总结

通过这种设计，我们实现了：

1. **MVP简单性**：单用户阶段的实现非常直接
2. **未来扩展性**：所有接口都为多用户预留了参数
3. **平滑过渡**：从单用户到多用户只需配置改变
4. **数据安全**：物理隔离选项确保完全的数据隔离

关键是在所有数据流经的地方都保留了user_id，使得未来的升级可以通过配置和最小的代码改动完成。