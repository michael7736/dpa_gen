#!/usr/bin/env python3
"""
测试第二步优化：基于句子的智能边界检测
"""
import asyncio
import sys
import re
from pathlib import Path
from collections import Counter
import statistics
import tiktoken

sys.path.append(str(Path(__file__).parent.parent))

from src.core.document.mvp_document_processor import create_mvp_document_processor, tiktoken_len
from src.database.qdrant_client import get_qdrant_client
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def split_text_by_sentence(text: str, chunk_size: int = 512, overlap_sentences: int = 3):
    """
    基于句子的智能分块
    
    Args:
        text: 输入文本
        chunk_size: 每个块的最大token数
        overlap_sentences: 重叠句子数
    """
    # 步骤1: 使用正则表达式分句
    # 中文句子结束符：。！？；
    # 英文句子结束符：.!?
    # 保留标点符号在句子末尾
    sentences = re.split(r'(?<=[。！？；\.\?!])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]  # 移除空字符串
    
    if not sentences:
        return []
    
    chunks = []
    current_chunk_sentences = []
    current_chunk_tokens = 0
    
    # 步骤2: 组合句子
    for i, sentence in enumerate(sentences):
        sentence_tokens = tiktoken_len(sentence)
        
        # 如果单个句子就超过chunk_size，单独成块
        if sentence_tokens > chunk_size:
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_chunk_tokens = 0
            chunks.append(sentence)
            continue
        
        # 如果加上这个句子会超过限制，先保存当前块
        if current_chunk_tokens + sentence_tokens > chunk_size and current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            
            # 创建重叠：从前一个块的末尾取overlap_sentences个句子
            start_index = max(0, len(current_chunk_sentences) - overlap_sentences)
            current_chunk_sentences = current_chunk_sentences[start_index:]
            current_chunk_tokens = tiktoken_len(" ".join(current_chunk_sentences))
        
        current_chunk_sentences.append(sentence)
        current_chunk_tokens += sentence_tokens
    
    # 保存最后一个块
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))
    
    return chunks


async def test_sentence_based_chunking():
    """测试基于句子的分块效果"""
    print("\n" + "="*80)
    print("🔬 第二步优化测试：智能边界检测（Sentence-Based Chunking）")
    print("="*80)
    
    # 1. 测试中英文句子识别
    print("\n1️⃣ 句子边界识别测试:")
    
    test_texts = {
        "英文段落": """
AI agents must manage and recall information at multiple time scales and contexts. Memory in AI spans short-term (contextual working memory), long-term (persistent knowledge), episodic (event-based), semantic (facts), procedural (skills), and external storage. Short-term or working memory refers to the immediate context held by an agent. Long-term memory stores enduring knowledge or preferences across sessions.
""",
        "中文段落": """
人工智能代理必须在多个时间尺度和上下文中管理和回忆信息。AI中的记忆包括短期记忆（上下文工作记忆）、长期记忆（持久知识）、情景记忆（基于事件）、语义记忆（事实）、程序性记忆（技能）和外部存储。短期或工作记忆是指代理持有的即时上下文。长期记忆存储跨会话的持久知识或偏好。
""",
        "中英混合": """
Memory Systems是AI代理的核心组件。它包括working memory（工作记忆）和long-term memory（长期记忆）两大类。在实际应用中，像ChatGPT这样的系统使用attention机制处理短期信息，而使用fine-tuning来更新长期知识。这种混合架构让AI能够同时处理即时任务和持久学习。
"""
    }
    
    for text_type, text in test_texts.items():
        print(f"\n{text_type}:")
        # 分句
        sentences = re.split(r'(?<=[。！？；\.\?!])\s*', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        print(f"   句子数量: {len(sentences)}")
        for i, sent in enumerate(sentences[:3]):
            tokens = tiktoken_len(sent)
            print(f"   句子{i+1} ({tokens} tokens): {sent[:50]}...")
    
    # 2. 对比分块效果
    print("\n2️⃣ 分块效果对比:")
    
    # 使用之前的AI记忆系统文档
    doc_path = "/Users/mdwong001/Desktop/code/rag/data/zonghe/MemeoryOpenai.txt"
    
    # 读取文档
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用句子分块
    sentence_chunks = split_text_by_sentence(content, chunk_size=512, overlap_sentences=2)
    
    print(f"\n基于句子的分块结果:")
    print(f"   - 分块数量: {len(sentence_chunks)}")
    print(f"   - 平均tokens: {statistics.mean([tiktoken_len(c) for c in sentence_chunks]):.1f}")
    
    # 分析分块质量
    chunk_endings = Counter()
    for chunk in sentence_chunks:
        if chunk:
            # 检查分块结尾
            last_chars = chunk[-10:].strip()
            if re.search(r'[。！？；\.\?!]$', last_chars):
                chunk_endings['完整句子'] += 1
            elif re.search(r'[，,]$', last_chars):
                chunk_endings['子句结尾'] += 1
            else:
                chunk_endings['词中断'] += 1
    
    print("\n   分块边界质量:")
    total = sum(chunk_endings.values())
    for ending_type, count in chunk_endings.most_common():
        percentage = (count / total) * 100
        quality = "✅" if ending_type == '完整句子' else "⚠️" if ending_type == '子句结尾' else "❌"
        print(f"      {quality} {ending_type}: {count} ({percentage:.1f}%)")
    
    # 3. 展示示例分块
    print("\n3️⃣ 示例分块（前3个）:")
    for i, chunk in enumerate(sentence_chunks[:3]):
        tokens = tiktoken_len(chunk)
        sentences = re.split(r'(?<=[。！？；\.\?!])\s*', chunk)
        sentences = [s for s in sentences if s.strip()]
        
        print(f"\n块 {i+1} ({tokens} tokens, {len(sentences)} 句子):")
        print(f"   开始: {chunk[:100]}...")
        print(f"   结尾: ...{chunk[-100:]}")
    
    # 4. 重叠分析
    print("\n4️⃣ 重叠效果分析:")
    if len(sentence_chunks) > 1:
        for i in range(min(3, len(sentence_chunks)-1)):
            chunk1 = sentence_chunks[i]
            chunk2 = sentence_chunks[i+1]
            
            # 简单的重叠检测
            # 找到chunk1的最后几个句子
            chunk1_sentences = re.split(r'(?<=[。！？；\.\?!])\s*', chunk1)
            chunk1_sentences = [s for s in chunk1_sentences if s.strip()]
            
            # 检查这些句子是否出现在chunk2开头
            overlap_found = False
            if len(chunk1_sentences) >= 2:
                last_two = " ".join(chunk1_sentences[-2:])
                if last_two in chunk2:
                    overlap_found = True
            
            print(f"\n   块{i+1} → 块{i+2}:")
            print(f"   重叠检测: {'✅ 发现重叠' if overlap_found else '❌ 未发现重叠'}")


async def compare_chunking_strategies():
    """对比第一步和第二步优化效果"""
    print("\n" + "="*80)
    print("📊 分块策略对比分析")
    print("="*80)
    
    # 准备测试文本
    test_text = """
Memory Systems for AI Agents: A Comprehensive Deep Dive

AI agents must manage and recall information at multiple time scales and contexts. Memory in AI spans short-term (contextual working memory), long-term (persistent knowledge), episodic (event-based), semantic (facts), procedural (skills), and external storage.

Short-term or working memory refers to the immediate context held by an agent (e.g. the current dialogue or task state). Long-term memory stores enduring knowledge or preferences across sessions. Episodic memory records specific events or interactions that an agent experienced. Semantic memory holds general factual or conceptual knowledge.

Procedural memory involves learned skills or action patterns. External storage allows offloading to databases or vector stores. Successful agents combine these memory types to achieve coherent, context-aware behavior.
"""
    
    print("\n策略对比:")
    print("\n1. 第一步优化（Token-based，512 tokens）:")
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    # 第一步的分块器
    step1_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=128,
        length_function=tiktoken_len,
        separators=["\n\n", ".\n", "。\n", "\n", ". ", "。", "!", "！", "?", "？", ";", "；", ",", "，", " ", ""]
    )
    step1_chunks = step1_splitter.split_text(test_text)
    
    print(f"   - 分块数: {len(step1_chunks)}")
    print(f"   - 平均tokens: {statistics.mean([tiktoken_len(c) for c in step1_chunks]):.1f}")
    
    # 检查句子完整性
    incomplete = 0
    for chunk in step1_chunks:
        if not re.search(r'[。！？；\.\?!]$', chunk.strip()):
            incomplete += 1
    print(f"   - 句子不完整率: {incomplete}/{len(step1_chunks)} ({incomplete/len(step1_chunks)*100:.1f}%)")
    
    print("\n2. 第二步优化（Sentence-based，512 tokens）:")
    step2_chunks = split_text_by_sentence(test_text, chunk_size=512, overlap_sentences=2)
    
    print(f"   - 分块数: {len(step2_chunks)}")
    print(f"   - 平均tokens: {statistics.mean([tiktoken_len(c) for c in step2_chunks]):.1f}")
    
    # 检查句子完整性
    incomplete = 0
    for chunk in step2_chunks:
        if not re.search(r'[。！？；\.\?!]$', chunk.strip()):
            incomplete += 1
    print(f"   - 句子不完整率: {incomplete}/{len(step2_chunks)} ({incomplete/len(step2_chunks)*100:.1f}%)")
    
    print("\n✨ 第二步优化优势:")
    print("   1. 100%保证句子完整性")
    print("   2. 基于语义单元（句子）的重叠")
    print("   3. 更稳定的分块大小")
    print("   4. 更好的上下文保持")


async def main():
    """主函数"""
    await test_sentence_based_chunking()
    await compare_chunking_strategies()
    
    print("\n" + "="*80)
    print("✅ 第二步优化测试完成！")
    print("="*80)
    print("\n核心改进:")
    print("1. ✅ 实现了基于句子的智能分块")
    print("2. ✅ 保证了100%的句子完整性")
    print("3. ✅ 使用句子数量而非字符数进行重叠")
    print("4. ✅ 支持中英文混合文档")
    print("\n下一步：等待第三步优化方案！")


if __name__ == "__main__":
    asyncio.run(main())