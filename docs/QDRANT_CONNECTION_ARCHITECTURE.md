# Qdrant 连接架构

## 概述
DPA 项目使用进程安全的 Qdrant 客户端架构，确保在多进程环境中稳定运行。

## 文件结构

### 核心文件
1. **`qdrant.py`** - 主要接口文件
   - 继承自 `ProcessSafeQdrantManager`
   - 提供统一的 `QdrantManager` 类
   - 导出 `get_qdrant_manager()` 和 `get_qdrant_client()` 函数

2. **`qdrant_process_safe.py`** - 进程安全实现
   - 核心功能：为每个进程/线程创建独立的客户端实例
   - 使用线程本地存储管理连接
   - 自动禁用代理设置
   - 提供重试机制

3. **`qdrant_mock.py`** - 模拟客户端
   - 作为连接失败时的后备方案
   - 使用内存存储模拟向量数据库功能

## 使用方式

```python
from src.database.qdrant import get_qdrant_manager

# 获取管理器实例
qdrant_manager = get_qdrant_manager()

# 创建集合
await qdrant_manager.create_collection(
    collection_name="my_collection",
    vector_size=1536
)

# 搜索向量
results = await qdrant_manager.search(
    collection_name="my_collection",
    query_vector=query_embedding,
    limit=10
)
```

## 配置要求

### 环境变量 (.env)
```
QDRANT_HOST=rtx4080
QDRANT_PORT=6333
QDRANT_URL=http://rtx4080:6333
```

### 关键设置
- **禁用代理**: 自动设置 `NO_PROXY` 环境变量
- **超时时间**: 30秒
- **连接模式**: REST API (非 gRPC)

## 问题处理

### 连接失败时的行为
1. 记录错误日志
2. 自动切换到模拟客户端 (`MockQdrantClient`)
3. 系统继续运行，但使用内存存储

### 性能优化
- 批量操作支持
- 连接池管理
- 缓存集合信息