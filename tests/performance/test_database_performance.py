"""
数据库性能测试
测试PostgreSQL、Neo4j、Qdrant和Redis的性能
"""

import asyncio
import time
import uuid
import random
import statistics
from typing import List, Dict, Any
from datetime import datetime, timedelta
import psutil
import asyncpg
from neo4j import AsyncGraphDatabase
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import redis.asyncio as aioredis
import numpy as np
from dataclasses import dataclass

# 测试配置
DB_CONFIG = {
    "postgresql": {
        "host": "rtx4080",
        "port": 5432,
        "database": "dpa_db",
        "user": "dpa_user",
        "password": "your_password"
    },
    "neo4j": {
        "uri": "bolt://rtx4080:7687",
        "auth": ("neo4j", "your_password")
    },
    "qdrant": {
        "host": "rtx4080",
        "port": 6333
    },
    "redis": {
        "host": "rtx4080",
        "port": 6379,
        "password": "your_password",
        "db": 0
    }
}

# 向量维度
VECTOR_DIM = 1536  # OpenAI text-embedding-3-large


@dataclass
class BenchmarkResult:
    """性能测试结果"""
    database: str
    operation: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    min_time: float
    max_time: float
    mean_time: float
    median_time: float
    p95_time: float
    p99_time: float
    throughput: float
    cpu_usage: float
    memory_usage: float
    timestamp: datetime


class DatabaseBenchmark:
    """数据库性能基准测试"""
    
    def __init__(self):
        self.results = []
        
    async def benchmark_postgresql(self, num_operations: int = 1000):
        """测试PostgreSQL性能"""
        print("\n" + "="*60)
        print("PostgreSQL 性能测试")
        print("="*60)
        
        # 连接池
        pool = await asyncpg.create_pool(**DB_CONFIG["postgresql"])
        
        try:
            # 1. 插入性能测试
            await self._test_postgres_insert(pool, num_operations)
            
            # 2. 查询性能测试
            await self._test_postgres_query(pool, num_operations)
            
            # 3. 更新性能测试
            await self._test_postgres_update(pool, num_operations // 10)
            
            # 4. 复杂查询测试
            await self._test_postgres_complex_query(pool, num_operations // 100)
            
        finally:
            await pool.close()
    
    async def _test_postgres_insert(self, pool, num_operations):
        """PostgreSQL插入测试"""
        print("\n测试插入操作...")
        
        times = []
        success_count = 0
        
        # 准备测试数据
        test_data = [
            (
                str(uuid.uuid4()),
                f"项目{i}",
                f"这是项目{i}的描述",
                "research",
                datetime.now()
            )
            for i in range(num_operations)
        ]
        
        # 创建测试表
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS perf_test_projects (
                    id UUID PRIMARY KEY,
                    name VARCHAR(255),
                    description TEXT,
                    type VARCHAR(50),
                    created_at TIMESTAMP
                )
            """)
        
        # 批量插入测试
        batch_size = 100
        start_time = time.time()
        cpu_start = psutil.cpu_percent(interval=0.1)
        mem_start = psutil.virtual_memory().percent
        
        for i in range(0, num_operations, batch_size):
            batch = test_data[i:i+batch_size]
            op_start = time.time()
            
            try:
                async with pool.acquire() as conn:
                    await conn.executemany(
                        """
                        INSERT INTO perf_test_projects 
                        (id, name, description, type, created_at)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        batch
                    )
                success_count += len(batch)
                times.extend([time.time() - op_start] * len(batch))
            except Exception as e:
                print(f"插入错误: {e}")
        
        total_time = time.time() - start_time
        cpu_usage = psutil.cpu_percent(interval=0.1) - cpu_start
        mem_usage = psutil.virtual_memory().percent - mem_start
        
        # 记录结果
        result = self._calculate_metrics(
            "PostgreSQL", "INSERT", num_operations,
            success_count, times, total_time,
            cpu_usage, mem_usage
        )
        self.results.append(result)
        self._print_result(result)
        
        # 清理
        async with pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS perf_test_projects")
    
    async def _test_postgres_query(self, pool, num_operations):
        """PostgreSQL查询测试"""
        print("\n测试查询操作...")
        
        # 准备测试数据
        async with pool.acquire() as conn:
            # 创建索引测试表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS perf_test_data (
                    id SERIAL PRIMARY KEY,
                    user_id UUID,
                    value FLOAT,
                    category VARCHAR(50),
                    created_at TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_category (category),
                    INDEX idx_created_at (created_at)
                )
            """)
            
            # 插入测试数据
            test_data = [
                (
                    str(uuid.uuid4()),
                    random.uniform(0, 1000),
                    random.choice(['A', 'B', 'C', 'D', 'E']),
                    datetime.now() - timedelta(days=random.randint(0, 365))
                )
                for _ in range(10000)
            ]
            
            await conn.executemany(
                """
                INSERT INTO perf_test_data (user_id, value, category, created_at)
                VALUES ($1, $2, $3, $4)
                """,
                test_data
            )
        
        times = []
        success_count = 0
        
        # 执行查询测试
        for _ in range(num_operations):
            start_time = time.time()
            
            try:
                async with pool.acquire() as conn:
                    # 随机选择查询类型
                    query_type = random.choice(['simple', 'filter', 'aggregate'])
                    
                    if query_type == 'simple':
                        await conn.fetch("SELECT * FROM perf_test_data LIMIT 100")
                    elif query_type == 'filter':
                        category = random.choice(['A', 'B', 'C', 'D', 'E'])
                        await conn.fetch(
                            "SELECT * FROM perf_test_data WHERE category = $1",
                            category
                        )
                    else:  # aggregate
                        await conn.fetchrow(
                            """
                            SELECT category, COUNT(*), AVG(value)
                            FROM perf_test_data
                            GROUP BY category
                            """
                        )
                
                times.append(time.time() - start_time)
                success_count += 1
            except Exception as e:
                print(f"查询错误: {e}")
        
        # 记录结果
        result = self._calculate_metrics(
            "PostgreSQL", "QUERY", num_operations,
            success_count, times, sum(times), 0, 0
        )
        self.results.append(result)
        self._print_result(result)
        
        # 清理
        async with pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS perf_test_data")
    
    async def benchmark_neo4j(self, num_operations: int = 1000):
        """测试Neo4j性能"""
        print("\n" + "="*60)
        print("Neo4j 性能测试")
        print("="*60)
        
        driver = AsyncGraphDatabase.driver(**DB_CONFIG["neo4j"])
        
        try:
            # 1. 节点创建测试
            await self._test_neo4j_create(driver, num_operations)
            
            # 2. 关系创建测试
            await self._test_neo4j_relationships(driver, num_operations // 10)
            
            # 3. 图查询测试
            await self._test_neo4j_query(driver, num_operations)
            
        finally:
            await driver.close()
    
    async def _test_neo4j_create(self, driver, num_operations):
        """Neo4j节点创建测试"""
        print("\n测试节点创建...")
        
        times = []
        success_count = 0
        
        async with driver.session() as session:
            # 批量创建节点
            batch_size = 50
            
            for i in range(0, num_operations, batch_size):
                start_time = time.time()
                
                try:
                    # 创建批量节点
                    query = """
                    UNWIND $nodes AS node
                    CREATE (n:Document {
                        id: node.id,
                        title: node.title,
                        content: node.content,
                        created_at: datetime()
                    })
                    """
                    
                    nodes = [
                        {
                            "id": str(uuid.uuid4()),
                            "title": f"文档{j}",
                            "content": f"这是文档{j}的内容"
                        }
                        for j in range(i, min(i + batch_size, num_operations))
                    ]
                    
                    await session.run(query, nodes=nodes)
                    success_count += len(nodes)
                    times.extend([time.time() - start_time] * len(nodes))
                    
                except Exception as e:
                    print(f"创建节点错误: {e}")
        
        # 记录结果
        result = self._calculate_metrics(
            "Neo4j", "CREATE_NODE", num_operations,
            success_count, times, sum(times), 0, 0
        )
        self.results.append(result)
        self._print_result(result)
        
        # 清理
        async with driver.session() as session:
            await session.run("MATCH (n:Document) DELETE n")
    
    async def _test_neo4j_query(self, driver, num_operations):
        """Neo4j查询测试"""
        print("\n测试图查询...")
        
        # 创建测试图
        async with driver.session() as session:
            # 创建知识图谱
            await session.run("""
                // 创建概念节点
                CREATE (ai:Concept {name: 'AI', id: 'ai'})
                CREATE (ml:Concept {name: 'Machine Learning', id: 'ml'})
                CREATE (dl:Concept {name: 'Deep Learning', id: 'dl'})
                CREATE (nn:Concept {name: 'Neural Network', id: 'nn'})
                CREATE (nlp:Concept {name: 'NLP', id: 'nlp'})
                
                // 创建关系
                CREATE (ai)-[:INCLUDES]->(ml)
                CREATE (ml)-[:INCLUDES]->(dl)
                CREATE (dl)-[:USES]->(nn)
                CREATE (ai)-[:APPLIES_TO]->(nlp)
                CREATE (nlp)-[:USES]->(dl)
            """)
            
            # 创建文档节点并关联
            for i in range(100):
                await session.run("""
                    CREATE (d:Document {
                        id: $id,
                        title: $title,
                        content: $content
                    })
                    WITH d
                    MATCH (c:Concept)
                    WHERE rand() < 0.3
                    CREATE (d)-[:MENTIONS]->(c)
                """, id=str(uuid.uuid4()), title=f"文档{i}", content=f"内容{i}")
        
        times = []
        success_count = 0
        
        # 执行查询测试
        queries = [
            # 简单查询
            "MATCH (n:Concept) RETURN n LIMIT 10",
            # 路径查询
            "MATCH path = (a:Concept)-[*1..3]->(b:Concept) RETURN path LIMIT 10",
            # 复杂查询
            """
            MATCH (d:Document)-[:MENTIONS]->(c:Concept)
            WHERE c.name = 'AI'
            RETURN d, collect(c) as concepts
            LIMIT 10
            """,
            # 聚合查询
            """
            MATCH (d:Document)-[:MENTIONS]->(c:Concept)
            RETURN c.name, count(d) as doc_count
            ORDER BY doc_count DESC
            """
        ]
        
        for _ in range(num_operations):
            query = random.choice(queries)
            start_time = time.time()
            
            try:
                async with driver.session() as session:
                    result = await session.run(query)
                    await result.consume()
                
                times.append(time.time() - start_time)
                success_count += 1
            except Exception as e:
                print(f"查询错误: {e}")
        
        # 记录结果
        result = self._calculate_metrics(
            "Neo4j", "QUERY", num_operations,
            success_count, times, sum(times), 0, 0
        )
        self.results.append(result)
        self._print_result(result)
        
        # 清理
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
    
    async def benchmark_qdrant(self, num_operations: int = 1000):
        """测试Qdrant性能"""
        print("\n" + "="*60)
        print("Qdrant 性能测试")
        print("="*60)
        
        client = AsyncQdrantClient(**DB_CONFIG["qdrant"])
        
        try:
            # 创建测试集合
            collection_name = "perf_test"
            
            await client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=VECTOR_DIM,
                    distance=Distance.COSINE
                )
            )
            
            # 1. 向量插入测试
            await self._test_qdrant_insert(client, collection_name, num_operations)
            
            # 2. 向量搜索测试
            await self._test_qdrant_search(client, collection_name, num_operations // 10)
            
            # 3. 带过滤的搜索测试
            await self._test_qdrant_filtered_search(client, collection_name, num_operations // 10)
            
            # 清理
            await client.delete_collection(collection_name)
            
        finally:
            await client.close()
    
    async def _test_qdrant_insert(self, client, collection_name, num_operations):
        """Qdrant向量插入测试"""
        print("\n测试向量插入...")
        
        times = []
        success_count = 0
        batch_size = 100
        
        for i in range(0, num_operations, batch_size):
            # 生成随机向量
            points = [
                PointStruct(
                    id=j,
                    vector=np.random.randn(VECTOR_DIM).tolist(),
                    payload={
                        "doc_id": str(uuid.uuid4()),
                        "title": f"文档{j}",
                        "category": random.choice(['tech', 'science', 'business']),
                        "score": random.uniform(0, 1)
                    }
                )
                for j in range(i, min(i + batch_size, num_operations))
            ]
            
            start_time = time.time()
            
            try:
                await client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                success_count += len(points)
                times.extend([time.time() - start_time] * len(points))
            except Exception as e:
                print(f"插入错误: {e}")
        
        # 记录结果
        result = self._calculate_metrics(
            "Qdrant", "INSERT", num_operations,
            success_count, times, sum(times), 0, 0
        )
        self.results.append(result)
        self._print_result(result)
    
    async def _test_qdrant_search(self, client, collection_name, num_operations):
        """Qdrant向量搜索测试"""
        print("\n测试向量搜索...")
        
        times = []
        success_count = 0
        
        for _ in range(num_operations):
            # 生成随机查询向量
            query_vector = np.random.randn(VECTOR_DIM).tolist()
            
            start_time = time.time()
            
            try:
                results = await client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=10
                )
                times.append(time.time() - start_time)
                success_count += 1
            except Exception as e:
                print(f"搜索错误: {e}")
        
        # 记录结果
        result = self._calculate_metrics(
            "Qdrant", "SEARCH", num_operations,
            success_count, times, sum(times), 0, 0
        )
        self.results.append(result)
        self._print_result(result)
    
    async def benchmark_redis(self, num_operations: int = 10000):
        """测试Redis性能"""
        print("\n" + "="*60)
        print("Redis 性能测试")
        print("="*60)
        
        redis_client = await aioredis.from_url(
            f"redis://{DB_CONFIG['redis']['host']}:{DB_CONFIG['redis']['port']}",
            password=DB_CONFIG['redis']['password'],
            db=DB_CONFIG['redis']['db']
        )
        
        try:
            # 1. 基础操作测试
            await self._test_redis_basic(redis_client, num_operations)
            
            # 2. 批量操作测试
            await self._test_redis_pipeline(redis_client, num_operations)
            
            # 3. 复杂数据结构测试
            await self._test_redis_complex(redis_client, num_operations // 100)
            
        finally:
            await redis_client.close()
    
    async def _test_redis_basic(self, client, num_operations):
        """Redis基础操作测试"""
        print("\n测试基础操作...")
        
        times = []
        success_count = 0
        
        # SET/GET测试
        for i in range(num_operations):
            key = f"test_key_{i}"
            value = f"test_value_{i}" * 10  # 增加数据大小
            
            start_time = time.time()
            
            try:
                # SET操作
                await client.set(key, value, ex=300)  # 5分钟过期
                # GET操作
                result = await client.get(key)
                
                if result:
                    success_count += 1
                times.append(time.time() - start_time)
            except Exception as e:
                print(f"操作错误: {e}")
        
        # 记录结果
        result = self._calculate_metrics(
            "Redis", "SET/GET", num_operations,
            success_count, times, sum(times), 0, 0
        )
        self.results.append(result)
        self._print_result(result)
        
        # 清理
        pattern = "test_key_*"
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    
    async def _test_redis_pipeline(self, client, num_operations):
        """Redis管道操作测试"""
        print("\n测试管道操作...")
        
        times = []
        success_count = 0
        batch_size = 100
        
        for i in range(0, num_operations, batch_size):
            start_time = time.time()
            
            try:
                # 使用管道批量操作
                pipe = client.pipeline()
                
                for j in range(i, min(i + batch_size, num_operations)):
                    key = f"pipe_key_{j}"
                    value = f"pipe_value_{j}"
                    pipe.set(key, value, ex=300)
                    pipe.get(key)
                
                results = await pipe.execute()
                success_count += len(results) // 2  # SET和GET各算一次
                times.append(time.time() - start_time)
                
            except Exception as e:
                print(f"管道错误: {e}")
        
        # 记录结果
        result = self._calculate_metrics(
            "Redis", "PIPELINE", num_operations,
            success_count, times, sum(times), 0, 0
        )
        self.results.append(result)
        self._print_result(result)
        
        # 清理
        pattern = "pipe_key_*"
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    
    def _calculate_metrics(
        self,
        database: str,
        operation: str,
        total: int,
        success: int,
        times: List[float],
        total_time: float,
        cpu_usage: float,
        memory_usage: float
    ) -> BenchmarkResult:
        """计算性能指标"""
        if times:
            sorted_times = sorted(times)
            return BenchmarkResult(
                database=database,
                operation=operation,
                total_operations=total,
                successful_operations=success,
                failed_operations=total - success,
                min_time=min(times),
                max_time=max(times),
                mean_time=statistics.mean(times),
                median_time=statistics.median(times),
                p95_time=sorted_times[int(len(sorted_times) * 0.95)],
                p99_time=sorted_times[int(len(sorted_times) * 0.99)],
                throughput=total / total_time if total_time > 0 else 0,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                timestamp=datetime.now()
            )
        else:
            return BenchmarkResult(
                database=database,
                operation=operation,
                total_operations=total,
                successful_operations=success,
                failed_operations=total - success,
                min_time=0,
                max_time=0,
                mean_time=0,
                median_time=0,
                p95_time=0,
                p99_time=0,
                throughput=0,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                timestamp=datetime.now()
            )
    
    def _print_result(self, result: BenchmarkResult):
        """打印测试结果"""
        print(f"\n{result.database} - {result.operation}")
        print(f"总操作数: {result.total_operations}")
        print(f"成功: {result.successful_operations} | 失败: {result.failed_operations}")
        print(f"吞吐量: {result.throughput:.2f} ops/秒")
        print(f"响应时间 (毫秒):")
        print(f"  最小: {result.min_time*1000:.2f}")
        print(f"  最大: {result.max_time*1000:.2f}")
        print(f"  平均: {result.mean_time*1000:.2f}")
        print(f"  中位数: {result.median_time*1000:.2f}")
        print(f"  P95: {result.p95_time*1000:.2f}")
        print(f"  P99: {result.p99_time*1000:.2f}")
        if result.cpu_usage > 0:
            print(f"CPU使用率: {result.cpu_usage:.1f}%")
            print(f"内存使用率: {result.memory_usage:.1f}%")
    
    def generate_report(self, filename: str = "database_benchmark_report.md"):
        """生成测试报告"""
        with open(filename, "w") as f:
            f.write("# DPA 数据库性能基准测试报告\n\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 按数据库分组
            db_results = {}
            for result in self.results:
                if result.database not in db_results:
                    db_results[result.database] = []
                db_results[result.database].append(result)
            
            # 生成各数据库报告
            for db, results in db_results.items():
                f.write(f"\n## {db} 性能测试\n\n")
                
                f.write("| 操作 | 总数 | 成功率 | 吞吐量(ops/s) | 平均响应(ms) | P95(ms) | P99(ms) |\n")
                f.write("|------|------|--------|---------------|--------------|---------|----------|\n")
                
                for r in results:
                    success_rate = r.successful_operations / r.total_operations * 100
                    f.write(f"| {r.operation} | {r.total_operations} | "
                           f"{success_rate:.1f}% | {r.throughput:.1f} | "
                           f"{r.mean_time*1000:.2f} | {r.p95_time*1000:.2f} | "
                           f"{r.p99_time*1000:.2f} |\n")
            
            # 总结
            f.write("\n## 性能总结\n\n")
            f.write("### 最佳性能\n")
            
            # 找出最快的操作
            if self.results:
                fastest = min(self.results, key=lambda x: x.mean_time)
                f.write(f"- 最快响应: {fastest.database} - {fastest.operation} "
                       f"(平均 {fastest.mean_time*1000:.2f}ms)\n")
                
                highest_throughput = max(self.results, key=lambda x: x.throughput)
                f.write(f"- 最高吞吐: {highest_throughput.database} - "
                       f"{highest_throughput.operation} "
                       f"({highest_throughput.throughput:.1f} ops/s)\n")
        
        print(f"\n\n性能测试报告已保存到: {filename}")


async def run_database_benchmarks():
    """运行所有数据库性能测试"""
    benchmark = DatabaseBenchmark()
    
    print("DPA 数据库性能基准测试")
    print("="*60)
    print("注意：请确保已配置正确的数据库连接信息")
    print("测试数据库：PostgreSQL, Neo4j, Qdrant, Redis")
    print("="*60)
    
    # PostgreSQL测试
    try:
        await benchmark.benchmark_postgresql(num_operations=1000)
    except Exception as e:
        print(f"PostgreSQL测试失败: {e}")
    
    # Neo4j测试
    try:
        await benchmark.benchmark_neo4j(num_operations=500)
    except Exception as e:
        print(f"Neo4j测试失败: {e}")
    
    # Qdrant测试
    try:
        await benchmark.benchmark_qdrant(num_operations=1000)
    except Exception as e:
        print(f"Qdrant测试失败: {e}")
    
    # Redis测试
    try:
        await benchmark.benchmark_redis(num_operations=10000)
    except Exception as e:
        print(f"Redis测试失败: {e}")
    
    # 生成报告
    benchmark.generate_report()


if __name__ == "__main__":
    asyncio.run(run_database_benchmarks())