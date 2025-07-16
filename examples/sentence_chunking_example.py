#!/usr/bin/env python3
"""
句子分块器使用示例
演示如何使用智能句子边界分块器处理文档
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.document.sentence_based_chunker import chunk_by_sentence
from src.core.chunking import ChunkingStrategy, document_chunker


async def example_basic_usage():
    """基础使用示例"""
    print("=== 基础使用示例 ===\n")
    
    # 示例文档
    document = """
    人工智能（AI）正在改变我们的世界。机器学习算法能够从数据中学习模式。
    深度学习是机器学习的一个子集，它使用多层神经网络。这些技术在图像识别、
    自然语言处理和自动驾驶等领域取得了巨大成功。
    
    AI is transforming various industries. From healthcare to finance, 
    intelligent systems are making processes more efficient. Machine learning 
    models can predict outcomes with high accuracy. The future of AI looks 
    promising with continuous advancements in technology.
    """
    
    # 使用句子分块器
    chunks = await chunk_by_sentence(
        text=document,
        document_id="example_doc_001",
        max_tokens=100,  # 每块最多100个token
        sentence_overlap=1,  # 1个句子的重叠
        metadata={
            "source": "example_document",
            "type": "mixed_language"
        }
    )
    
    # 显示结果
    print(f"文档被分成了 {len(chunks)} 块\n")
    
    for i, chunk in enumerate(chunks):
        print(f"块 {i+1}:")
        print(f"  内容: {chunk.content}")
        print(f"  Token数: {chunk.metadata['token_count']}")
        print(f"  句子数: {chunk.metadata['sentence_count']}")
        print(f"  语言: {chunk.metadata['language']}")
        print()


async def example_with_configuration():
    """配置选项示例"""
    print("\n=== 配置选项示例 ===\n")
    
    document = """
    大语言模型（LLM）是当前AI领域的热点。GPT、Claude和其他模型展示了惊人的能力。
    这些模型可以理解和生成人类语言。它们在对话、翻译、摘要等任务中表现出色。
    然而，我们也需要关注AI的伦理和安全问题。确保AI系统的可靠性和公平性至关重要。
    """
    
    # 使用不同的配置
    configs = [
        {"max_tokens": 50, "sentence_overlap": 0, "name": "小块无重叠"},
        {"max_tokens": 150, "sentence_overlap": 2, "name": "大块有重叠"},
    ]
    
    for config in configs:
        print(f"\n配置: {config['name']}")
        chunks = await chunk_by_sentence(
            text=document,
            document_id="config_example",
            max_tokens=config["max_tokens"],
            sentence_overlap=config["sentence_overlap"]
        )
        
        print(f"  块数: {len(chunks)}")
        print(f"  平均token数: {sum(c.metadata['token_count'] for c in chunks) / len(chunks):.1f}")


async def example_integration():
    """与主分块系统集成示例"""
    print("\n=== 集成示例 ===\n")
    
    document = """
    自然语言处理技术的发展历程充满了突破。从早期的规则系统到统计方法，
    再到现在的深度学习。每一次技术革新都带来了性能的飞跃。BERT、GPT等
    预训练模型的出现，更是将NLP推向了新的高度。
    
    The evolution of NLP has been remarkable. Early rule-based systems 
    gave way to statistical methods. Now, deep learning dominates the field.
    Transformer architectures have revolutionized how we process language.
    """
    
    # 使用主分块系统的句子分块策略
    chunks = await document_chunker.chunk_document(
        text=document,
        document_id="integration_example",
        strategy=ChunkingStrategy.SENTENCE_BASED,
        chunk_size=120,  # 会被转换为max_tokens
        chunk_overlap=100,  # 会被转换为1个句子的重叠
        metadata={
            "experiment": "integration_test",
            "version": "1.0"
        }
    )
    
    print(f"使用集成的分块系统，文档被分成了 {len(chunks)} 块\n")
    
    # 显示每块的信息
    for i, chunk in enumerate(chunks):
        print(f"块 {i+1}:")
        print(f"  开始位置: {chunk.start_index}")
        print(f"  结束位置: {chunk.end_index}")
        print(f"  内容预览: {chunk.content[:50]}...")
        print()


async def example_performance_comparison():
    """性能对比示例"""
    print("\n=== 性能对比示例 ===\n")
    
    # 较长的测试文档
    long_document = """
    深度学习在过去十年中取得了巨大的进展。卷积神经网络（CNN）在计算机视觉领域
    取得了突破性成果。循环神经网络（RNN）和长短期记忆网络（LSTM）在序列数据
    处理方面表现出色。然而，真正的革命来自于Transformer架构的提出。
    
    Transformer模型完全基于注意力机制，摒弃了传统的循环结构。这使得模型可以
    并行处理序列数据，大大提高了训练效率。BERT模型通过双向预训练，在多项
    NLP任务上刷新了记录。GPT系列模型则展示了强大的生成能力。
    
    The impact of these models extends beyond academia. In industry,
    they power search engines, translation services, and virtual assistants.
    Companies are investing heavily in AI research. The competition is fierce,
    but it drives innovation forward. We are witnessing a new era of AI.
    
    未来的挑战包括提高模型的效率、可解释性和安全性。研究人员正在探索更小、
    更快的模型架构。同时，确保AI系统的公平性和避免偏见也是重要课题。
    我们需要在技术进步和伦理考虑之间找到平衡。
    """ * 3  # 重复3次以创建更长的文档
    
    import time
    
    # 测试不同策略的性能
    strategies = [
        (ChunkingStrategy.FIXED_SIZE, "固定大小"),
        (ChunkingStrategy.SENTENCE_BASED, "句子边界"),
    ]
    
    for strategy, name in strategies:
        start_time = time.time()
        
        chunks = await document_chunker.chunk_document(
            text=long_document,
            document_id=f"perf_test_{strategy.value}",
            strategy=strategy,
            chunk_size=500 if strategy == ChunkingStrategy.SENTENCE_BASED else 1000
        )
        
        end_time = time.time()
        
        print(f"{name}分块:")
        print(f"  块数: {len(chunks)}")
        print(f"  耗时: {end_time - start_time:.3f}秒")
        print(f"  平均块大小: {sum(len(c.content) for c in chunks) / len(chunks):.0f}字符")
        print()


async def main():
    """运行所有示例"""
    await example_basic_usage()
    await example_with_configuration()
    await example_integration()
    await example_performance_comparison()


if __name__ == "__main__":
    asyncio.run(main())