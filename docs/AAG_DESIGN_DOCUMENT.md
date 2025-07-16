# DPA-AAG: 基于分析增强生成的智能文档处理系统设计文档

## 1. 项目概述

### 1.1 愿景声明
DPA-AAG（Document Processing Agent with Analysis-Augmented Generation）旨在构建一个超越传统RAG系统的**认知增强平台**。系统不仅支持文档的存储和检索，更是一个能够深度理解、批判性分析和创造性输出的智能伙伴。

### 1.2 核心理念
- **分析增强生成（AAG）**：在生成答案前，引入结构化的深度分析步骤
- **玻璃箱协驾（Glass Box Co-pilot）**：让AI的分析过程可视化、可控制、可追溯
- **渐进式认知增强**：从简单的文档理解到复杂的知识创造，逐步提升用户的认知能力

### 1.3 与现有系统的关系
基于当前已实现的文档管理系统，AAG将作为核心智能引擎，增强现有功能：
- 保留现有的文档上传、摘要、索引功能
- 扩展深度分析能力，从单一的"分析"升级为多维度、多层次的智能分析体系
- 整合到现有的前后端架构中，无需重构基础设施

## 2. 系统架构

### 2.1 总体架构图
```
┌─────────────────────────────────────────────────────────────┐
│                     前端展示层 (Next.js)                      │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌─────────────┐  │
│  │文档管理│  │分析工作台│  │玻璃箱视图│  │知识产品输出│  │
│  └─────────┘  └─────────┘  └──────────┘  └─────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ WebSocket/SSE
┌─────────────────────────┴───────────────────────────────────┐
│                    API网关层 (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │文档路由  │  │分析路由  │  │实时通信  │  │输出路由   │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                  AAG智能引擎层 (LangGraph)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │规划代理  │  │分析代理  │  │综合代理  │  │输出代理   │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
│                    步进式执行引擎                             │
│                 (Stepped Execution Engine)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                     数据持久层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │PostgreSQL│  │Qdrant    │  │Neo4j     │  │MinIO      │  │
│  │(元数据)  │  │(向量)    │  │(图谱)    │  │(文档/物料)│  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明

#### 2.2.1 规划代理（Planner Agent）
- **职责**：接收用户的高层次分析需求，分解为结构化的任务计划
- **实现**：基于LangChain的Agent，使用专门的规划提示词
- **输出**：JSON格式的任务列表，包含步骤、依赖关系和预估耗时

#### 2.2.2 步进式执行引擎（Stepped Execution Engine）
- **职责**：管理任务的执行流程，支持暂停、恢复和干预
- **实现**：基于LangGraph构建有状态的执行图
- **特性**：
  - 支持同步和异步两种执行模式
  - 实时状态更新和进度追踪
  - 中间结果的持久化存储

#### 2.2.3 分析物料库（Analysis Artifact Store）
- **职责**：存储和管理所有分析过程产生的中间结果
- **结构**：
  ```json
  {
    "artifact_id": "uuid",
    "document_id": "doc_uuid",
    "analysis_type": "summary|outline|knowledge_graph|...",
    "version": 1,
    "created_at": "timestamp",
    "updated_at": "timestamp",
    "metadata": {
      "depth_level": "basic|standard|deep|expert|comprehensive",
      "execution_time": 120,
      "token_usage": 5000,
      "user_corrections": []
    },
    "content": {
      // 具体的分析结果
    }
  }
  ```

#### 2.2.4 玻璃箱视图（Glass Box View）
- **职责**：实时展示AI的分析过程和思考链路
- **功能**：
  - 步骤列表和执行状态
  - 实时日志流
  - 中间结果预览
  - 干预控制面板

## 3. 文档处理生命周期

### 3.1 处理阶段概览
```
文档上传 → 快速略读 → 智能索引 → 深度分析 → 知识整合 → 成果输出
   ↓          ↓          ↓          ↓          ↓          ↓
[原始文档] [Skim摘要] [向量索引] [分析物料] [综合报告] [知识产品]
```

### 3.2 详细阶段说明

#### 阶段1：文档上传与预处理
- 保持现有功能不变
- 增强元数据提取能力
- 支持更多文档格式

#### 阶段2：快速略读（Skimming）
```python
# 略读提示词模板
SKIM_PROMPT = """
请快速浏览这份文档，提供以下信息：
1. 文档类型识别（学术论文/技术报告/商业文档等）
2. 核心主题（50字以内）
3. 关键要点（3-5个要点）
4. 目标受众
5. 文档质量初评（高/中/低）
6. 建议的深度分析方向

输出格式：JSON
"""
```

#### 阶段3：智能索引
- **多策略分块**：
  - 语义分块（Semantic Chunking）
  - 结构化分块（按章节、段落）
  - 滑动窗口分块（重叠上下文）
- **层次化索引**：
  - 文档级摘要
  - 章节级摘要
  - 段落级内容
  - 关键句提取

#### 阶段4：深度分析（核心AAG功能）

##### 4.1 宏观理解模块
```python
# 渐进式摘要
PROGRESSIVE_SUMMARY = {
    "level_1": "用50字概括文档核心价值",
    "level_2": "用200字总结主要论点和结论",
    "level_3": "用500字详述论证结构和关键发现"
}

# 多维大纲提取
MULTI_DIM_OUTLINE = {
    "logical": "章节层级和论述流程",
    "thematic": "核心概念及关系网络",
    "temporal": "时序信息和发展脉络",
    "causal": "因果关系链条"
}
```

##### 4.2 深度探索模块
```python
# 分层提问框架
LAYERED_QUESTIONS = {
    "基础层": ["概念定义", "基本事实"],
    "分析层": ["逻辑关系", "论证分析"],
    "综合层": ["跨章节整合", "观点归纳"],
    "创新层": ["应用扩展", "新领域探索"]
}

# 证据链追踪
EVIDENCE_CHAIN_ANALYSIS = {
    "claim_extraction": "提取核心论点",
    "evidence_mapping": "映射支撑证据",
    "strength_evaluation": "评估证据强度",
    "gap_identification": "识别论证缺口"
}
```

##### 4.3 批判性分析模块
```python
# 多视角审视
CRITICAL_PERSPECTIVES = {
    "methodology": "研究方法严谨性",
    "stakeholder": "利益相关者分析",
    "temporal": "时效性评估",
    "interdisciplinary": "跨学科视角"
}

# 假设检验
ASSUMPTION_TESTING = {
    "explicit": "显性假设识别",
    "implicit": "隐性假设挖掘",
    "boundary": "适用边界分析",
    "sensitivity": "敏感性测试"
}
```

#### 阶段5：知识整合
- 主题综合报告生成
- 跨文档比较分析
- 知识图谱融合
- 洞察提炼与总结

#### 阶段6：成果输出
- **多格式输出**：
  - 执行摘要（1页纸）
  - 技术报告（详细版）
  - 演示材料（PPT大纲）
  - 行动方案（具体建议）
- **知识产品创造**：
  - 检查清单
  - 决策树
  - 最佳实践指南
  - 培训材料

## 4. 技术实现方案

### 4.1 基于LangGraph的任务编排
```python
from langgraph.graph import StateGraph, State
from typing import TypedDict, List, Dict, Any

class AnalysisState(TypedDict):
    document_id: str
    current_step: int
    total_steps: int
    artifacts: List[Dict[str, Any]]
    user_interventions: List[Dict[str, Any]]
    status: str  # planning|executing|paused|completed|failed

# 构建分析图
def build_analysis_graph():
    graph = StateGraph(AnalysisState)
    
    # 添加节点
    graph.add_node("planner", planning_node)
    graph.add_node("skimmer", skimming_node)
    graph.add_node("outliner", outline_extraction_node)
    graph.add_node("analyzer", deep_analysis_node)
    graph.add_node("synthesizer", synthesis_node)
    
    # 添加边和条件
    graph.add_edge("planner", "skimmer")
    graph.add_conditional_edges(
        "skimmer",
        should_continue_analysis,
        {
            True: "outliner",
            False: "synthesizer"
        }
    )
    
    # 支持人工干预的检查点
    graph.add_checkpoint("outliner", allow_intervention=True)
    graph.add_checkpoint("analyzer", allow_intervention=True)
    
    return graph.compile()
```

### 4.2 实时通信架构
```python
# WebSocket管理器
class AnalysisWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.analysis_sessions: Dict[str, AnalysisState] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    async def send_progress(self, session_id: str, progress: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json({
                "type": "progress",
                "data": progress
            })
    
    async def send_artifact(self, session_id: str, artifact: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json({
                "type": "artifact",
                "data": artifact
            })
```

### 4.3 异步任务处理
```python
from celery import Celery
from typing import Optional

celery_app = Celery('dpa_aag')

@celery_app.task(bind=True)
def execute_analysis_step(
    self,
    step_id: str,
    document_id: str,
    step_config: dict,
    previous_artifacts: Optional[List[dict]] = None
):
    """执行单个分析步骤"""
    try:
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'current': step_id, 'status': 'executing'}
        )
        
        # 执行分析
        result = analysis_engine.execute_step(
            document_id=document_id,
            step_type=step_config['type'],
            parameters=step_config['parameters'],
            context=previous_artifacts
        )
        
        # 保存结果到物料库
        artifact = artifact_store.save(
            document_id=document_id,
            analysis_type=step_config['type'],
            content=result
        )
        
        return {
            'status': 'completed',
            'artifact_id': artifact.id,
            'next_step': step_config.get('next_step')
        }
        
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'exc': str(e)}
        )
        raise
```

### 4.4 元数据Schema v2.0
```sql
-- 文档元数据表（扩展版）
CREATE TABLE document_metadata_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    version INTEGER NOT NULL DEFAULT 1,
    
    -- 基础信息
    skim_summary JSONB,
    document_type VARCHAR(50),
    quality_score FLOAT,
    target_audience TEXT[],
    
    -- 分析状态
    analysis_status VARCHAR(50) DEFAULT 'pending',
    analysis_depth VARCHAR(50) DEFAULT 'basic',
    last_analysis_at TIMESTAMP,
    
    -- 分析计划
    analysis_plan JSONB,
    completed_steps TEXT[],
    
    -- 统计信息
    total_analyses INTEGER DEFAULT 0,
    total_artifacts INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    
    -- 扩展字段
    ext JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(document_id, version)
);

-- 分析物料表
CREATE TABLE analysis_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    analysis_type VARCHAR(100) NOT NULL,
    depth_level VARCHAR(50),
    
    -- 内容
    content JSONB NOT NULL,
    summary TEXT,
    
    -- 执行信息
    execution_time_seconds INTEGER,
    token_usage INTEGER,
    model_used VARCHAR(100),
    
    -- 用户干预
    user_corrections JSONB DEFAULT '[]',
    is_user_approved BOOLEAN DEFAULT FALSE,
    
    -- 版本控制
    version INTEGER NOT NULL DEFAULT 1,
    parent_artifact_id UUID REFERENCES analysis_artifacts(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    INDEX idx_document_type (document_id, analysis_type),
    INDEX idx_created_at (created_at DESC)
);

-- 分析任务表
CREATE TABLE analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    
    -- 任务信息
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    
    -- 执行计划
    execution_plan JSONB NOT NULL,
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER NOT NULL,
    
    -- 执行状态
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- 结果引用
    artifact_ids UUID[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    INDEX idx_status (status, priority DESC)
);
```

## 5. API设计

### 5.1 分析任务API
```python
# 创建分析任务
POST /api/v1/documents/{document_id}/analyze
{
    "analysis_type": "comprehensive",  # basic|standard|deep|expert|comprehensive
    "analysis_goals": ["理解核心论点", "评估方法论", "提取行动建议"],
    "output_formats": ["executive_summary", "technical_report"],
    "execution_mode": "stepped",  # stepped|async
    "allow_intervention": true
}

# 获取分析计划
GET /api/v1/analysis/{task_id}/plan

# 控制分析执行
POST /api/v1/analysis/{task_id}/control
{
    "action": "pause|resume|cancel|skip_step",
    "step_id": "optional_step_id"
}

# 提交用户干预
POST /api/v1/analysis/{task_id}/intervene
{
    "step_id": "current_step_id",
    "intervention_type": "correction|additional_context|parameter_adjustment",
    "content": {
        // 具体的干预内容
    }
}

# 获取分析物料
GET /api/v1/documents/{document_id}/artifacts
?type=summary,outline,knowledge_graph
&depth=deep
&version=latest
```

### 5.2 实时通信API
```python
# WebSocket连接
WS /api/v1/ws/analysis/{task_id}

# 消息格式
{
    "type": "progress|log|artifact|intervention_request",
    "timestamp": "ISO8601",
    "data": {
        // 具体内容
    }
}
```

## 6. 前端界面设计

### 6.1 分析工作台
```typescript
// 分析工作台组件结构
interface AnalysisWorkbenchProps {
    document: Document;
    onAnalysisComplete: (artifacts: AnalysisArtifact[]) => void;
}

const AnalysisWorkbench: React.FC<AnalysisWorkbenchProps> = ({
    document,
    onAnalysisComplete
}) => {
    return (
        <div className="analysis-workbench">
            {/* 左侧：分析控制面板 */}
            <AnalysisControlPanel 
                onStartAnalysis={handleStartAnalysis}
                analysisOptions={analysisOptions}
            />
            
            {/* 中间：玻璃箱视图 */}
            <GlassBoxView
                currentStep={currentStep}
                logs={executionLogs}
                onIntervene={handleIntervention}
            />
            
            {/* 右侧：物料预览 */}
            <ArtifactPreview
                artifacts={generatedArtifacts}
                onEdit={handleArtifactEdit}
            />
        </div>
    );
};
```

### 6.2 玻璃箱视图组件
```typescript
interface GlassBoxViewProps {
    taskId: string;
    allowIntervention: boolean;
}

const GlassBoxView: React.FC<GlassBoxViewProps> = ({
    taskId,
    allowIntervention
}) => {
    // WebSocket连接管理
    const { logs, currentStep, artifacts } = useAnalysisWebSocket(taskId);
    
    return (
        <div className="glass-box-view">
            {/* 步骤进度条 */}
            <StepProgressBar 
                steps={analysisSteps}
                currentStep={currentStep}
            />
            
            {/* 实时日志流 */}
            <LogStream logs={logs} />
            
            {/* 干预控制 */}
            {allowIntervention && (
                <InterventionControls
                    onPause={handlePause}
                    onResume={handleResume}
                    onModify={handleModify}
                />
            )}
        </div>
    );
};
```

## 7. 性能与成本优化

### 7.1 缓存策略
- **物料缓存**：相同文档的相同分析类型结果缓存
- **模板缓存**：常用提示词模板预编译
- **向量缓存**：热点文档的向量表示缓存

### 7.2 成本控制
```python
# 成本预估器
class CostEstimator:
    def estimate_analysis_cost(
        self,
        document_length: int,
        analysis_depth: str,
        output_formats: List[str]
    ) -> Dict[str, float]:
        base_tokens = self.estimate_tokens(document_length)
        depth_multiplier = self.DEPTH_MULTIPLIERS[analysis_depth]
        
        estimated_tokens = base_tokens * depth_multiplier
        estimated_cost = (estimated_tokens / 1000) * self.PRICE_PER_1K_TOKENS
        estimated_time = estimated_tokens / self.TOKENS_PER_SECOND
        
        return {
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": estimated_cost,
            "estimated_time_seconds": estimated_time
        }
```

### 7.3 并发控制
- 任务队列优先级管理
- 资源池限制
- 熔断机制

## 8. 监控与运维

### 8.1 关键指标
- **性能指标**：
  - 分析任务完成率
  - 平均执行时间
  - 用户干预频率
- **质量指标**：
  - 用户满意度评分
  - 物料复用率
  - 分析准确性
- **成本指标**：
  - Token使用量
  - API调用成本
  - 存储成本

### 8.2 日志与追踪
```python
# 分析追踪
@trace_analysis
async def execute_deep_analysis(
    document_id: str,
    analysis_config: AnalysisConfig
) -> AnalysisResult:
    with tracer.start_span("deep_analysis") as span:
        span.set_attribute("document_id", document_id)
        span.set_attribute("analysis_depth", analysis_config.depth)
        
        # 执行分析...
        
        span.set_attribute("artifacts_generated", len(artifacts))
        span.set_attribute("total_tokens", total_tokens)
```

## 9. 安全与合规

### 9.1 数据安全
- 敏感信息脱敏
- 访问控制（基于项目和用户）
- 审计日志

### 9.2 知识产权保护
- 分析结果的版权标注
- 引用来源追踪
- 跨文档分析的权限控制

## 10. 未来扩展

### 10.1 智能化增强
- 基于用户反馈的模型微调
- 个性化分析模板学习
- 自适应分析深度调整

### 10.2 协作功能
- 多用户协同分析
- 分析结果的评论和讨论
- 知识图谱的协作编辑

### 10.3 生态系统集成
- 第三方知识库接入
- 外部API集成（学术数据库、专业工具）
- 插件市场（自定义分析模块）

## 附录：核心提示词模板

### A.1 规划代理提示词
```python
PLANNER_PROMPT = """
你是一位专业的研究分析规划师。用户想要对以下文档进行深度分析：

文档信息：
- 标题：{document_title}
- 类型：{document_type}
- 长度：{document_length}
- 初步摘要：{skim_summary}

用户目标：{user_goals}

请制定一个详细的分析计划，包括：
1. 分析步骤列表（每步包含：名称、目的、预计耗时、所需前置步骤）
2. 关键决策点（需要用户确认的环节）
3. 预期产出物

输出格式：
{
    "analysis_plan": {
        "total_steps": 数字,
        "estimated_time": "预计总耗时",
        "steps": [
            {
                "id": "step_1",
                "name": "步骤名称",
                "purpose": "步骤目的",
                "estimated_time": "预计耗时",
                "dependencies": ["前置步骤ID"],
                "requires_user_input": true/false
            }
        ],
        "expected_artifacts": ["产出物列表"]
    }
}
"""
```

### A.2 深度分析提示词集
```python
# 证据链追踪
EVIDENCE_CHAIN_PROMPT = """
对文档中的核心论点'{claim}'进行证据链追踪：

1. 识别所有支撑该论点的证据
2. 评估每个证据的类型（数据/引用/案例/逻辑推理）
3. 判断证据强度（强/中/弱）
4. 标注证据来源和可信度
5. 识别论证中的逻辑跳跃或薄弱环节
6. 提出可能的反驳论点

输出结构化的证据链分析报告。
"""

# 多视角批判性分析
CRITICAL_ANALYSIS_PROMPT = """
从以下视角对文档进行批判性分析：

1. 方法论视角：
   - 研究方法的严谨性如何？
   - 样本选择是否合理？
   - 数据分析是否恰当？

2. 利益相关者视角：
   - 谁会从这个观点中受益？
   - 谁的声音可能被忽略了？
   - 是否存在潜在的偏见？

3. 时代背景视角：
   - 哪些结论可能已经过时？
   - 当前环境下是否仍然适用？

4. 跨学科视角：
   - 其他领域会如何看待这些观点？
   - 是否有相关领域的反例？

提供平衡、客观的批判性评估。
"""
```

## 结语

DPA-AAG系统通过引入分析增强生成（AAG）和玻璃箱协驾原则，将传统的文档处理系统升级为真正的认知增强平台。系统不仅能够帮助用户快速理解文档，更能够进行深度分析、批判性思考和创造性输出，成为知识工作者的智能伙伴。

通过分阶段实施和模块化设计，我们可以在保持系统稳定性的同时，逐步增强其智能化水平，最终实现从"信息检索"到"智能功放"的飞跃。