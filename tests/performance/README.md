# DPA性能测试指南

## 概述

DPA性能测试套件提供全面的性能基准测试，帮助评估系统在不同负载下的表现。

## 测试类型

### 1. API性能测试
- **文件**: `test_api_performance.py`
- **功能**: 测试核心API端点的响应时间、吞吐量和并发处理能力
- **指标**: 
  - 响应时间（最小、最大、平均、中位数、P95、P99）
  - 吞吐量（请求/秒）
  - 错误率
  - 并发性能

### 2. 负载测试场景
- **文件**: `test_load_scenarios.py`
- **功能**: 模拟真实世界的负载模式
- **场景**:
  - 持续负载测试：固定RPS持续运行
  - 峰值负载测试：模拟流量峰值
  - 阶梯负载测试：逐步增加负载找出系统容量
  - 混合工作负载：模拟多种用户行为

### 3. 数据库性能测试
- **文件**: `test_database_performance.py`
- **功能**: 测试各数据库的操作性能
- **数据库**:
  - PostgreSQL：结构化数据操作
  - Neo4j：图数据库查询
  - Qdrant：向量搜索性能
  - Redis：缓存操作性能

### 4. AI模型性能测试
- **文件**: `test_model_performance.py`
- **功能**: 对比不同AI模型的性能和质量
- **模型**:
  - OpenAI: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
  - Anthropic: Claude-3 Opus, Sonnet, Haiku
  - DeepSeek: DeepSeek-Chat
- **测试用例**:
  - 简单问答
  - 复杂推理
  - 代码生成
  - 文本摘要
  - 结构化提取

## 快速开始

### 1. 环境准备

```bash
# 安装性能测试依赖
pip install aiohttp psutil matplotlib tiktoken asyncpg neo4j qdrant-client redis

# 设置环境变量
export DPA_API_URL="http://localhost:8001/api/v1"
export DPA_TEST_TOKEN="your-test-token"
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export DEEPSEEK_API_KEY="your-deepseek-key"
```

### 2. 运行测试

#### 运行所有测试
```bash
python scripts/run_performance_tests.py
```

#### 运行特定测试
```bash
# 只运行API测试
python scripts/run_performance_tests.py --only api

# 只运行数据库测试
python scripts/run_performance_tests.py --only database

# 只运行负载测试
python scripts/run_performance_tests.py --only load

# 只运行模型测试
python scripts/run_performance_tests.py --only model
```

#### 快速测试模式
```bash
# 减少测试迭代次数，快速获得结果
python scripts/run_performance_tests.py --quick
```

#### 跳过某些测试
```bash
# 跳过数据库测试
python scripts/run_performance_tests.py --skip-database

# 跳过模型测试（节省API成本）
python scripts/run_performance_tests.py --skip-model
```

### 3. 单独运行测试模块

```python
# API性能测试
python -m tests.performance.test_api_performance

# 负载测试
python -m tests.performance.test_load_scenarios

# 数据库性能测试
python -m tests.performance.test_database_performance

# 模型性能测试
python -m tests.performance.test_model_performance
```

## 测试配置

### API测试配置
```python
# 在test_api_performance.py中修改
BASE_URL = "http://localhost:8001/api/v1"
TEST_TOKEN = "your-test-token"

# 测试参数
num_requests = 100  # 每个端点的请求数
concurrent_requests = 10  # 并发请求数
```

### 负载测试配置
```python
# 持续负载测试
duration_seconds = 300  # 测试持续时间
requests_per_second = 10  # 每秒请求数

# 峰值负载测试
normal_rps = 10  # 正常负载
spike_rps = 100  # 峰值负载

# 阶梯负载测试
initial_rps = 5  # 初始负载
step_size = 5  # 每步增加的RPS
max_rps = 50  # 最大负载
```

### 数据库测试配置
```python
DB_CONFIG = {
    "postgresql": {
        "host": "rtx4080",
        "port": 5432,
        "database": "dpa_db",
        "user": "dpa_user",
        "password": "your_password"
    },
    # ... 其他数据库配置
}
```

### 模型测试配置
```python
# 测试迭代次数
test_iterations = 10  # 每个测试用例运行次数

# 测试用例配置
TEST_CASES = {
    "simple_qa": {
        "max_tokens": 100,
        "temperature": 0.7
    },
    # ... 其他测试用例
}
```

## 测试结果

### 输出文件
- `performance_report.json` - API性能详细报告
- `database_benchmark_report.md` - 数据库性能报告
- `model_performance_report.md` - AI模型性能报告
- `model_performance_comparison.png` - 模型性能对比图

### 性能指标解读

#### 响应时间
- **P95/P99**: 95%/99%的请求响应时间低于此值
- **中位数**: 比平均值更能反映典型性能
- **最大值**: 最坏情况下的响应时间

#### 吞吐量
- **RPS**: 每秒处理的请求数
- **并发数**: 同时处理的请求数

#### 错误率
- **成功率**: 成功请求占总请求的比例
- **错误类型**: 超时、连接错误、服务器错误等

## 性能优化建议

### 1. API优化
- 使用连接池减少连接开销
- 实现请求批处理
- 添加缓存层（Redis）
- 优化数据库查询

### 2. 数据库优化
- PostgreSQL: 添加适当索引，优化查询计划
- Neo4j: 使用索引和约束，优化Cypher查询
- Qdrant: 调整HNSW参数，使用过滤器加速搜索
- Redis: 使用Pipeline减少网络往返

### 3. 负载优化
- 实现请求限流
- 使用负载均衡
- 异步处理长时间任务
- 实现优雅降级

### 4. 模型优化
- 选择合适的模型大小
- 实现模型缓存
- 使用流式响应
- 批量处理请求

## 故障排除

### 常见问题

1. **连接错误**
   - 检查服务是否运行
   - 验证端口和地址配置
   - 检查防火墙设置

2. **认证失败**
   - 确认API令牌有效
   - 检查环境变量设置

3. **性能异常**
   - 检查系统资源（CPU、内存）
   - 查看应用日志
   - 确认数据库连接池配置

4. **测试失败**
   - 查看详细错误信息
   - 检查依赖服务状态
   - 验证测试数据准备

## 最佳实践

1. **定期运行**: 在每次重要更新后运行性能测试
2. **建立基线**: 记录正常情况下的性能指标
3. **监控趋势**: 跟踪性能随时间的变化
4. **负载测试**: 在生产环境容量规划前进行充分测试
5. **成本控制**: 注意AI模型API调用成本

## 扩展测试

如需添加新的性能测试：

1. 在`tests/performance/`目录创建新的测试文件
2. 实现测试类和测试方法
3. 在`__init__.py`中导出测试函数
4. 更新`run_performance_tests.py`添加新测试

示例：
```python
# test_custom_performance.py
async def run_custom_tests():
    # 实现自定义测试逻辑
    pass
```

## 相关资源

- [FastAPI性能优化](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL性能调优](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Neo4j性能指南](https://neo4j.com/docs/operations-manual/current/performance/)
- [Qdrant性能调优](https://qdrant.tech/documentation/performance/)

---

需要帮助？请联系 DPA 开发团队或查看项目文档。