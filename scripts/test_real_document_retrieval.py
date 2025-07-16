#!/usr/bin/env python3
"""
使用真实长文档测试检索优化效果
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.core.document.mvp_document_processor import create_mvp_document_processor
from src.core.retrieval.mvp_hybrid_retriever import create_mvp_hybrid_retriever
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def main():
    print("\n" + "="*80)
    print("🔍 真实文档检索测试 - Memory Systems for AI Agents")
    print("="*80)
    
    # 1. 处理真实文档
    print("\n📄 处理文档...")
    processor = create_mvp_document_processor()
    
    # 使用Memory Systems文档
    doc_path = "/Users/mdwong001/Desktop/code/rag/data/zonghe/MemeoryOpenai.txt"
    
    # 处理文档
    result = await processor.process_document(
        file_path=doc_path,
        project_id="memory_systems_demo"
    )
    
    print(f"✅ 文档处理完成:")
    print(f"   - 文档ID: {result.document_id}")
    print(f"   - 分块数量: {result.chunk_count}")
    print(f"   - 分块策略: 150字符/块，30字符重叠")
    
    # 等待存储完成
    await asyncio.sleep(3)
    
    # 2. 测试各种查询
    print("\n🔍 测试检索效果...")
    retriever = create_mvp_hybrid_retriever()
    
    test_queries = [
        # 概念性查询
        ("What is episodic memory?", "情景记忆查询"),
        ("semantic memory", "语义记忆查询"),
        ("working memory vs long-term memory", "工作记忆vs长期记忆"),
        
        # 技术性查询
        ("RAG implementation", "RAG实现"),
        ("fine-tuning for memory", "微调记忆"),
        ("vector stores", "向量存储"),
        ("catastrophic forgetting", "灾难性遗忘"),
        
        # 应用性查询
        ("personal assistant memory", "个人助手记忆"),
        ("continual learning", "持续学习"),
        ("memory types in AI", "AI中的记忆类型")
    ]
    
    success_count = 0
    for query, desc in test_queries:
        print(f"\n查询: {query} ({desc})")
        result = await retriever.retrieve(
            query=query,
            project_id="memory_systems_demo",
            top_k=3
        )
        
        print(f"✅ 检索结果:")
        print(f"   - 向量搜索: {len(result.vector_results)} 结果")
        
        if result.fused_results:
            success_count += 1
            print("   Top结果:")
            for i, res in enumerate(result.fused_results[:2]):
                print(f"   {i+1}. [分数:{res.score:.3f}]")
                # 清理内容中的换行符
                content = res.content.replace('\n', ' ').strip()
                print(f"      {content[:100]}...")
        else:
            print("   ❌ 未找到相关结果")
    
    # 3. 统计分析
    print("\n" + "="*80)
    print("📊 检索效果分析")
    print("="*80)
    print(f"✅ 检索成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    print("\n优化效果:")
    print("1. 分块策略: 150字符分块确保细粒度匹配")
    print("2. 相似度阈值: 0.3提高召回率")
    print("3. 真实文档: 专业内容的语义检索测试")
    
    # 4. 展示分块效果
    print("\n📄 分块示例（前3个块）:")
    # 从Qdrant获取一些分块
    from src.database.qdrant_client import get_qdrant_client
    qdrant = get_qdrant_client()
    
    try:
        # 获取集合中的前几个点
        points = await qdrant.scroll_points(
            collection_name=f"project_memory_systems_demo",
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        for i, point in enumerate(points[0][:3]):
            print(f"\n块 {i+1}:")
            content = point.payload.get('content', '').replace('\n', ' ').strip()
            print(f"  内容: {content[:150]}...")
            print(f"  长度: {len(content)} 字符")
    except Exception as e:
        print(f"无法获取分块示例: {e}")


if __name__ == "__main__":
    asyncio.run(main())