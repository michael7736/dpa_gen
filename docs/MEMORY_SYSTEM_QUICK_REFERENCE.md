# DPA记忆系统 - 快速参考指南

## 核心概念速查

### 🧠 四层记忆架构
```python
memory_layers = {
    "sensory": "原始输入缓冲 (<1秒)",
    "working": "当前任务上下文 (7±2项)",
    "episodic": "具体事件和经历 (中期)",
    "semantic": "概念和事实知识 (长期)"
}
```

### 🔄 认知循环
```
感知 → 注意 → 编码 → 存储 → 检索 → 推理 → 规划 → 执行 → 反思
```

### 📁 记忆库结构
```
memory-bank/
├── metadata.json          # 元数据
├── source_documents.md    # 源文档
├── key_concepts.md       # 关键概念
├── dynamic_summary.md    # 动态摘要
├── learning_journal/     # 学习日志
├── hypotheses/          # 假设验证
└── agent_rules.md       # 智能体规则
```

## 快速开始

### 1. 环境设置
```bash
# 克隆项目
git clone <repo>
cd DPA

# 创建环境
conda env create -f environment.yml
conda activate dpa_gen

# 安装额外依赖
pip install langgraph==0.2.0
pip install torch torch-geometric
```

### 2. 配置数据库
```bash
# PostgreSQL
createdb dpa_cognitive
psql dpa_cognitive < scripts/init_postgres.sql

# Neo4j
neo4j-admin import --database=dpa --nodes=init/nodes.csv --relationships=init/rels.csv

# Redis
redis-server --appendonly yes
```

### 3. 最小示例
```python
from src.core.memory.workflow import build_cognitive_workflow
from src.core.memory.state import DPACognitiveState

# 构建工作流
app = build_cognitive_workflow()

# 初始状态
initial_state = {
    "messages": [HumanMessage(content="分析这份文档")],
    "current_documents": [document],
    "user_id": "researcher_001",
    "project_id": "project_001"
}

# 执行
config = {"configurable": {"thread_id": "session_001"}}
result = await app.ainvoke(initial_state, config)
```

## 关键组件

### 1. S2语义分块
```python
from src.core.chunking.s2_chunker import S2SemanticChunker

chunker = S2SemanticChunker()
chunks = await chunker.chunk_document(
    document_text,
    metadata={"title": "...", "type": "..."}
)
```

### 2. 混合检索
```python
from src.services.hybrid_retrieval import EnhancedHybridRetriever

retriever = EnhancedHybridRetriever()
results = await retriever.hybrid_retrieve(
    query="深度学习在NLP中的应用",
    state=current_state
)
```

### 3. GNN学习
```python
from src.learning.gnn_completion import GNNKnowledgeCompletion

gnn = GNNKnowledgeCompletion()
hypotheses = await gnn.predict_missing_links(
    knowledge_graph,
    confidence_threshold=0.8
)
```

### 4. 记忆库管理
```python
from src.core.memory.memory_bank import MemoryBankManager

memory_bank = MemoryBankManager()
await memory_bank.read_verify_update_execute(state)
```

## 常用命令

### 开发
```bash
# 运行测试
pytest tests/test_memory_system.py -v

# 启动服务
uvicorn src.api.main:app --reload

# 监控性能
python scripts/monitor_performance.py
```

### 数据管理
```bash
# 备份记忆库
tar -czf memory-bank-backup.tar.gz memory-bank/

# 导出知识图谱
python scripts/export_knowledge_graph.py

# 清理过期记忆
python scripts/cleanup_expired_memories.py
```

## 故障排除

### 常见问题

1. **内存溢出**
```python
# 检查工作记忆大小
if len(state["working_memory"]) > 9:
    state = StateManager.compress_working_memory(state)
```

2. **查询超时**
```python
# 使用缓存
results = await cache.get_or_compute(
    key=query_hash,
    compute_fn=lambda: retriever.search(query),
    ttl=1800
)
```

3. **图谱查询慢**
```cypher
// 确保有合适的索引
CREATE INDEX ON :Concept(name);
CREATE INDEX ON :Concept(embedding_id);
```

## 性能优化技巧

1. **批量处理**
```python
# 批量嵌入
embeddings = await batch_embed(texts, batch_size=50)

# 批量图查询
results = await batch_graph_query(queries, max_concurrent=10)
```

2. **异步并发**
```python
# 并行检索
tasks = [
    vector_search(query),
    graph_search(query),
    memory_bank_search(query)
]
results = await asyncio.gather(*tasks)
```

3. **智能缓存**
```python
# 多级缓存策略
cache_config = {
    "local": {"size": 1000, "ttl": 300},
    "redis": {"ttl": 3600},
    "preload": ["hot_concepts", "frequent_queries"]
}
```

## 监控指标

```python
# Prometheus指标
metrics = {
    "memory_operations_total": Counter,
    "query_latency_seconds": Histogram,
    "knowledge_graph_nodes": Gauge,
    "learning_progress": Gauge
}

# 健康检查端点
GET /health
GET /metrics
GET /memory-stats
```

## 扩展点

### 添加新的记忆类型
```python
class CustomMemoryLayer:
    def encode(self, data): ...
    def store(self, encoded): ...
    def retrieve(self, query): ...
    def decay(self, time_delta): ...
```

### 自定义学习策略
```python
class CustomLearningStrategy:
    def identify_gaps(self, state): ...
    def generate_plan(self, gaps): ...
    def execute_step(self, step): ...
```

### 集成外部工具
```python
@tool
def custom_research_tool(query: str) -> str:
    """自定义研究工具"""
    # 实现逻辑
    return results
```

## 相关资源

- [完整设计文档](./MEMORY_SYSTEM_DESIGN_V3_FINAL.md)
- [实施路线图](./MEMORY_SYSTEM_IMPLEMENTATION_ROADMAP.md)
- [API文档](http://localhost:8000/docs)
- [监控面板](http://localhost:3000/d/memory-system)

---

💡 **提示**：先从最小示例开始，逐步添加高级功能。记得经常查看记忆库文件，了解系统的"思考过程"。