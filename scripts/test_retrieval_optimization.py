#!/usr/bin/env python3
"""
测试检索优化效果
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
    print("\n" + "="*60)
    print("🔍 检索优化测试")
    print("="*60)
    
    # 1. 首先处理文档（使用新的分块策略）
    print("\n📄 处理文档（优化后的分块）...")
    processor = create_mvp_document_processor()
    
    # 删除并重新创建测试文档
    test_file = Path("./data/test_doc.txt")
    if test_file.exists():
        test_file.unlink()
    
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
    
    # 处理文档
    result = await processor.process_document(
        file_path=str(test_file),
        project_id="optimized_demo"
    )
    
    print(f"✅ 文档处理完成:")
    print(f"   - 文档ID: {result.document_id}")
    print(f"   - 分块数量: {result.chunk_count}")
    print(f"   - 每个分块大小: ~300字符")
    
    # 等待一下让存储完成
    await asyncio.sleep(2)
    
    # 2. 测试检索
    print("\n🔍 测试优化后的检索...")
    retriever = create_mvp_hybrid_retriever()
    
    test_queries = [
        "什么是CNN？",
        "卷积神经网络",
        "Transformer和RNN的区别",
        "LSTM是什么",
        "深度学习的基础是什么？",
        "神经网络",
        "图像处理",
        "序列数据处理",
        "注意力机制"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        result = await retriever.retrieve(
            query=query,
            project_id="optimized_demo",
            top_k=3
        )
        
        print(f"✅ 检索结果:")
        print(f"   - 向量搜索: {len(result.vector_results)} 结果")
        print(f"   - 融合结果: {len(result.fused_results)} 结果")
        
        if result.fused_results:
            print("   Top结果:")
            for i, res in enumerate(result.fused_results[:2]):
                print(f"   {i+1}. 分数:{res.score:.2f}")
                print(f"      {res.content[:80]}...")
    
    # 3. 对比统计
    print("\n" + "="*60)
    print("📊 优化效果总结")
    print("="*60)
    print("✅ 分块策略优化:")
    print("   - 分块大小: 1000 → 300 字符")
    print("   - 重叠大小: 200 → 50 字符")
    print("   - 预期效果: 更细粒度的检索")
    print("\n✅ 相似度阈值优化:")
    print("   - 阈值: 0.6 → 0.3")
    print("   - 预期效果: 更高的召回率")


if __name__ == "__main__":
    asyncio.run(main())