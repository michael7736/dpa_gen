# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DPA（Document Processing Agent）智能知识引擎是一个基于LangGraph和LangChain构建的智能体系统，旨在处理大量学术文献和商务文档，构建可行动的知识洞察。项目当前处于MVP阶段（完成度40%）。

## 开发环境设置

### Conda环境（推荐）
```bash
# 创建并激活dpa_gen环境
conda env create -f environment.yml
conda activate dpa_gen
```

### 环境配置
```bash
# 复制环境模板
cp env.template .env
# 编辑.env文件，配置数据库连接（rtx4080服务器）和AI API密钥
```

## 常用开发命令

### 启动服务
```bash
# 启动开发服务器
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 使用开发脚本（包含环境检查和依赖安装）
./scripts/dev_setup.sh
```

### 测试和代码质量
```bash
# 运行测试
pytest -v
pytest tests/test_specific.py -v  # 运行特定测试

# 代码格式化
ruff format .

# 代码检查
ruff check . --fix

# 类型检查
mypy src/ --strict

# 安全扫描
bandit -r src/ -f json -o security-report.json
```

### 配置和组件测试
```bash
# 测试配置是否正确
python scripts/test_config.py

# 测试核心组件
python scripts/test_components.py

# 查看测试报告
python scripts/test_report.py
```

### 数据库操作
```bash
# 初始化数据库
python scripts/setup_databases.py

# 运行数据库迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "描述"
```

## 核心架构

### 技术栈和关键版本
- **Python**: 3.11.5（通过dpa_gen conda环境）
- **LangGraph**: 0.4.8 - 智能体工作流编排
- **LangChain**: 0.3.26 - RAG工具链
- **FastAPI**: 0.115.13 - API框架
- **数据库集群**: rtx4080服务器
  - PostgreSQL (5432) - 结构化数据
  - Qdrant (6333) - 向量存储
  - Neo4j (7687) - 知识图谱
  - Redis (6379) - 缓存

### 项目结构
```
src/
├── api/            # FastAPI应用和路由
├── core/           # 核心功能（向量化、分块、知识索引）
├── graphs/         # LangGraph智能体实现
├── models/         # 数据模型（SQLAlchemy + Pydantic）
├── database/       # 数据库客户端和连接管理
├── services/       # 业务服务层
├── config/         # 配置管理
└── utils/          # 工具函数
```

### 核心工作流

#### 1. 文档处理智能体 (LangGraph)
基于状态机的文档处理流程：
- parse_document → extract_structure → semantic_chunking
- → generate_embeddings → extract_entities → build_knowledge_graph

#### 2. 研究规划智能体 (基于DeepResearch)
多阶段研究工作流：
- analyze_query → create_plan → generate_searches
- → execute_search → synthesize_findings → generate_report

#### 3. 知识问答智能体 (RAG增强)
混合检索和重排序：
- analyze_question → retrieve_context → rerank_results
- → generate_answer → validate_answer → generate_follow_ups

### 关键设计模式

1. **LangGraph状态管理**：所有复杂工作流使用StateGraph实现
2. **LangChain工具集成**：充分利用LangChain生态系统
3. **异步优先**：使用FastAPI异步特性处理高并发
4. **多数据库协同**：不同类型数据存储在专门的数据库中

## 开发注意事项

### 依赖管理
- 优先使用conda环境（dpa_gen）
- LangChain版本锁定在0.3.26，避免兼容性问题
- 新依赖添加到requirements.txt和environment.yml

### 数据库连接
- 所有数据库服务都在rtx4080服务器上
- 使用连接池管理数据库连接
- 配置在.env文件中，勿提交到版本控制

### AI模型配置
- 主模型：OpenAI GPT-4o
- 嵌入模型：text-embedding-3-large
- 备选模型：Anthropic Claude-3.5, DeepSeek-V3
- API密钥通过环境变量管理

### 错误处理
- 所有API端点返回标准化错误响应
- 使用structlog进行结构化日志记录
- 智能体状态包含error_message字段

### 性能优化
- 文档处理使用异步任务队列
- 向量检索使用批处理
- Redis缓存高频查询结果

## 监控和调试

### 日志查看
```bash
# 应用日志
tail -f data/logs/app.log

# 错误日志
tail -f data/logs/error.log
```

### API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

### LangSmith集成
配置LANGCHAIN_TRACING_V2=true启用LangSmith监控，用于追踪LangChain/LangGraph执行链路。

## 项目状态和开发重点

### 当前进度（40%完成）
- ✅ 基础架构和数据模型
- ✅ 配置管理系统
- ✅ 文档解析器
- 🔄 LangGraph智能体（40%）
- 🔄 向量化系统（60%）
- ⏳ 前端界面（0%）

### 近期开发重点
1. 完善文档处理智能体的向量化和索引功能
2. 实现基础的RAG问答功能
3. 优化文档分块策略
4. 开发项目记忆系统