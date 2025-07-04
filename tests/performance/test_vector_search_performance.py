#!/usr/bin/env python
"""
向量搜索性能测试
测试不同规模数据集下的向量搜索性能
"""

import asyncio
import time
import random
import statistics
from typing import List, Dict, Any, Tuple
import json
import numpy as np
from datetime import datetime

from ...src.database.qdrant_client import get_qdrant_manager
from ...src.core.vectorization import VectorStore
from ...src.config.settings import get_settings

settings = get_settings()


class VectorSearchBenchmark:
    """向量搜索性能基准测试"""
    
    def __init__(self):
        self.qdrant = get_qdrant_manager()
        self.vector_store = VectorStore()
        self.test_collection = "vector_benchmark"
        self.vector_dim = settings.ai_model.embedding_dimension
        self.results = {}
    
    async def setup_test_data(self, num_vectors: int) -> None:
        """准备测试数据"""
        print(f"\n准备 {num_vectors} 个测试向量...")
        
        # 创建测试集合
        await self.qdrant.create_collection(
            collection_name=self.test_collection,
            vector_size=self.vector_dim,
            on_disk=False  # 内存模式，性能更好
        )
        
        # 批量插入向量
        batch_size = 100
        for i in range(0, num_vectors, batch_size):
            points = []
            for j in range(min(batch_size, num_vectors - i)):
                idx = i + j
                # 生成随机向量
                vector = np.random.rand(self.vector_dim).tolist()
                
                # 创建元数据
                payload = {
                    "id": f"doc_{idx}",
                    "text": f"这是测试文档 {idx} 的内容",
                    "category": random.choice(["tech", "science", "business", "health"]),
                    "score": random.random(),
                    "timestamp": datetime.now().isoformat()
                }
                
                points.append({
                    "id": str(idx),
                    "vector": vector,
                    "payload": payload
                })
            
            await self.qdrant.upsert(
                collection_name=self.test_collection,
                points=points
            )
            
            if (i + batch_size) % 1000 == 0:
                print(f"  已插入 {i + batch_size} 个向量")
    
    async def benchmark_search_performance(
        self,
        num_queries: int = 100,
        top_k_values: List[int] = [1, 5, 10, 20, 50]
    ) -> Dict[str, Any]:
        """测试搜索性能"""
        results = {}
        
        for top_k in top_k_values:
            print(f"\n测试 top_k={top_k} 的搜索性能...")
            
            search_times = []
            for _ in range(num_queries):
                # 生成随机查询向量
                query_vector = np.random.rand(self.vector_dim).tolist()
                
                start = time.time()
                results_list = await self.qdrant.search(
                    collection_name=self.test_collection,
                    query_vector=query_vector,
                    limit=top_k
                )
                search_time = time.time() - start
                search_times.append(search_time)
            
            results[f"top_{top_k}"] = {
                "num_queries": num_queries,
                "mean_time_ms": statistics.mean(search_times) * 1000,
                "median_time_ms": statistics.median(search_times) * 1000,
                "min_time_ms": min(search_times) * 1000,
                "max_time_ms": max(search_times) * 1000,
                "p95_time_ms": sorted(search_times)[int(len(search_times) * 0.95)] * 1000,
                "p99_time_ms": sorted(search_times)[int(len(search_times) * 0.99)] * 1000,
                "queries_per_second": num_queries / sum(search_times)
            }
        
        return results
    
    async def benchmark_filtered_search(self, num_queries: int = 100) -> Dict[str, Any]:
        """测试带过滤条件的搜索性能"""
        print("\n测试带过滤条件的搜索...")
        
        filter_conditions = [
            {"category": "tech"},
            {"score": {"$gte": 0.5}},
            {"$and": [{"category": "science"}, {"score": {"$gte": 0.7}}]},
            {"$or": [{"category": "tech"}, {"category": "business"}]}
        ]
        
        results = {}
        
        for i, filter_cond in enumerate(filter_conditions):
            search_times = []
            
            for _ in range(num_queries):
                query_vector = np.random.rand(self.vector_dim).tolist()
                
                start = time.time()
                results_list = await self.qdrant.search(
                    collection_name=self.test_collection,
                    query_vector=query_vector,
                    query_filter=filter_cond,
                    limit=10
                )
                search_time = time.time() - start
                search_times.append(search_time)
            
            results[f"filter_{i}"] = {
                "filter": str(filter_cond),
                "mean_time_ms": statistics.mean(search_times) * 1000,
                "median_time_ms": statistics.median(search_times) * 1000,
                "p95_time_ms": sorted(search_times)[int(len(search_times) * 0.95)] * 1000
            }
        
        return results
    
    async def benchmark_batch_search(self, batch_sizes: List[int] = [1, 5, 10, 20]) -> Dict[str, Any]:
        """测试批量搜索性能"""
        print("\n测试批量搜索性能...")
        
        results = {}
        
        for batch_size in batch_sizes:
            print(f"  批量大小: {batch_size}")
            
            total_time = 0
            num_batches = 20
            
            for _ in range(num_batches):
                # 生成批量查询向量
                query_vectors = [
                    np.random.rand(self.vector_dim).tolist()
                    for _ in range(batch_size)
                ]
                
                start = time.time()
                
                # 批量搜索
                tasks = [
                    self.qdrant.search(
                        collection_name=self.test_collection,
                        query_vector=qv,
                        limit=10
                    )
                    for qv in query_vectors
                ]
                
                await asyncio.gather(*tasks)
                batch_time = time.time() - start
                total_time += batch_time
            
            avg_batch_time = total_time / num_batches
            queries_per_second = batch_size / avg_batch_time
            
            results[f"batch_{batch_size}"] = {
                "batch_size": batch_size,
                "avg_batch_time_ms": avg_batch_time * 1000,
                "queries_per_second": queries_per_second,
                "avg_time_per_query_ms": (avg_batch_time / batch_size) * 1000
            }
        
        return results
    
    async def benchmark_scalability(
        self,
        dataset_sizes: List[int] = [1000, 5000, 10000, 50000]
    ) -> Dict[str, Any]:
        """测试可扩展性"""
        print("\n=== 可扩展性测试 ===")
        
        results = {}
        
        for size in dataset_sizes:
            print(f"\n测试数据集大小: {size}")
            
            # 清理并重建数据
            await self.qdrant.delete_collection(self.test_collection)
            await self.setup_test_data(size)
            
            # 测试搜索性能
            search_times = []
            num_queries = 50
            
            for _ in range(num_queries):
                query_vector = np.random.rand(self.vector_dim).tolist()
                
                start = time.time()
                await self.qdrant.search(
                    collection_name=self.test_collection,
                    query_vector=query_vector,
                    limit=10
                )
                search_times.append(time.time() - start)
            
            results[f"size_{size}"] = {
                "dataset_size": size,
                "mean_search_time_ms": statistics.mean(search_times) * 1000,
                "median_search_time_ms": statistics.median(search_times) * 1000,
                "p95_search_time_ms": sorted(search_times)[int(len(search_times) * 0.95)] * 1000
            }
        
        return results
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """运行综合性能测试"""
        print("\n=== 向量搜索综合性能测试 ===")
        
        # 准备标准测试数据集
        await self.setup_test_data(10000)
        
        # 1. 基础搜索性能
        search_results = await self.benchmark_search_performance()
        
        # 2. 过滤搜索性能
        filter_results = await self.benchmark_filtered_search()
        
        # 3. 批量搜索性能
        batch_results = await self.benchmark_batch_search()
        
        # 4. 可扩展性测试
        scalability_results = await self.benchmark_scalability()
        
        # 清理测试数据
        await self.qdrant.delete_collection(self.test_collection)
        
        return {
            "search_performance": search_results,
            "filtered_search": filter_results,
            "batch_search": batch_results,
            "scalability": scalability_results
        }
    
    def generate_optimization_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 分析搜索性能
        if results["search_performance"]["top_10"]["mean_time_ms"] > 50:
            recommendations.append("搜索延迟较高，建议优化索引参数或使用更快的硬件")
        
        # 分析可扩展性
        scalability = results["scalability"]
        if scalability["size_50000"]["mean_search_time_ms"] > scalability["size_1000"]["mean_search_time_ms"] * 5:
            recommendations.append("大数据集性能下降明显，建议使用分片或优化HNSW参数")
        
        # 分析批量搜索
        batch = results["batch_search"]
        if batch["batch_10"]["avg_time_per_query_ms"] > batch["batch_1"]["avg_batch_time_ms"] / 5:
            recommendations.append("批量搜索效率低，建议实现真正的批量搜索API")
        
        return recommendations


async def main():
    """主测试函数"""
    benchmark = VectorSearchBenchmark()
    
    start_time = datetime.now()
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行综合测试
    results = await benchmark.run_comprehensive_benchmark()
    
    # 生成优化建议
    recommendations = benchmark.generate_optimization_recommendations(results)
    
    # 生成报告
    report = {
        "test_date": datetime.now().isoformat(),
        "test_duration_seconds": (datetime.now() - start_time).total_seconds(),
        "environment": {
            "vector_dimension": benchmark.vector_dim,
            "database": "Qdrant",
            "host": settings.qdrant.host
        },
        "results": results,
        "recommendations": recommendations,
        "summary": {
            "avg_search_10_ms": results["search_performance"]["top_10"]["mean_time_ms"],
            "search_qps": results["search_performance"]["top_10"]["queries_per_second"],
            "scalability_factor": (
                results["scalability"]["size_50000"]["mean_search_time_ms"] /
                results["scalability"]["size_1000"]["mean_search_time_ms"]
            )
        }
    }
    
    # 保存报告
    report_file = f"vector_search_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存到: {report_file}")
    
    # 打印摘要
    print("\n=== 性能摘要 ===")
    print(f"平均搜索时间 (top-10): {report['summary']['avg_search_10_ms']:.2f} ms")
    print(f"搜索QPS: {report['summary']['search_qps']:.1f}")
    print(f"扩展性因子 (50k/1k): {report['summary']['scalability_factor']:.2f}x")
    
    if recommendations:
        print("\n=== 优化建议 ===")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")


if __name__ == "__main__":
    asyncio.run(main())