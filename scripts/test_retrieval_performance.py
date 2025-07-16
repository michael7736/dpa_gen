"""
测试检索系统性能
比较不同检索策略的响应时间和质量
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from typing import List, Dict, Any

from src.core.retrieval.mvp_hybrid_retriever import create_mvp_hybrid_retriever
from src.core.retrieval.simple_retriever import get_simple_retriever
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


async def test_hybrid_retriever(queries: List[str], project_id: str = None):
    """测试混合检索器性能"""
    retriever = create_mvp_hybrid_retriever()
    results = []
    
    for query in queries:
        start_time = time.time()
        try:
            result = await retriever.retrieve(
                query=query,
                project_id=project_id,
                top_k=10
            )
            duration = time.time() - start_time
            
            results.append({
                "query": query,
                "time": duration,
                "vector_count": len(result.vector_results),
                "graph_count": len(result.graph_results),
                "memory_count": len(result.memory_results),
                "total_count": result.total_results,
                "status": "success"
            })
        except Exception as e:
            duration = time.time() - start_time
            results.append({
                "query": query,
                "time": duration,
                "error": str(e),
                "status": "error"
            })
    
    return results


async def test_simple_retriever(queries: List[str], project_id: str = None):
    """测试简化检索器性能"""
    retriever = get_simple_retriever()
    results = []
    
    for query in queries:
        start_time = time.time()
        try:
            result = await retriever.retrieve(
                query=query,
                project_id=project_id,
                top_k=5
            )
            duration = time.time() - start_time
            
            results.append({
                "query": query,
                "time": duration,
                "count": len(result),
                "avg_score": sum(r.score for r in result) / len(result) if result else 0,
                "status": "success"
            })
        except Exception as e:
            duration = time.time() - start_time
            results.append({
                "query": query,
                "time": duration,
                "error": str(e),
                "status": "error"
            })
    
    return results


async def test_batch_retrieval(queries: List[str], project_id: str = None):
    """测试批量检索性能"""
    retriever = get_simple_retriever()
    
    start_time = time.time()
    try:
        results = await retriever.batch_retrieve(
            queries=queries,
            project_id=project_id,
            top_k=3
        )
        duration = time.time() - start_time
        
        return {
            "total_time": duration,
            "avg_time_per_query": duration / len(queries),
            "queries_processed": len(results),
            "status": "success"
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            "total_time": duration,
            "error": str(e),
            "status": "error"
        }


async def main():
    """运行性能测试"""
    test_queries = [
        "什么是人工智能？",
        "深度学习的优势",
        "机器学习应用",
        "神经网络原理",
        "自然语言处理技术"
    ]
    
    print("="*60)
    print("检索系统性能测试")
    print("="*60)
    
    # 测试混合检索器
    print("\n1. 测试混合检索器（三阶段）...")
    hybrid_start = time.time()
    hybrid_results = await test_hybrid_retriever(test_queries)
    hybrid_total = time.time() - hybrid_start
    
    print(f"\n混合检索结果:")
    for result in hybrid_results:
        if result["status"] == "success":
            print(f"  - {result['query'][:20]}... : {result['time']:.3f}秒 "
                  f"(向量:{result['vector_count']}, 图谱:{result['graph_count']}, "
                  f"记忆:{result['memory_count']})")
        else:
            print(f"  - {result['query'][:20]}... : 错误 - {result['error']}")
    
    hybrid_avg = sum(r["time"] for r in hybrid_results) / len(hybrid_results)
    print(f"\n总耗时: {hybrid_total:.3f}秒, 平均: {hybrid_avg:.3f}秒/查询")
    
    # 测试简化检索器
    print("\n2. 测试简化检索器（仅向量）...")
    simple_start = time.time()
    simple_results = await test_simple_retriever(test_queries)
    simple_total = time.time() - simple_start
    
    print(f"\n简化检索结果:")
    for result in simple_results:
        if result["status"] == "success":
            print(f"  - {result['query'][:20]}... : {result['time']:.3f}秒 "
                  f"(结果数:{result['count']}, 平均分:{result['avg_score']:.3f})")
        else:
            print(f"  - {result['query'][:20]}... : 错误 - {result['error']}")
    
    simple_avg = sum(r["time"] for r in simple_results) / len(simple_results)
    print(f"\n总耗时: {simple_total:.3f}秒, 平均: {simple_avg:.3f}秒/查询")
    
    # 测试批量检索
    print("\n3. 测试批量检索...")
    batch_result = await test_batch_retrieval(test_queries)
    
    if batch_result["status"] == "success":
        print(f"\n批量检索结果:")
        print(f"  - 总耗时: {batch_result['total_time']:.3f}秒")
        print(f"  - 平均每查询: {batch_result['avg_time_per_query']:.3f}秒")
        print(f"  - 处理查询数: {batch_result['queries_processed']}")
    else:
        print(f"\n批量检索失败: {batch_result['error']}")
    
    # 性能对比
    print("\n="*60)
    print("性能对比总结:")
    print("="*60)
    print(f"混合检索器平均响应时间: {hybrid_avg:.3f}秒")
    print(f"简化检索器平均响应时间: {simple_avg:.3f}秒")
    if batch_result["status"] == "success":
        print(f"批量检索平均响应时间: {batch_result['avg_time_per_query']:.3f}秒")
    
    improvement = (hybrid_avg - simple_avg) / hybrid_avg * 100
    print(f"\n性能提升: {improvement:.1f}%")
    
    if simple_avg < 0.5:
        print("✅ 检索性能优秀 (<0.5秒)")
    elif simple_avg < 1.0:
        print("✅ 检索性能良好 (<1秒)")
    else:
        print("⚠️ 检索性能需要进一步优化")


if __name__ == "__main__":
    asyncio.run(main())