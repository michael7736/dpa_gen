#!/usr/bin/env python3
"""
分析当前分块策略的效果和优化空间
"""
import asyncio
import sys
from pathlib import Path
from collections import Counter
import statistics

sys.path.append(str(Path(__file__).parent.parent))

from src.core.document.mvp_document_processor import create_mvp_document_processor
from src.database.qdrant_client import get_qdrant_client
from src.utils.logging_utils import get_logger
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = get_logger(__name__)


async def analyze_current_chunking():
    """分析当前分块策略"""
    print("\n" + "="*80)
    print("📊 当前分块策略分析")
    print("="*80)
    
    # 1. 当前配置
    print("\n1️⃣ 当前分块配置:")
    print("   - 分块大小: 150 字符")
    print("   - 重叠大小: 30 字符 (20%)")
    print("   - 分割优先级: \\n\\n > \\n > 。！？ > .!? > 空格 > 字符")
    print("   - 分割器类型: RecursiveCharacterTextSplitter")
    
    # 2. 测试不同类型的文本
    test_texts = {
        "技术文档": """
深度学习基础教程

第一章：神经网络简介
神经网络是深度学习的基础，它模拟人脑的工作方式，通过多层神经元来学习数据的特征表示。

第二章：卷积神经网络（CNN）
CNN在计算机视觉领域表现出色，特别适合处理图像数据。它使用卷积层、池化层和全连接层的组合。
""",
        "对话记录": """
用户：你好，我想了解一下深度学习的应用场景。
助手：深度学习有很多应用场景，主要包括：
1. 计算机视觉：图像分类、目标检测、人脸识别等
2. 自然语言处理：机器翻译、情感分析、文本生成等
3. 语音识别：语音转文字、语音合成等
用户：那在实际项目中如何选择合适的模型？
助手：选择模型需要考虑数据量、计算资源、准确度要求等因素。
""",
        "学术论文": """
Abstract: This paper presents a novel approach to memory systems in AI agents. We propose a hybrid architecture that combines episodic memory, semantic memory, and procedural memory to create more adaptive and intelligent agents. Our experiments show that this integrated approach significantly improves agent performance in complex, long-term tasks.

Introduction: Memory is a fundamental component of intelligent behavior. In artificial intelligence, the ability to store, retrieve, and utilize past experiences is crucial for creating agents that can learn and adapt over time.
"""
    }
    
    # 3. 分析每种文本的分块效果
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=30,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    print("\n2️⃣ 不同文本类型的分块效果:")
    for text_type, text in test_texts.items():
        chunks = splitter.split_text(text)
        chunk_lengths = [len(chunk) for chunk in chunks]
        
        print(f"\n{text_type}:")
        print(f"   - 分块数量: {len(chunks)}")
        print(f"   - 平均长度: {statistics.mean(chunk_lengths):.1f} 字符")
        print(f"   - 长度范围: {min(chunk_lengths)} - {max(chunk_lengths)} 字符")
        print("   - 示例分块:")
        for i, chunk in enumerate(chunks[:2]):
            print(f"     块{i+1}: {chunk[:50]}...")
    
    # 4. 分析真实文档的分块情况
    print("\n3️⃣ 真实文档分块分析:")
    
    # 从Qdrant获取已存储的分块
    qdrant = get_qdrant_client()
    try:
        # 获取最近处理的文档分块
        collection_name = "project_memory_systems_demo"
        points, _ = await qdrant.scroll_points(
            collection_name=collection_name,
            limit=50,
            with_payload=True,
            with_vectors=False
        )
        
        if points:
            chunk_lengths = []
            chunk_endings = Counter()
            
            for point in points:
                content = point.payload.get('content', '')
                chunk_lengths.append(len(content))
                
                # 分析分块结尾
                if content:
                    last_char = content[-1]
                    if last_char in ['.', '。', '!', '！', '?', '？']:
                        chunk_endings['句号结尾'] += 1
                    elif last_char in ['\n']:
                        chunk_endings['换行结尾'] += 1
                    elif last_char in [' ', '　']:
                        chunk_endings['空格结尾'] += 1
                    else:
                        chunk_endings['词中断'] += 1
            
            print(f"   - 分析样本: {len(chunk_lengths)} 个分块")
            print(f"   - 平均长度: {statistics.mean(chunk_lengths):.1f} 字符")
            print(f"   - 标准差: {statistics.stdev(chunk_lengths):.1f}")
            print(f"   - 中位数: {statistics.median(chunk_lengths)}")
            print(f"   - 长度分布:")
            print(f"     < 100字符: {sum(1 for l in chunk_lengths if l < 100)}")
            print(f"     100-150字符: {sum(1 for l in chunk_lengths if 100 <= l <= 150)}")
            print(f"     > 150字符: {sum(1 for l in chunk_lengths if l > 150)}")
            
            print("\n   - 分块边界质量:")
            total = sum(chunk_endings.values())
            for ending_type, count in chunk_endings.most_common():
                percentage = (count / total) * 100
                print(f"     {ending_type}: {count} ({percentage:.1f}%)")
    except Exception as e:
        print(f"   ❌ 无法获取分块数据: {e}")
    
    # 5. 优化建议
    print("\n4️⃣ 优化建议:")
    print("\n   🎯 当前问题:")
    print("   - 固定分块大小可能不适合所有文档类型")
    print("   - 150字符对于某些内容可能太小，导致上下文碎片化")
    print("   - 中文和英文混合时，字符计数可能不准确")
    print("   - 没有考虑语义完整性")
    
    print("\n   💡 优化方案:")
    print("   1. 动态分块大小：根据文档类型调整")
    print("   2. 语义分块：使用句子边界检测")
    print("   3. 滑动窗口：增加上下文连续性")
    print("   4. 混合策略：结合字符数和语义边界")
    print("   5. 元数据增强：为每个分块添加位置和上下文信息")


async def test_optimized_chunking():
    """测试优化的分块策略"""
    print("\n\n" + "="*80)
    print("🔧 优化分块策略测试")
    print("="*80)
    
    # 测试文本
    test_text = """
Memory Systems for AI Agents: A Comprehensive Deep Dive

AI agents must manage and recall information at multiple time scales and contexts. Memory in AI spans short-term (contextual working memory), long-term (persistent knowledge), episodic (event-based), semantic (facts), procedural (skills), and external storage.

Short-term or working memory refers to the immediate context held by an agent (e.g. the current dialogue or task state). Long-term memory stores enduring knowledge or preferences across sessions. Episodic memory records specific events or interactions that an agent experienced. Semantic memory holds general factual or conceptual knowledge.
"""
    
    # 1. 当前策略
    current_splitter = RecursiveCharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=30,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )
    
    # 2. 优化策略1：增大分块，增加重叠
    optimized_1 = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", "! ", "? ", "。", "！", "？", ", ", "，", " "]
    )
    
    # 3. 优化策略2：基于句子的分块
    from langchain.text_splitter import NLTKTextSplitter
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        sentence_splitter = NLTKTextSplitter(chunk_size=200)
        use_sentence = True
    except:
        use_sentence = False
        print("   ⚠️  NLTK未安装，跳过句子分块测试")
    
    # 比较结果
    strategies = [
        ("当前策略(150字符)", current_splitter),
        ("优化策略1(300字符+优化分隔符)", optimized_1)
    ]
    
    if use_sentence:
        strategies.append(("优化策略2(句子分块)", sentence_splitter))
    
    print("\n策略对比:")
    for name, splitter in strategies:
        chunks = splitter.split_text(test_text)
        print(f"\n{name}:")
        print(f"   - 分块数: {len(chunks)}")
        print(f"   - 示例:")
        for i, chunk in enumerate(chunks[:2]):
            print(f"     块{i+1}: {chunk[:80]}...")
            

async def main():
    """主函数"""
    await analyze_current_chunking()
    await test_optimized_chunking()
    
    # 实施建议
    print("\n\n" + "="*80)
    print("🚀 实施建议")
    print("="*80)
    
    print("\n1. 短期优化（立即可实施）:")
    print("   - 将分块大小增加到 256-512 字符")
    print("   - 优化分隔符顺序，优先保持句子完整性")
    print("   - 为不同文档类型设置不同的分块参数")
    
    print("\n2. 中期优化（需要开发）:")
    print("   - 实现基于句子边界的智能分块")
    print("   - 添加分块质量评分机制")
    print("   - 支持中英文混合的分词优化")
    
    print("\n3. 长期优化（架构升级）:")
    print("   - 实现语义感知的分块（基于embedding相似度）")
    print("   - 层次化分块（段落->句子->短语）")
    print("   - 动态分块大小（基于内容复杂度）")


if __name__ == "__main__":
    asyncio.run(main())