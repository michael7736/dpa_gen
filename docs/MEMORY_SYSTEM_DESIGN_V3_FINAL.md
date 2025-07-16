# DPA记忆系统设计文档 V3.0 - 融合版

## 概述

本版本融合了LangGraph深度集成方案和Gemini认知架构理论，构建了一个真正具备"学习如何学习"能力的智能研究助手。系统基于严谨的认知科学理论，采用PostgreSQL和Neo4j作为核心存储，实现了从被动检索到主动探究的跃迁。

## 1. 理论基础：认知架构设计

### 1.1 从RAG到认知实体的进化

传统RAG系统是被动的、无状态的。我们的目标是构建一个具有**记忆（Memory）、规划（Planning）和行动（Action）**三大支柱的认知实体。

```mermaid
graph LR
    A[传统RAG] --> B[记忆增强RAG]
    B --> C[认知架构]
    
    subgraph "认知实体"
        D[记忆系统]
        E[规划系统]
        F[行动系统]
        D <--> E
        E <--> F
        F <--> D
    end
    
    C --> D
```

### 1.2 多层记忆模型（融合人类认知科学）

基于认知科学理论，我们设计了一个更加完善的四层记忆架构：

```python
class CognitiveMemoryModel:
    """基于认知科学的记忆模型"""
    
    # 1. 感觉记忆（Sensory Memory）- 极短期
    sensory_buffer: Dict[str, Any]  # 原始输入缓冲，<1秒
    
    # 2. 工作记忆（Working Memory）- 短期
    working_memory: Dict[str, Any]   # 当前任务上下文，7±2项
    attention_focus: List[str]       # 注意力焦点
    
    # 3. 情节记忆（Episodic Memory）- 中期
    episodic_memory: List[Episode]   # 具体事件和经历
    temporal_context: Dict           # 时间上下文
    
    # 4. 语义记忆（Semantic Memory）- 长期
    semantic_memory: KnowledgeGraph  # 概念和事实
    procedural_memory: Dict          # 技能和方法
```

### 1.3 核心认知循环

```python
# 主认知循环
COGNITIVE_CYCLE = """
感知(Perceive) -> 注意(Attend) -> 编码(Encode) -> 
存储(Store) -> 检索(Retrieve) -> 推理(Reason) -> 
规划(Plan) -> 执行(Execute) -> 反思(Reflect)
"""
```

## 2. 增强的LangGraph状态设计

### 2.1 全面的状态定义

```python
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import MessagesState, add_messages
from datetime import datetime

class DPACognitiveState(TypedDict):
    """DPA认知系统的完整状态定义"""
    
    # === 对话与交互 ===
    messages: Annotated[List[BaseMessage], add_messages]
    thread_id: str
    user_id: str
    project_id: str
    
    # === 记忆层次 ===
    sensory_buffer: Dict[str, Any]      # 感觉缓冲
    working_memory: Dict[str, Any]      # 工作记忆（限制大小）
    attention_weights: Dict[str, float]  # 注意力权重
    episodic_memory: List[Dict]         # 情节记忆
    semantic_memory: Dict[str, Any]     # 语义记忆引用
    
    # === 文档处理 ===
    current_documents: List[Dict]
    document_hierarchy: Dict[str, Any]   # 三层结构
    s2_chunks: List[Dict]               # S2语义分块
    extracted_graph_documents: List[Any] # 待入图谱的数据
    
    # === 知识图谱 ===
    knowledge_graph_snapshot: Dict       # 当前图谱快照
    concept_embeddings: Dict            # 概念向量
    relation_weights: Dict              # 关系权重
    graph_metrics: Dict                 # 图谱统计指标
    
    # === 学习与规划 ===
    knowledge_gaps: List[Dict]          # 识别的知识盲点
    learning_hypotheses: List[Dict]     # GNN生成的假设
    learning_plan: Dict                 # 学习计划
    research_progress: Dict             # 研究进度
    
    # === 记忆库（Memory Bank）===
    memory_bank_path: str               # 记忆库路径
    memory_bank_state: Dict             # 记忆库状态快照
    
    # === 元认知 ===
    confidence_scores: Dict             # 知识置信度
    uncertainty_map: Dict               # 不确定性地图
    self_evaluation: Dict               # 自我评估结果
    
    # === 控制流 ===
    error_log: List[Dict]               # 错误日志（含时间戳）
    recursion_depth: int                # 递归深度控制
    execution_history: List[str]        # 执行历史
    checkpoint_metadata: Dict           # 检查点元数据
```

### 2.2 状态管理最佳实践

```python
class StateManager:
    """状态管理器 - 确保状态一致性和约束"""
    
    # 工作记忆大小限制（认知科学：7±2）
    WORKING_MEMORY_LIMIT = 9
    
    # 注意力焦点限制
    ATTENTION_FOCUS_LIMIT = 3
    
    # 递归深度限制
    MAX_RECURSION_DEPTH = 5
    
    @staticmethod
    def validate_state(state: DPACognitiveState) -> bool:
        """验证状态约束"""
        # 检查工作记忆大小
        if len(state["working_memory"]) > StateManager.WORKING_MEMORY_LIMIT:
            # 触发记忆整理
            return False
            
        # 检查递归深度
        if state["recursion_depth"] > StateManager.MAX_RECURSION_DEPTH:
            raise RecursionError("Maximum recursion depth exceeded")
            
        return True
    
    @staticmethod
    def compress_working_memory(state: DPACognitiveState) -> DPACognitiveState:
        """压缩工作记忆 - 基于注意力权重"""
        items = list(state["working_memory"].items())
        weights = state["attention_weights"]
        
        # 按注意力权重排序
        sorted_items = sorted(
            items, 
            key=lambda x: weights.get(x[0], 0), 
            reverse=True
        )
        
        # 保留前N个
        state["working_memory"] = dict(
            sorted_items[:StateManager.WORKING_MEMORY_LIMIT]
        )
        
        # 将其余转入情节记忆
        for key, value in sorted_items[StateManager.WORKING_MEMORY_LIMIT:]:
            state["episodic_memory"].append({
                "key": key,
                "value": value,
                "timestamp": datetime.now(),
                "attention_weight": weights.get(key, 0)
            })
        
        return state
```

## 3. 记忆库（Memory Bank）子系统

### 3.1 记忆库架构

受Cline启发，我们实现一个基于文件系统的持久化记忆层：

```yaml
memory-bank/
├── metadata.json              # 记忆库元数据
├── source_documents.md        # 源文档列表
├── key_concepts.md           # 关键概念和实体
├── knowledge_graph/          # 知识图谱可视化
│   ├── graph_snapshot.json   # 图谱快照
│   └── visualizations/       # Mermaid图表
├── dynamic_summary.md        # 动态摘要
├── learning_journal/         # 学习日志
│   ├── 2024-01-15.md        # 按日期的学习记录
│   └── insights.md          # 关键洞察
├── hypotheses/              # 假设和验证
│   ├── active.md           # 活跃假设
│   ├── verified.md         # 已验证
│   └── rejected.md         # 已否定
├── agent_rules.md          # 智能体规则
└── research_plans/         # 研究计划
    ├── current_plan.md     # 当前计划
    └── completed/          # 已完成计划
```

### 3.2 记忆库生命周期管理

```python
class MemoryBankManager:
    """记忆库管理器"""
    
    def __init__(self, base_path: str = "./memory-bank"):
        self.base_path = Path(base_path)
        self.ensure_structure()
    
    async def read_verify_update_execute(self, state: DPACognitiveState):
        """RVUE生命周期"""
        
        # 1. Read - 读取记忆库
        memory_content = await self.read_all_memories()
        state["memory_bank_state"] = memory_content
        
        # 2. Verify - 验证一致性
        verification_result = await self.verify_consistency(
            memory_content, 
            state["knowledge_graph_snapshot"]
        )
        
        if not verification_result["is_consistent"]:
            # 3. Reconcile - 调和差异
            reconciled_state = await self.reconcile_differences(
                memory_content,
                state,
                verification_result["conflicts"]
            )
            state = reconciled_state
        
        # 4. Execute - 执行核心任务
        # (由其他节点完成)
        
        # 5. Update - 更新记忆库
        await self.update_memories(state)
        
        return state
    
    async def update_dynamic_summary(self, state: DPACognitiveState):
        """更新动态摘要 - 使用渐进式摘要技术"""
        
        current_summary = await self.read_file("dynamic_summary.md")
        new_insights = state.get("new_insights", [])
        
        # 使用LLM进行渐进式摘要
        updated_summary = await self.progressive_summarize(
            current_summary,
            new_insights,
            max_length=2000
        )
        
        # 添加时间戳和版本
        versioned_summary = f"""# 动态知识摘要
        
最后更新: {datetime.now().isoformat()}
版本: {state.get('summary_version', 1) + 1}

{updated_summary}

---
### 最新洞察
{self._format_insights(new_insights[-5:])}
"""
        
        await self.write_file("dynamic_summary.md", versioned_summary)
```

### 3.3 结构化概念管理

```python
async def update_key_concepts(self, extracted_entities: List[Dict]):
    """更新关键概念文档"""
    
    concepts_by_type = defaultdict(list)
    for entity in extracted_entities:
        concepts_by_type[entity["type"]].append(entity)
    
    # 生成Mermaid图
    mermaid_graph = self.generate_concept_graph(extracted_entities)
    
    content = f"""# 关键概念和实体

## 概念分类

"""
    
    for entity_type, entities in concepts_by_type.items():
        content += f"\n### {entity_type}\n"
        for entity in entities[:20]:  # 限制每类显示数量
            confidence = entity.get("confidence", 0.5)
            content += f"- **{entity['name']}** (置信度: {confidence:.2f})\n"
            if entity.get("definition"):
                content += f"  - {entity['definition']}\n"
    
    content += f"\n## 概念关系图\n\n```mermaid\n{mermaid_graph}\n```"
    
    await self.write_file("key_concepts.md", content)
```

## 4. 混合检索增强（KG-RAG优化）

### 4.1 三阶段混合检索流程

```python
class EnhancedHybridRetriever:
    """增强的混合检索器 - 融合向量、图谱和记忆库"""
    
    async def hybrid_retrieve(
        self, 
        query: str, 
        state: DPACognitiveState
    ) -> Dict[str, Any]:
        """三阶段混合检索"""
        
        # Phase 1: 向量检索定位入口点
        entry_points = await self.vector_search_entry_points(
            query,
            top_k=10,
            collections=["concepts", "chunks", "summaries"]
        )
        
        # Phase 2: 图遍历扩展上下文
        expanded_context = await self.graph_traversal_expansion(
            entry_points,
            max_hops=2,
            relationship_weights=state["relation_weights"]
        )
        
        # Phase 3: 记忆库增强
        memory_enhanced = await self.memory_bank_augmentation(
            query,
            expanded_context,
            state["memory_bank_state"]
        )
        
        # 融合和重排序
        final_context = await self.fuse_and_rerank(
            vector_results=entry_points,
            graph_results=expanded_context,
            memory_results=memory_enhanced,
            fusion_weights={
                "vector": 0.4,
                "graph": 0.4,
                "memory": 0.2
            }
        )
        
        return {
            "context": final_context,
            "provenance": self._track_provenance(final_context),
            "confidence": self._calculate_confidence(final_context)
        }
    
    async def graph_traversal_expansion(
        self,
        entry_points: List[Dict],
        max_hops: int,
        relationship_weights: Dict
    ):
        """智能图遍历 - 基于关系权重的扩展"""
        
        # 构建加权遍历查询
        cypher_query = """
        UNWIND $entry_points as entry
        MATCH (start:Concept {id: entry.id})
        CALL apoc.path.expandConfig(start, {
            maxLevel: $max_hops,
            relationshipFilter: $rel_filter,
            uniqueness: 'NODE_GLOBAL',
            bfs: false
        })
        YIELD path
        WITH path, 
             reduce(score = 1.0, r in relationships(path) | 
                    score * coalesce($weights[type(r)], 0.5)) as path_score
        WHERE path_score > $min_score
        RETURN path, path_score
        ORDER BY path_score DESC
        LIMIT 50
        """
        
        # 执行查询
        paths = await self.neo4j.execute(
            cypher_query,
            entry_points=[{"id": ep["id"]} for ep in entry_points],
            max_hops=max_hops,
            rel_filter="|".join(relationship_weights.keys()),
            weights=relationship_weights,
            min_score=0.1
        )
        
        return self._paths_to_context(paths)
```

### 4.2 上下文污染防护

```python
class ContextValidator:
    """上下文验证器 - 防止上下文污染"""
    
    async def validate_context(
        self,
        context_chunks: List[Dict],
        query: str,
        threshold: float = 0.7
    ) -> List[Dict]:
        """验证上下文相关性"""
        
        validated_chunks = []
        
        for chunk in context_chunks:
            # 多维度验证
            scores = {
                "semantic": await self._semantic_relevance(chunk, query),
                "logical": await self._logical_coherence(chunk, query),
                "temporal": self._temporal_relevance(chunk),
                "source_reliability": self._source_reliability(chunk)
            }
            
            # 加权综合评分
            weighted_score = (
                scores["semantic"] * 0.4 +
                scores["logical"] * 0.3 +
                scores["temporal"] * 0.2 +
                scores["source_reliability"] * 0.1
            )
            
            if weighted_score >= threshold:
                chunk["validation_score"] = weighted_score
                chunk["validation_details"] = scores
                validated_chunks.append(chunk)
        
        return validated_chunks
```

## 5. 基于GNN的主动学习系统

### 5.1 知识图谱补全与假设生成

```python
class GNNKnowledgeCompletion:
    """基于图神经网络的知识补全"""
    
    def __init__(self):
        self.link_predictor = self._init_gnn_model()
        self.hypothesis_generator = HypothesisGenerator()
    
    def _init_gnn_model(self):
        """初始化GNN链接预测模型"""
        import torch
        import torch_geometric
        from torch_geometric.nn import GCNConv, global_mean_pool
        
        class LinkPredictionGNN(torch.nn.Module):
            def __init__(self, num_features, hidden_dim=128):
                super().__init__()
                self.conv1 = GCNConv(num_features, hidden_dim)
                self.conv2 = GCNConv(hidden_dim, hidden_dim)
                self.conv3 = GCNConv(hidden_dim, 64)
                self.classifier = torch.nn.Linear(128, 1)
                
            def forward(self, x, edge_index, edge_batch):
                # 图卷积层
                x = torch.relu(self.conv1(x, edge_index))
                x = torch.dropout(x, p=0.2, train=self.training)
                x = torch.relu(self.conv2(x, edge_index))
                x = self.conv3(x, edge_index)
                
                # 边预测
                row, col = edge_index
                edge_features = torch.cat([x[row], x[col]], dim=-1)
                return torch.sigmoid(self.classifier(edge_features))
        
        return LinkPredictionGNN(num_features=3072)  # embedding dimension
    
    async def predict_missing_links(
        self,
        knowledge_graph: Dict,
        confidence_threshold: float = 0.8
    ) -> List[Dict]:
        """预测缺失的链接"""
        
        # 将知识图谱转换为PyG格式
        graph_data = self._kg_to_pyg(knowledge_graph)
        
        # 执行链接预测
        with torch.no_grad():
            predictions = self.link_predictor(
                graph_data.x,
                graph_data.edge_index,
                graph_data.batch
            )
        
        # 筛选高置信度预测
        missing_links = []
        for idx, score in enumerate(predictions):
            if score > confidence_threshold:
                head, relation, tail = self._decode_prediction(idx, graph_data)
                missing_links.append({
                    "head": head,
                    "relation": relation,
                    "tail": tail,
                    "confidence": float(score),
                    "hypothesis": self._generate_hypothesis(head, relation, tail)
                })
        
        return missing_links
    
    def _generate_hypothesis(self, head: str, relation: str, tail: str) -> str:
        """将三元组转换为自然语言假设"""
        
        templates = {
            "RELATES_TO": f"是否 {head} 与 {tail} 存在关联？",
            "CAUSES": f"{head} 是否会导致或引起 {tail}？",
            "DEPENDS_ON": f"{tail} 是否依赖于 {head}？",
            "EVOLVES_TO": f"{head} 是否会演化或发展成 {tail}？",
            "CONFLICTS_WITH": f"{head} 与 {tail} 之间是否存在冲突？"
        }
        
        return templates.get(relation, f"{head} 是否通过'{relation}'关系连接到 {tail}？")
```

### 5.2 主动学习规划器

```python
class ActiveLearningPlanner:
    """主动学习规划器 - 基于不确定性和信息增益"""
    
    async def generate_learning_plan(
        self,
        state: DPACognitiveState
    ) -> Dict[str, Any]:
        """生成优化的学习计划"""
        
        # 1. 收集所有学习信号
        learning_signals = {
            "knowledge_gaps": state["knowledge_gaps"],
            "gnn_hypotheses": await self._get_gnn_predictions(state),
            "low_confidence_areas": self._identify_low_confidence(state),
            "user_questions": self._extract_unanswered_questions(state),
            "graph_anomalies": await self._detect_graph_anomalies(state)
        }
        
        # 2. 计算信息增益
        prioritized_items = []
        for signal_type, items in learning_signals.items():
            for item in items:
                info_gain = self._calculate_information_gain(
                    item,
                    state["knowledge_graph_snapshot"],
                    state["uncertainty_map"]
                )
                
                prioritized_items.append({
                    "item": item,
                    "type": signal_type,
                    "info_gain": info_gain,
                    "estimated_effort": self._estimate_effort(item),
                    "prerequisites": self._identify_prerequisites(item, state)
                })
        
        # 3. 优化学习序列（考虑依赖关系）
        optimal_sequence = self._optimize_learning_sequence(
            prioritized_items,
            max_items=10,
            time_budget=3600  # 1小时
        )
        
        # 4. 生成具体的学习任务
        learning_tasks = []
        for item in optimal_sequence:
            task = {
                "id": str(uuid.uuid4()),
                "type": item["type"],
                "description": self._generate_task_description(item),
                "actions": self._generate_task_actions(item),
                "success_criteria": self._define_success_criteria(item),
                "estimated_duration": item["estimated_effort"],
                "dependencies": item["prerequisites"]
            }
            learning_tasks.append(task)
        
        return {
            "plan_id": str(uuid.uuid4()),
            "created_at": datetime.now(),
            "tasks": learning_tasks,
            "total_duration": sum(t["estimated_duration"] for t in learning_tasks),
            "expected_info_gain": sum(item["info_gain"] for item in optimal_sequence),
            "execution_strategy": self._determine_execution_strategy(learning_tasks)
        }
    
    def _calculate_information_gain(
        self,
        item: Dict,
        knowledge_graph: Dict,
        uncertainty_map: Dict
    ) -> float:
        """计算学习项目的预期信息增益"""
        
        # 基于香农熵的信息增益计算
        current_entropy = self._calculate_entropy(
            knowledge_graph,
            uncertainty_map
        )
        
        # 模拟学习该项目后的熵减少
        simulated_kg = self._simulate_learning(item, knowledge_graph)
        predicted_entropy = self._calculate_entropy(
            simulated_kg,
            self._update_uncertainty(item, uncertainty_map)
        )
        
        info_gain = current_entropy - predicted_entropy
        
        # 考虑网络效应（学习一个概念可能解锁多个相关概念）
        network_effect = self._estimate_network_effect(item, knowledge_graph)
        
        return info_gain * (1 + network_effect)
```

## 6. 元认知与自我评估

### 6.1 知识置信度管理

```python
class MetacognitionEngine:
    """元认知引擎 - 自我意识和评估"""
    
    async def evaluate_knowledge_confidence(
        self,
        state: DPACognitiveState
    ) -> Dict[str, Any]:
        """评估知识置信度"""
        
        confidence_report = {
            "timestamp": datetime.now(),
            "overall_confidence": 0.0,
            "domain_confidence": {},
            "weak_areas": [],
            "strong_areas": [],
            "recommendations": []
        }
        
        # 1. 评估各领域的知识置信度
        for domain, concepts in self._group_by_domain(state["semantic_memory"]).items():
            domain_score = await self._evaluate_domain_confidence(
                domain,
                concepts,
                state["knowledge_graph_snapshot"]
            )
            confidence_report["domain_confidence"][domain] = domain_score
            
            if domain_score < 0.5:
                confidence_report["weak_areas"].append({
                    "domain": domain,
                    "score": domain_score,
                    "missing_concepts": self._identify_missing_concepts(domain)
                })
            elif domain_score > 0.8:
                confidence_report["strong_areas"].append({
                    "domain": domain,
                    "score": domain_score,
                    "key_strengths": self._identify_strengths(domain, concepts)
                })
        
        # 2. 计算整体置信度
        confidence_report["overall_confidence"] = np.mean(
            list(confidence_report["domain_confidence"].values())
        )
        
        # 3. 生成改进建议
        confidence_report["recommendations"] = await self._generate_recommendations(
            confidence_report,
            state
        )
        
        return confidence_report
    
    async def reflect_on_learning_progress(
        self,
        state: DPACognitiveState
    ) -> Dict[str, Any]:
        """反思学习进展"""
        
        # 分析学习历史
        learning_history = state.get("execution_history", [])
        
        reflection = {
            "learning_velocity": self._calculate_learning_velocity(learning_history),
            "knowledge_growth": self._measure_knowledge_growth(state),
            "hypothesis_accuracy": self._evaluate_hypothesis_accuracy(state),
            "bottlenecks": self._identify_learning_bottlenecks(state),
            "insights": []
        }
        
        # 生成洞察
        insights_prompt = f"""基于以下学习数据，生成3-5个关键洞察：
        
学习速度: {reflection['learning_velocity']}
知识增长率: {reflection['knowledge_growth']}
假设准确率: {reflection['hypothesis_accuracy']}
瓶颈: {reflection['bottlenecks']}

请提供深刻的、可行动的洞察。"""
        
        insights = await self.llm.ainvoke([HumanMessage(content=insights_prompt)])
        reflection["insights"] = self._parse_insights(insights.content)
        
        return reflection
```

## 7. 完整的LangGraph工作流实现

### 7.1 核心工作流构建

```python
def build_cognitive_workflow() -> CompiledGraph:
    """构建完整的认知工作流"""
    
    workflow = StateGraph(DPACognitiveState)
    
    # === 核心节点定义 ===
    
    # 感知与注意力节点
    workflow.add_node("perceive", perceive_input)
    workflow.add_node("attend", focus_attention)
    
    # 记忆管理节点
    workflow.add_node("encode_memory", encode_to_memory)
    workflow.add_node("consolidate_memory", consolidate_memories)
    workflow.add_node("retrieve_memory", retrieve_from_memory)
    
    # 文档处理节点
    workflow.add_node("process_document", process_with_s2)
    workflow.add_node("extract_knowledge", extract_to_graph)
    
    # 推理与理解节点
    workflow.add_node("reason", reasoning_engine)
    workflow.add_node("understand", semantic_understanding)
    
    # 学习规划节点
    workflow.add_node("identify_gaps", identify_knowledge_gaps)
    workflow.add_node("generate_hypotheses", generate_gnn_hypotheses)
    workflow.add_node("plan_learning", create_learning_plan)
    
    # 行动执行节点
    workflow.add_node("execute_action", execute_planned_action)
    workflow.add_node("verify_hypothesis", verify_hypothesis)
    
    # 元认知节点
    workflow.add_node("self_evaluate", evaluate_performance)
    workflow.add_node("reflect", reflect_on_progress)
    workflow.add_node("adapt", adapt_strategy)
    
    # 记忆库节点
    workflow.add_node("sync_memory_bank", sync_with_memory_bank)
    workflow.add_node("update_summary", update_dynamic_summary)
    
    # === 条件路由 ===
    
    # 入口路由
    workflow.add_conditional_edges(
        "perceive",
        route_by_input_type,
        {
            "document": "process_document",
            "query": "attend",
            "hypothesis": "verify_hypothesis"
        }
    )
    
    # 记忆路由
    workflow.add_conditional_edges(
        "consolidate_memory",
        check_memory_overflow,
        {
            "overflow": "compress_memory",
            "normal": "retrieve_memory"
        }
    )
    
    # 学习路由
    workflow.add_conditional_edges(
        "identify_gaps",
        evaluate_gap_severity,
        {
            "critical": "plan_learning",
            "minor": "continue",
            "none": "self_evaluate"
        }
    )
    
    # === 循环设置 ===
    
    # 主认知循环
    workflow.add_edge("reflect", "perceive")  # 持续感知
    
    # 学习循环
    workflow.add_edge("execute_action", "verify_hypothesis")
    workflow.add_edge("verify_hypothesis", "update_knowledge")
    workflow.add_edge("update_knowledge", "identify_gaps")
    
    # === 编译选项 ===
    
    # 设置入口和检查点
    workflow.set_entry_point("perceive")
    
    # 编译工作流
    app = workflow.compile(
        checkpointer=PostgresSaver(
            connection_string=settings.postgresql.connection_string,
            serde=EnhancedSerializer()  # 支持复杂对象序列化
        ),
        # 中断点 - 允许人工干预
        interrupt_before=[
            "execute_action",      # 执行重要操作前
            "update_knowledge",    # 更新知识库前
            "adapt"               # 调整策略前
        ]
    )
    
    return app
```

### 7.2 高级执行模式

```python
class CognitiveOrchestrator:
    """认知编排器 - 管理复杂的执行模式"""
    
    def __init__(self, app: CompiledGraph):
        self.app = app
        self.execution_modes = {
            "research": self._research_mode,
            "learning": self._learning_mode,
            "dialogue": self._dialogue_mode,
            "exploration": self._exploration_mode
        }
    
    async def run_session(
        self,
        mode: str,
        initial_input: Dict,
        config: Dict
    ):
        """运行认知会话"""
        
        # 初始化状态
        initial_state = self._initialize_state(mode, initial_input)
        
        # 选择执行模式
        execution_fn = self.execution_modes.get(mode, self._default_mode)
        
        # 执行会话
        async for state in execution_fn(initial_state, config):
            # 实时监控
            await self._monitor_progress(state)
            
            # 检查中断条件
            if await self._should_interrupt(state):
                user_input = await self._get_user_input(state)
                state = self._process_user_input(state, user_input)
            
            # 更新记忆库
            if state.get("checkpoint_ready"):
                await self._checkpoint_to_memory_bank(state)
        
        return state
    
    async def _research_mode(self, initial_state: Dict, config: Dict):
        """研究模式 - 深度文档分析"""
        
        # 配置研究模式特定参数
        initial_state["mode_config"] = {
            "depth": "comprehensive",
            "hypothesis_generation": True,
            "citation_tracking": True,
            "synthesis_level": "advanced"
        }
        
        # 执行研究流程
        async for state in self.app.astream(initial_state, config):
            # 研究模式特定的监控和调整
            if state.get("new_hypothesis_generated"):
                # 动态调整研究方向
                state = await self._adjust_research_focus(state)
            
            yield state
```

## 8. 技术实现要点

### 8.1 PostgreSQL优化配置

```sql
-- 为LangGraph检查点优化的PostgreSQL配置

-- 1. 创建专用schema
CREATE SCHEMA IF NOT EXISTS langgraph;

-- 2. 检查点表优化
CREATE TABLE langgraph.checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    parent_id TEXT,
    state JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_id)
);

-- 3. 创建索引
CREATE INDEX idx_checkpoints_thread_created 
ON langgraph.checkpoints(thread_id, created_at DESC);

CREATE INDEX idx_checkpoints_parent 
ON langgraph.checkpoints(parent_id);

-- GIN索引用于JSONB查询
CREATE INDEX idx_checkpoints_state_gin 
ON langgraph.checkpoints USING GIN (state);

-- 4. 分区策略（按月）
CREATE TABLE langgraph.checkpoints_y2024m01 
PARTITION OF langgraph.checkpoints 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 8.2 Neo4j图谱优化

```cypher
// Neo4j优化配置

// 1. 创建约束和索引
CREATE CONSTRAINT concept_id IF NOT EXISTS 
FOR (c:Concept) REQUIRE c.id IS UNIQUE;

CREATE INDEX concept_name IF NOT EXISTS 
FOR (c:Concept) ON (c.name);

CREATE INDEX concept_embedding IF NOT EXISTS 
FOR (c:Concept) ON (c.embedding_id);

// 2. 全文搜索索引
CALL db.index.fulltext.createNodeIndex(
    "conceptSearch",
    ["Concept"],
    ["name", "definition", "description"]
);

// 3. 向量索引（如果使用Neo4j向量功能）
CREATE VECTOR INDEX concept_vector IF NOT EXISTS
FOR (c:Concept) ON (c.embedding)
OPTIONS {indexConfig: {
    `vector.dimensions`: 3072,
    `vector.similarity_function`: 'cosine'
}};
```

### 8.3 性能监控配置

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# 定义度量指标
memory_operations = Counter(
    'dpa_memory_operations_total',
    'Total memory operations',
    ['operation_type', 'memory_layer']
)

query_latency = Histogram(
    'dpa_query_latency_seconds',
    'Query latency in seconds',
    ['query_type']
)

knowledge_graph_size = Gauge(
    'dpa_knowledge_graph_nodes',
    'Number of nodes in knowledge graph',
    ['node_type']
)

learning_progress = Gauge(
    'dpa_learning_progress',
    'Learning progress percentage',
    ['project_id']
)
```

## 9. 部署架构

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dpa_cognitive
      POSTGRES_USER: dpa
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    
  neo4j:
    image: neo4j:5.14
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"
      - "7687:7687"
    
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    
  dpa_cognitive:
    build: .
    environment:
      - DATABASE_URL=postgresql://dpa:${POSTGRES_PASSWORD}@postgres:5432/dpa_cognitive
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - neo4j
      - redis
    ports:
      - "8000:8000"
    volumes:
      - ./memory-bank:/app/memory-bank

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
```

## 10. 总结与创新点

### 10.1 架构创新
1. **真正的认知架构**：基于认知科学理论的四层记忆模型
2. **记忆库子系统**：人类可读的持久化记忆层
3. **GNN驱动的主动学习**：数学严谨的假设生成
4. **三阶段混合检索**：向量→图谱→记忆库的递进式检索

### 10.2 技术创新
1. **S2语义分块**：支持500K+ token的超长文档
2. **动态模式演化**：知识图谱的自适应成长
3. **元认知引擎**：自我评估和策略调整
4. **RVUE生命周期**：记忆库的完整管理流程

### 10.3 工程创新
1. **LangGraph深度集成**：状态机驱动的复杂工作流
2. **PostgreSQL检查点优化**：分区和索引策略
3. **混合持久化**：PostgreSQL + Neo4j + Redis的协同
4. **中断点机制**：人机协作的关键节点

这个融合版设计充分吸收了各方案的精华，构建了一个真正具备持续学习能力的认知系统。