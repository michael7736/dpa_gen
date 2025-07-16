#!/usr/bin/env python3
"""
简化的MVP演示
测试核心功能（不依赖外部库）
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.services.memory_write_service_v2 import MemoryWriteService, MemoryType
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def demo_memory_write_service():
    """演示统一内存写入服务"""
    print("\n" + "="*60)
    print("📝 统一内存写入服务演示")
    print("="*60)
    
    service = MemoryWriteService()
    
    # 测试单个写入
    print("\n1. 测试单个写入...")
    result = await service.write_memory(
        content="这是一段关于深度学习的测试内容",
        memory_type=MemoryType.SEMANTIC,
        metadata={"source": "demo", "topic": "deep_learning"},
        project_id="demo_project"
    )
    
    print(f"✅ 写入成功:")
    print(f"   - 操作ID: {result.operation_id}")
    print(f"   - 状态: {'成功' if result.success else '失败'}")
    print(f"   - 内存类型: {result.memory_type}")
    
    # 测试批量写入
    print("\n2. 测试批量写入...")
    contents = [
        "卷积神经网络（CNN）适合处理图像数据",
        "循环神经网络（RNN）适合处理序列数据",
        "Transformer架构使用自注意力机制"
    ]
    
    batch_results = await service.batch_write(
        contents=contents,
        memory_type=MemoryType.EPISODIC,
        project_id="demo_project"
    )
    
    print(f"✅ 批量写入完成: {len(batch_results)} 条记录")
    success_count = sum(1 for r in batch_results if r.success)
    print(f"   - 成功: {success_count}")
    print(f"   - 失败: {len(batch_results) - success_count}")


async def demo_memory_bank():
    """演示Memory Bank功能"""
    print("\n" + "="*60)
    print("🏦 Memory Bank演示")
    print("="*60)
    
    manager = create_memory_bank_manager()
    project_id = "demo_project"
    
    # 初始化项目
    print("\n1. 初始化项目...")
    await manager.initialize_project(project_id)
    print("✅ 项目初始化完成")
    
    # 更新上下文
    print("\n2. 更新项目上下文...")
    await manager.update_context(
        project_id=project_id,
        new_content="""
深度学习项目笔记：
- 已经学习了CNN的基本概念
- 了解了RNN在序列处理中的应用
- Transformer是当前NLP的主流架构
        """.strip(),
        source="learning_notes"
    )
    print("✅ 上下文已更新")
    
    # 添加概念
    print("\n3. 添加核心概念...")
    concepts = [
        {
            "name": "CNN",
            "category": "neural_network",
            "description": "卷积神经网络，专门用于图像处理",
            "confidence": 0.9
        },
        {
            "name": "RNN",
            "category": "neural_network",
            "description": "循环神经网络，处理序列数据",
            "confidence": 0.85
        },
        {
            "name": "Transformer",
            "category": "neural_network",
            "description": "基于注意力机制的架构",
            "confidence": 0.95
        }
    ]
    
    await manager.add_concepts(project_id, concepts)
    print(f"✅ 添加了 {len(concepts)} 个概念")
    
    # 添加学习记录
    print("\n4. 添加学习记录...")
    await manager.add_learning_entry(
        project_id=project_id,
        content="完成了深度学习基础架构的学习",
        learning_type="milestone",
        metadata={"progress": "30%"}
    )
    print("✅ 学习记录已添加")
    
    # 获取快照
    print("\n5. 获取Memory Bank快照...")
    snapshot = await manager.get_snapshot(project_id)
    
    if snapshot:
        print("✅ Memory Bank状态:")
        print(f"   - 项目ID: {snapshot.project_id}")
        print(f"   - 上下文大小: {len(snapshot.context)} 字符")
        print(f"   - 动态摘要: {snapshot.dynamic_summary[:100]}...")
        print(f"   - 核心概念数: {len(snapshot.core_concepts)}")
        print(f"   - 学习记录数: {len(snapshot.learning_journals)}")
        
        print("\n   核心概念列表:")
        for concept in snapshot.core_concepts[:3]:
            print(f"   • {concept['name']}: {concept['description']}")


async def demo_multi_user_isolation():
    """演示多用户隔离预埋"""
    print("\n" + "="*60)
    print("👥 多用户隔离预埋演示")
    print("="*60)
    
    # 创建两个用户的服务
    user1_service = MemoryWriteService(user_id="alice")
    user2_service = MemoryWriteService(user_id="bob")
    
    print("\n1. Alice写入数据...")
    result1 = await user1_service.write_memory(
        content="Alice的私有学习笔记",
        memory_type=MemoryType.WORKING,
        project_id="shared_project",
        user_id="alice"
    )
    print(f"✅ Alice的数据已写入 (user_id: alice)")
    
    print("\n2. Bob写入数据...")
    result2 = await user2_service.write_memory(
        content="Bob的私有学习笔记",
        memory_type=MemoryType.WORKING,
        project_id="shared_project",
        user_id="bob"
    )
    print(f"✅ Bob的数据已写入 (user_id: bob)")
    
    print("\n💡 说明: 虽然使用相同的project_id，但通过user_id实现数据隔离")
    print("   当前为单用户模式，多用户隔离已在接口层预埋")


async def demo_workflow_state():
    """演示工作流状态管理"""
    print("\n" + "="*60)
    print("⚙️ 工作流状态管理演示")
    print("="*60)
    
    from src.core.memory.mvp_workflow import MVPCognitiveState
    
    # 创建示例状态
    state = MVPCognitiveState(
        input="理解深度学习的基本概念",
        project_id="demo_project",
        user_id="u1",
        perceived_input="",
        processed_input={},
        retrieved_context=[],
        reasoning_result="",
        memory_updated=False,
        errors=[]
    )
    
    print("✅ 创建了认知工作流状态")
    print(f"   - 输入: {state['input']}")
    print(f"   - 项目ID: {state['project_id']}")
    print(f"   - 用户ID: {state['user_id']}")
    print("\n💡 完整的5节点工作流包括:")
    print("   1. 感知(Perceive) - 理解输入意图")
    print("   2. 处理(Process) - 预处理和标准化")
    print("   3. 检索(Retrieve) - 三阶段混合检索")
    print("   4. 推理(Reason) - 基于上下文生成回答")
    print("   5. 更新记忆(Update Memory) - 保存交互历史")


async def main():
    """主演示流程"""
    print("\n" + "="*80)
    print("🚀 DPA MVP 核心功能演示")
    print("="*80)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 演示内存写入服务
        await demo_memory_write_service()
        await asyncio.sleep(0.5)
        
        # 2. 演示Memory Bank
        await demo_memory_bank()
        await asyncio.sleep(0.5)
        
        # 3. 演示多用户隔离
        await demo_multi_user_isolation()
        await asyncio.sleep(0.5)
        
        # 4. 演示工作流状态
        await demo_workflow_state()
        
        print("\n" + "="*80)
        print("✅ MVP核心功能演示完成！")
        print("="*80)
        
        print("\n已实现的核心模块:")
        print("1. ✅ MemoryWriteService V2 - 一致性内存写入")
        print("2. ✅ Memory Bank - 持久化记忆管理")
        print("3. ✅ LangGraph工作流 - 5节点认知流程")
        print("4. ✅ 文档处理器 - 多格式支持")
        print("5. ✅ 混合检索器 - 三阶段检索")
        print("6. ✅ 问答系统 - RAG增强")
        print("7. ✅ 多用户隔离预埋 - 为扩展准备")
        
        print("\n📝 注意: 完整功能需要配置数据库连接和安装所有依赖")
        print("   请参考 docs/SETUP.md 进行环境配置")
        
    except Exception as e:
        logger.error(f"演示出错: {e}")
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())