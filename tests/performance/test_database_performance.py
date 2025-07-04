#!/usr/bin/env python
"""
数据库性能基准测试
测试PostgreSQL、Qdrant、Neo4j和Redis的性能
"""

import asyncio
import time
import random
import statistics
from typing import List, Dict, Any
from datetime import datetime
import json
import numpy as np

from ...src.database.postgresql import get_session
from ...src.database.qdrant_client import get_qdrant_manager
from ...src.database.neo4j_client import get_neo4j_manager
from ...src.database.redis_client import get_redis_client
from ...src.models.document import Document
from ...src.models.chunk import Chunk
from ...src.config.settings import get_settings

settings = get_settings()


class DatabaseBenchmark:
    """数据库性能基准测试"""
    
    def __init__(self):
        self.results = {
            "postgresql": {},
            "qdrant": {},
            "neo4j": {},
            "redis": {}
        }
    
    async def benchmark_postgresql(self):
        """PostgreSQL性能测试"""
        print("\n=== PostgreSQL性能测试 ===")
        
        # 1. 插入性能测试
        print("\n1. 测试插入性能...")
        insert_times = []
        
        async with get_session() as session:
            for i in range(100):
                start = time.time()
                
                doc = Document(
                    title=f"测试文档_{i}",
                    content=f"这是测试内容 " * 100,
                    type="text",
                    project_id="test_project",
                    status="pending"
                )
                session.add(doc)
                await session.commit()
                
                insert_times.append(time.time() - start)
        
        self.results["postgresql"]["insert"] = {
            "count": len(insert_times),
            "mean": statistics.mean(insert_times),
            "median": statistics.median(insert_times),
            "min": min(insert_times),
            "max": max(insert_times)
        }
        
        # 2. 查询性能测试
        print("2. 测试查询性能...")
        query_times = []
        
        async with get_session() as session:
            for _ in range(100):
                start = time.time()
                
                # 随机查询
                result = await session.execute(
                    select(Document)
                    .where(Document.status == "pending")
                    .limit(10)
                )
                documents = result.scalars().all()
                
                query_times.append(time.time() - start)
        
        self.results["postgresql"]["query"] = {
            "count": len(query_times),
            "mean": statistics.mean(query_times),
            "median": statistics.median(query_times),
            "min": min(query_times),
            "max": max(query_times)
        }
        
        # 3. 批量操作测试
        print("3. 测试批量操作性能...")
        batch_sizes = [10, 50, 100, 500]
        batch_results = {}
        
        for size in batch_sizes:
            async with get_session() as session:
                start = time.time()
                
                docs = [
                    Document(
                        title=f"批量文档_{i}",
                        content="批量测试内容",
                        type="text",
                        project_id="test_project",
                        status="pending"
                    )
                    for i in range(size)
                ]
                
                session.add_all(docs)
                await session.commit()
                
                batch_results[f"batch_{size}"] = time.time() - start
        
        self.results["postgresql"]["batch_insert"] = batch_results
    
    async def benchmark_qdrant(self):
        """Qdrant向量数据库性能测试"""
        print("\n=== Qdrant性能测试 ===")
        
        qdrant = get_qdrant_manager()
        collection_name = "benchmark_test"
        
        # 创建测试集合
        await qdrant.create_collection(
            collection_name=collection_name,
            vector_size=1536,
            on_disk=False
        )
        
        # 1. 向量插入性能
        print("\n1. 测试向量插入性能...")
        insert_times = []
        
        for i in range(100):
            start = time.time()
            
            # 生成随机向量
            vector = np.random.rand(1536).tolist()
            
            await qdrant.upsert(
                collection_name=collection_name,
                points=[{
                    "id": str(i),
                    "vector": vector,
                    "payload": {
                        "text": f"测试文本_{i}",
                        "metadata": {"index": i}
                    }
                }]
            )
            
            insert_times.append(time.time() - start)
        
        self.results["qdrant"]["insert"] = {
            "count": len(insert_times),
            "mean": statistics.mean(insert_times),
            "median": statistics.median(insert_times)
        }
        
        # 2. 向量搜索性能
        print("2. 测试向量搜索性能...")
        search_times = []
        
        for _ in range(50):
            start = time.time()
            
            # 随机查询向量
            query_vector = np.random.rand(1536).tolist()
            
            results = await qdrant.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=10
            )
            
            search_times.append(time.time() - start)
        
        self.results["qdrant"]["search"] = {
            "count": len(search_times),
            "mean": statistics.mean(search_times),
            "median": statistics.median(search_times),
            "p95": sorted(search_times)[int(len(search_times) * 0.95)]
        }
        
        # 3. 批量向量插入
        print("3. 测试批量向量插入...")
        batch_sizes = [10, 50, 100, 500]
        batch_results = {}
        
        for size in batch_sizes:
            start = time.time()
            
            points = []
            for j in range(size):
                points.append({
                    "id": f"batch_{size}_{j}",
                    "vector": np.random.rand(1536).tolist(),
                    "payload": {"batch": size, "index": j}
                })
            
            await qdrant.upsert(
                collection_name=collection_name,
                points=points
            )
            
            batch_results[f"batch_{size}"] = time.time() - start
        
        self.results["qdrant"]["batch_insert"] = batch_results
        
        # 清理测试集合
        await qdrant.delete_collection(collection_name)
    
    async def benchmark_redis(self):
        """Redis缓存性能测试"""
        print("\n=== Redis性能测试 ===")
        
        redis = get_redis_client()
        
        # 1. 基本操作性能
        print("\n1. 测试基本操作性能...")
        operations = {
            "set": [],
            "get": [],
            "delete": []
        }
        
        # SET操作
        for i in range(1000):
            key = f"benchmark_key_{i}"
            value = f"测试值_{i}" * 10
            
            start = time.time()
            await redis.set(key, value)
            operations["set"].append(time.time() - start)
        
        # GET操作
        for i in range(1000):
            key = f"benchmark_key_{i}"
            
            start = time.time()
            await redis.get(key)
            operations["get"].append(time.time() - start)
        
        # DELETE操作
        for i in range(1000):
            key = f"benchmark_key_{i}"
            
            start = time.time()
            await redis.delete(key)
            operations["delete"].append(time.time() - start)
        
        for op, times in operations.items():
            self.results["redis"][op] = {
                "count": len(times),
                "mean": statistics.mean(times) * 1000,  # 转换为毫秒
                "median": statistics.median(times) * 1000,
                "ops_per_second": len(times) / sum(times)
            }
        
        # 2. 批量操作性能
        print("2. 测试批量操作性能...")
        
        # Pipeline批量SET
        start = time.time()
        pipe = redis.pipeline()
        for i in range(1000):
            pipe.set(f"pipeline_key_{i}", f"value_{i}")
        await pipe.execute()
        pipeline_time = time.time() - start
        
        self.results["redis"]["pipeline_set_1000"] = {
            "total_time": pipeline_time,
            "ops_per_second": 1000 / pipeline_time
        }
        
        # 3. 数据结构操作
        print("3. 测试数据结构操作...")
        
        # List操作
        list_times = []
        for i in range(100):
            start = time.time()
            await redis.lpush("benchmark_list", f"item_{i}")
            list_times.append(time.time() - start)
        
        # Hash操作
        hash_times = []
        for i in range(100):
            start = time.time()
            await redis.hset("benchmark_hash", f"field_{i}", f"value_{i}")
            hash_times.append(time.time() - start)
        
        self.results["redis"]["list_push"] = {
            "mean": statistics.mean(list_times) * 1000
        }
        self.results["redis"]["hash_set"] = {
            "mean": statistics.mean(hash_times) * 1000
        }
        
        # 清理测试数据
        await redis.flushdb()
    
    async def benchmark_neo4j(self):
        """Neo4j图数据库性能测试"""
        print("\n=== Neo4j性能测试 ===")
        
        neo4j = get_neo4j_manager()
        
        # 1. 节点创建性能
        print("\n1. 测试节点创建性能...")
        create_times = []
        
        for i in range(100):
            start = time.time()
            
            await neo4j.create_node(
                labels=["Document"],
                properties={
                    "id": f"doc_{i}",
                    "title": f"文档_{i}",
                    "created_at": datetime.now().isoformat()
                }
            )
            
            create_times.append(time.time() - start)
        
        self.results["neo4j"]["create_node"] = {
            "count": len(create_times),
            "mean": statistics.mean(create_times),
            "median": statistics.median(create_times)
        }
        
        # 2. 关系创建性能
        print("2. 测试关系创建性能...")
        relation_times = []
        
        for i in range(50):
            start = time.time()
            
            await neo4j.create_relationship(
                start_node_id=f"doc_{i}",
                end_node_id=f"doc_{i+1}",
                relationship_type="REFERENCES",
                properties={"weight": random.random()}
            )
            
            relation_times.append(time.time() - start)
        
        self.results["neo4j"]["create_relationship"] = {
            "count": len(relation_times),
            "mean": statistics.mean(relation_times),
            "median": statistics.median(relation_times)
        }
        
        # 3. 图查询性能
        print("3. 测试图查询性能...")
        query_times = []
        
        queries = [
            # 简单查询
            "MATCH (n:Document) RETURN n LIMIT 10",
            # 路径查询
            "MATCH p=(d1:Document)-[:REFERENCES*1..3]->(d2:Document) RETURN p LIMIT 10",
            # 聚合查询
            "MATCH (d:Document) RETURN count(d) as total"
        ]
        
        for query in queries:
            times = []
            for _ in range(20):
                start = time.time()
                await neo4j.execute_query(query)
                times.append(time.time() - start)
            
            self.results["neo4j"][f"query_{queries.index(query)}"] = {
                "query": query,
                "mean": statistics.mean(times),
                "median": statistics.median(times)
            }
        
        # 清理测试数据
        await neo4j.execute_query("MATCH (n) DETACH DELETE n")
    
    async def run_all_benchmarks(self):
        """运行所有基准测试"""
        await self.benchmark_postgresql()
        await self.benchmark_qdrant()
        await self.benchmark_redis()
        await self.benchmark_neo4j()
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            "test_date": datetime.now().isoformat(),
            "environment": {
                "database_host": "rtx4080",
                "test_type": "database_performance"
            },
            "results": self.results,
            "summary": self._generate_summary()
        }
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        summary = {
            "postgresql": {
                "avg_insert_time_ms": self.results["postgresql"].get("insert", {}).get("mean", 0) * 1000,
                "avg_query_time_ms": self.results["postgresql"].get("query", {}).get("mean", 0) * 1000
            },
            "qdrant": {
                "avg_vector_insert_ms": self.results["qdrant"].get("insert", {}).get("mean", 0) * 1000,
                "avg_search_time_ms": self.results["qdrant"].get("search", {}).get("mean", 0) * 1000,
                "search_p95_ms": self.results["qdrant"].get("search", {}).get("p95", 0) * 1000
            },
            "redis": {
                "get_ops_per_second": self.results["redis"].get("get", {}).get("ops_per_second", 0),
                "set_ops_per_second": self.results["redis"].get("set", {}).get("ops_per_second", 0)
            },
            "neo4j": {
                "avg_node_create_ms": self.results["neo4j"].get("create_node", {}).get("mean", 0) * 1000,
                "avg_relationship_create_ms": self.results["neo4j"].get("create_relationship", {}).get("mean", 0) * 1000
            }
        }
        
        return summary


async def main():
    """主测试函数"""
    benchmark = DatabaseBenchmark()
    
    print("=== DPA数据库性能基准测试 ===")
    print("开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 运行基准测试
    results = await benchmark.run_all_benchmarks()
    
    # 生成报告
    report = benchmark.generate_report()
    
    # 保存报告
    report_file = f"database_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存到: {report_file}")
    
    # 打印摘要
    print("\n=== 性能摘要 ===")
    summary = report["summary"]
    
    print("\nPostgreSQL:")
    print(f"  - 平均插入时间: {summary['postgresql']['avg_insert_time_ms']:.2f} ms")
    print(f"  - 平均查询时间: {summary['postgresql']['avg_query_time_ms']:.2f} ms")
    
    print("\nQdrant:")
    print(f"  - 平均向量插入: {summary['qdrant']['avg_vector_insert_ms']:.2f} ms")
    print(f"  - 平均搜索时间: {summary['qdrant']['avg_search_time_ms']:.2f} ms")
    print(f"  - 搜索P95: {summary['qdrant']['search_p95_ms']:.2f} ms")
    
    print("\nRedis:")
    print(f"  - GET操作: {summary['redis']['get_ops_per_second']:.0f} ops/s")
    print(f"  - SET操作: {summary['redis']['set_ops_per_second']:.0f} ops/s")
    
    print("\nNeo4j:")
    print(f"  - 节点创建: {summary['neo4j']['avg_node_create_ms']:.2f} ms")
    print(f"  - 关系创建: {summary['neo4j']['avg_relationship_create_ms']:.2f} ms")


if __name__ == "__main__":
    asyncio.run(main())