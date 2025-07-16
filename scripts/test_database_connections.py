#!/usr/bin/env python3
"""
数据库连接测试脚本
测试所有配置的数据库是否可以正常连接
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import get_settings
from src.database.postgresql import get_db_session
from src.database.qdrant import get_qdrant_manager
from src.database.neo4j_manager import Neo4jManager
import redis
import asyncpg
from qdrant_client import QdrantClient
from neo4j import GraphDatabase

settings = get_settings()

# 测试结果统计
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"🔗 {title}")
    print("=" * 60)


def print_test(name: str, passed: bool, error: str = None, details: str = None):
    """打印测试结果"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {error}")
        print(f"❌ {name}")
        if error:
            print(f"   错误: {error}")


async def test_postgresql():
    """测试PostgreSQL连接"""
    print_header("PostgreSQL 连接测试")
    
    try:
        # 测试基本连接
        conn = await asyncpg.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password,
            database=settings.database.name
        )
        
        # 测试查询
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        
        print_test(
            "PostgreSQL连接",
            True,
            details=f"版本: {version.split(',')[0]}"
        )
        
        # 测试数据库池
        try:
            db_session = get_db_session()
            print_test("数据库会话池", True, details="连接池创建成功")
        except Exception as e:
            print_test("数据库会话池", False, str(e))
            
    except Exception as e:
        print_test("PostgreSQL连接", False, str(e))


async def test_qdrant():
    """测试Qdrant连接"""
    print_header("Qdrant 连接测试")
    
    try:
        # 测试直接连接
        client = QdrantClient(
            url=settings.qdrant.url,
            timeout=10
        )
        
        collections = client.get_collections()
        print_test(
            "Qdrant直接连接",
            True,
            details=f"集合数量: {len(collections.collections)}"
        )
        
        # 测试项目管理器
        try:
            qdrant_manager = get_qdrant_manager()
            print_test("Qdrant管理器", True, details="管理器创建成功")
        except Exception as e:
            print_test("Qdrant管理器", False, str(e))
            
    except Exception as e:
        print_test("Qdrant连接", False, str(e))


async def test_neo4j():
    """测试Neo4j连接"""
    print_header("Neo4j 连接测试")
    
    try:
        # 测试直接连接
        driver = GraphDatabase.driver(
            settings.neo4j.url,
            auth=(settings.neo4j.username, settings.neo4j.password)
        )
        
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions")
            components = list(result)
            
        driver.close()
        
        if components:
            neo4j_version = components[0]["versions"][0]
            print_test(
                "Neo4j直接连接",
                True,
                details=f"版本: {neo4j_version}"
            )
        else:
            print_test("Neo4j直接连接", True, details="连接成功")
        
        # 测试项目管理器
        try:
            neo4j_manager = Neo4jManager()
            print_test("Neo4j管理器", True, details="管理器创建成功")
        except Exception as e:
            print_test("Neo4j管理器", False, str(e))
            
    except Exception as e:
        print_test("Neo4j连接", False, str(e))


async def test_redis():
    """测试Redis连接"""
    print_header("Redis 连接测试")
    
    try:
        # 测试直接连接
        r = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password,
            db=settings.redis.db,
            decode_responses=True,
            socket_timeout=5
        )
        
        # 测试基本操作
        r.ping()
        info = r.info()
        
        print_test(
            "Redis连接",
            True,
            details=f"版本: {info['redis_version']}, 内存: {info['used_memory_human']}"
        )
        
        # 测试缓存操作
        test_key = "test_connection"
        r.set(test_key, "test_value", ex=10)
        value = r.get(test_key)
        r.delete(test_key)
        
        print_test(
            "Redis缓存操作",
            value == "test_value",
            details="读写操作正常"
        )
        
    except Exception as e:
        print_test("Redis连接", False, str(e))


async def test_all_databases():
    """测试所有数据库连接"""
    print("\n" + "🔗" * 20)
    print("数据库连接测试")
    print("🔗" * 20)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"配置环境: {getattr(settings, 'environment', 'development')}")
    
    # 运行所有测试
    await test_postgresql()
    await test_qdrant()
    await test_neo4j()
    await test_redis()
    
    # 打印总结
    print_header("📊 测试总结")
    print(f"总测试数: {test_results['total']}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    success_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"成功率: {success_rate:.1f}%")
    
    if test_results['errors']:
        print("\n❌ 错误列表:")
        for error in test_results['errors']:
            print(f"   - {error}")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_rate >= 75.0  # 返回是否大部分测试通过


if __name__ == "__main__":
    asyncio.run(test_all_databases())