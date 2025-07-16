#!/usr/bin/env python3
"""
测试优化的向量检索服务
"""

import asyncio
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.optimized_retrieval import OptimizedVectorRetrieval, QueryOptimizer
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_query_optimizer():
    """测试查询优化器"""
    logger.info("开始测试查询优化器...")
    
    optimizer = QueryOptimizer()
    
    test_queries = [
        "深度学习在自然语言处理中的应用有哪些？",
        "比较BERT和GPT模型的区别",
        "如何使用Python实现机器学习",
        "2023年最新的AI技术进展",
        "什么是Transformer架构"
    ]
    
    for query in test_queries:
        logger.info(f"\n优化查询: {query}")
        suggestions = await optimizer.optimize_query(query)
        
        logger.info(f"意图: {suggestions['intent']}")
        logger.info(f"实体: {suggestions['entities']}")
        logger.info(f"推荐策略: {suggestions['search_strategy']}")
        logger.info(f"过滤器: {suggestions['filters']}")
        logger.info(f"扩展查询: {suggestions['expanded_queries']}")


async def test_optimized_search():
    """测试优化的搜索功能"""
    logger.info("\n开始测试优化搜索...")
    
    retrieval = OptimizedVectorRetrieval()
    
    # 测试不同搜索策略
    test_cases = [
        {
            "query": "深度学习自然语言处理应用",
            "strategy": "dense",
            "desc": "密集向量搜索"
        },
        {
            "query": "BERT GPT Transformer",
            "strategy": "sparse",
            "desc": "稀疏向量搜索"
        },
        {
            "query": "如何实现文本分类模型",
            "strategy": "hybrid",
            "desc": "混合搜索"
        }
    ]
    
    for case in test_cases:
        logger.info(f"\n测试 {case['desc']}: {case['query']}")
        
        start_time = time.time()
        results = await retrieval.optimized_search(
            collection_name="documents",  # 假设存在这个集合
            query=case["query"],
            top_k=5,
            search_strategy=case["strategy"]
        )
        end_time = time.time()
        
        logger.info(f"搜索策略: {case['strategy']}")
        logger.info(f"返回结果数: {len(results)}")
        logger.info(f"搜索耗时: {end_time - start_time:.2f}秒")
        
        if results:
            logger.info("前3个结果:")
            for i, result in enumerate(results[:3]):
                logger.info(f"{i+1}. 分数: {result.get('score', 0):.3f}")
                logger.info(f"   内容: {result.get('content', '')[:100]}...")


async def test_batch_search():
    """测试批量搜索"""
    logger.info("\n开始测试批量搜索...")
    
    retrieval = OptimizedVectorRetrieval()
    
    queries = [
        "深度学习基础概念",
        "机器学习算法分类",
        "神经网络训练技巧",
        "自然语言处理工具",
        "计算机视觉应用"
    ]
    
    start_time = time.time()
    results = await retrieval.batch_search(
        collection_name="documents",
        queries=queries,
        top_k=3
    )
    end_time = time.time()
    
    logger.info(f"批量搜索 {len(queries)} 个查询")
    logger.info(f"总耗时: {end_time - start_time:.2f}秒")
    logger.info(f"平均每个查询: {(end_time - start_time) / len(queries):.2f}秒")
    
    for query, query_results in results.items():
        logger.info(f"\n查询: {query}")
        logger.info(f"结果数: {len(query_results)}")


async def test_performance_comparison():
    """性能对比测试"""
    logger.info("\n开始性能对比测试...")
    
    retrieval = OptimizedVectorRetrieval()
    query = "深度学习在文本分类中的应用"
    
    # 测试不同策略的性能
    strategies = ["dense", "sparse", "hybrid"]
    
    for strategy in strategies:
        # 预热
        await retrieval.optimized_search(
            collection_name="documents",
            query=query,
            top_k=10,
            search_strategy=strategy
        )
        
        # 实际测试（多次运行取平均）
        times = []
        for _ in range(3):
            start = time.time()
            results = await retrieval.optimized_search(
                collection_name="documents",
                query=query,
                top_k=10,
                search_strategy=strategy
            )
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        logger.info(f"{strategy} 策略平均耗时: {avg_time:.3f}秒")


async def test_cache_effectiveness():
    """测试缓存效果"""
    logger.info("\n开始测试缓存效果...")
    
    retrieval = OptimizedVectorRetrieval()
    query = "机器学习模型评估指标"
    
    # 第一次搜索（无缓存）
    start1 = time.time()
    results1 = await retrieval.optimized_search(
        collection_name="documents",
        query=query,
        top_k=10
    )
    time1 = time.time() - start1
    
    # 第二次搜索（有缓存）
    start2 = time.time()
    results2 = await retrieval.optimized_search(
        collection_name="documents",
        query=query,
        top_k=10
    )
    time2 = time.time() - start2
    
    logger.info(f"第一次搜索（无缓存）: {time1:.3f}秒")
    logger.info(f"第二次搜索（有缓存）: {time2:.3f}秒")
    logger.info(f"加速比: {time1/time2:.2f}x")
    
    # 获取搜索统计
    stats = await retrieval.get_search_stats()
    logger.info(f"\n搜索统计: {stats}")


async def main():
    """主测试函数"""
    try:
        # 运行所有测试
        await test_query_optimizer()
        await test_optimized_search()
        await test_batch_search()
        await test_performance_comparison()
        await test_cache_effectiveness()
        
        logger.info("\n🎉 所有优化检索测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)