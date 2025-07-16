"""
元认知模块

DPA认知系统的元认知层，负责监控、评估和调节整个认知过程。

核心组件：
- MetacognitiveEngine: 元认知引擎主控制器
- CognitiveMonitor: 认知监控器  
- StrategySelector: 策略选择器
- PerformanceEvaluator: 性能评估器

主要功能：
1. 认知监控 - 实时监控认知状态和过程
2. 策略选择 - 根据情况选择最适合的认知策略  
3. 性能评估 - 评估认知系统的表现
4. 自适应调节 - 根据评估结果调整认知策略
5. 元认知洞察 - 提供认知过程的深度分析

数据结构：
- MetacognitiveState: 元认知状态
- PerformanceMetrics: 性能评估指标
- ConfidenceLevel: 置信度等级
- CognitiveStrategy: 认知策略类型
"""

from .metacognitive_engine import (
    # 主要类
    MetacognitiveEngine,
    CognitiveMonitor,
    StrategySelector, 
    PerformanceEvaluator,
    
    # 数据结构
    MetacognitiveState,
    PerformanceMetrics,
    
    # 枚举类型
    ConfidenceLevel,
    CognitiveStrategy,
    
    # 工厂函数
    create_metacognitive_engine
)

__all__ = [
    # 主要类
    "MetacognitiveEngine",
    "CognitiveMonitor", 
    "StrategySelector",
    "PerformanceEvaluator",
    
    # 数据结构
    "MetacognitiveState",
    "PerformanceMetrics",
    
    # 枚举类型
    "ConfidenceLevel",
    "CognitiveStrategy",
    
    # 工厂函数
    "create_metacognitive_engine"
]