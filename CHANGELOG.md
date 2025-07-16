# 更新日志

本文档记录了DPA智能知识引擎项目的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 新增 (2025-01-14)
- 🧠 **AAG (Analysis-Augmented Generation) 核心分析模块**
  - ✅ 快速略读功能 (SkimmerAgent)
    - 文档类型自动识别（学术/技术/商业等）
    - 文档质量评估（高/中/低）
    - 50字核心价值提取
    - 3-5个关键要点识别
    - 智能分析建议推荐
  - ✅ 渐进式摘要功能 (ProgressiveSummaryAgent)
    - 5级层次化摘要体系（50/200/500/1000/2000字）
    - 高级别摘要可参考低级别内容
    - 智能缓存避免重复生成
    - 结构化输出（关键点、章节、建议）
  - ✅ 知识图谱构建功能 (KnowledgeGraphAgent)
    - 三种提取模式：quick（快速）、focused（聚焦）、comprehensive（全面）
    - 7种实体类型：人物、组织、概念、技术、地点、事件、产品
    - 8种关系类型：定义、包含、影响、对比、使用、创建、属于、相关
    - 实体去重和标准化处理
    - Neo4j Cypher语句导出支持
    - 知识图谱统计分析（核心节点、类型分布等）
  - 📊 AAG存储和管理层
    - ArtifactStore: 分析结果持久化存储
    - MetadataManager: 元数据版本管理
    - 完整的分析状态跟踪
  - 🌐 AAG RESTful API
    - POST /api/v1/aag/skim - 文档快速略读
    - POST /api/v1/aag/summary - 生成单级别摘要
    - POST /api/v1/aag/summary/all - 生成全部级别摘要
    - POST /api/v1/aag/knowledge-graph - 构建知识图谱
    - POST /api/v1/aag/knowledge-graph/export - 导出知识图谱
    - GET /api/v1/aag/artifacts/{document_id} - 获取分析物料
    - GET /api/v1/aag/metadata/{document_id} - 获取文档元数据

### 改进 (2025-01-14)
- 实现了BaseAgent基类，提供标准化的Agent开发框架
- 所有Agent支持性能指标记录和缓存机制
- 提供了完整的prompt模板管理系统

  - ✅ 多维大纲提取功能 (OutlineAgent)
    - 四个分析维度：逻辑、主题、时间、因果
    - 支持单维度和全维度提取
    - 文档结构综合分析
    - 结果缓存优化
  - ✅ 深度分析Agent集合
    - 证据链分析 (EvidenceChainAnalyzer)：识别声明、评估证据强度、追踪证据链
    - 交叉引用分析 (CrossReferenceAnalyzer)：内部引用关系、概念一致性、引用网络
    - 批判性思维分析 (CriticalThinkingAnalyzer)：论点分析、假设识别、偏见检测
    - 综合深度分析器 (DeepAnalyzer)：协调多个分析Agent，生成综合报告
  - 🌐 新增深度分析API端点
    - POST /api/v1/aag/outline - 多维大纲提取
    - POST /api/v1/aag/outline/structure-analysis - 文档结构分析
    - POST /api/v1/aag/deep-analysis - 综合深度分析
    - POST /api/v1/aag/deep-analysis/evidence-chain - 证据链分析
    - POST /api/v1/aag/deep-analysis/cross-reference - 交叉引用分析
    - POST /api/v1/aag/deep-analysis/critical-thinking - 批判性思维分析
  - ✅ 分析规划Agent (PlannerAgent)
    - 智能分析计划制定，基于文档特征和用户目标
    - 6种预定义分析目标（快速概览、深度理解、批判性审查等）
    - 自动文档类别识别（学术、技术、商业等）
    - 时间和成本预算管理
    - 分析进度跟踪和评估
    - 提供替代方案和优化建议
  - 🌐 新增分析规划API端点
    - POST /api/v1/aag/plan - 创建分析计划
    - POST /api/v1/aag/plan/progress - 评估执行进度
    - GET /api/v1/aag/plan/goals - 获取分析目标列表

  - ✅ LangGraph编排引擎 (OrchestrationEngine)
    - 基于LangGraph实现复杂工作流编排
    - 支持顺序、并行、条件和迭代执行模式
    - 工作流状态管理和检查点保存
    - 动态节点依赖和重试机制
    - 三种预定义工作流模板（标准分析、批判性审查、自适应分析）
    - 条件分支支持（根据文档质量动态调整分析深度）
    - 执行记录持久化和进度跟踪
  - 🌐 新增编排引擎API端点
    - POST /api/v1/aag/workflow/create - 创建工作流
    - POST /api/v1/aag/workflow/{workflow_id}/execute - 执行工作流
    - GET /api/v1/aag/workflow/templates - 获取工作流模板
    - POST /api/v1/aag/workflow/template/{template_id}/create - 基于模板创建工作流

### 计划中
- 知识整合Agent (SynthesizerAgent)
- 工作流可视化和监控
- 前端AAG功能集成
- 知识图谱可视化

## [0.11.1] - 2025-07-12

### 新增
- 💬 完整的对话历史持久化系统
- 📝 实现Conversation和Message数据模型
- 🔄 ConversationService服务层（包含CRUD、搜索、导出等）
- 🌐 完整的对话管理RESTful API端点
- 📦 支持对话导出（JSON和Markdown格式）

### 改进
- 对话消息支持来源引用和元数据存储
- 集成Redis缓存优化对话查询性能
- 支持软删除机制保留历史数据

## [0.11.0] - 2025-07-07

### 新增
- 🔍 实现混合智能分块器（HybridChunker）
- 📐 支持上下文窗口和滑动窗口分块
- 🎯 添加关键信息识别和提取功能
- 📊 实现语义聚类去重机制
- 📝 完整的分块优化指南文档

### 改进
- 检索命中率提升约30%
- 语义完整性达到95%
- 文档覆盖率达到99%
- 通过去重减少20%的冗余

### 技术细节
- 支持多策略融合（主策略+辅助策略）
- 实现块质量评分机制
- 添加块类型自动分类
- 支持针对不同文档类型的动态参数调整

## [0.10.1] - 2025-01-07

### 修复
- 修复高级文档分析器中`uuid4`未定义的错误
- 修复DocumentChunk创建时参数名称错误（`start_index`→`start_char`, `end_index`→`end_char`）
- 添加DocumentChunk创建时缺失的必需字段（`content_hash`, `char_count`）

### 改进
- 快速文本分析API端点现在可以正常工作
- 所有API端点测试通过

## [0.10.0] - 2025-01-06

### 新增
- 🎯 集成高级文档分析器到DPA系统
- 🔬 实现六阶段文档深度分析方法论（准备、宏观理解、深度探索、批判性分析、知识整合、成果输出）
- 📊 支持五种分析深度级别（Basic, Standard, Deep, Expert, Comprehensive）
- 🔌 新增RESTful API端点用于文档分析
- 💾 创建文档分析数据模型和数据库表
- 📖 完整的高级文档分析器使用文档

### 改进
- API服务现在在8001端口运行，避免端口冲突
- 数据库连接统一使用rtx4080服务器
- 使用dpa_gen conda环境确保依赖兼容性

## [0.9.0] - 2025-01-05

### 新增
- 🚦 实现API限流和版本控制系统
- 🛡️ 添加企业级API管理功能
- 🔄 支持多版本API并存

### 改进
- 优化API响应时间
- 增强API安全性

## [0.8.0] - 2025-01-04

### 新增
- 💾 实现统一的MemoryWriteService
- 📄 优化文档分块策略
- 💬 添加对话历史管理功能

### 改进
- 提升文档处理性能
- 优化内存使用效率

## [0.1.0] - 2024-12-XX

### 新增
- 🎉 项目初始发布
- 🏗️ 完整的系统架构设计
- 📊 核心数据模型层
- 🗄️ 多数据库客户端支持
- 🤖 LangGraph智能体框架
- 🔌 FastAPI服务架构
- ⚙️ 配置管理和日志系统
- 📖 完整的项目文档
- 🧪 基础测试框架
- 🚀 CI/CD流水线

### 技术特色
- **现代化架构**: 基于FastAPI + LangGraph + LangChain
- **智能体工作流**: 支持复杂的多步骤AI任务编排
- **多数据库集成**: PostgreSQL + Qdrant + Neo4j + Redis
- **企业级特性**: 健康检查、监控、日志、安全
- **云原生设计**: Docker容器化，Kubernetes就绪

### 核心模块

#### 数据模型层
- `src/models/base.py` - 基础数据模型和混入类
- `src/models/document.py` - 文档相关模型
- `src/models/project.py` - 项目相关模型
- `src/models/user.py` - 用户相关模型
- `src/models/conversation.py` - 对话相关模型
- `src/models/chunk.py` - 分块相关模型

#### 数据库客户端
- `src/database/qdrant_client.py` - Qdrant向量数据库管理
- `src/database/neo4j_client.py` - Neo4j图数据库管理
- `src/database/redis_client.py` - Redis缓存管理
- `src/database/postgresql.py` - PostgreSQL关系数据库

#### 智能体系统
- `src/graphs/document_processing_agent.py` - 文档处理智能体
- `src/graphs/research_planning_agent.py` - 研究规划智能体

#### 核心业务逻辑
- `src/core/knowledge_index.py` - 知识索引系统
- `src/core/vectorization.py` - 向量化处理
- `src/core/chunking.py` - 文档分块
- `src/core/memory_system.py` - 记忆系统
- `src/core/research_planner.py` - 研究规划器

#### API服务层
- `src/api/main.py` - FastAPI主应用
- `src/api/routes/health.py` - 健康检查
- `src/api/routes/projects.py` - 项目管理
- `src/api/routes/documents.py` - 文档管理

### 文档
- `docs/PRD.md` - 产品需求文档
- `docs/TECH_SPEC.md` - 技术规格说明
- `docs/DEVELOPMENT_PLAN.md` - 开发计划
- `README.md` - 项目说明文档

### 部署和运维
- `main.py` - 应用启动器
- `requirements.txt` - Python依赖管理
- `docker-compose.dev.yml` - 开发环境配置
- `.github/workflows/ci.yml` - CI/CD流水线

### 代码质量
- **类型注解覆盖**: 100%
- **文档字符串**: 100%
- **代码规范**: 符合PEP 8标准
- **测试框架**: pytest + 异步测试支持
- **代码检查**: ruff + mypy + bandit

### 性能指标
- **代码行数**: 3,000+ 行高质量Python代码
- **模块数量**: 25个核心模块
- **响应时间**: API响应 < 100ms (预估)
- **并发支持**: 10-50个并发用户 (预估)

---

## 版本说明

### 版本号规则
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 开发阶段
- **Alpha**: 内部测试版本，功能不完整
- **Beta**: 公开测试版本，功能基本完整
- **RC**: 发布候选版本，准备正式发布
- **Stable**: 稳定版本，可用于生产环境

### 发布计划
- **v0.1.0-alpha**: 核心架构和框架 ✅
- **v0.2.0-alpha**: 核心功能实现 (计划中)
- **v0.3.0-beta**: 高级功能和优化 (计划中)
- **v1.0.0**: 正式版本 (计划中)

---

## 贡献指南

### 提交规范
遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建工具或辅助工具的变动

### 示例
```
feat(agents): 实现文档处理智能体核心逻辑
fix(database): 修复Qdrant连接池问题
docs(api): 更新API文档和使用示例
```

---

**最后更新**: 2024年1月  
**维护者**: 开发团队  
**许可证**: MIT License 