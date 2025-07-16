"""
元认知引擎 - DPA认知系统的自我监控和调节模块

元认知功能包括：
1. 认知监控 (Metacognitive Monitoring)
2. 认知调节 (Metacognitive Regulation)  
3. 策略选择 (Strategy Selection)
4. 性能评估 (Performance Assessment)
5. 自适应优化 (Adaptive Optimization)
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..state import DPACognitiveState
from ...utils.logger import get_logger
from ...config.settings import get_settings

logger = get_logger(__name__)


class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_LOW = "very_low"     # < 0.3
    LOW = "low"               # 0.3 - 0.5
    MEDIUM = "medium"         # 0.5 - 0.7
    HIGH = "high"             # 0.7 - 0.9
    VERY_HIGH = "very_high"   # > 0.9


class CognitiveStrategy(Enum):
    """认知策略类型"""
    EXPLORATION = "exploration"         # 探索性学习
    EXPLOITATION = "exploitation"       # 利用现有知识
    VERIFICATION = "verification"       # 验证和确认
    REFLECTION = "reflection"           # 反思和总结
    ADAPTATION = "adaptation"           # 策略适应


@dataclass
class MetacognitiveState:
    """元认知状态"""
    current_strategy: CognitiveStrategy = CognitiveStrategy.EXPLORATION
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    attention_focus: List[str] = field(default_factory=list)
    
    # 性能指标
    accuracy_score: float = 0.0
    efficiency_score: float = 0.0
    coherence_score: float = 0.0
    learning_rate: float = 0.0
    
    # 自我评估
    self_assessment: Dict[str, float] = field(default_factory=dict)
    strategy_effectiveness: Dict[str, float] = field(default_factory=dict)
    
    # 历史追踪
    strategy_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_trend: List[float] = field(default_factory=list)
    
    # 适应性参数
    adaptation_threshold: float = 0.3
    exploration_rate: float = 0.2
    last_strategy_change: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """性能评估指标"""
    timestamp: datetime
    task_type: str
    
    # 核心指标
    accuracy: float = 0.0              # 准确性
    response_time: float = 0.0         # 响应时间
    memory_usage: float = 0.0          # 记忆使用率
    confidence: float = 0.0            # 置信度
    
    # 质量指标
    coherence: float = 0.0             # 连贯性
    relevance: float = 0.0             # 相关性
    completeness: float = 0.0          # 完整性
    novelty: float = 0.0               # 新颖性
    
    # 学习指标
    knowledge_gain: float = 0.0        # 知识增益
    skill_improvement: float = 0.0     # 技能提升
    error_reduction: float = 0.0       # 错误减少
    
    # 综合评分
    overall_score: float = 0.0
    
    def calculate_overall_score(self):
        """计算综合评分"""
        weights = {
            'accuracy': 0.25,
            'coherence': 0.20,
            'relevance': 0.20,
            'knowledge_gain': 0.15,
            'confidence': 0.10,
            'completeness': 0.10
        }
        
        self.overall_score = (
            weights['accuracy'] * self.accuracy +
            weights['coherence'] * self.coherence +
            weights['relevance'] * self.relevance +
            weights['knowledge_gain'] * self.knowledge_gain +
            weights['confidence'] * self.confidence +
            weights['completeness'] * self.completeness
        )
        
        return self.overall_score


class CognitiveMonitor:
    """认知监控器 - 实时监控认知过程"""
    
    def __init__(self):
        self.monitoring_history: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            'low_confidence': 0.3,
            'high_memory_usage': 0.8,
            'slow_response': 5.0,  # 秒
            'low_coherence': 0.4
        }
    
    async def monitor_cognitive_state(
        self,
        state: DPACognitiveState,
        metacog_state: MetacognitiveState
    ) -> Dict[str, Any]:
        """监控当前认知状态"""
        logger.info("执行认知状态监控...")
        
        monitoring_result = {
            "timestamp": datetime.now(),
            "alerts": [],
            "recommendations": [],
            "state_assessment": {}
        }
        
        # 1. 监控工作记忆使用
        memory_usage = len(state["working_memory"]) / 7  # 7±2规则
        monitoring_result["state_assessment"]["memory_usage"] = memory_usage
        
        if memory_usage > self.alert_thresholds['high_memory_usage']:
            monitoring_result["alerts"].append({
                "type": "high_memory_usage",
                "severity": "warning",
                "message": f"工作记忆使用率过高: {memory_usage:.2f}"
            })
            monitoring_result["recommendations"].append({
                "action": "consolidate_memory",
                "priority": "high",
                "description": "建议进行记忆巩固"
            })
        
        # 2. 监控注意力分散
        attention_weights = state.get("attention_weights", {})
        if attention_weights:
            attention_entropy = self._calculate_attention_entropy(attention_weights)
            monitoring_result["state_assessment"]["attention_entropy"] = attention_entropy
            
            if attention_entropy > 2.0:  # 高熵表示注意力分散
                monitoring_result["alerts"].append({
                    "type": "attention_scattered",
                    "severity": "info",
                    "message": f"注意力较为分散: {attention_entropy:.2f}"
                })
        
        # 3. 监控情节记忆增长
        episodic_count = len(state["episodic_memory"])
        monitoring_result["state_assessment"]["episodic_memory_count"] = episodic_count
        
        if episodic_count > 100:
            monitoring_result["recommendations"].append({
                "action": "episodic_consolidation",
                "priority": "medium",
                "description": "情节记忆过多，建议整理"
            })
        
        # 4. 监控学习进展
        if hasattr(state, 'learning_progress'):
            learning_rate = state.get('learning_progress', {}).get('rate', 0)
            if learning_rate < 0.1:
                monitoring_result["alerts"].append({
                    "type": "slow_learning",
                    "severity": "warning", 
                    "message": f"学习进展缓慢: {learning_rate:.3f}"
                })
        
        # 5. 监控策略效果
        if metacog_state.strategy_effectiveness:
            current_strategy = metacog_state.current_strategy.value
            effectiveness = metacog_state.strategy_effectiveness.get(current_strategy, 0)
            
            if effectiveness < 0.5:
                monitoring_result["recommendations"].append({
                    "action": "strategy_change",
                    "priority": "high",
                    "description": f"当前策略{current_strategy}效果不佳，建议调整"
                })
        
        # 记录监控历史
        self.monitoring_history.append(monitoring_result)
        
        # 保持历史记录在合理范围内
        if len(self.monitoring_history) > 1000:
            self.monitoring_history = self.monitoring_history[-800:]
        
        logger.info(f"监控完成，发现 {len(monitoring_result['alerts'])} 个警报")
        return monitoring_result
    
    def _calculate_attention_entropy(self, attention_weights: Dict[str, float]) -> float:
        """计算注意力熵（衡量注意力分散程度）"""
        if not attention_weights:
            return 0.0
        
        weights = np.array(list(attention_weights.values()))
        weights = weights / np.sum(weights)  # 归一化
        
        # 计算香农熵
        entropy = -np.sum(weights * np.log2(weights + 1e-10))
        return entropy
    
    async def detect_cognitive_patterns(self) -> Dict[str, Any]:
        """检测认知模式"""
        if len(self.monitoring_history) < 10:
            return {"patterns": [], "trends": {}}
        
        patterns = {
            "patterns": [],
            "trends": {},
            "recommendations": []
        }
        
        # 分析记忆使用模式
        memory_usage_trend = [
            h["state_assessment"].get("memory_usage", 0) 
            for h in self.monitoring_history[-20:]
        ]
        
        if len(memory_usage_trend) > 5:
            trend_slope = np.polyfit(range(len(memory_usage_trend)), memory_usage_trend, 1)[0]
            patterns["trends"]["memory_usage_slope"] = trend_slope
            
            if trend_slope > 0.1:
                patterns["patterns"].append({
                    "type": "increasing_memory_pressure",
                    "description": "工作记忆使用呈上升趋势"
                })
        
        return patterns


class StrategySelector:
    """策略选择器 - 根据情况选择最适合的认知策略"""
    
    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self.strategy_library = {
            CognitiveStrategy.EXPLORATION: {
                "description": "探索性学习策略",
                "use_cases": ["新领域", "知识盲点", "创新需求"],
                "parameters": {"risk_tolerance": 0.7, "curiosity_weight": 0.8}
            },
            CognitiveStrategy.EXPLOITATION: {
                "description": "利用现有知识策略", 
                "use_cases": ["熟悉任务", "快速响应", "效率优先"],
                "parameters": {"risk_tolerance": 0.3, "efficiency_weight": 0.9}
            },
            CognitiveStrategy.VERIFICATION: {
                "description": "验证确认策略",
                "use_cases": ["关键决策", "高风险任务", "质量要求"],
                "parameters": {"thoroughness": 0.9, "accuracy_weight": 0.8}
            },
            CognitiveStrategy.REFLECTION: {
                "description": "反思总结策略",
                "use_cases": ["学习整理", "经验总结", "元学习"],
                "parameters": {"depth": 0.8, "synthesis_weight": 0.7}
            },
            CognitiveStrategy.ADAPTATION: {
                "description": "策略适应",
                "use_cases": ["策略失效", "环境变化", "性能下降"],
                "parameters": {"flexibility": 0.9, "learning_rate": 0.6}
            }
        }
        
        # 初始化LLM（如果不是模拟模式）
        if not mock_mode:
            try:
                settings = get_settings()
                if settings.ai_model.openai_api_key:
                    self.llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=0.3,
                        openai_api_key=settings.ai_model.openai_api_key,
                        openai_api_base=settings.ai_model.openai_base_url
                    )
                    logger.info("Strategy Selector LLM initialized successfully")
                else:
                    logger.warning("OpenAI API key not found for Strategy Selector, using mock mode")
                    self.mock_mode = True
            except Exception as e:
                logger.warning(f"Failed to initialize LLM for Strategy Selector: {e}, using mock mode")
                self.mock_mode = True
    
    async def select_strategy(
        self,
        state: DPACognitiveState,
        metacog_state: MetacognitiveState,
        context: Dict[str, Any]
    ) -> CognitiveStrategy:
        """选择最适合的认知策略"""
        logger.info("选择认知策略...")
        
        # 收集决策因素
        decision_factors = self._analyze_decision_factors(state, metacog_state, context)
        
        if self.mock_mode:
            # 模拟策略选择
            return self._mock_strategy_selection(decision_factors)
        
        # 使用LLM辅助策略选择
        strategy = await self._llm_assisted_selection(decision_factors)
        
        logger.info(f"选择策略: {strategy.value}")
        return strategy
    
    def _analyze_decision_factors(
        self,
        state: DPACognitiveState,
        metacog_state: MetacognitiveState,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析策略选择的决策因素"""
        factors = {
            "task_complexity": self._assess_task_complexity(context),
            "knowledge_coverage": self._assess_knowledge_coverage(state),
            "time_pressure": context.get("time_pressure", 0.5),
            "accuracy_requirement": context.get("accuracy_requirement", 0.7),
            "current_performance": metacog_state.self_assessment.get("overall", 0.5),
            "recent_strategy_effectiveness": metacog_state.strategy_effectiveness,
            "memory_pressure": len(state["working_memory"]) / 7,
            "confidence_level": metacog_state.confidence_level.value
        }
        
        return factors
    
    def _assess_task_complexity(self, context: Dict[str, Any]) -> float:
        """评估任务复杂度"""
        complexity_indicators = [
            context.get("entity_count", 0) / 10,  # 实体数量
            context.get("relation_count", 0) / 20,  # 关系数量
            context.get("query_length", 0) / 100,   # 查询长度
            context.get("domain_unfamiliarity", 0)  # 领域不熟悉度
        ]
        
        return min(np.mean(complexity_indicators), 1.0)
    
    def _assess_knowledge_coverage(self, state: DPACognitiveState) -> float:
        """评估知识覆盖度"""
        semantic_memory_size = len(state["semantic_memory"])
        episodic_memory_size = len(state["episodic_memory"])
        
        # 简化的覆盖度评估
        coverage = min((semantic_memory_size + episodic_memory_size * 0.5) / 100, 1.0)
        return coverage
    
    def _mock_strategy_selection(self, factors: Dict[str, Any]) -> CognitiveStrategy:
        """模拟策略选择"""
        complexity = factors["task_complexity"]
        performance = factors["current_performance"]
        coverage = factors["knowledge_coverage"]
        
        # 简单的规则基础选择
        if complexity > 0.7 and coverage < 0.5:
            return CognitiveStrategy.EXPLORATION
        elif performance < 0.4:
            return CognitiveStrategy.ADAPTATION
        elif factors["accuracy_requirement"] > 0.8:
            return CognitiveStrategy.VERIFICATION
        elif coverage > 0.8 and complexity < 0.5:
            return CognitiveStrategy.EXPLOITATION
        else:
            return CognitiveStrategy.REFLECTION
    
    async def _llm_assisted_selection(self, factors: Dict[str, Any]) -> CognitiveStrategy:
        """LLM辅助的策略选择"""
        prompt = f"""
        根据以下认知状态因素，选择最适合的认知策略：
        
        决策因素：
        - 任务复杂度: {factors['task_complexity']:.2f}
        - 知识覆盖度: {factors['knowledge_coverage']:.2f}
        - 时间压力: {factors['time_pressure']:.2f}
        - 准确性要求: {factors['accuracy_requirement']:.2f}
        - 当前性能: {factors['current_performance']:.2f}
        - 记忆压力: {factors['memory_pressure']:.2f}
        - 置信水平: {factors['confidence_level']}
        
        可选策略：
        1. exploration - 探索性学习（适合新领域、知识盲点）
        2. exploitation - 利用现有知识（适合熟悉任务、效率优先）
        3. verification - 验证确认（适合关键决策、高准确性要求）
        4. reflection - 反思总结（适合学习整理、经验总结）
        5. adaptation - 策略适应（适合性能下降、环境变化）
        
        请只返回策略名称（如：exploration）。
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="你是一个元认知策略专家。"),
                HumanMessage(content=prompt)
            ])
            
            strategy_name = response.content.strip().lower()
            
            # 映射到枚举
            strategy_map = {
                "exploration": CognitiveStrategy.EXPLORATION,
                "exploitation": CognitiveStrategy.EXPLOITATION,
                "verification": CognitiveStrategy.VERIFICATION,
                "reflection": CognitiveStrategy.REFLECTION,
                "adaptation": CognitiveStrategy.ADAPTATION
            }
            
            return strategy_map.get(strategy_name, CognitiveStrategy.EXPLORATION)
            
        except Exception as e:
            logger.warning(f"LLM策略选择失败: {e}，使用默认策略")
            return self._mock_strategy_selection(factors)


class PerformanceEvaluator:
    """性能评估器 - 评估认知系统的表现"""
    
    def __init__(self):
        self.evaluation_history: List[PerformanceMetrics] = []
        self.baseline_metrics: Optional[PerformanceMetrics] = None
    
    async def evaluate_performance(
        self,
        state: DPACognitiveState,
        task_context: Dict[str, Any],
        start_time: datetime,
        end_time: datetime
    ) -> PerformanceMetrics:
        """评估单次任务性能"""
        logger.info("评估任务性能...")
        
        metrics = PerformanceMetrics(
            timestamp=end_time,
            task_type=task_context.get("task_type", "unknown")
        )
        
        # 1. 基础指标
        metrics.response_time = (end_time - start_time).total_seconds()
        metrics.memory_usage = len(state["working_memory"]) / 7
        
        # 2. 质量指标评估
        metrics.coherence = await self._evaluate_coherence(state)
        metrics.relevance = await self._evaluate_relevance(state, task_context)
        metrics.completeness = await self._evaluate_completeness(state, task_context)
        
        # 3. 学习指标
        metrics.knowledge_gain = await self._evaluate_knowledge_gain(state)
        metrics.skill_improvement = await self._evaluate_skill_improvement()
        
        # 4. 置信度评估
        metrics.confidence = self._calculate_confidence(state)
        
        # 5. 准确性评估（如果有标准答案）
        if "expected_output" in task_context:
            metrics.accuracy = await self._evaluate_accuracy(state, task_context)
        else:
            metrics.accuracy = 0.7  # 默认值
        
        # 计算综合评分
        metrics.calculate_overall_score()
        
        # 记录评估历史
        self.evaluation_history.append(metrics)
        
        # 设置基线（如果是第一次评估）
        if self.baseline_metrics is None:
            self.baseline_metrics = metrics
        
        logger.info(f"性能评估完成，综合评分: {metrics.overall_score:.3f}")
        return metrics
    
    async def _evaluate_coherence(self, state: DPACognitiveState) -> float:
        """评估响应连贯性"""
        if not state["messages"]:
            return 0.0
        
        # 简化的连贯性评估
        # 实际实现可以使用更复杂的NLP技术
        recent_messages = [msg.content for msg in state["messages"][-3:] 
                          if hasattr(msg, 'content')]
        
        if len(recent_messages) < 2:
            return 0.8  # 默认值
        
        # 基于消息长度和复杂度的简单评估
        avg_length = np.mean([len(msg) for msg in recent_messages])
        coherence = min(avg_length / 200, 1.0) * 0.7 + 0.3  # 0.3-1.0范围
        
        return coherence
    
    async def _evaluate_relevance(
        self, 
        state: DPACognitiveState, 
        task_context: Dict[str, Any]
    ) -> float:
        """评估响应相关性"""
        query = task_context.get("query", "")
        if not query or not state["messages"]:
            return 0.5
        
        # 简化的相关性评估
        latest_response = state["messages"][-1].content if state["messages"] else ""
        
        # 基于关键词重叠的简单评估
        query_words = set(query.lower().split())
        response_words = set(latest_response.lower().split())
        
        if not query_words:
            return 0.5
        
        overlap = len(query_words.intersection(response_words))
        relevance = min(overlap / len(query_words), 1.0)
        
        return max(relevance, 0.3)  # 最低0.3
    
    async def _evaluate_completeness(
        self,
        state: DPACognitiveState,
        task_context: Dict[str, Any]
    ) -> float:
        """评估响应完整性"""
        expected_elements = task_context.get("expected_elements", [])
        if not expected_elements:
            return 0.8  # 默认值
        
        latest_response = state["messages"][-1].content if state["messages"] else ""
        
        # 检查预期元素是否在响应中
        covered_elements = 0
        for element in expected_elements:
            if element.lower() in latest_response.lower():
                covered_elements += 1
        
        completeness = covered_elements / len(expected_elements)
        return completeness
    
    async def _evaluate_knowledge_gain(self, state: DPACognitiveState) -> float:
        """评估知识增益"""
        if len(self.evaluation_history) < 2:
            return 0.5  # 初始默认值
        
        # 比较语义记忆的增长
        current_knowledge = len(state["semantic_memory"])
        
        # 与历史平均值比较
        historical_knowledge = [
            len(getattr(eval_record, 'state_snapshot', {}).get('semantic_memory', {}))
            for eval_record in self.evaluation_history[-5:]
        ]
        
        if historical_knowledge:
            avg_historical = np.mean(historical_knowledge)
            knowledge_gain = max(0, (current_knowledge - avg_historical) / max(avg_historical, 1))
            return min(knowledge_gain, 1.0)
        
        return 0.5
    
    async def _evaluate_skill_improvement(self) -> float:
        """评估技能提升"""
        if len(self.evaluation_history) < 5:
            return 0.5  # 数据不足
        
        # 分析最近的性能趋势
        recent_scores = [eval.overall_score for eval in self.evaluation_history[-5:]]
        
        if len(recent_scores) >= 3:
            # 计算趋势斜率
            x = np.arange(len(recent_scores))
            slope = np.polyfit(x, recent_scores, 1)[0]
            
            # 归一化到0-1范围
            improvement = (slope + 0.1) / 0.2  # 假设最大改进率为0.1
            return max(0, min(improvement, 1.0))
        
        return 0.5
    
    def _calculate_confidence(self, state: DPACognitiveState) -> float:
        """计算当前置信度"""
        # 基于多个因素计算置信度
        factors = []
        
        # 1. 知识覆盖度
        knowledge_coverage = min(len(state["semantic_memory"]) / 50, 1.0)
        factors.append(knowledge_coverage)
        
        # 2. 记忆一致性
        if state["episodic_memory"]:
            recent_episodes = state["episodic_memory"][-10:]
            # 简化的一致性评估
            consistency = 0.8  # 默认值
            factors.append(consistency)
        
        # 3. 注意力集中度
        attention_weights = state.get("attention_weights", {})
        if attention_weights:
            max_attention = max(attention_weights.values())
            factors.append(max_attention)
        
        # 综合置信度
        if factors:
            confidence = np.mean(factors)
        else:
            confidence = 0.5
        
        return confidence
    
    async def _evaluate_accuracy(
        self,
        state: DPACognitiveState,
        task_context: Dict[str, Any]
    ) -> float:
        """评估准确性（需要标准答案）"""
        expected = task_context.get("expected_output", "")
        actual = state["messages"][-1].content if state["messages"] else ""
        
        if not expected or not actual:
            return 0.5
        
        # 简化的准确性评估
        # 实际实现可以使用语义相似度等更精确的方法
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return 0.5
        
        intersection = expected_words.intersection(actual_words)
        union = expected_words.union(actual_words)
        
        jaccard_similarity = len(intersection) / len(union) if union else 0
        return jaccard_similarity
    
    def get_performance_trend(self, window: int = 10) -> Dict[str, Any]:
        """获取性能趋势分析"""
        if len(self.evaluation_history) < window:
            return {"trend": "insufficient_data", "metrics": {}}
        
        recent_evaluations = self.evaluation_history[-window:]
        
        trends = {}
        for metric in ['overall_score', 'accuracy', 'efficiency_score', 'coherence']:
            values = [getattr(eval, metric, 0) for eval in recent_evaluations]
            
            if len(values) >= 3:
                x = np.arange(len(values))
                slope = np.polyfit(x, values, 1)[0]
                
                if slope > 0.01:
                    trend = "improving"
                elif slope < -0.01:
                    trend = "declining"
                else:
                    trend = "stable"
                
                trends[metric] = {
                    "trend": trend,
                    "slope": slope,
                    "current": values[-1],
                    "average": np.mean(values)
                }
        
        return {
            "trend": "analyzed",
            "metrics": trends,
            "evaluation_count": len(recent_evaluations)
        }


class MetacognitiveEngine:
    """元认知引擎主控制器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.mock_mode = self.config.get("mock_mode", False)
        
        # 初始化子模块
        self.monitor = CognitiveMonitor()
        self.strategy_selector = StrategySelector(self.mock_mode)
        self.performance_evaluator = PerformanceEvaluator()
        
        # 元认知状态
        self.metacognitive_state = MetacognitiveState()
        
        # 历史记录
        self.session_history: List[Dict[str, Any]] = []
        
        logger.info("元认知引擎初始化完成")
    
    async def metacognitive_cycle(
        self,
        state: DPACognitiveState,
        task_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行完整的元认知循环"""
        logger.info("开始元认知循环...")
        
        cycle_start = datetime.now()
        
        # 1. 认知监控
        monitoring_result = await self.monitor.monitor_cognitive_state(
            state, self.metacognitive_state
        )
        
        # 2. 策略选择
        recommended_strategy = await self.strategy_selector.select_strategy(
            state, self.metacognitive_state, task_context
        )
        
        # 3. 策略调整判断
        strategy_changed = await self._consider_strategy_change(recommended_strategy)
        
        # 4. 性能评估
        if task_context.get("task_completed", False):
            performance_metrics = await self.performance_evaluator.evaluate_performance(
                state,
                task_context,
                task_context.get("start_time", cycle_start),
                datetime.now()
            )
        else:
            performance_metrics = None
        
        # 5. 自我评估更新
        await self._update_self_assessment(monitoring_result, performance_metrics)
        
        # 6. 生成元认知报告
        metacognitive_report = await self._generate_metacognitive_report(
            monitoring_result, recommended_strategy, strategy_changed, performance_metrics
        )
        
        # 7. 记录会话历史
        session_record = {
            "timestamp": cycle_start,
            "monitoring": monitoring_result,
            "strategy": recommended_strategy.value,
            "strategy_changed": strategy_changed,
            "performance": performance_metrics.__dict__ if performance_metrics else None,
            "metacognitive_state": self.metacognitive_state.__dict__.copy()
        }
        self.session_history.append(session_record)
        
        logger.info("元认知循环完成")
        return metacognitive_report
    
    async def _consider_strategy_change(self, recommended_strategy: CognitiveStrategy) -> bool:
        """考虑是否需要改变策略"""
        current_strategy = self.metacognitive_state.current_strategy
        
        if recommended_strategy == current_strategy:
            return False
        
        # 检查策略改变的条件
        time_since_last_change = datetime.now() - (
            self.metacognitive_state.last_strategy_change or datetime.now() - timedelta(hours=1)
        )
        
        # 最短策略持续时间（避免频繁切换）
        min_strategy_duration = timedelta(minutes=5)
        
        if time_since_last_change < min_strategy_duration:
            logger.info(f"策略切换过于频繁，保持当前策略: {current_strategy.value}")
            return False
        
        # 评估当前策略效果
        current_effectiveness = self.metacognitive_state.strategy_effectiveness.get(
            current_strategy.value, 0.5
        )
        
        # 如果当前策略效果不佳，允许切换
        if current_effectiveness < self.metacognitive_state.adaptation_threshold:
            logger.info(f"策略切换: {current_strategy.value} -> {recommended_strategy.value}")
            self.metacognitive_state.current_strategy = recommended_strategy
            self.metacognitive_state.last_strategy_change = datetime.now()
            
            # 记录策略历史
            self.metacognitive_state.strategy_history.append({
                "timestamp": datetime.now(),
                "from_strategy": current_strategy.value,
                "to_strategy": recommended_strategy.value,
                "reason": "low_effectiveness"
            })
            
            return True
        
        return False
    
    async def _update_self_assessment(
        self,
        monitoring_result: Dict[str, Any],
        performance_metrics: Optional[PerformanceMetrics]
    ):
        """更新自我评估"""
        # 基于监控结果更新
        state_assessment = monitoring_result.get("state_assessment", {})
        
        # 记忆使用效率
        memory_usage = state_assessment.get("memory_usage", 0.5)
        memory_efficiency = 1.0 - memory_usage if memory_usage <= 1.0 else 0.0
        self.metacognitive_state.self_assessment["memory_efficiency"] = memory_efficiency
        
        # 注意力管理
        attention_entropy = state_assessment.get("attention_entropy", 1.0)
        attention_focus = max(0, 1.0 - attention_entropy / 3.0)  # 归一化
        self.metacognitive_state.self_assessment["attention_focus"] = attention_focus
        
        # 基于性能指标更新
        if performance_metrics:
            self.metacognitive_state.self_assessment.update({
                "accuracy": performance_metrics.accuracy,
                "coherence": performance_metrics.coherence,
                "confidence": performance_metrics.confidence,
                "overall": performance_metrics.overall_score
            })
            
            # 更新策略效果
            current_strategy = self.metacognitive_state.current_strategy.value
            self.metacognitive_state.strategy_effectiveness[current_strategy] = \
                performance_metrics.overall_score
        
        # 更新置信度等级
        overall_confidence = self.metacognitive_state.self_assessment.get("overall", 0.5)
        if overall_confidence < 0.3:
            self.metacognitive_state.confidence_level = ConfidenceLevel.VERY_LOW
        elif overall_confidence < 0.5:
            self.metacognitive_state.confidence_level = ConfidenceLevel.LOW
        elif overall_confidence < 0.7:
            self.metacognitive_state.confidence_level = ConfidenceLevel.MEDIUM
        elif overall_confidence < 0.9:
            self.metacognitive_state.confidence_level = ConfidenceLevel.HIGH
        else:
            self.metacognitive_state.confidence_level = ConfidenceLevel.VERY_HIGH
    
    async def _generate_metacognitive_report(
        self,
        monitoring_result: Dict[str, Any],
        recommended_strategy: CognitiveStrategy,
        strategy_changed: bool,
        performance_metrics: Optional[PerformanceMetrics]
    ) -> Dict[str, Any]:
        """生成元认知报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "metacognitive_state": {
                "current_strategy": self.metacognitive_state.current_strategy.value,
                "confidence_level": self.metacognitive_state.confidence_level.value,
                "self_assessment": self.metacognitive_state.self_assessment.copy()
            },
            "monitoring": {
                "alerts_count": len(monitoring_result.get("alerts", [])),
                "recommendations_count": len(monitoring_result.get("recommendations", [])),
                "key_alerts": monitoring_result.get("alerts", [])[:3]  # 前3个警报
            },
            "strategy": {
                "current": self.metacognitive_state.current_strategy.value,
                "recommended": recommended_strategy.value,
                "changed": strategy_changed,
                "effectiveness": self.metacognitive_state.strategy_effectiveness.copy()
            },
            "performance": {},
            "recommendations": []
        }
        
        # 添加性能信息
        if performance_metrics:
            report["performance"] = {
                "overall_score": performance_metrics.overall_score,
                "accuracy": performance_metrics.accuracy,
                "coherence": performance_metrics.coherence,
                "confidence": performance_metrics.confidence,
                "response_time": performance_metrics.response_time
            }
        
        # 生成建议
        recommendations = monitoring_result.get("recommendations", [])
        
        # 基于置信度的建议
        if self.metacognitive_state.confidence_level in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW]:
            recommendations.append({
                "action": "confidence_building",
                "priority": "high",
                "description": "当前置信度较低，建议进行知识巩固和验证"
            })
        
        # 基于策略效果的建议
        current_strategy = self.metacognitive_state.current_strategy.value
        current_effectiveness = self.metacognitive_state.strategy_effectiveness.get(current_strategy, 0.5)
        
        if current_effectiveness < 0.4:
            recommendations.append({
                "action": "strategy_review",
                "priority": "high",
                "description": f"当前策略{current_strategy}效果不佳，建议重新评估"
            })
        
        report["recommendations"] = recommendations
        
        return report
    
    def get_metacognitive_insights(self) -> Dict[str, Any]:
        """获取元认知洞察"""
        if len(self.session_history) < 3:
            return {"insights": [], "patterns": [], "trends": {}}
        
        insights = {
            "insights": [],
            "patterns": [],
            "trends": {},
            "session_count": len(self.session_history)
        }
        
        # 分析策略使用模式
        strategy_usage = {}
        for session in self.session_history:
            strategy = session["strategy"]
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        most_used_strategy = max(strategy_usage, key=strategy_usage.get)
        insights["insights"].append({
            "type": "strategy_preference",
            "description": f"最常使用的策略是: {most_used_strategy}",
            "data": strategy_usage
        })
        
        # 分析性能趋势
        performance_trend = self.performance_evaluator.get_performance_trend()
        if performance_trend["trend"] != "insufficient_data":
            insights["trends"]["performance"] = performance_trend
        
        # 分析置信度变化
        confidence_levels = [
            session["metacognitive_state"]["confidence_level"] 
            for session in self.session_history[-10:]
        ]
        
        if len(set(confidence_levels)) > 1:
            insights["patterns"].append({
                "type": "confidence_variation",
                "description": "置信度存在波动",
                "recent_levels": confidence_levels
            })
        
        return insights
    
    async def save_metacognitive_state(self, filepath: Optional[str] = None):
        """保存元认知状态"""
        if filepath is None:
            filepath = "data/metacognitive_state.json"
        
        state_data = {
            "metacognitive_state": {
                "current_strategy": self.metacognitive_state.current_strategy.value,
                "confidence_level": self.metacognitive_state.confidence_level.value,
                "self_assessment": self.metacognitive_state.self_assessment,
                "strategy_effectiveness": self.metacognitive_state.strategy_effectiveness,
                "strategy_history": self.metacognitive_state.strategy_history,
                "last_strategy_change": self.metacognitive_state.last_strategy_change.isoformat() 
                                     if self.metacognitive_state.last_strategy_change else None
            },
            "session_history": self.session_history[-50:],  # 保存最近50个会话
            "timestamp": datetime.now().isoformat()
        }
        
        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"元认知状态已保存到: {filepath}")


# 工厂函数
def create_metacognitive_engine(config: Optional[Dict[str, Any]] = None) -> MetacognitiveEngine:
    """创建元认知引擎实例"""
    return MetacognitiveEngine(config)