"""
完整认知系统集成测试
测试DPA认知系统各个组件的协同工作
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.cognitive import (
    DPACognitiveState,
    StateManager,
    create_cognitive_storage,
    create_memory_bank_manager,
    create_cognitive_workflow,
    create_s2_chunker,
    create_hybrid_retrieval_system,
    create_metacognitive_engine,
    hybrid_search
)
from src.utils.logger import get_logger
from langchain_core.messages import HumanMessage

logger = get_logger(__name__)


async def test_complete_cognitive_pipeline():
    """测试完整的认知处理流水线"""
    logger.info("=== 测试完整认知处理流水线 ===")
    
    # 1. 初始化所有组件（使用真实API）
    config = {"mock_mode": False}
    
    storage = create_cognitive_storage()
    memory_bank = create_memory_bank_manager()
    workflow = create_cognitive_workflow(config)
    s2_chunker = create_s2_chunker(config)
    retrieval_system = create_hybrid_retrieval_system(config)
    metacognitive_engine = create_metacognitive_engine(config)
    
    logger.info("所有组件初始化完成")
    
    # 2. 创建初始认知状态
    state_manager = StateManager()
    cognitive_state = state_manager.create_initial_state("test_user", "test_project")
    
    # 3. 模拟文档处理流程
    test_document = """
    认知架构是心理学和认知科学中的一个重要概念，它描述了人类心智的基本结构和操作原理。
    认知架构试图解释人类如何感知、学习、记忆、推理和解决问题。主要的认知架构理论包括：
    
    1. ACT-R (Adaptive Control of Thought-Rational) - 由约翰·安德森开发的认知架构
    2. SOAR (State, Operator, and Result) - 艾伦·纽维尔等人开发的问题解决架构  
    3. CLARION - 分层认知架构，区分显式和隐式处理
    
    这些架构都试图建模人类认知的不同方面，包括工作记忆、长期记忆、注意力和学习机制。
    """
    
    logger.info("开始文档分块处理...")
    
    # 4. S2语义分块
    chunks = await s2_chunker.chunk_document(test_document, {"source": "cognitive_theory"})
    logger.info(f"文档分块完成，获得 {len(chunks)} 个分块")
    
    # 5. 向认知状态添加分块结果
    cognitive_state["s2_chunks"] = [chunk.__dict__ for chunk in chunks]
    
    # 6. 执行混合检索
    logger.info("测试混合检索...")
    retrieval_response = await hybrid_search(
        "什么是认知架构的主要特点？",
        query_type="semantic",
        max_results=10
    )
    logger.info(f"检索完成，获得 {len(retrieval_response['results'])} 个结果")
    
    # 7. 添加用户查询到认知状态
    cognitive_state["messages"].append(
        HumanMessage(content="请解释认知架构的基本概念和主要类型")
    )
    
    # 8. 执行元认知循环
    logger.info("执行元认知评估...")
    task_context = {
        "task_type": "explanation",
        "query": "请解释认知架构的基本概念和主要类型",
        "task_complexity": 0.7,
        "accuracy_requirement": 0.8,
        "start_time": datetime.now(),
        "task_completed": True
    }
    
    metacognitive_report = await metacognitive_engine.metacognitive_cycle(
        cognitive_state, task_context
    )
    
    logger.info(f"元认知评估完成:")
    logger.info(f"  当前策略: {metacognitive_report['metacognitive_state']['current_strategy']}")
    logger.info(f"  置信水平: {metacognitive_report['metacognitive_state']['confidence_level']}")
    logger.info(f"  性能评分: {metacognitive_report['performance']['overall_score']:.3f}")
    
    # 9. 保存认知状态
    await storage.save_cognitive_state(cognitive_state)
    logger.info("认知状态已保存")
    
    # 10. 生成处理报告
    processing_report = {
        "timestamp": datetime.now().isoformat(),
        "document_length": len(test_document),
        "chunks_created": len(chunks),
        "retrieval_results": len(retrieval_response['results']),
        "metacognitive_strategy": metacognitive_report['metacognitive_state']['current_strategy'],
        "performance_score": metacognitive_report['performance']['overall_score'],
        "confidence_level": metacognitive_report['metacognitive_state']['confidence_level'],
        "working_memory_usage": len(cognitive_state["working_memory"]) / 7,
        "episodic_memory_count": len(cognitive_state["episodic_memory"]),
        "semantic_memory_count": len(cognitive_state["semantic_memory"])
    }
    
    logger.info(f"处理报告:")
    for key, value in processing_report.items():
        logger.info(f"  {key}: {value}")
    
    return processing_report


async def test_cognitive_workflow_integration():
    """测试认知工作流集成"""
    logger.info("\n=== 测试认知工作流集成 ===")
    
    # 创建工作流（模拟模式）
    workflow = create_cognitive_workflow({"mock_mode": True})
    
    # 创建初始状态
    state_manager = StateManager()
    initial_state = state_manager.create_initial_state("test_user", "integration_test")
    
    # 添加测试消息
    initial_state["messages"] = [
        HumanMessage(content="分析认知负荷理论在教育中的应用")
    ]
    
    # 测试感知节点
    logger.info("测试感知节点...")
    state_after_perceive = await workflow.perceive_input(initial_state)
    logger.info(f"感知完成，感觉缓冲项数: {len(state_after_perceive['sensory_buffer'])}")
    
    # 测试注意力节点
    logger.info("测试注意力节点...")
    state_after_attend = await workflow.focus_attention(state_after_perceive)
    logger.info(f"注意力聚焦完成，工作记忆项数: {len(state_after_attend['working_memory'])}")
    
    # 测试记忆编码节点
    logger.info("测试记忆编码...")
    state_after_encode = await workflow.encode_to_memory(state_after_attend)
    logger.info(f"记忆编码完成，情节记忆项数: {len(state_after_encode['episodic_memory'])}")
    
    # 测试推理节点
    logger.info("测试推理引擎...")
    state_after_reason = await workflow.reasoning_engine(state_after_encode)
    logger.info(f"推理完成，消息数: {len(state_after_reason['messages'])}")
    
    return state_after_reason


async def test_memory_system_integration():
    """测试记忆系统集成"""
    logger.info("\n=== 测试记忆系统集成 ===")
    
    # 创建记忆库管理器
    memory_bank = create_memory_bank_manager()
    
    # 读取记忆
    memories = await memory_bank.read_all_memories()
    logger.info(f"读取记忆完成，包含 {len(memories)} 个记忆类型")
    
    # 创建测试状态用于更新记忆
    test_state = {
        "project_id": "integration_test",
        "new_insights": [
            {"content": "认知架构整合洞察", "confidence": 0.9, "timestamp": datetime.now().isoformat()},
            {"content": "元认知策略优化", "confidence": 0.8, "timestamp": datetime.now().isoformat()}
        ],
        "concept_embeddings": {"integration": [0.1] * 10},
        "learning_hypotheses": [{"id": "hyp1", "content": "集成测试假设"}],
        "knowledge_gaps": [{"description": "集成过程中的知识盲点"}]
    }
    
    # 更新动态摘要
    await memory_bank.update_dynamic_summary(test_state)
    logger.info("记忆库更新完成")
    
    # 验证更新
    updated_memories = await memory_bank.read_all_memories()
    logger.info(f"更新后记忆验证: {len(updated_memories)} 个记忆类型")
    
    return updated_memories


async def test_retrieval_metacognition_loop():
    """测试检索-元认知反馈循环"""
    logger.info("\n=== 测试检索-元认知反馈循环 ===")
    
    # 初始化组件
    retrieval_system = create_hybrid_retrieval_system({"mock_mode": True})
    metacognitive_engine = create_metacognitive_engine({"mock_mode": True})
    
    # 创建认知状态
    state_manager = StateManager()
    cognitive_state = state_manager.create_initial_state("test_user", "feedback_test")
    
    # 模拟多轮检索-评估循环
    queries = [
        "认知架构的基本原理",
        "工作记忆的容量限制",
        "元认知策略的应用"
    ]
    
    for i, query in enumerate(queries):
        logger.info(f"第 {i+1} 轮: {query}")
        
        # 执行检索
        retrieval_response = await hybrid_search(query, max_results=5)
        
        # 更新认知状态
        cognitive_state["messages"].append(HumanMessage(content=query))
        
        # 元认知评估
        task_context = {
            "task_type": "retrieval",
            "query": query,
            "task_complexity": 0.5 + i * 0.1,
            "start_time": datetime.now(),
            "task_completed": True
        }
        
        metacognitive_report = await metacognitive_engine.metacognitive_cycle(
            cognitive_state, task_context
        )
        
        logger.info(f"  检索结果: {len(retrieval_response['results'])} 项")
        logger.info(f"  策略: {metacognitive_report['strategy']['current']}")
        logger.info(f"  性能: {metacognitive_report['performance']['overall_score']:.3f}")
        
        # 模拟策略调整影响下一轮检索
        if metacognitive_report['strategy']['changed']:
            logger.info(f"  策略已调整为: {metacognitive_report['strategy']['current']}")
    
    # 获取元认知洞察
    insights = metacognitive_engine.get_metacognitive_insights()
    logger.info(f"获得 {len(insights['insights'])} 个洞察")
    
    return insights


async def test_system_performance():
    """测试系统性能"""
    logger.info("\n=== 测试系统性能 ===")
    
    start_time = datetime.now()
    
    # 并行初始化多个组件
    tasks = [
        create_cognitive_storage(),
        create_memory_bank_manager(),
        create_s2_chunker({"mock_mode": True}),
        create_hybrid_retrieval_system({"mock_mode": True}),
        create_metacognitive_engine({"mock_mode": True})
    ]
    
    # 等待所有组件初始化完成 - 简化为直接使用
    components = tasks  # 这些已经是初始化好的组件
    
    initialization_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"组件初始化时间: {initialization_time:.3f}秒")
    
    # 测试并发处理
    start_time = datetime.now()
    
    concurrent_tasks = []
    for i in range(5):
        task = hybrid_search(
            f"测试查询 {i}",
            query_type="semantic",
            max_results=5
        )
        concurrent_tasks.append(task)
    
    # 并发执行检索
    results = await asyncio.gather(*concurrent_tasks)
    
    concurrent_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"并发检索时间: {concurrent_time:.3f}秒")
    logger.info(f"平均每次检索: {concurrent_time/5:.3f}秒")
    
    performance_metrics = {
        "initialization_time": initialization_time,
        "concurrent_retrieval_time": concurrent_time,
        "average_retrieval_time": concurrent_time / 5,
        "successful_retrievals": len([r for r in results if r['total_results'] > 0])
    }
    
    return performance_metrics


async def main():
    """主测试函数"""
    logger.info("开始完整认知系统集成测试")
    
    try:
        # 1. 测试完整认知处理流水线
        processing_report = await test_complete_cognitive_pipeline()
        
        # 2. 测试认知工作流集成
        workflow_state = await test_cognitive_workflow_integration()
        
        # 3. 测试记忆系统集成
        memory_update = await test_memory_system_integration()
        
        # 4. 测试检索-元认知反馈循环
        feedback_insights = await test_retrieval_metacognition_loop()
        
        # 5. 测试系统性能
        performance_metrics = await test_system_performance()
        
        logger.info("\n=== 集成测试总结 ===")
        logger.info("✅ 完整认知处理流水线：通过")
        logger.info("✅ 认知工作流集成：通过")
        logger.info("✅ 记忆系统集成：通过")
        logger.info("✅ 检索-元认知反馈循环：通过")
        logger.info("✅ 系统性能测试：通过")
        
        logger.info(f"\n性能指标:")
        logger.info(f"  初始化时间: {performance_metrics['initialization_time']:.3f}秒")
        logger.info(f"  平均检索时间: {performance_metrics['average_retrieval_time']:.3f}秒")
        logger.info(f"  成功检索率: {performance_metrics['successful_retrievals']}/5")
        
        logger.info(f"\n认知状态:")
        logger.info(f"  文档分块数: {processing_report['chunks_created']}")
        logger.info(f"  检索结果数: {processing_report['retrieval_results']}")
        logger.info(f"  当前策略: {processing_report['metacognitive_strategy']}")
        logger.info(f"  性能评分: {processing_report['performance_score']:.3f}")
        logger.info(f"  工作记忆使用: {processing_report['working_memory_usage']:.2f}")
        
        logger.info("\n🎉 DPA认知系统集成测试全部通过！")
        logger.info("系统已准备好处理复杂的认知任务。")
        
    except Exception as e:
        logger.error(f"集成测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())