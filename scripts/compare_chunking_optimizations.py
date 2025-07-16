#!/usr/bin/env python3
"""
对比第一步和第二步优化的实际效果
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.core.document.mvp_document_processor import create_mvp_document_processor
from src.core.retrieval.mvp_hybrid_retriever import create_mvp_hybrid_retriever
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def process_and_test(doc_path: str, project_id: str, use_sentence_chunking: bool):
    """处理文档并测试检索效果"""
    print(f"\n{'='*60}")
    print(f"🔧 使用{'句子分块' if use_sentence_chunking else 'Token分块'}策略")
    print(f"{'='*60}")
    
    # 1. 创建处理器
    processor = create_mvp_document_processor(use_sentence_chunking=use_sentence_chunking)
    
    # 2. 处理文档
    result = await processor.process_document(
        file_path=doc_path,
        project_id=project_id
    )
    
    print(f"✅ 文档处理完成:")
    print(f"   - 分块数量: {result.chunk_count}")
    
    # 等待存储完成
    await asyncio.sleep(3)
    
    # 3. 测试检索
    retriever = create_mvp_hybrid_retriever()
    
    test_queries = [
        "episodic memory",
        "working memory vs long-term memory",
        "RAG implementation",
        "catastrophic forgetting",
        "memory types in AI"
    ]
    
    success_count = 0
    for query in test_queries:
        result = await retriever.retrieve(
            query=query,
            project_id=project_id,
            top_k=3
        )
        
        if result.fused_results:
            success_count += 1
    
    print(f"\n📊 检索成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    return success_count / len(test_queries)


async def main():
    print("\n" + "="*80)
    print("🚀 第一步 vs 第二步优化对比测试")
    print("="*80)
    
    doc_path = "/Users/mdwong001/Desktop/code/rag/data/zonghe/MemeoryOpenai.txt"
    
    # 测试第一步优化（Token分块）
    success_rate_step1 = await process_and_test(
        doc_path=doc_path,
        project_id="optimization_step1",
        use_sentence_chunking=False
    )
    
    # 测试第二步优化（句子分块）
    success_rate_step2 = await process_and_test(
        doc_path=doc_path,
        project_id="optimization_step2",
        use_sentence_chunking=True
    )
    
    # 对比分析
    print("\n" + "="*80)
    print("📈 优化效果对比")
    print("="*80)
    
    print(f"\n第一步优化（Token分块）:")
    print(f"  - 检索成功率: {success_rate_step1*100:.1f}%")
    print(f"  - 特点: 基于token计数，优化的分隔符顺序")
    
    print(f"\n第二步优化（句子分块）:")
    print(f"  - 检索成功率: {success_rate_step2*100:.1f}%")
    print(f"  - 特点: 100%句子完整性，基于句子的重叠")
    
    improvement = (success_rate_step2 - success_rate_step1) * 100
    if improvement > 0:
        print(f"\n✨ 第二步优化提升了 {improvement:.1f}% 的检索成功率！")
    elif improvement == 0:
        print(f"\n🔄 两种策略的检索成功率相同")
    else:
        print(f"\n⚠️ 第二步优化的检索成功率略低 {abs(improvement):.1f}%")
    
    print("\n💡 关键洞察:")
    print("1. 句子分块确保了语义的完整性")
    print("2. 基于句子的重叠保持了更好的上下文连续性")
    print("3. 对于学术文档，句子边界是自然的语义分割点")


if __name__ == "__main__":
    asyncio.run(main())