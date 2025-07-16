# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DPA（Document Processing Agent）智能知识引擎是一个基于LangGraph和LangChain构建的智能体系统，用于处理学术文献和商务文档，构建可行动的知识洞察。项目采用前后端分离架构，目前处于AAG核心模块完成阶段（整体完成度75%）。

### 最新进展
- ✅ AAG智能分析引擎核心功能完成
- ✅ 现代化界面设计和布局优化
- ✅ 端到端功能测试和文档更新
- ✅ 完整的文档上传和智能问答流程

## 开发环境设置
# 🐍 Python & Conda 环境设置

在运行任何 Python、测试或脚本前，请先执行：

```bash
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)" && conda activate dpa_gen

### 后端环境（Python）
```bash
# 创建并激活conda环境
conda env create -f environment.yml
conda activate dpa_gen

# 配置环境变量
cp env.template .env
# 编辑.env文件，配置数据库连接（rtx4080服务器）和AI API密钥
```

### 前端环境（Next.js）
```bash
cd frontend
npm install
npm run dev  # 开发服务器运行在 http://localhost:8230
```

### 一键启动所有服务
```bash
# 项目根目录下
./start-all.sh
```

## 常用开发命令

### 后端开发
```bash
# 启动FastAPI开发服务器（端口8200）
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload

# 运行测试
pytest -v
pytest tests/test_specific.py::test_function -v  # 运行特定测试

# 代码质量检查
ruff format .              # 格式化代码
ruff check . --fix        # 修复代码问题
mypy src/ --strict        # 类型检查
bandit -r src/ -f json    # 安全扫描

# 数据库操作
python scripts/setup_databases.py     # 初始化所有数据库
python scripts/init_mvp_db.py        # 初始化MVP数据库
alembic upgrade head                 # 运行数据库迁移
alembic revision --autogenerate -m "description"  # 创建新迁移

# 系统测试
python scripts/test_config.py        # 测试配置
python scripts/test_components.py    # 测试组件连接
python scripts/mvp_demo.py          # 运行MVP演示
```

### 前端开发
```bash
cd frontend
npm run dev    # 开发服务器 (http://localhost:8230)
npm run build  # 构建生产版本
npm run lint   # 代码检查

# 端到端测试
node test_frontend_e2e.js   # 前端自动化测试
node test_qa_complete.js    # QA功能完整测试
```

## 核心架构

### 技术栈
- **后端**: Python 3.11.5, FastAPI, LangGraph 0.4.8, LangChain 0.3.26
- **前端**: Next.js 15.3.5, React 19, TypeScript 5, Tailwind CSS 4
- **数据库**: PostgreSQL, Qdrant, Neo4j, Redis (全部在rtx4080服务器)
- **AI模型**: OpenAI GPT-4o, text-embedding-3-large

### 项目结构
```
DPA/
├── src/
│   ├── api/          # FastAPI路由和中间件
│   ├── core/         # 核心功能（向量化、分块、索引）
│   │   └── document/ # 文档处理模块
│   │       └── sentence_based_chunker.py  # 智能句子分块器
│   ├── graphs/       # LangGraph智能体实现
│   │   ├── advanced_document_analyzer.py  # 高级文档分析器（六阶段）
│   │   ├── simplified_document_processor.py  # 简化文档处理器
│   │   └── document_processing_agent.py  # 文档处理智能体
│   ├── models/       # 数据模型
│   ├── database/     # 数据库连接管理
│   ├── services/     # 业务服务层
│   └── config/       # 配置管理
├── frontend/         # Next.js前端应用
│   ├── src/
│   │   ├── app/      # App Router页面
│   │   ├── components/  # UI组件
│   │   ├── services/    # API服务
│   │   └── store/       # Zustand状态管理
│   └── public/       # 静态资源
├── docs/             # 项目文档
│   ├── ADVANCED_DOCUMENT_ANALYZER.md  # 高级文档分析器指南
│   ├── DOCUMENT_ANALYSIS_IMPLEMENTATION.md
│   └── DOCUMENT_ANALYSIS_INTEGRATION.md
└── scripts/          # 实用脚本
```

### 核心工作流

1. **文档处理流程** (SimplifiedDocumentProcessor)
   - 文档上传 → PDF解析 → 文本提取 → 智能分块
   - 向量生成 → 存储到Qdrant → 更新索引

2. **高级文档分析** (AdvancedDocumentAnalyzer) - NEW!
   - 六阶段深度分析：准备预处理 → 宏观理解 → 深度探索
   - 批判性分析 → 知识整合 → 成果输出
   - 支持5种分析深度级别：Basic, Standard, Deep, Expert, Comprehensive
   - 生成执行摘要、详细报告、可视化数据和行动方案

3. **问答系统** (BasicKnowledgeQA)
   - 问题分析 → 向量检索 → 重排序 → 生成答案
   - 支持对话历史和来源引用

4. **混合检索系统** (HybridRetrievalService)
   - 第一阶段：向量检索（语义相似度）
   - 第二阶段：关键词检索（BM25）
   - 第三阶段：知识图谱查询（Neo4j）

## API端点说明

**API服务运行在**: http://localhost:8200  
**前端服务运行在**: http://localhost:8230

### 认证
所有API请求需要在Header中包含：`X-USER-ID: u1`

### 主要端点
- `GET /health` - 健康检查
- `GET /api/v1/projects` - 项目列表
- `POST /api/v1/documents/upload?project_id={id}` - 上传文档
- `POST /api/v1/qa/answer` - 问答接口
- `GET /api/v1/conversations?project_id={id}` - 对话列表

## 开发注意事项

### 数据库连接
- 所有数据库服务运行在rtx4080服务器上
- 连接配置在.env文件中，不要提交到版本控制
- 使用连接池管理数据库连接

### 前端开发
- 使用Zustand进行状态管理，支持持久化
- API调用统一通过services目录的服务类
- 关键布局组件使用内联样式而非Tailwind（避免渲染问题）

### 错误处理
- 后端使用标准化错误响应格式
- 前端显示友好的错误消息
- 所有异步操作要有loading状态

### 性能优化
- 文档处理使用后台任务（BackgroundTasks）
- 向量检索使用批处理
- Redis缓存高频查询结果
- 高级文档分析支持缓存和并发处理

### 高级文档分析使用
```python
# 使用示例
from src.graphs.advanced_document_analyzer import AdvancedDocumentAnalyzer, AnalysisDepth

analyzer = AdvancedDocumentAnalyzer()
result = await analyzer.analyze_document({
    "document_id": "doc_123",
    "project_id": "proj_456",
    "file_path": "/path/to/doc.pdf",
    "file_name": "research.pdf",
    "analysis_depth": AnalysisDepth.COMPREHENSIVE,
    "analysis_goal": "深入理解AI应用前景"
})
```

### 混合分块策略使用
```python
# 使用混合分块器优化检索
from src.core.chunking import ChunkingStrategy, document_chunker

chunks = await document_chunker.chunk_document(
    text=document_text,
    document_id=doc_id,
    strategy=ChunkingStrategy.HYBRID,  # 使用混合策略
    chunk_size=500,
    chunk_overlap=100
)

# 或者使用自定义配置
from src.core.document.hybrid_chunker import create_hybrid_chunker

chunker = create_hybrid_chunker(
    enable_context_windows=True,     # 启用上下文窗口
    enable_sliding_windows=True,     # 启用滑动窗口
    enable_key_info_extraction=True  # 启用关键信息提取
)
```

## 监控和调试

### 日志
```bash
tail -f data/logs/app.log      # 应用日志
tail -f data/logs/error.log    # 错误日志
```

### API文档
- Swagger UI: http://localhost:8200/docs
- ReDoc: http://localhost:8200/redoc

### 调试技巧
1. 使用`python scripts/test_components.py`检查所有组件状态
2. 配置`LANGCHAIN_TRACING_V2=true`启用LangSmith追踪
3. 前端开发者工具查看网络请求和控制台日志

## 当前状态和重点任务

### 已完成功能
- ✅ 基础架构和数据模型
- ✅ 文档上传和处理
- ✅ 向量化和检索系统
- ✅ 基础问答功能
- ✅ 前端界面（项目管理、文档管理、QA界面）
- ✅ 高级文档深度分析器（六阶段分析方法论）
- ✅ 智能句子分块器（支持中英文混合）
- ✅ 多种分块策略（固定大小、语义、结构化、句子边界）
- ✅ API集成（完整的文档分析RESTful API端点）
- ✅ 五级分析深度支持（Basic到Comprehensive）
- ✅ 混合智能分块器（HybridChunker）- 优化检索命中率
- ✅ 修复快速文本分析的uuid4和Chunk参数错误

### 当前问题
- 对话历史管理尚未实现持久化
- 知识图谱构建功能需要完善

### 优先任务
1. ✅ 集成高级文档分析器到API端点（已完成）
2. ✅ 优化文档分块策略，提高检索命中率（已完成）
3. 实现对话历史的持久化存储
4. 完善知识图谱构建功能
5. 前端集成高级分析功能展示
6. 实现研究规划智能体

## 最近修复的问题（2025-07-17）

### 1. API导入错误
- **问题**: `No module named 'src.models.processing_stage'`
- **修复**: 修正导入路径，使用 `ProcessingPipeline` 模块中的 `PipelineStage` 和 `ProcessingStage`

### 2. Redis认证错误
- **问题**: `Failed to connect to Redis: Authentication required`
- **修复**: 更新 `.env` 中的 `REDIS_URL` 和 `CELERY_BROKER_URL`，添加密码

### 3. VectorStore embed_texts错误
- **问题**: `'VectorStore' object has no attribute 'embed_texts'`
- **修复**: 使用 `EmbeddingService` 替代 `VectorStore` 进行嵌入向量生成

### 4. EmbeddingService初始化错误
- **问题**: `EmbeddingService.__init__() missing 1 required positional argument: 'config'`
- **修复**: 添加 `VectorConfig` 参数到所有 `EmbeddingService` 初始化

### 5. 知识图谱为空问题
- **问题**: `Built knowledge graph: 0 entities, 0 relationships`
- **修复**: 
  - 改进实体提取提示词（使用中文）
  - 增加处理的文本块数量
  - 添加后备方案（分块失败时使用原始内容）
  - 改进关系提取逻辑

### 6. 用户ID UUID格式错误
- **问题**: `invalid input syntax for type uuid: "u1"`
- **修复**: 在 `auth.py` 中添加映射逻辑，将 "u1" 等简化ID映射到真实UUID

### 7. Neo4j数据库错误
- **问题**: `Graph not found: dpa_graph`
- **修复**: 修改 `.env` 中的 `NEO4J_DATABASE=neo4j`（使用默认数据库）

## 自动化测试

### 一键启动和测试
```bash
# 使用Python脚本进行自动化测试
python simple_auto_test.py
```

测试包括：
- 服务启动（后端+前端）
- 健康检查
- 项目管理
- 文档上传
- 摘要生成
- 问答系统

### 测试脚本说明
- `simple_auto_test.py` - 简化的自动化测试脚本，包含启动和测试
- `auto_test_system.py` - 完整的集成测试框架
- `test_browser_simple.html` - 浏览器端测试工具
- `websocket_diagnostic.html` - WebSocket诊断工具

## 故障处理原则

1. **保持用户上下文**：记录所有修复的问题和解决方案
2. **渐进式修复**：从最关键的错误开始，逐步解决
3. **验证每个修复**：确保修复不会引入新问题
4. **更新文档**：将解决方案记录在CLAUDE.md中
5. **自动化测试**：使用集成测试验证系统功能