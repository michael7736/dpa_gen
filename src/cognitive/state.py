"""
DPA认知系统状态定义 - V3.0
基于认知科学的四层记忆模型和完整状态管理
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class DPACognitiveState(TypedDict):
    """DPA认知系统的完整状态定义"""
    
    # === 对话与交互 ===
    messages: Annotated[List[BaseMessage], add_messages]
    thread_id: str
    user_id: str
    project_id: str
    
    # === 四层记忆模型 ===
    # 1. 感觉记忆 - 极短期缓冲（<1秒）
    sensory_buffer: Dict[str, Any]      # 原始输入缓冲
    
    # 2. 工作记忆 - 短期（7±2项限制）
    working_memory: Dict[str, Any]      # 当前任务上下文
    attention_weights: Dict[str, float]  # 注意力权重
    focus_item: Optional[str]           # 当前焦点
    
    # 3. 情节记忆 - 中期
    episodic_memory: List[Dict]         # 事件和经历
    temporal_context: Dict              # 时间上下文
    
    # 4. 语义记忆 - 长期
    semantic_memory: Dict[str, Any]     # 概念和事实
    procedural_memory: Dict             # 技能和方法
    
    # === 文档处理 ===
    current_documents: List[Dict]
    document_hierarchy: Dict[str, Any]   # 三层文档结构
    s2_chunks: List[Dict]               # S2语义分块（支持500K+ tokens）
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
    processing_status: str              # 当前处理状态


class StateManager:
    """状态管理器 - 确保状态一致性和约束"""
    
    # 认知科学约束
    WORKING_MEMORY_LIMIT = 9    # 7±2 规则
    ATTENTION_FOCUS_LIMIT = 3   # 注意力焦点限制
    MAX_RECURSION_DEPTH = 5     # 最大递归深度
    SENSORY_BUFFER_TTL = 1.0    # 感觉缓冲生存时间（秒）
    
    @staticmethod
    def create_initial_state(
        user_id: str,
        project_id: str,
        thread_id: Optional[str] = None
    ) -> DPACognitiveState:
        """创建初始认知状态"""
        from uuid import uuid4
        
        return DPACognitiveState(
            # 基础信息
            messages=[],
            thread_id=thread_id or str(uuid4()),
            user_id=user_id,
            project_id=project_id,
            
            # 记忆层初始化
            sensory_buffer={},
            working_memory={},
            attention_weights={},
            focus_item=None,
            episodic_memory=[],
            temporal_context={"start_time": datetime.now()},
            semantic_memory={},
            procedural_memory={},
            
            # 文档处理
            current_documents=[],
            document_hierarchy={},
            s2_chunks=[],
            extracted_graph_documents=[],
            
            # 知识图谱
            knowledge_graph_snapshot={},
            concept_embeddings={},
            relation_weights={
                "RELATES_TO": 1.0,
                "DEPENDS_ON": 0.8,
                "CAUSES": 0.9,
                "PART_OF": 0.7,
                "CONFLICTS_WITH": 0.6
            },
            graph_metrics={},
            
            # 学习系统
            knowledge_gaps=[],
            learning_hypotheses=[],
            learning_plan={},
            research_progress={},
            
            # 记忆库
            memory_bank_path=f"./memory-bank/project_{project_id}",
            memory_bank_state={},
            
            # 元认知
            confidence_scores={},
            uncertainty_map={},
            self_evaluation={},
            
            # 控制流
            error_log=[],
            recursion_depth=0,
            execution_history=[],
            checkpoint_metadata={},
            processing_status="initialized"
        )
    
    @staticmethod
    def validate_state(state: DPACognitiveState) -> bool:
        """验证状态约束"""
        # 检查工作记忆大小
        if len(state["working_memory"]) > StateManager.WORKING_MEMORY_LIMIT:
            return False
            
        # 检查注意力焦点数量
        high_attention_items = [k for k, v in state["attention_weights"].items() if v > 0.7]
        if len(high_attention_items) > StateManager.ATTENTION_FOCUS_LIMIT:
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
        
        # 保留前N个高权重项
        state["working_memory"] = dict(
            sorted_items[:StateManager.WORKING_MEMORY_LIMIT]
        )
        
        # 将其余转入情节记忆
        for key, value in sorted_items[StateManager.WORKING_MEMORY_LIMIT:]:
            state["episodic_memory"].append({
                "key": key,
                "value": value,
                "timestamp": datetime.now(),
                "attention_weight": weights.get(key, 0),
                "source": "working_memory_overflow"
            })
        
        return state
    
    @staticmethod
    def update_attention(
        state: DPACognitiveState,
        item_key: str,
        weight_delta: float
    ) -> DPACognitiveState:
        """更新注意力权重"""
        current_weight = state["attention_weights"].get(item_key, 0.5)
        new_weight = max(0.0, min(1.0, current_weight + weight_delta))
        state["attention_weights"][item_key] = new_weight
        
        # 如果权重超过阈值，设置为焦点
        if new_weight > 0.8:
            state["focus_item"] = item_key
        elif state["focus_item"] == item_key and new_weight < 0.5:
            state["focus_item"] = None
            
        return state
    
    @staticmethod
    def clear_sensory_buffer(state: DPACognitiveState) -> DPACognitiveState:
        """清理过期的感觉缓冲"""
        current_time = datetime.now()
        
        # 移除超过TTL的项
        items_to_remove = []
        for key, item in state["sensory_buffer"].items():
            if isinstance(item, dict) and "timestamp" in item:
                age = (current_time - item["timestamp"]).total_seconds()
                if age > StateManager.SENSORY_BUFFER_TTL:
                    items_to_remove.append(key)
        
        for key in items_to_remove:
            del state["sensory_buffer"][key]
            
        return state
    
    @staticmethod
    def add_to_execution_history(
        state: DPACognitiveState,
        action: str
    ) -> DPACognitiveState:
        """添加执行历史记录"""
        state["execution_history"].append(f"{datetime.now().isoformat()}: {action}")
        
        # 限制历史记录长度
        if len(state["execution_history"]) > 100:
            state["execution_history"] = state["execution_history"][-100:]
            
        return state