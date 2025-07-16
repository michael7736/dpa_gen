# DPA记忆系统MVP实施路线图

## 概述

基于风险控制原则，我们将记忆系统实施分为两个阶段：
- **Phase 1 (MVP)**：认知循环 + 三阶段混检 + Memory Bank
- **Phase 2 (Advanced)**：GNN主动学习 + 元认知引擎

## Phase 1: MVP核心功能（5天）

### 目标
构建一个可用的认知记忆系统，实现基础的持续学习能力。

### 核心交付物
1. **认知循环**：感知→编码→存储→检索→推理
2. **三阶段混合检索**：向量→图谱→记忆库
3. **Memory Bank**：持久化记忆存储

### 详细计划

#### Day 1: LangGraph基础架构
**目标**：搭建状态管理和工作流框架

**任务清单**：
- [ ] 创建简化的`MVPCognitiveState`定义
- [ ] 实现PostgreSQL检查点存储
- [ ] 构建基础认知循环工作流
- [ ] 设置开发环境和测试框架

**关键代码**：
```python
class MVPCognitiveState(TypedDict):
    """MVP版本的认知状态"""
    # 核心字段
    messages: Annotated[List[BaseMessage], add_messages]
    working_memory: Dict[str, Any]  # 限制为20项
    episodic_memory: List[Dict]     # 限制为100项
    
    # 文档处理
    current_documents: List[Dict]
    document_chunks: List[Dict]
    
    # 检索结果
    retrieved_context: Dict[str, Any]
    
    # Memory Bank
    memory_bank_state: Dict
    
    # 控制流
    thread_id: str
    project_id: str
    error_log: List[str]
```

**验收标准**：
- 能够创建和恢复检查点
- 基础工作流可以运行
- 通过单元测试

#### Day 2: Memory Bank子系统
**目标**：实现文件系统持久化记忆

**任务清单**：
- [ ] 创建Memory Bank目录结构
- [ ] 实现RVUE生命周期（Read-Verify-Update-Execute）
- [ ] 开发动态摘要功能
- [ ] 实现关键概念管理

**Memory Bank结构（简化版）**：
```
memory-bank/
├── metadata.json           # 元数据
├── current_context.md      # 当前上下文
├── key_concepts.md        # 关键概念
├── dynamic_summary.md     # 动态摘要
└── learning_log.md        # 学习日志
```

**关键功能**：
```python
class MemoryBankManager:
    async def initialize(self, project_id: str):
        """初始化记忆库"""
        
    async def read_context(self) -> Dict:
        """读取当前上下文"""
        
    async def update_summary(self, new_content: str):
        """更新动态摘要"""
        
    async def log_learning(self, entry: Dict):
        """记录学习事件"""
```

**验收标准**：
- Memory Bank文件正确创建和更新
- 摘要功能正常工作
- 支持并发访问

#### Day 3: 文档处理与基础分块
**目标**：实现文档处理管道（不含S2算法）

**任务清单**：
- [ ] 实现多格式文档加载（PDF、TXT、MD）
- [ ] 使用标准分块算法（RecursiveCharacterTextSplitter）
- [ ] 创建文档元数据管理
- [ ] 集成向量化流程

**简化的处理流程**：
```python
class SimpleDocumentProcessor:
    async def process_document(self, doc_path: str):
        # 1. 加载文档
        content = self.load_document(doc_path)
        
        # 2. 标准分块（1000 tokens，200重叠）
        chunks = self.split_text(content)
        
        # 3. 生成嵌入
        embeddings = await self.embed_chunks(chunks)
        
        # 4. 存储到向量数据库
        await self.store_vectors(chunks, embeddings)
        
        # 5. 更新Memory Bank
        await self.update_memory_bank(doc_metadata)
```

**验收标准**：
- 支持主流文档格式
- 分块质量合理
- 向量存储成功

#### Day 4: 三阶段混合检索
**目标**：实现核心检索功能

**任务清单**：
- [ ] 实现向量搜索（Qdrant）
- [ ] 实现基础图搜索（Neo4j）
- [ ] 实现Memory Bank搜索
- [ ] 开发结果融合算法

**三阶段流程**：
```python
class ThreeStageRetriever:
    async def retrieve(self, query: str) -> Dict:
        # Stage 1: 向量搜索获取入口点
        vector_results = await self.vector_search(
            query, top_k=10
        )
        
        # Stage 2: 图遍历扩展（1跳）
        graph_context = await self.graph_expand(
            entry_points=vector_results,
            max_hops=1  # MVP限制为1跳
        )
        
        # Stage 3: Memory Bank增强
        memory_context = await self.memory_search(
            query, 
            current_context=graph_context
        )
        
        # 融合结果
        return self.fuse_results(
            vector_results,
            graph_context,
            memory_context
        )
```

**验收标准**：
- 三个阶段都能返回结果
- 融合算法合理
- 响应时间 < 500ms

#### Day 5: 认知循环集成与测试
**目标**：集成所有组件，完成MVP

**任务清单**：
- [ ] 集成认知循环工作流
- [ ] 实现简单的知识更新机制
- [ ] 开发基础API接口
- [ ] 执行集成测试
- [ ] 准备演示Demo

**认知循环实现**：
```python
def build_mvp_cognitive_workflow():
    workflow = StateGraph(MVPCognitiveState)
    
    # 核心节点
    workflow.add_node("perceive", perceive_input)
    workflow.add_node("process", process_content)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("reason", basic_reasoning)
    workflow.add_node("update_memory", update_memories)
    
    # 连接
    workflow.add_edge("perceive", "process")
    workflow.add_edge("process", "retrieve")
    workflow.add_edge("retrieve", "reason")
    workflow.add_edge("reason", "update_memory")
    workflow.add_edge("update_memory", "perceive")  # 循环
    
    return workflow.compile(checkpointer=checkpointer)
```

**验收标准**：
- 端到端流程通过
- 能处理基础查询
- 能更新Memory Bank
- Demo可演示

### MVP功能边界

#### 包含 ✅
1. **基础认知循环**
   - 文档处理和存储
   - 查询和检索
   - 简单推理
   - 记忆更新

2. **三阶段检索**
   - 向量搜索
   - 1跳图扩展
   - Memory Bank增强

3. **Memory Bank**
   - 文件持久化
   - 动态摘要
   - 学习日志

#### 不包含 ❌
1. **高级功能**
   - S2语义分块
   - GNN链接预测
   - 假设生成
   - 元认知评估

2. **复杂特性**
   - 多跳图遍历
   - 知识冲突解决
   - 自动学习规划
   - 置信度管理

## Phase 2: 高级功能（预计3-4周）

### 功能列表
1. **S2语义分块**
   - 实现谱聚类算法
   - 支持超长文档

2. **GNN主动学习**
   - 知识图谱嵌入
   - 链接预测模型
   - 假设生成器

3. **元认知引擎**
   - 知识置信度评估
   - 学习效果分析
   - 策略自适应

4. **高级特性**
   - 四层完整记忆模型
   - 知识演化机制
   - 冲突解决策略

## 风险控制措施

### 1. 技术风险
- **简化算法**：使用成熟的标准算法
- **限制规模**：限制记忆大小和图遍历深度
- **降级方案**：每个组件都有简单备选

### 2. 进度风险
- **每日验收**：每天完成可演示功能
- **增量交付**：功能逐步添加
- **灵活调整**：根据进度调整范围

### 3. 质量风险
- **测试驱动**：先写测试再实现
- **代码审查**：关键代码peer review
- **监控指标**：性能和错误监控

## 成功标准

### MVP成功指标
1. **功能完整性**
   - [ ] 能处理PDF/TXT文档
   - [ ] 能回答基础问题
   - [ ] 能更新记忆库
   - [ ] 能展示学习过程

2. **性能指标**
   - [ ] 文档处理 > 1K tokens/秒
   - [ ] 查询响应 < 500ms
   - [ ] 内存使用 < 2GB

3. **可用性**
   - [ ] API文档完整
   - [ ] 有演示Demo
   - [ ] 错误处理完善

## 项目结构

```
dpa/
├── src/
│   ├── core/
│   │   ├── state.py          # MVP状态定义
│   │   ├── workflow.py       # 认知循环
│   │   └── memory_bank.py    # Memory Bank
│   ├── processing/
│   │   ├── loader.py         # 文档加载
│   │   └── chunker.py        # 标准分块
│   ├── retrieval/
│   │   ├── vector_search.py  # 向量检索
│   │   ├── graph_search.py   # 图检索
│   │   └── fusion.py         # 结果融合
│   └── api/
│       └── main.py           # FastAPI接口
├── tests/
│   ├── test_memory_bank.py
│   ├── test_retrieval.py
│   └── test_workflow.py
├── memory-bank/              # 记忆库文件
└── scripts/
    ├── setup_mvp.py         # MVP环境设置
    └── demo.py              # 演示脚本
```

## 每日进度跟踪

### Day 1 Checklist
- [ ] 环境搭建完成
- [ ] 状态定义完成
- [ ] 基础工作流运行
- [ ] 单元测试通过

### Day 2 Checklist
- [ ] Memory Bank创建
- [ ] RVUE循环实现
- [ ] 摘要功能完成
- [ ] 文件操作测试通过

### Day 3 Checklist
- [ ] 文档加载器完成
- [ ] 分块功能实现
- [ ] 向量化集成
- [ ] 处理性能达标

### Day 4 Checklist
- [ ] 三阶段检索实现
- [ ] 结果融合完成
- [ ] 性能优化
- [ ] 集成测试通过

### Day 5 Checklist
- [ ] 完整流程集成
- [ ] API接口完成
- [ ] Demo准备就绪
- [ ] 文档更新完成

## 总结

通过将项目分为MVP和Advanced两个阶段，我们可以：
1. **快速交付价值**：5天内交付可用系统
2. **控制技术风险**：避免过早引入复杂技术
3. **验证核心概念**：确保认知循环可行
4. **保留扩展性**：为Phase 2预留接口

MVP完成后，我们将有一个功能完整的认知记忆系统，能够处理文档、回答问题并持续学习，为后续的高级功能奠定坚实基础。