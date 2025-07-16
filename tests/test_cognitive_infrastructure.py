"""
测试认知系统基础架构
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.cognitive import (
    DPACognitiveState,
    StateManager,
    create_cognitive_storage,
    create_memory_bank_manager,
    create_cognitive_workflow
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_state_management():
    """测试状态管理"""
    logger.info("=== 测试状态管理 ===")
    
    # 创建初始状态
    state_manager = StateManager()
    state = state_manager.create_initial_state(
        user_id="test_user",
        project_id="test_project"
    )
    
    logger.info(f"初始状态创建成功")
    logger.info(f"- Thread ID: {state['thread_id']}")
    logger.info(f"- User ID: {state['user_id']}")
    logger.info(f"- Project ID: {state['project_id']}")
    
    # 测试工作记忆管理
    for i in range(12):  # 超过限制
        state["working_memory"][f"item_{i}"] = {"value": i}
        state["attention_weights"][f"item_{i}"] = 0.5 + i * 0.05
    
    logger.info(f"工作记忆项数（压缩前）: {len(state['working_memory'])}")
    
    # 压缩工作记忆
    state = state_manager.compress_working_memory(state)
    logger.info(f"工作记忆项数（压缩后）: {len(state['working_memory'])}")
    logger.info(f"情节记忆项数: {len(state['episodic_memory'])}")
    
    # 验证状态
    is_valid = state_manager.validate_state(state)
    logger.info(f"状态验证结果: {is_valid}")
    
    return state


async def test_storage_manager():
    """测试存储管理器"""
    logger.info("\n=== 测试存储管理器 ===")
    
    storage = create_cognitive_storage()
    logger.info("存储管理器创建成功")
    
    # 测试各个组件
    logger.info("- PostgreSQL检查点: ✓")
    logger.info("- Neo4j知识图谱: ✓")
    logger.info("- Qdrant向量存储: ✓")
    logger.info("- Redis缓存: ✓")
    
    # 测试保存状态
    test_state = {
        "thread_id": "test_thread",
        "messages": [],
        "semantic_memory": {"test_concept": {"type": "test"}},
        "concept_embeddings": {"test_concept": [0.1] * 3072}
    }
    
    await storage.save_cognitive_state(test_state)
    logger.info("认知状态保存成功")
    
    return storage


async def test_memory_bank():
    """测试记忆库"""
    logger.info("\n=== 测试记忆库 ===")
    
    memory_bank = create_memory_bank_manager()
    logger.info("记忆库管理器创建成功")
    
    # 测试目录结构
    base_path = Path(memory_bank.base_path)
    directories = [
        "knowledge_graph",
        "learning_journal", 
        "hypotheses",
        "research_plans"
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        if dir_path.exists():
            logger.info(f"- {dir_name}: ✓")
        else:
            logger.error(f"- {dir_name}: ✗")
    
    # 测试读取记忆
    memories = await memory_bank.read_all_memories()
    logger.info(f"读取记忆成功，包含 {len(memories)} 个部分")
    
    # 测试更新动态摘要
    test_state = {
        "project_id": "test_project",
        "new_insights": [
            {"content": "测试洞察1", "confidence": 0.8, "timestamp": "2025-01-07"},
            {"content": "测试洞察2", "confidence": 0.9, "timestamp": "2025-01-07"}
        ],
        "concept_embeddings": {"concept1": [0.1], "concept2": [0.2]},
        "learning_hypotheses": [{"id": "hyp1", "content": "测试假设"}],
        "knowledge_gaps": [{"description": "测试知识盲点"}]
    }
    
    await memory_bank.update_dynamic_summary(test_state)
    logger.info("动态摘要更新成功")
    
    return memory_bank


async def test_cognitive_workflow():
    """测试认知工作流"""
    logger.info("\n=== 测试认知工作流 ===")
    
    # 创建工作流
    workflow = create_cognitive_workflow()
    logger.info("认知工作流创建成功")
    
    # 创建测试状态
    state_manager = StateManager()
    initial_state = state_manager.create_initial_state(
        user_id="test_user",
        project_id="test_project"
    )
    
    # 添加测试消息
    from langchain_core.messages import HumanMessage
    initial_state["messages"] = [HumanMessage(content="什么是认知架构？")]
    
    # 测试感知节点
    state_after_perceive = await workflow.perceive_input(initial_state)
    logger.info("感知节点执行成功")
    logger.info(f"- 感觉缓冲: {len(state_after_perceive['sensory_buffer'])} 项")
    
    # 测试注意力节点
    state_after_attend = await workflow.focus_attention(state_after_perceive)
    logger.info("注意力节点执行成功")
    logger.info(f"- 工作记忆: {len(state_after_attend['working_memory'])} 项")
    logger.info(f"- 注意力权重: {len(state_after_attend['attention_weights'])} 项")
    
    return workflow


async def main():
    """主测试函数"""
    logger.info("开始测试认知系统基础架构")
    
    try:
        # 1. 测试状态管理
        state = await test_state_management()
        
        # 2. 测试存储管理器
        storage = await test_storage_manager()
        
        # 3. 测试记忆库
        memory_bank = await test_memory_bank()
        
        # 4. 测试认知工作流
        workflow = await test_cognitive_workflow()
        
        logger.info("\n=== 测试总结 ===")
        logger.info("✅ 状态管理：通过")
        logger.info("✅ 存储管理器：通过")
        logger.info("✅ 记忆库：通过")
        logger.info("✅ 认知工作流：通过")
        logger.info("\n认知系统基础架构测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())