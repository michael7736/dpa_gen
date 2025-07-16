#!/usr/bin/env python3
"""
测试重排序服务
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.reranker import RerankerService
from src.utils.logger import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)


async def test_reranker():
    """测试重排序服务"""
    logger.info("开始测试重排序服务...")
    
    reranker = RerankerService()
    
    # 准备测试数据
    query = "深度学习在自然语言处理中的应用"
    
    chunks = [
        {
            "content": "深度学习是机器学习的一个分支，它通过多层神经网络来学习数据的表示。在自然语言处理领域，深度学习已经取得了显著的成果。",
            "score": 0.85,
            "metadata": {"created_at": datetime.now() - timedelta(days=10)}
        },
        {
            "content": "传统的机器学习方法在处理文本数据时存在局限性。支持向量机和决策树等算法需要手工设计特征。",
            "score": 0.65,
            "metadata": {"created_at": datetime.now() - timedelta(days=30)}
        },
        {
            "content": "自然语言处理（NLP）是人工智能的重要分支。深度学习模型如BERT、GPT等在NLP任务中表现出色，包括文本分类、命名实体识别、机器翻译等。",
            "score": 0.92,
            "metadata": {"created_at": datetime.now() - timedelta(days=5)}
        },
        {
            "content": "深度学习在计算机视觉领域也有广泛应用，如图像分类、目标检测等。卷积神经网络（CNN）是处理图像数据的主要架构。",
            "score": 0.70,
            "metadata": {"created_at": datetime.now() - timedelta(days=15)}
        },
        {
            "content": "Transformer架构彻底改变了NLP领域。通过自注意力机制，Transformer能够更好地捕捉长距离依赖关系。BERT和GPT都基于Transformer架构。",
            "score": 0.88,
            "metadata": {"created_at": datetime.now() - timedelta(days=3)}
        },
        {
            "content": "深度学习模型在NLP中的应用包括：情感分析、文本摘要、问答系统、对话系统等。这些应用已经在实际产品中得到广泛部署。",
            "score": 0.90,
            "metadata": {"created_at": datetime.now() - timedelta(days=7)}
        },
        {
            "content": "深度学习是机器学习的一个分支，使用多层神经网络。在自然语言处理中，深度学习技术已经成为主流方法。",  # 与第一个相似
            "score": 0.83,
            "metadata": {"created_at": datetime.now() - timedelta(days=20)}
        }
    ]
    
    # 测试1: 相似度重排序
    logger.info("\n测试1: 相似度重排序")
    similarity_result = await reranker.rerank(
        query=query,
        chunks=chunks,
        strategy="similarity",
        top_k=5
    )
    
    logger.info("相似度重排序结果:")
    for i, chunk in enumerate(similarity_result):
        logger.info(f"{i+1}. 分数: {chunk['score']:.2f} - {chunk['content'][:50]}...")
    
    # 测试2: 混合重排序
    logger.info("\n测试2: 混合重排序")
    hybrid_result = await reranker.rerank(
        query=query,
        chunks=chunks,
        strategy="hybrid",
        top_k=5
    )
    
    logger.info("混合重排序结果:")
    for i, chunk in enumerate(hybrid_result):
        score = chunk.get('hybrid_score', chunk.get('score', 0))
        logger.info(f"{i+1}. 综合分数: {score:.2f} - {chunk['content'][:50]}...")
    
    # 测试3: 相关性重排序（使用LLM）
    logger.info("\n测试3: 相关性重排序")
    relevance_result = await reranker.rerank(
        query=query,
        chunks=chunks[:3],  # 只用前3个以节省API调用
        strategy="relevance",
        top_k=3
    )
    
    logger.info("相关性重排序结果:")
    for i, chunk in enumerate(relevance_result):
        score = chunk.get('relevance_score', chunk.get('score', 0))
        logger.info(f"{i+1}. 相关性分数: {score:.2f} - {chunk['content'][:50]}...")
    
    # 测试去重功能
    logger.info("\n测试去重功能:")
    logger.info(f"原始块数: {len(chunks)}")
    logger.info(f"混合重排序后块数: {len(hybrid_result)}")
    
    # 验证是否去除了相似内容
    contents = [chunk['content'][:50] for chunk in hybrid_result]
    logger.info(f"去重效果: {'成功' if len(contents) == len(set(contents)) else '有重复'}")
    
    return True


async def test_keyword_matching():
    """测试关键词匹配功能"""
    logger.info("\n测试关键词匹配功能...")
    
    reranker = RerankerService()
    
    # 测试关键词匹配分数计算
    test_cases = [
        {
            "query": "深度学习 自然语言处理",
            "content": "深度学习在自然语言处理中的应用非常广泛",
            "expected": "高分"
        },
        {
            "query": "深度学习 自然语言处理",
            "content": "机器学习是人工智能的一个分支",
            "expected": "低分"
        },
        {
            "query": "BERT transformer",
            "content": "BERT是基于Transformer架构的预训练模型",
            "expected": "高分"
        }
    ]
    
    for case in test_cases:
        score = reranker._calculate_keyword_score(case["query"], case["content"])
        logger.info(f"查询: {case['query']}")
        logger.info(f"内容: {case['content']}")
        logger.info(f"关键词匹配分数: {score:.2f} (预期: {case['expected']})")
        logger.info("")


async def test_freshness_score():
    """测试新鲜度评分"""
    logger.info("\n测试新鲜度评分...")
    
    reranker = RerankerService()
    
    # 测试不同时间的新鲜度分数
    test_dates = [
        (datetime.now() - timedelta(days=1), "1天前"),
        (datetime.now() - timedelta(days=15), "15天前"),
        (datetime.now() - timedelta(days=60), "60天前"),
        (datetime.now() - timedelta(days=200), "200天前"),
        (datetime.now() - timedelta(days=400), "400天前"),
    ]
    
    for date, desc in test_dates:
        metadata = {"created_at": date.isoformat()}
        score = reranker._calculate_freshness_score(metadata)
        logger.info(f"{desc}: 新鲜度分数 = {score:.1f}")


async def main():
    """主测试函数"""
    try:
        # 运行所有测试
        await test_reranker()
        await test_keyword_matching()
        await test_freshness_score()
        
        logger.info("\n🎉 所有重排序测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)