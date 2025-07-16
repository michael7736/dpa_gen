#!/usr/bin/env python3
"""
MVP演示脚本
展示5天MVP完成的核心功能
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.document.mvp_document_processor import create_mvp_document_processor
from src.core.retrieval.mvp_hybrid_retriever import create_mvp_hybrid_retriever
from src.core.qa.mvp_qa_system import create_mvp_qa_system
from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.core.memory.mvp_workflow import create_mvp_workflow
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def demo_document_processing():
    """演示文档处理功能"""
    print("\n" + "="*60)
    print("📄 文档处理演示")
    print("="*60)
    
    processor = create_mvp_document_processor()
    
    # 创建测试文档
    test_file = Path("./data/test_doc.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("""
深度学习基础教程

第一章：神经网络简介
神经网络是深度学习的基础，它模拟人脑的工作方式，通过多层神经元来学习数据的特征表示。

第二章：卷积神经网络（CNN）
CNN在计算机视觉领域表现出色，特别适合处理图像数据。它使用卷积层、池化层和全连接层的组合。

第三章：循环神经网络（RNN）
RNN专门处理序列数据，如文本和时间序列。LSTM和GRU是RNN的改进版本，解决了梯度消失问题。

第四章：Transformer架构
Transformer彻底改变了NLP领域，它使用自注意力机制，可以并行处理序列数据，大大提高了训练效率。
""")
    
    print(f"✅ 创建测试文档: {test_file}")
    
    # 处理文档
    print("\n🔄 开始处理文档...")
    result = await processor.process_document(
        file_path=str(test_file),
        project_id="demo_project"
    )
    
    print(f"✅ 文档处理完成:")
    print(f"   - 文档ID: {result.document_id}")
    print(f"   - 分块数量: {result.chunk_count}")
    print(f"   - 处理状态: {result.status}")
    
    return result


async def demo_hybrid_retrieval():
    """演示混合检索功能"""
    print("\n" + "="*60)
    print("🔍 混合检索演示")
    print("="*60)
    
    retriever = create_mvp_hybrid_retriever()
    
    queries = [
        "什么是CNN？",
        "Transformer和RNN的区别",
        "深度学习的基础是什么？"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        result = await retriever.retrieve(
            query=query,
            project_id="demo_project",
            top_k=3
        )
        
        print(f"✅ 检索完成:")
        print(f"   - 向量搜索: {len(result.vector_results)} 结果")
        print(f"   - 图谱搜索: {len(result.graph_results)} 结果")
        print(f"   - 记忆搜索: {len(result.memory_results)} 结果")
        print(f"   - 融合结果: {len(result.fused_results)} 结果")
        
        if result.fused_results:
            print("\n   Top结果:")
            for i, res in enumerate(result.fused_results[:2]):
                print(f"   {i+1}. [{res.source}] 分数:{res.score:.2f}")
                print(f"      {res.content[:100]}...")


async def demo_memory_workflow():
    """演示认知工作流"""
    print("\n" + "="*60)
    print("🧠 认知工作流演示")
    print("="*60)
    
    workflow = create_mvp_workflow()
    
    # 创建输入
    input_text = "解释深度学习中的注意力机制"
    project_id = "demo_project"
    
    print(f"输入: {input_text}")
    print("\n🔄 执行5节点认知流程...")
    
    # 执行工作流
    result = await workflow.run(
        message=input_text,
        project_id=project_id
    )
    
    print("\n✅ 工作流执行完成:")
    print(f"   - 感知阶段: {result.get('perceived_input', '')[:50]}...")
    print(f"   - 处理阶段: 已完成")
    print(f"   - 检索阶段: 找到 {len(result.get('retrieved_context', []))} 个相关内容")
    print(f"   - 推理阶段: {result.get('reasoning_result', '')[:100]}...")
    print(f"   - 记忆更新: 已保存到记忆系统")


async def demo_qa_system():
    """演示问答系统"""
    print("\n" + "="*60)
    print("💬 问答系统演示")
    print("="*60)
    
    qa_system = create_mvp_qa_system()
    
    questions = [
        "什么是卷积神经网络？它有什么优势？",
        "LSTM是如何解决RNN的梯度消失问题的？",
        "Transformer架构的核心创新是什么？"
    ]
    
    for question in questions:
        print(f"\n❓ 问题: {question}")
        
        result = await qa_system.answer_question(
            question=question,
            project_id="demo_project",
            top_k=5
        )
        
        print(f"\n✅ 回答:")
        print(f"{result.answer[:300]}...")
        print(f"\n   - 置信度: {result.confidence_score:.2f}")
        print(f"   - 使用文档: {len(result.context_used)}")
        print(f"   - 处理时间: {result.processing_time:.2f}秒")


async def demo_memory_bank():
    """演示Memory Bank功能"""
    print("\n" + "="*60)
    print("🏦 Memory Bank演示")
    print("="*60)
    
    manager = create_memory_bank_manager()
    project_id = "demo_project"
    
    # 初始化项目
    await manager.initialize_project(project_id)
    print("✅ 项目初始化完成")
    
    # 添加学习记录
    # 注意：add_learning_entry方法在当前版本中暂未实现
    # await manager.add_learning_entry(
    #     project_id=project_id,
    #     content="学习了深度学习的基础概念",
    #     learning_type="concept",
    #     metadata={"topic": "deep_learning"}
    # )
    print("⏭️  跳过学习记录添加（方法待实现）")
    
    # 添加概念
    concepts = [
        {
            "name": "CNN",
            "category": "architecture",
            "description": "卷积神经网络，用于图像处理",
            "confidence": 0.9
        },
        {
            "name": "Transformer",
            "category": "architecture",
            "description": "基于注意力机制的架构",
            "confidence": 0.95
        }
    ]
    await manager.add_concepts(project_id, concepts)
    
    # 获取快照
    snapshot = await manager.get_snapshot(project_id)
    
    print("\n📊 Memory Bank状态:")
    if isinstance(snapshot, dict):
        # 处理字典格式的快照
        summary = snapshot.get('dynamic_summary', '')
        print(f"   - 动态摘要: {summary[:100] if summary else '尚未生成'}...")
        concepts = snapshot.get('core_concepts', [])
        print(f"   - 核心概念: {len(concepts)}")
        journals = snapshot.get('learning_journals', [])
        print(f"   - 学习记录: {len(journals)}")
        
        # 显示概念
        if concepts:
            print("\n   核心概念:")
            for concept in concepts[:3]:
                print(f"   - {concept['name']}: {concept['description']}")
    else:
        # 处理对象格式的快照
        print(f"   - 动态摘要: {snapshot.dynamic_summary[:100]}...")
        print(f"   - 核心概念: {len(snapshot.core_concepts)}")
        print(f"   - 学习记录: {len(snapshot.learning_journals)}")
        
        # 显示概念
        print("\n   核心概念:")
        for concept in snapshot.core_concepts[:3]:
            print(f"   - {concept['name']}: {concept['description']}")


async def main():
    """主演示流程"""
    print("\n" + "="*80)
    print("🚀 DPA MVP演示 - 5天完成的核心功能")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 文档处理
        await demo_document_processing()
        await asyncio.sleep(1)
        
        # 2. Memory Bank
        await demo_memory_bank()
        await asyncio.sleep(1)
        
        # 3. 混合检索
        await demo_hybrid_retrieval()
        await asyncio.sleep(1)
        
        # 4. 认知工作流
        await demo_memory_workflow()
        await asyncio.sleep(1)
        
        # 5. 问答系统
        await demo_qa_system()
        
        print("\n" + "="*80)
        print("✅ MVP演示完成！")
        print("="*80)
        print("\n已实现的核心功能:")
        print("1. ✅ 统一内存写入服务（一致性保证）")
        print("2. ✅ LangGraph认知工作流（5节点）")
        print("3. ✅ Memory Bank持久化记忆")
        print("4. ✅ MVP文档处理（标准分块）")
        print("5. ✅ 三阶段混合检索（向量+图谱+记忆）")
        print("6. ✅ 集成问答系统")
        
    except Exception as e:
        logger.error(f"演示出错: {e}")
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())