#!/usr/bin/env python
"""
核心功能测试
专注于验证最基础的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_config():
    """测试配置模块"""
    print("\n=== 测试配置系统 ===")
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        
        print("✅ 配置加载成功")
        print(f"  - 环境: {settings.app.env}")
        print(f"  - 调试模式: {settings.app.debug}")
        print(f"  - PostgreSQL: {settings.database.host}:{settings.database.port}")
        print(f"  - Redis: {settings.redis.host}:{settings.redis.port}")
        print(f"  - Qdrant: {settings.qdrant.host}:{settings.qdrant.port}")
        
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


async def test_postgresql():
    """测试PostgreSQL连接"""
    print("\n=== 测试PostgreSQL ===")
    try:
        from src.database.postgresql import test_connection
        result = await test_connection()
        if result:
            print("✅ PostgreSQL连接成功")
        else:
            print("❌ PostgreSQL连接失败")
        return result
    except Exception as e:
        print(f"❌ PostgreSQL测试失败: {e}")
        return False


async def test_redis():
    """测试Redis连接"""
    print("\n=== 测试Redis ===")
    try:
        from src.database.redis_client import get_redis_client
        from src.config.settings import get_settings
        
        settings = get_settings()
        redis = get_redis_client()
        
        # 设置测试值
        await redis.set("test_key", "test_value", ex=10)
        value = await redis.get("test_key")
        
        if value == b"test_value":
            print("✅ Redis连接成功")
            print(f"  - 主机: {settings.redis.host}")
            print(f"  - 端口: {settings.redis.port}")
            print(f"  - 数据库: {settings.redis.db}")
            await redis.delete("test_key")
            return True
        else:
            print("❌ Redis连接失败: 数据不匹配")
            return False
            
    except Exception as e:
        print(f"❌ Redis测试失败: {e}")
        return False


async def test_qdrant():
    """测试Qdrant连接"""
    print("\n=== 测试Qdrant ===")
    try:
        from src.database.qdrant_client import get_qdrant_manager
        
        qdrant = get_qdrant_manager()
        collections = await qdrant.list_collections()
        
        print("✅ Qdrant连接成功")
        print(f"  - 集合数量: {len(collections)}")
        
        # 测试默认集合
        if await qdrant.collection_exists("dpa_documents"):
            print("  - 默认集合已存在")
        else:
            print("  - 默认集合不存在")
            
        return True
        
    except Exception as e:
        print(f"❌ Qdrant测试失败: {e}")
        return False


async def test_simple_api():
    """测试简单的API端点"""
    print("\n=== 测试API端点 ===")
    try:
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        with TestClient(app) as client:
            # 健康检查
            response = client.get("/health")
            if response.status_code == 200:
                print("✅ 健康检查端点正常")
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                
            # API文档
            response = client.get("/docs")
            if response.status_code == 200:
                print("✅ API文档端点正常")
            else:
                print(f"❌ API文档访问失败: {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=== DPA核心功能测试 ===")
    print(f"Python版本: {sys.version}")
    print(f"项目路径: {Path(__file__).parent}")
    
    # 运行测试
    results = {
        "配置系统": test_config(),
        "PostgreSQL": await test_postgresql(),
        "Redis": await test_redis(),
        "Qdrant": await test_qdrant(),
        "API端点": await test_simple_api()
    }
    
    # 生成报告
    print("\n=== 测试结果总结 ===")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有核心功能测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要修复。")


if __name__ == "__main__":
    asyncio.run(main())