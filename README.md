# DPA智能知识引擎

> 基于大语言模型的智能知识引擎系统，支持深度研究、持续学习和知识图谱构建

[![CI/CD](https://github.com/michael7736/dpa_gen/actions/workflows/ci.yml/badge.svg)](https://github.com/michael7736/dpa_gen/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Progress](https://img.shields.io/badge/Progress-50%25-yellow)](https://github.com/michael7736/dpa_gen)

**🔗 GitHub仓库**: [michael7736/dpa_gen](https://github.com/michael7736/dpa_gen)

## 📊 项目状态

- **当前版本**: v0.12.0-alpha (AAG核心分析模块)
- **完成度**: 58%
- **最后更新**: 2025-07-14
- **当前重点**: 🔥 **AAG (Analysis-Augmented Generation) 模块开发**
- **最新进展**: 
  - ✅ 实现快速略读、渐进式摘要、知识图谱构建功能
  - ✅ 完成AAG基础架构和API集成
  - 🚧 正在开发多维大纲提取和深度分析功能

## 🚀 项目概述

DPA（Deep research & Progressive learning Agent）智能知识引擎是一个基于LangGraph和LangChain构建的智能体系统，专门用于处理大量学术论文和参考手册，实现深度研究和持续学习。

### 核心特性

#### 🔥 AAG (Analysis-Augmented Generation) - 当前开发重点
- **快速略读 (SkimmerAgent)**: 智能识别文档类型，评估质量，提取核心价值
- **渐进式摘要 (ProgressiveSummaryAgent)**: 5级层次化摘要体系（50-2000字）
- **知识图谱构建 (KnowledgeGraphAgent)**: 多模式实体关系提取，支持Neo4j导出
- **多维分析** (开发中): 逻辑、主题、时间、因果等多维度文档解析
- **深度分析集合** (计划中): 证据链追踪、交叉引用、批判性思维分析

#### 基础能力
- 🧠 **智能文档处理**: 支持PDF、Word、Markdown等多种格式，自动解析文档结构
- 🔍 **层次化知识索引**: 构建文档、章节、段落的多层次索引体系
- 📊 **知识图谱构建**: 自动提取实体关系，构建领域知识图谱
- 🎯 **智能研究规划**: 参考OpenAI DeepResearch工作流，自动制定研究计划
- 💾 **渐进式学习**: 建立项目记忆库，跟踪研究进展
- 🔄 **多模态理解**: 集成最新AI技术，支持文本、图像等多模态内容

#### 企业级特性
- 🚦 **API限流与版本控制**: 企业级API管理，支持多版本并存
- 📈 **性能监控**: 完整的监控体系，实时跟踪系统性能
- 🐳 **容器化部署**: 支持Docker和Kubernetes部署
- 🛡️ **安全加固**: 多层安全防护，保护数据安全
- ✨ **六阶段深度分析**: 高级文档分析器，提供从准备到输出的完整分析流程
- 🎨 **五级分析深度**: 支持Basic、Standard、Deep、Expert、Comprehensive五种分析级别
- 🔍 **智能混合分块**: 结合多种策略优化检索命中率，支持上下文窗口和滑动窗口

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                              │
├─────────────────────────────────────────────────────────────┤
│                        API网关层                              │
├─────────────────────────────────────────────────────────────┤
│                      业务逻辑层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│  │文档处理智能体│ │研究规划智能体│ │知识管理智能体│             │
│  └─────────────┘ └─────────────┘ └─────────────┘             │
├─────────────────────────────────────────────────────────────┤
│                       AI服务层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│  │ LangGraph   │ │ LangChain   │ │   OpenAI    │             │
│  └─────────────┘ └─────────────┘ └─────────────┘             │
├─────────────────────────────────────────────────────────────┤
│                      数据存储层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│  │ PostgreSQL  │ │   Qdrant    │ │   Neo4j     │             │
│  └─────────────┘ └─────────────┘ └─────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 技术栈

### 后端框架
- **FastAPI**: 高性能异步Web框架
- **LangGraph 0.4.8**: 智能体工作流编排
- **LangChain 0.3.26**: LLM应用开发框架
- **Celery**: 异步任务队列

### AI/ML技术
- **OpenAI GPT-4o**: 文本理解和生成
- **OpenAI Embeddings**: text-embedding-3-large向量化
- **Semantic Chunking**: 语义分块技术
- **NER**: 命名实体识别

### 数据存储
- **PostgreSQL 15**: 关系数据存储
- **Qdrant 1.7**: 向量数据库
- **Neo4j 5.0**: 图数据库
- **Redis 7.0**: 缓存和会话存储

### 开发工具
- **Docker**: 容器化部署
- **Pytest**: 单元测试
- **Ruff**: 代码格式化和检查
- **MyPy**: 类型检查
- **Prometheus + Grafana**: 监控系统

## 📦 快速开始

### 🔥 AAG模块快速体验

```bash
# 1. 激活环境
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)" && conda activate dpa_gen

# 2. 启动API服务
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. 快速测试AAG功能
curl -X POST http://localhost:8000/api/v1/aag/skim \
  -H "X-USER-ID: u1" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "test_doc",
    "document_content": "您的文档内容..."
  }'
```

详细使用指南请参考 [AAG快速开始](docs/AAG_QUICK_START.md)

### 环境要求

- Python 3.11.5
- Docker & Docker Compose 2.0+
- Conda (推荐使用dpa_gen环境)
- 数据库服务器: rtx4080 (PostgreSQL, Redis, Qdrant, Neo4j)

### 完整安装步骤

1. **创建并激活环境**
```bash
conda env create -f environment.yml
conda activate dpa_gen
```

2. **克隆项目**
```bash
git clone https://github.com/michael7736/dpa_gen.git
cd dpa_gen
```

3. **配置环境变量**
```bash
cp env.template .env
# 编辑 .env 文件，确保数据库连接到rtx4080服务器
```

4. **运行开发服务器**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker快速部署

```bash
# 使用部署脚本
./scripts/deploy.sh deploy dev

# 或手动部署
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f dpa-api
```

### 生产环境部署

```bash
# 构建生产镜像
docker build -t dpa:latest .

# 使用生产配置部署
docker-compose -f docker-compose.prod.yml up -d

# Kubernetes部署
kubectl apply -f deploy/k8s/
```

## 🔧 配置说明

### 必需配置

```bash
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
POSTGRESQL_URL=postgresql+asyncpg://user:pass@localhost:5432/dpa
QDRANT_URL=http://localhost:6333
NEO4J_URL=bolt://localhost:7687
REDIS_URL=redis://localhost:6379/0
```

### 可选配置

```bash
# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=8200

# 文档处理配置
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=100

# 研究规划配置
MAX_RESEARCH_DEPTH=5
DEFAULT_SEARCH_RESULTS=50
```

## 📚 API文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8200/docs
- **ReDoc**: http://localhost:8200/redoc
- **健康检查**: http://localhost:8200/health

### 主要API端点

#### 项目管理
- `POST /api/v1/projects` - 创建项目
- `GET /api/v1/projects` - 列出项目
- `GET /api/v1/projects/{project_id}` - 获取项目详情

#### 文档管理
- `POST /api/v1/documents/upload` - 上传文档
- `GET /api/v1/documents/{document_id}/status` - 获取处理状态
- `GET /api/v1/documents/{document_id}/outline` - 获取文档大纲

#### 对话管理 🆕
- `POST /api/v1/conversations` - 创建对话
- `GET /api/v1/conversations` - 获取对话列表
- `POST /api/v1/conversations/{id}/messages` - 添加消息
- `GET /api/v1/conversations/{id}/messages` - 获取对话消息
- `GET /api/v1/conversations/{id}/export` - 导出对话

#### 问答系统
- `POST /api/v1/qa/answer` - 基础问答
- `POST /api/v1/enhanced-qa/answer` - 增强问答（支持对话历史）

#### 研究规划
- `POST /api/v1/research/plans` - 创建研究计划
- `GET /api/v1/research/plans/{plan_id}` - 获取计划详情
- `POST /api/v1/research/plans/{plan_id}/execute` - 执行计划

#### 知识管理
- `POST /api/v1/knowledge/search` - 知识搜索
- `GET /api/v1/knowledge/graph/{project_id}` - 获取知识图谱

## 🧪 使用示例

### 1. 创建项目

```python
import httpx

# 创建项目
project_data = {
    "name": "AI研究项目",
    "description": "深度学习相关研究",
    "domain": "人工智能",
    "objectives": ["研究最新技术", "构建知识体系"]
}

response = httpx.post("http://localhost:8200/api/v1/projects", json=project_data)
project = response.json()
project_id = project["project_id"]
```

### 2. 上传文档

```python
# 上传PDF文档
with open("research_paper.pdf", "rb") as f:
    files = {"file": f}
    data = {"project_id": project_id}
    
    response = httpx.post(
        "http://localhost:8200/api/v1/documents/upload",
        files=files,
        data=data
    )
    
upload_result = response.json()
document_id = upload_result["document_id"]
```

### 3. 创建研究计划

```python
# 创建研究计划
research_data = {
    "project_id": project_id,
    "research_topic": "深度学习在NLP中的应用",
    "research_objectives": [
        "调研最新技术",
        "分析技术趋势",
        "总结最佳实践"
    ]
}

response = httpx.post("http://localhost:8200/api/v1/research/plans", json=research_data)
plan = response.json()
```

### 4. 知识搜索

```python
# 搜索知识
search_data = {
    "query": "transformer模型的注意力机制",
    "project_id": project_id,
    "limit": 10
}

response = httpx.post("http://localhost:8200/api/v1/knowledge/search", json=search_data)
results = response.json()
```

## 🧩 核心组件

### 文档处理智能体

基于LangGraph构建的文档处理工作流：

1. **文档解析**: 支持多种格式的文档解析
2. **结构提取**: 自动识别文档章节结构
3. **语义分块**: 基于语义的智能分块
4. **向量化**: 生成高质量的文档嵌入
5. **实体提取**: 识别文档中的关键实体
6. **知识图谱**: 构建实体关系图谱

### 研究规划智能体

参考OpenAI DeepResearch的多阶段研究工作流：

1. **主题分析**: 深入分析研究主题
2. **问题生成**: 自动生成研究问题
3. **信息缺口**: 识别知识缺口
4. **搜索策略**: 设计信息收集策略
5. **计划制定**: 创建详细的研究计划
6. **执行监控**: 跟踪研究进展

### 知识索引系统

多层次的知识组织和检索：

1. **层次化索引**: 文档→章节→段落→句子
2. **语义检索**: 基于向量相似度的检索
3. **图谱查询**: 基于知识图谱的关系查询
4. **混合搜索**: 结合多种检索策略
5. **上下文增强**: 提供丰富的上下文信息

## 🔍 监控和调试

### 健康检查

```bash
# 检查系统健康状态
curl http://localhost:8200/health

# 检查服务详细状态
curl http://localhost:8200/api/v1/health/services

# 检查系统指标
curl http://localhost:8200/api/v1/health/metrics
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看Docker日志
docker-compose logs -f app

# 查看特定服务日志
docker-compose logs -f qdrant
```

### 性能监控

系统集成了Prometheus监控，可以通过以下方式查看指标：

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (如果配置)

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_document_processing.py

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试类型

- **单元测试**: 测试单个组件功能
- **集成测试**: 测试组件间交互
- **端到端测试**: 测试完整工作流
- **性能测试**: 测试系统性能

## 🚀 完整功能

### ✅ 已实现功能

- **文档处理**: 多格式文档解析、语义分块、元数据提取
- **向量化索引**: 高质量文档嵌入、层次化索引
- **知识图谱**: 实体识别、关系抽取、图谱构建
- **RAG问答**: 混合检索、重排序、上下文增强
- **记忆系统**: 对话历史、知识积累、上下文管理
- **API管理**: 限流控制、版本管理、认证授权
- **监控系统**: Prometheus指标、Grafana仪表板、日志聚合
- **部署方案**: Docker容器化、K8s编排、CI/CD流水线

### 🚧 开发中功能

- **研究规划智能体**: DeepResearch工作流实现
- **多模态支持**: 图像理解、表格解析
- **协作功能**: 多用户协作、知识共享
- **前端界面**: Web UI开发

## 📈 性能指标

基于性能测试结果，系统达到以下指标：

- **API响应时间**: P95 < 200ms
- **系统吞吐量**: > 1000 RPS
- **向量搜索**: > 100 QPS
- **并发用户**: > 1000
- **系统可用性**: > 99.9%

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 使用`ruff`进行代码格式化
- 使用`mypy`进行类型检查
- 编写单元测试
- 更新文档

## 📄 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - LLM应用开发框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 智能体工作流
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代Web框架
- [Qdrant](https://github.com/qdrant/qdrant) - 向量数据库
- [Neo4j](https://github.com/neo4j/neo4j) - 图数据库

## 📞 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 邮箱: your-email@example.com

---

**DPA智能知识引擎** - 让知识管理更智能，让研究更高效！ 