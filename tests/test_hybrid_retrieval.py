"""
测试三阶段混合检索系统
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.cognitive.retrieval.hybrid_retrieval import (
    HybridRetrievalSystem,
    HybridQuery,
    hybrid_search,
    create_hybrid_retrieval_system
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_hybrid_query_creation():
    """测试混合查询创建"""
    logger.info("=== 测试混合查询创建 ===")
    
    # 创建基本查询
    query = HybridQuery(
        query="什么是认知架构？",
        query_type="semantic",
        max_results=10
    )
    
    logger.info(f"查询内容: {query.query}")
    logger.info(f"查询类型: {query.query_type}")
    logger.info(f"最大结果数: {query.max_results}")
    logger.info(f"权重配置: Vector={query.vector_weight}, Graph={query.graph_weight}, Memory={query.memory_weight}")
    
    # 创建探索性查询
    explore_query = HybridQuery(
        query="深度学习在认知科学中的应用",
        query_type="exploratory",
        max_results=15,
        vector_weight=0.3,
        graph_weight=0.4,
        memory_weight=0.3
    )
    
    logger.info(f"探索性查询: {explore_query.query}")
    logger.info(f"权重调整: Vector={explore_query.vector_weight}, Graph={explore_query.graph_weight}, Memory={explore_query.memory_weight}")
    
    return query, explore_query


async def test_vector_retriever():
    """测试向量检索器"""
    logger.info("\n=== 测试向量检索器 ===")
    
    system = create_hybrid_retrieval_system({"mock_mode": True})
    
    query = HybridQuery(
        query="认知架构的核心组件",
        query_type="semantic",
        vector_top_k=20
    )
    
    # 测试向量检索
    vector_results = await system.vector_retriever.retrieve(query)
    
    logger.info(f"向量检索结果数: {len(vector_results)}")
    
    # 分析结果类型
    type_counts = {}
    for result in vector_results:
        result_type = result.type
        type_counts[result_type] = type_counts.get(result_type, 0) + 1
    
    logger.info("结果类型分布:")
    for result_type, count in type_counts.items():
        logger.info(f"  {result_type}: {count}")
    
    # 显示前5个结果
    logger.info("前5个结果:")
    for i, result in enumerate(vector_results[:5]):
        logger.info(f"  {i+1}. [{result.type}] {result.content[:50]}... (分数: {result.score:.3f})")
    
    return vector_results


async def test_graph_enhancer():
    """测试图谱增强器"""
    logger.info("\n=== 测试图谱增强器 ===")
    
    system = create_hybrid_retrieval_system({"mock_mode": True})
    
    query = HybridQuery(
        query="认知架构与人工智能的关系",
        query_type="semantic"
    )
    
    # 先获取向量结果
    vector_results = await system.vector_retriever.retrieve(query)
    
    # 图谱增强
    graph_results = await system.graph_enhancer.enhance(query, vector_results)
    
    logger.info(f"图谱增强结果数: {len(graph_results)}")
    
    # 分析增强类型
    enhancement_types = {}
    for result in graph_results:
        enhancement_type = result.metadata.get("enhancement_type", result.type)
        enhancement_types[enhancement_type] = enhancement_types.get(enhancement_type, 0) + 1
    
    logger.info("增强类型分布:")
    for enhancement_type, count in enhancement_types.items():
        logger.info(f"  {enhancement_type}: {count}")
    
    # 显示前3个增强结果
    logger.info("前3个增强结果:")
    for i, result in enumerate(graph_results[:3]):
        logger.info(f"  {i+1}. [{result.type}] {result.content[:50]}... (分数: {result.score:.3f})")
    
    return graph_results


async def test_memory_retriever():
    """测试记忆库检索器"""
    logger.info("\n=== 测试记忆库检索器 ===")
    
    system = create_hybrid_retrieval_system({"mock_mode": True})
    
    query = HybridQuery(
        query="学习效果评估方法",
        query_type="factual"
    )
    
    # 模拟前置结果
    previous_results = []
    
    # 记忆库检索
    memory_results = await system.memory_retriever.retrieve(query, previous_results)
    
    logger.info(f"记忆库检索结果数: {len(memory_results)}")
    
    # 分析记忆类型
    memory_types = {}
    for result in memory_results:
        memory_type = result.metadata.get("memory_type", result.type)
        memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
    
    logger.info("记忆类型分布:")
    for memory_type, count in memory_types.items():
        logger.info(f"  {memory_type}: {count}")
    
    # 显示前3个记忆结果
    logger.info("前3个记忆结果:")
    for i, result in enumerate(memory_results[:3]):
        logger.info(f"  {i+1}. [{result.type}] {result.content[:50]}... (分数: {result.score:.3f})")
    
    return memory_results


async def test_complete_hybrid_retrieval():
    """测试完整的混合检索"""
    logger.info("\n=== 测试完整混合检索 ===")
    
    system = create_hybrid_retrieval_system({"mock_mode": True})
    
    # 测试语义查询
    semantic_query = HybridQuery(
        query="认知负荷理论在教育中的应用",
        query_type="semantic",
        max_results=15
    )
    
    semantic_response = await system.retrieve(semantic_query)
    
    logger.info(f"语义查询响应:")
    logger.info(f"  查询: {semantic_response['query']}")
    logger.info(f"  总结果数: {semantic_response['total_results']}")
    logger.info(f"  返回结果数: {len(semantic_response['results'])}")
    logger.info(f"  检索时间: {semantic_response['retrieval_time']:.3f}秒")
    
    # 阶段统计
    stats = semantic_response['stage_statistics']
    logger.info(f"  阶段统计:")
    logger.info(f"    向量检索: {stats['vector_results']}")
    logger.info(f"    图谱增强: {stats['graph_results']}")
    logger.info(f"    记忆库检索: {stats['memory_results']}")
    
    # 显示前5个最终结果
    logger.info("前5个最终结果:")
    for i, result in enumerate(semantic_response['results'][:5]):
        result_dict = result.__dict__ if hasattr(result, '__dict__') else result
        logger.info(f"  {i+1}. [{result_dict['stage']}|{result_dict['type']}] {result_dict['content'][:50]}... (分数: {result_dict['score']:.3f})")
    
    return semantic_response


async def test_convenience_function():
    """测试便捷函数"""
    logger.info("\n=== 测试便捷函数 ===")
    
    # 使用便捷函数
    response = await hybrid_search(
        query="元认知策略的实际应用",
        query_type="exploratory",
        max_results=10
    )
    
    logger.info(f"便捷函数响应:")
    logger.info(f"  查询: {response['query']}")
    logger.info(f"  结果数: {len(response['results'])}")
    logger.info(f"  检索时间: {response['retrieval_time']:.3f}秒")
    
    return response


async def test_caching():
    """测试缓存功能"""
    logger.info("\n=== 测试缓存功能 ===")
    
    system = create_hybrid_retrieval_system({"mock_mode": True})
    
    query = HybridQuery(
        query="工作记忆的容量限制",
        query_type="factual"
    )
    
    # 第一次查询
    import time
    start_time = time.time()
    response1 = await system.retrieve(query, use_cache=True)
    first_time = time.time() - start_time
    
    # 第二次查询（应该使用缓存）
    start_time = time.time()
    response2 = await system.retrieve(query, use_cache=True)
    second_time = time.time() - start_time
    
    logger.info(f"缓存测试:")
    logger.info(f"  首次查询时间: {first_time:.3f}秒")
    logger.info(f"  缓存查询时间: {second_time:.3f}秒")
    logger.info(f"  结果一致性: {response1['total_results'] == response2['total_results']}")
    
    # 清除缓存
    await system.clear_cache()
    logger.info("缓存已清除")
    
    return response1, response2


async def main():
    """主测试函数"""
    logger.info("开始测试三阶段混合检索系统")
    
    try:
        # 1. 测试查询创建
        query, explore_query = await test_hybrid_query_creation()
        
        # 2. 测试向量检索器
        vector_results = await test_vector_retriever()
        
        # 3. 测试图谱增强器
        graph_results = await test_graph_enhancer()
        
        # 4. 测试记忆库检索器
        memory_results = await test_memory_retriever()
        
        # 5. 测试完整混合检索
        hybrid_response = await test_complete_hybrid_retrieval()
        
        # 6. 测试便捷函数
        convenience_response = await test_convenience_function()
        
        # 7. 测试缓存功能
        cache_response1, cache_response2 = await test_caching()
        
        logger.info("\n=== 测试总结 ===")
        logger.info("✅ 混合查询创建：通过")
        logger.info("✅ 向量检索器：通过")
        logger.info("✅ 图谱增强器：通过")
        logger.info("✅ 记忆库检索器：通过")
        logger.info("✅ 完整混合检索：通过")
        logger.info("✅ 便捷函数：通过")
        logger.info("✅ 缓存功能：通过")
        logger.info("\n三阶段混合检索系统测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())