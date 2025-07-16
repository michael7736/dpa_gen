#!/usr/bin/env python3
"""
MVP简化演示脚本
展示核心功能，跳过数据库存储
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.core.memory.mvp_state import MVPCognitiveState, create_initial_state
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


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


async def demo_cognitive_state():
    """演示认知状态管理"""
    print("\n" + "="*60)
    print("🧠 认知状态演示")
    print("="*60)
    
    # 创建初始状态
    state = create_initial_state(
        input_text="解释深度学习中的注意力机制",
        project_id="demo_project",
        user_id="u1"
    )
    
    print(f"\n初始状态:")
    print(f"   - 输入: {state['input']}")
    print(f"   - 项目ID: {state['project_id']}")
    print(f"   - 用户ID: {state['user_id']}")
    print(f"   - 错误列表: {state['errors']}")
    
    # 模拟认知流程
    print("\n模拟5节点认知流程:")
    
    # 1. 感知阶段
    state['perceived_input'] = "用户想了解深度学习中的注意力机制概念"
    print("   ✅ 1. 感知: 理解用户意图")
    
    # 2. 处理阶段
    state['processed_input'] = {
        "topic": "attention_mechanism",
        "domain": "deep_learning",
        "intent": "explain"
    }
    print("   ✅ 2. 处理: 提取关键信息")
    
    # 3. 检索阶段
    state['retrieved_context'] = [
        "注意力机制允许模型关注输入的不同部分",
        "Transformer使用自注意力机制",
        "注意力权重表示重要性分数"
    ]
    print("   ✅ 3. 检索: 找到相关上下文")
    
    # 4. 推理阶段
    state['reasoning_result'] = """
注意力机制是深度学习中的一个重要概念，它允许模型在处理输入时动态地关注不同部分。
主要特点包括：
1. 计算注意力权重来表示不同输入部分的重要性
2. 在Transformer架构中被广泛应用
3. 提高了模型对长序列的处理能力
    """.strip()
    print("   ✅ 4. 推理: 生成回答")
    
    # 5. 记忆更新
    state['memory_updated'] = True
    print("   ✅ 5. 更新: 保存到记忆系统")
    
    print("\n认知流程完成！")


async def demo_document_chunking():
    """演示文档分块"""
    print("\n" + "="*60)
    print("📄 文档分块演示")
    print("="*60)
    
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    # 创建示例文档
    document_text = """
深度学习基础教程

第一章：神经网络简介
神经网络是深度学习的基础，它模拟人脑的工作方式，通过多层神经元来学习数据的特征表示。

第二章：卷积神经网络（CNN）
CNN在计算机视觉领域表现出色，特别适合处理图像数据。它使用卷积层、池化层和全连接层的组合。

第三章：循环神经网络（RNN）
RNN专门处理序列数据，如文本和时间序列。LSTM和GRU是RNN的改进版本，解决了梯度消失问题。

第四章：Transformer架构
Transformer彻底改变了NLP领域，它使用自注意力机制，可以并行处理序列数据，大大提高了训练效率。
    """.strip()
    
    # 创建文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    # 分割文档
    chunks = text_splitter.split_text(document_text)
    
    print(f"\n文档分块结果:")
    print(f"   - 原文长度: {len(document_text)} 字符")
    print(f"   - 分块数量: {len(chunks)}")
    print(f"   - 分块大小: 200 字符")
    print(f"   - 重叠大小: 50 字符")
    
    print("\n分块内容预览:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n   块 {i+1}:")
        print(f"   {chunk[:100]}...")
        print(f"   (长度: {len(chunk)} 字符)")


async def demo_embedding_generation():
    """演示嵌入向量生成（模拟）"""
    print("\n" + "="*60)
    print("🔢 嵌入向量演示")
    print("="*60)
    
    import numpy as np
    
    # 模拟文本
    texts = [
        "深度学习是机器学习的一个分支",
        "CNN适合处理图像数据",
        "RNN适合处理序列数据"
    ]
    
    print("\n生成嵌入向量（模拟）:")
    embeddings = []
    
    for i, text in enumerate(texts):
        # 模拟生成1536维向量
        embedding = np.random.randn(1536)
        embedding = embedding / np.linalg.norm(embedding)  # 归一化
        embeddings.append(embedding)
        
        print(f"\n   文本 {i+1}: {text}")
        print(f"   向量维度: {len(embedding)}")
        print(f"   向量范数: {np.linalg.norm(embedding):.4f}")
        print(f"   前5个值: {embedding[:5].round(4)}")
    
    # 计算相似度
    print("\n\n相似度计算（余弦相似度）:")
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            similarity = np.dot(embeddings[i], embeddings[j])
            print(f"   文本{i+1} vs 文本{j+1}: {similarity:.4f}")


async def main():
    """主演示流程"""
    print("\n" + "="*80)
    print("🚀 DPA MVP核心功能演示（简化版）")
    print("="*80)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Memory Bank演示
        await demo_memory_bank()
        await asyncio.sleep(0.5)
        
        # 2. 认知状态演示
        await demo_cognitive_state()
        await asyncio.sleep(0.5)
        
        # 3. 文档分块演示
        await demo_document_chunking()
        await asyncio.sleep(0.5)
        
        # 4. 嵌入向量演示
        await demo_embedding_generation()
        
        print("\n" + "="*80)
        print("✅ MVP核心功能演示完成！")
        print("="*80)
        
        print("\n已演示的核心功能:")
        print("1. ✅ Memory Bank - 持久化记忆管理")
        print("2. ✅ 认知状态 - 5节点工作流状态")
        print("3. ✅ 文档分块 - 递归字符分割")
        print("4. ✅ 嵌入向量 - 向量化和相似度")
        
        print("\n💡 说明:")
        print("   - 这是简化演示版本，跳过了数据库存储")
        print("   - 完整版本需要配置PostgreSQL、Qdrant、Neo4j等服务")
        print("   - 核心算法和数据结构已经实现")
        
    except Exception as e:
        logger.error(f"演示出错: {e}")
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())