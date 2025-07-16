#!/usr/bin/env python3
"""
测试句子分块器功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.document.sentence_based_chunker import (
    create_sentence_chunker,
    chunk_by_sentence
)
from src.core.chunking import ChunkingStrategy, document_chunker


async def test_sentence_chunker():
    """测试句子分块器"""
    
    # 测试文本样例
    test_texts = {
        "english": """
        Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence. 
        It is concerned with the interactions between computers and human language. In particular, NLP focuses on how 
        to program computers to process and analyze large amounts of natural language data. The goal is a computer 
        capable of understanding the contents of documents, including the contextual nuances of the language within them.
        
        The technology can then accurately extract information and insights contained in the documents. It can also 
        categorize and organize the documents themselves. Challenges in natural language processing frequently involve 
        speech recognition, natural language understanding, and natural language generation.
        """,
        
        "chinese": """
        自然语言处理是语言学、计算机科学和人工智能的一个子领域。它关注计算机和人类语言之间的交互。
        特别是，自然语言处理专注于如何编程计算机来处理和分析大量的自然语言数据。目标是让计算机能够
        理解文档的内容，包括其中语言的上下文细微差别。
        
        该技术可以准确地提取文档中包含的信息和见解。它还可以对文档本身进行分类和组织。自然语言处理
        中的挑战经常涉及语音识别、自然语言理解和自然语言生成。
        """,
        
        "mixed": """
        NLP（自然语言处理）是一个跨学科领域。It combines linguistics, computer science, and AI技术。
        这个领域的主要目标是enable computers to understand人类语言。Through advanced algorithms和深度学习模型，
        NLP systems可以处理各种语言任务。
        
        现代NLP应用包括machine translation（机器翻译）、sentiment analysis（情感分析）和text summarization
        （文本摘要）。这些技术在many industries中得到广泛应用，from healthcare到finance行业。
        """
    }
    
    print("=" * 80)
    print("测试句子分块器")
    print("=" * 80)
    
    # 创建分块器
    chunker = create_sentence_chunker(
        max_tokens=100,  # 设置较小的token限制以便测试
        sentence_overlap=1,
        encoding_model="cl100k_base"
    )
    
    for lang_type, text in test_texts.items():
        print(f"\n\n{'='*40}")
        print(f"测试 {lang_type.upper()} 文本")
        print(f"{'='*40}")
        
        # 方法1：使用分块器实例
        chunks = await chunker.chunk_text(
            text,
            metadata={
                "document_id": f"test_{lang_type}",
                "language": lang_type
            }
        )
        
        print(f"\n分块结果（共 {len(chunks)} 块）：")
        for i, chunk in enumerate(chunks):
            print(f"\n--- 块 {i+1} ---")
            print(f"内容: {chunk.content[:100]}...")
            print(f"Token数: {chunk.metadata.get('token_count', 'N/A')}")
            print(f"句子数: {chunk.metadata.get('sentence_count', 'N/A')}")
            print(f"检测语言: {chunk.metadata.get('language', 'N/A')}")
        
        # 方法2：使用便捷函数
        print(f"\n\n使用便捷函数测试：")
        chunks2 = await chunk_by_sentence(
            text,
            document_id=f"test2_{lang_type}",
            max_tokens=150,
            sentence_overlap=2
        )
        print(f"便捷函数分块结果：{len(chunks2)} 块")
    
    # 测试与主分块系统的集成
    print("\n\n" + "="*80)
    print("测试与主分块系统的集成")
    print("="*80)
    
    chunks3 = await document_chunker.chunk_document(
        text=test_texts["mixed"],
        document_id="integrated_test",
        strategy=ChunkingStrategy.SENTENCE_BASED,
        chunk_size=200,  # 这会被转换为max_tokens
        chunk_overlap=200  # 这会被转换为2个句子的重叠
    )
    
    print(f"\n集成测试结果：{len(chunks3)} 块")
    for i, chunk in enumerate(chunks3):
        print(f"\n块 {i+1}: {chunk.content[:80]}...")


async def test_edge_cases():
    """测试边缘情况"""
    print("\n\n" + "="*80)
    print("测试边缘情况")
    print("="*80)
    
    edge_cases = {
        "no_punctuation": "这是一段没有标点符号的中文文本应该如何处理呢",
        "multiple_punctuation": "真的吗？！！太棒了。。。这样也可以！？",
        "short_text": "短文本。",
        "empty_text": "",
        "only_punctuation": "。。。！！！？？？",
        "mixed_quotes": '他说："这是引号内的内容。" 然后继续说道："还有更多。"',
    }
    
    chunker = create_sentence_chunker(max_tokens=50)
    
    for case_name, text in edge_cases.items():
        print(f"\n测试 {case_name}:")
        try:
            chunks = await chunker.chunk_text(text, {"document_id": f"edge_{case_name}"})
            print(f"  结果: {len(chunks)} 块")
            if chunks:
                print(f"  第一块: '{chunks[0].content}'")
        except Exception as e:
            print(f"  错误: {e}")


if __name__ == "__main__":
    asyncio.run(test_sentence_chunker())
    asyncio.run(test_edge_cases())