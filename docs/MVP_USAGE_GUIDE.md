# DPA记忆系统MVP使用指南

## 快速开始

### 1. 环境准备

```bash
# 激活conda环境
conda activate dpa_gen

# 安装依赖（如果还没有）
pip install -r requirements.txt
```

### 2. 启动数据库服务

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 或者单独启动
docker run -d --name dpa_postgres -p 5432:5432 -e POSTGRES_PASSWORD=yourpassword postgres:15
docker run -d --name dpa_neo4j -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/yourpassword neo4j:5-community
docker run -d --name dpa_qdrant -p 6333:6333 qdrant/qdrant
docker run -d --name dpa_redis -p 6379:6379 redis:7-alpine
```

### 3. 初始化数据库

```bash
# 运行初始化脚本
python scripts/init_mvp_db.py
```

### 4. 启动API服务器

```bash
# 开发模式
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 或使用启动脚本
./start-api.sh
```

## API使用示例

### 认知工作流聊天

```bash
# 单轮对话
curl -X POST http://localhost:8000/api/v1/memory/chat \
  -H "Content-Type: application/json" \
  -H "X-USER-ID: u1" \
  -d '{
    "message": "什么是深度学习？",
    "project_id": "test_project"
  }'

# 多轮对话（使用thread_id）
curl -X POST http://localhost:8000/api/v1/memory/chat \
  -H "Content-Type: application/json" \
  -H "X-USER-ID: u1" \
  -d '{
    "message": "它和机器学习有什么区别？",
    "thread_id": "previous-thread-id",
    "project_id": "test_project"
  }'
```

### 直接写入记忆

```bash
curl -X POST http://localhost:8000/api/v1/memory/write \
  -H "Content-Type: application/json" \
  -H "X-USER-ID: u1" \
  -d '{
    "content": "深度学习是机器学习的一个子领域",
    "memory_type": "semantic",
    "metadata": {"source": "manual"},
    "project_id": "test_project"
  }'
```

### 搜索记忆

```bash
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -H "X-USER-ID: u1" \
  -d '{
    "query": "深度学习",
    "project_id": "test_project",
    "limit": 10
  }'
```

## 命令行测试工具

### 交互式聊天

```bash
python scripts/test_memory_workflow.py
# 选择 1 进入交互式聊天模式
```

### 批量测试

```bash
# 运行所有测试
python scripts/test_memory_workflow.py
# 选择 5
```

## 多用户支持（预埋）

### 单用户阶段（当前）

- 所有请求使用 `X-USER-ID: u1`
- 数据存储在默认路径
- Neo4j使用单个实例

### 多用户阶段（未来）

#### 创建用户专属Neo4j实例

```bash
# 创建用户实例
./scripts/manage_user_neo4j.py create user123

# 查看所有实例
./scripts/manage_user_neo4j.py list

# 停止实例
./scripts/manage_user_neo4j.py stop user123

# 删除实例（含数据）
./scripts/manage_user_neo4j.py remove user123 --volumes
```

#### 使用不同用户ID

```bash
# 用户1
curl -X POST http://localhost:8000/api/v1/memory/chat \
  -H "X-USER-ID: user1" \
  -d '{"message": "用户1的查询"}'

# 用户2
curl -X POST http://localhost:8000/api/v1/memory/chat \
  -H "X-USER-ID: user2" \
  -d '{"message": "用户2的查询"}'
```

## Memory Bank文件结构

```
memory-bank/
├── project_default/           # 默认项目
│   ├── metadata.json         # 项目元数据
│   ├── context.md           # 当前上下文
│   ├── concepts.json        # 关键概念
│   └── summary.md          # 动态摘要
├── project_test/            # 测试项目
│   └── ...
└── operation_logs/          # 操作日志
    └── u1/                 # 用户操作日志
        └── 20240101.jsonl
```

## 监控和调试

### 查看日志

```bash
# API日志
tail -f data/logs/app.log

# 操作日志
tail -f memory-bank/operation_logs/u1/$(date +%Y%m%d).jsonl
```

### 健康检查

```bash
# 系统健康状态
curl http://localhost:8000/health

# API文档
open http://localhost:8000/docs
```

## 性能优化建议

1. **批量处理文档**
   ```python
   # 使用批量写入API
   POST /api/v1/memory/batch_write
   ```

2. **使用缓存**
   - 查询结果自动缓存30分钟
   - 相同查询会直接返回缓存结果

3. **限制工作记忆**
   - 自动维护最多20个工作记忆项
   - 基于访问频率和时间自动清理

## 故障排除

### PostgreSQL连接失败
```bash
# 检查连接
psql -h localhost -U postgres -d dpa

# 检查环境变量
echo $DATABASE_URL
```

### Neo4j连接失败
```bash
# 检查Neo4j状态
curl http://localhost:7474

# 查看日志
docker logs dpa_neo4j
```

### Memory Bank权限问题
```bash
# 确保目录可写
chmod -R 755 memory-bank/
```

## 下一步

1. 完成Memory Bank子系统（Day 2）
2. 实现文档处理管道（Day 3）
3. 实现三阶段混合检索（Day 4）
4. 集成测试和Demo（Day 5）

详见 [MVP路线图](./MEMORY_SYSTEM_MVP_ROADMAP.md)