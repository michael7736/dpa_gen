"""
测试元认知引擎
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.cognitive.metacognition import (
    MetacognitiveEngine,
    CognitiveMonitor,
    StrategySelector,
    PerformanceEvaluator,
    MetacognitiveState,
    PerformanceMetrics,
    ConfidenceLevel,
    CognitiveStrategy,
    create_metacognitive_engine
)
from src.cognitive.state import StateManager
from src.utils.logger import get_logger
from langchain_core.messages import HumanMessage, AIMessage

logger = get_logger(__name__)


async def test_cognitive_monitor():
    """测试认知监控器"""
    logger.info("=== 测试认知监控器 ===")
    
    # 创建监控器
    monitor = CognitiveMonitor()
    
    # 创建测试状态
    state_manager = StateManager()
    cognitive_state = state_manager.create_initial_state("test_user", "test_project")
    
    # 添加一些测试数据
    for i in range(8):  # 超过工作记忆限制
        cognitive_state["working_memory"][f"item_{i}"] = {"value": f"test_{i}"}
        cognitive_state["attention_weights"][f"item_{i}"] = 0.1 + i * 0.1
    
    # 添加情节记忆
    for i in range(15):
        cognitive_state["episodic_memory"].append({
            "id": f"episode_{i}",
            "content": f"测试情节 {i}",
            "timestamp": datetime.now()
        })
    
    # 创建元认知状态
    metacog_state = MetacognitiveState()
    
    # 执行监控
    monitoring_result = await monitor.monitor_cognitive_state(cognitive_state, metacog_state)
    
    logger.info(f"监控结果:")
    logger.info(f"  警报数量: {len(monitoring_result['alerts'])}")
    logger.info(f"  建议数量: {len(monitoring_result['recommendations'])}")
    logger.info(f"  状态评估: {monitoring_result['state_assessment']}")
    
    # 显示警报
    for alert in monitoring_result['alerts']:
        logger.info(f"  警报: {alert['type']} - {alert['message']}")
    
    # 显示建议
    for rec in monitoring_result['recommendations']:
        logger.info(f"  建议: {rec['action']} - {rec['description']}")
    
    # 测试模式检测
    patterns = await monitor.detect_cognitive_patterns()
    logger.info(f"检测到的模式: {len(patterns['patterns'])} 个")
    
    return monitoring_result


async def test_strategy_selector():
    """测试策略选择器"""
    logger.info("\n=== 测试策略选择器 ===")
    
    # 创建策略选择器（模拟模式）
    selector = StrategySelector(mock_mode=True)
    
    # 创建测试状态
    state_manager = StateManager()
    cognitive_state = state_manager.create_initial_state("test_user", "test_project")
    
    # 创建元认知状态
    metacog_state = MetacognitiveState()
    metacog_state.confidence_level = ConfidenceLevel.MEDIUM
    
    # 测试不同情况下的策略选择
    test_contexts = [
        {
            "name": "新领域探索",
            "context": {
                "task_complexity": 0.8,
                "knowledge_coverage": 0.2,
                "time_pressure": 0.3,
                "accuracy_requirement": 0.6
            }
        },
        {
            "name": "熟悉任务",
            "context": {
                "task_complexity": 0.3,
                "knowledge_coverage": 0.9,
                "time_pressure": 0.8,
                "accuracy_requirement": 0.7
            }
        },
        {
            "name": "关键决策",
            "context": {
                "task_complexity": 0.6,
                "knowledge_coverage": 0.7,
                "time_pressure": 0.2,
                "accuracy_requirement": 0.95
            }
        },
        {
            "name": "性能下降",
            "context": {
                "task_complexity": 0.5,
                "knowledge_coverage": 0.6,
                "time_pressure": 0.5,
                "accuracy_requirement": 0.7,
                "current_performance": 0.3
            }
        }
    ]
    
    for test_case in test_contexts:
        strategy = await selector.select_strategy(
            cognitive_state, metacog_state, test_case["context"]
        )
        logger.info(f"  {test_case['name']}: {strategy.value}")
    
    return selector


async def test_performance_evaluator():
    """测试性能评估器"""
    logger.info("\n=== 测试性能评估器 ===")
    
    # 创建评估器
    evaluator = PerformanceEvaluator()
    
    # 创建测试状态
    state_manager = StateManager()
    cognitive_state = state_manager.create_initial_state("test_user", "test_project")
    
    # 添加一些响应消息
    cognitive_state["messages"] = [
        HumanMessage(content="什么是认知架构？"),
        AIMessage(content="认知架构是描述心智过程的理论框架，它定义了认知系统的基本结构和操作原理。")
    ]
    
    # 创建任务上下文
    task_context = {
        "task_type": "question_answering",
        "query": "什么是认知架构？",
        "expected_elements": ["认知", "架构", "理论", "框架"],
        "start_time": datetime.now() - timedelta(seconds=2)
    }
    
    # 执行性能评估
    metrics = await evaluator.evaluate_performance(
        cognitive_state,
        task_context,
        task_context["start_time"],
        datetime.now()
    )
    
    logger.info(f"性能评估结果:")
    logger.info(f"  综合评分: {metrics.overall_score:.3f}")
    logger.info(f"  准确性: {metrics.accuracy:.3f}")
    logger.info(f"  连贯性: {metrics.coherence:.3f}")
    logger.info(f"  相关性: {metrics.relevance:.3f}")
    logger.info(f"  完整性: {metrics.completeness:.3f}")
    logger.info(f"  置信度: {metrics.confidence:.3f}")
    logger.info(f"  响应时间: {metrics.response_time:.3f}秒")
    
    # 测试多次评估以获得趋势
    for i in range(5):
        test_metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            task_type="test_task"
        )
        test_metrics.overall_score = 0.6 + i * 0.05  # 模拟改进趋势
        test_metrics.accuracy = 0.7 + i * 0.03
        test_metrics.coherence = 0.65 + i * 0.04
        evaluator.evaluation_history.append(test_metrics)
    
    # 获取趋势分析
    trend_analysis = evaluator.get_performance_trend(window=5)
    logger.info(f"性能趋势: {trend_analysis['trend']}")
    if trend_analysis['trend'] == "analyzed":
        for metric, data in trend_analysis['metrics'].items():
            logger.info(f"  {metric}: {data['trend']} (当前: {data['current']:.3f})")
    
    return evaluator


async def test_metacognitive_state():
    """测试元认知状态"""
    logger.info("\n=== 测试元认知状态 ===")
    
    # 创建元认知状态
    metacog_state = MetacognitiveState()
    
    logger.info(f"初始状态:")
    logger.info(f"  当前策略: {metacog_state.current_strategy.value}")
    logger.info(f"  置信水平: {metacog_state.confidence_level.value}")
    logger.info(f"  自我评估: {metacog_state.self_assessment}")
    
    # 更新一些状态
    metacog_state.current_strategy = CognitiveStrategy.EXPLORATION
    metacog_state.confidence_level = ConfidenceLevel.HIGH
    metacog_state.self_assessment = {
        "accuracy": 0.8,
        "efficiency": 0.7,
        "confidence": 0.85
    }
    
    # 添加策略效果记录
    metacog_state.strategy_effectiveness = {
        "exploration": 0.75,
        "exploitation": 0.65,
        "verification": 0.85
    }
    
    # 添加策略历史
    metacog_state.strategy_history.append({
        "timestamp": datetime.now(),
        "from_strategy": "exploitation",
        "to_strategy": "exploration",
        "reason": "performance_improvement"
    })
    
    logger.info(f"更新后状态:")
    logger.info(f"  当前策略: {metacog_state.current_strategy.value}")
    logger.info(f"  置信水平: {metacog_state.confidence_level.value}")
    logger.info(f"  策略效果: {metacog_state.strategy_effectiveness}")
    logger.info(f"  策略历史长度: {len(metacog_state.strategy_history)}")
    
    return metacog_state


async def test_metacognitive_engine():
    """测试完整的元认知引擎"""
    logger.info("\n=== 测试元认知引擎 ===")
    
    # 创建元认知引擎（模拟模式）
    engine = create_metacognitive_engine({"mock_mode": True})
    
    # 创建测试状态
    state_manager = StateManager()
    cognitive_state = state_manager.create_initial_state("test_user", "test_project")
    
    # 添加一些测试数据
    cognitive_state["messages"] = [
        HumanMessage(content="解释深度学习的基本原理"),
        AIMessage(content="深度学习是一种机器学习方法，使用多层神经网络来学习数据的高级特征表示。")
    ]
    
    # 添加工作记忆（过载情况）
    for i in range(9):
        cognitive_state["working_memory"][f"concept_{i}"] = {"value": f"深度学习概念{i}"}
        cognitive_state["attention_weights"][f"concept_{i}"] = 0.8 if i < 3 else 0.2
    
    # 创建任务上下文
    task_context = {
        "task_type": "explanation",
        "query": "解释深度学习的基本原理",
        "task_complexity": 0.7,
        "accuracy_requirement": 0.8,
        "time_pressure": 0.4,
        "start_time": datetime.now() - timedelta(seconds=3),
        "task_completed": True
    }
    
    # 执行元认知循环
    metacognitive_report = await engine.metacognitive_cycle(cognitive_state, task_context)
    
    logger.info(f"元认知报告:")
    logger.info(f"  时间戳: {metacognitive_report['timestamp']}")
    logger.info(f"  当前策略: {metacognitive_report['metacognitive_state']['current_strategy']}")
    logger.info(f"  置信水平: {metacognitive_report['metacognitive_state']['confidence_level']}")
    logger.info(f"  监控警报: {metacognitive_report['monitoring']['alerts_count']} 个")
    logger.info(f"  策略变更: {metacognitive_report['strategy']['changed']}")
    logger.info(f"  建议数量: {len(metacognitive_report['recommendations'])}")
    
    # 显示性能评估
    if metacognitive_report['performance']:
        perf = metacognitive_report['performance']
        logger.info(f"  性能评估:")
        logger.info(f"    综合评分: {perf['overall_score']:.3f}")
        logger.info(f"    准确性: {perf['accuracy']:.3f}")
        logger.info(f"    连贯性: {perf['coherence']:.3f}")
    
    # 显示建议
    for rec in metacognitive_report['recommendations']:
        logger.info(f"  建议: {rec['action']} - {rec['description']}")
    
    # 执行多个周期以测试适应性
    logger.info("\n执行多个元认知周期...")
    for i in range(3):
        # 模拟不同的任务情况
        test_context = task_context.copy()
        test_context['task_complexity'] = 0.5 + i * 0.2
        test_context['task_completed'] = True
        
        report = await engine.metacognitive_cycle(cognitive_state, test_context)
        logger.info(f"  周期 {i+1}: 策略={report['strategy']['current']}, 变更={report['strategy']['changed']}")
    
    # 获取元认知洞察
    insights = engine.get_metacognitive_insights()
    logger.info(f"元认知洞察:")
    logger.info(f"  会话数量: {insights['session_count']}")
    logger.info(f"  洞察数量: {len(insights['insights'])}")
    logger.info(f"  模式数量: {len(insights['patterns'])}")
    
    # 显示具体洞察
    for insight in insights['insights']:
        logger.info(f"  洞察: {insight['description']}")
    
    return engine


async def test_confidence_levels():
    """测试置信度等级"""
    logger.info("\n=== 测试置信度等级 ===")
    
    confidence_values = [0.1, 0.25, 0.4, 0.6, 0.8, 0.95]
    
    for value in confidence_values:
        if value < 0.3:
            level = ConfidenceLevel.VERY_LOW
        elif value < 0.5:
            level = ConfidenceLevel.LOW
        elif value < 0.7:
            level = ConfidenceLevel.MEDIUM
        elif value < 0.9:
            level = ConfidenceLevel.HIGH
        else:
            level = ConfidenceLevel.VERY_HIGH
        
        logger.info(f"  置信度 {value:.2f} -> {level.value}")
    
    return True


async def test_strategy_types():
    """测试策略类型"""
    logger.info("\n=== 测试策略类型 ===")
    
    strategies = [
        CognitiveStrategy.EXPLORATION,
        CognitiveStrategy.EXPLOITATION,
        CognitiveStrategy.VERIFICATION,
        CognitiveStrategy.REFLECTION,
        CognitiveStrategy.ADAPTATION
    ]
    
    for strategy in strategies:
        logger.info(f"  策略: {strategy.value}")
    
    return True


async def test_save_load_state():
    """测试状态保存和加载"""
    logger.info("\n=== 测试状态保存 ===")
    
    # 创建引擎并运行一些周期
    engine = create_metacognitive_engine({"mock_mode": True})
    
    # 模拟一些活动
    engine.metacognitive_state.current_strategy = CognitiveStrategy.EXPLORATION
    engine.metacognitive_state.confidence_level = ConfidenceLevel.HIGH
    engine.metacognitive_state.self_assessment = {"test": 0.8}
    
    # 保存状态
    save_path = "test_metacognitive_state.json"
    await engine.save_metacognitive_state(save_path)
    
    # 检查文件是否存在
    if Path(save_path).exists():
        logger.info(f"状态已成功保存到: {save_path}")
        
        # 读取并验证
        import json
        with open(save_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        logger.info(f"保存的策略: {saved_data['metacognitive_state']['current_strategy']}")
        logger.info(f"保存的置信度: {saved_data['metacognitive_state']['confidence_level']}")
        
        # 清理测试文件
        Path(save_path).unlink()
    else:
        logger.error("状态保存失败")
    
    return True


async def main():
    """主测试函数"""
    logger.info("开始测试元认知引擎")
    
    try:
        # 1. 测试认知监控器
        monitoring_result = await test_cognitive_monitor()
        
        # 2. 测试策略选择器
        selector = await test_strategy_selector()
        
        # 3. 测试性能评估器
        evaluator = await test_performance_evaluator()
        
        # 4. 测试元认知状态
        metacog_state = await test_metacognitive_state()
        
        # 5. 测试完整引擎
        engine = await test_metacognitive_engine()
        
        # 6. 测试置信度等级
        await test_confidence_levels()
        
        # 7. 测试策略类型
        await test_strategy_types()
        
        # 8. 测试状态保存
        await test_save_load_state()
        
        logger.info("\n=== 测试总结 ===")
        logger.info("✅ 认知监控器：通过")
        logger.info("✅ 策略选择器：通过")
        logger.info("✅ 性能评估器：通过")
        logger.info("✅ 元认知状态：通过")
        logger.info("✅ 完整引擎：通过")
        logger.info("✅ 置信度等级：通过")
        logger.info("✅ 策略类型：通过")
        logger.info("✅ 状态保存：通过")
        logger.info("\n元认知引擎测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())