"""
快速集成测试
验证核心组件是否正常工作
"""

import pytest
import asyncio
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """测试基本导入"""
    try:
        from src.api.main import app
        from src.database.postgresql import get_db_session
        from src.config.settings import get_settings
        print("✅ 基本导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


@pytest.mark.asyncio
async def test_database_connections():
    """测试数据库连接"""
    from src.config.settings import get_settings
    settings = get_settings()
    
    # 测试PostgreSQL
    try:
        from src.database.postgresql import get_engine
        engine = get_engine()
        print(f"✅ PostgreSQL连接成功: {settings.database.url}")
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
    
    # 测试Redis
    try:
        from src.database.redis_client import get_redis_client
        redis = get_redis_client()
        await redis.ping()
        print(f"✅ Redis连接成功: {settings.redis.host}:{settings.redis.port}")
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
    
    # 测试Qdrant
    try:
        from src.database.qdrant_client import get_qdrant_manager
        qdrant = get_qdrant_manager()
        await qdrant.collection_exists("test")
        print(f"✅ Qdrant连接成功: {settings.qdrant.url}")
    except Exception as e:
        print(f"❌ Qdrant连接失败: {e}")


@pytest.mark.asyncio
async def test_api_startup():
    """测试API启动"""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    with TestClient(app) as client:
        # 测试根路径
        response = client.get("/")
        assert response.status_code == 200
        print("✅ API根路径正常")
        
        # 测试健康检查
        response = client.get("/health")
        assert response.status_code == 200
        print("✅ 健康检查正常")


def test_configuration():
    """测试配置加载"""
    from src.config.settings import get_settings
    settings = get_settings()
    
    assert settings.database.host == "rtx4080"
    assert settings.redis.host == "rtx4080"
    assert settings.qdrant.host == "rtx4080"
    assert settings.neo4j.host == "rtx4080"
    
    print("✅ 配置加载正常")
    print(f"  - Database: {settings.database.host}:{settings.database.port}")
    print(f"  - Redis: {settings.redis.host}:{settings.redis.port}")
    print(f"  - Qdrant: {settings.qdrant.host}:{settings.qdrant.port}")
    print(f"  - Neo4j: {settings.neo4j.host}:{settings.neo4j.port}")


if __name__ == "__main__":
    print("=== DPA系统快速集成测试 ===\n")
    
    # 运行测试
    print("1. 测试导入...")
    test_imports()
    
    print("\n2. 测试配置...")
    test_configuration()
    
    print("\n3. 测试数据库连接...")
    asyncio.run(test_database_connections())
    
    print("\n4. 测试API启动...")
    asyncio.run(test_api_startup())
    
    print("\n=== 测试完成 ===")