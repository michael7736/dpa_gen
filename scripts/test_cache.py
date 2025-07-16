#!/usr/bin/env python3
"""
测试Redis缓存服务
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.cache_service import CacheService, CacheManager, CacheKeys
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def test_cache_service():
    """测试缓存服务基本功能"""
    logger.info("开始测试缓存服务...")
    
    cache = CacheService()
    
    # 测试1: 基本的get/set操作
    logger.info("测试1: 基本get/set操作")
    test_key = "test:basic"
    test_value = {"message": "Hello Cache!", "number": 42}
    
    # 设置缓存
    success = await cache.set(test_key, test_value, ttl=60)
    logger.info(f"设置缓存: {success}")
    
    # 获取缓存
    retrieved = await cache.get(test_key)
    logger.info(f"获取缓存: {retrieved}")
    
    # 验证
    assert retrieved == test_value, "缓存值不匹配"
    logger.info("✅ 测试1通过")
    
    # 测试2: 缓存过期
    logger.info("\n测试2: 缓存过期")
    expire_key = "test:expire"
    await cache.set(expire_key, "will expire", ttl=1)
    await asyncio.sleep(2)
    expired_value = await cache.get(expire_key)
    assert expired_value is None, "缓存应该已过期"
    logger.info("✅ 测试2通过")
    
    # 测试3: 删除缓存
    logger.info("\n测试3: 删除缓存")
    delete_key = "test:delete"
    await cache.set(delete_key, "to be deleted", ttl=60)
    await cache.delete(delete_key)
    deleted_value = await cache.get(delete_key)
    assert deleted_value is None, "缓存应该已删除"
    logger.info("✅ 测试3通过")
    
    # 测试4: 模式匹配清除
    logger.info("\n测试4: 模式匹配清除")
    for i in range(5):
        await cache.set(f"test:pattern:{i}", f"value_{i}", ttl=60)
    
    cleared = await cache.clear_pattern("test:pattern:*")
    logger.info(f"清除了 {cleared} 个缓存项")
    
    # 验证清除
    for i in range(5):
        value = await cache.get(f"test:pattern:{i}")
        assert value is None, f"缓存 test:pattern:{i} 应该已清除"
    logger.info("✅ 测试4通过")
    
    # 显示统计信息
    stats = cache.get_stats()
    logger.info(f"\n缓存统计: {stats}")
    
    return True


async def test_cache_manager():
    """测试缓存管理器高级功能"""
    logger.info("\n开始测试缓存管理器...")
    
    manager = CacheManager()
    
    # 测试5: get_or_compute
    logger.info("\n测试5: get_or_compute功能")
    compute_key = "test:compute"
    compute_count = 0
    
    def expensive_computation():
        nonlocal compute_count
        compute_count += 1
        return {"result": "computed", "count": compute_count}
    
    # 第一次调用应该计算
    result1 = await manager.get_or_compute(compute_key, expensive_computation, ttl=60)
    logger.info(f"第一次结果: {result1}")
    assert compute_count == 1, "应该执行了一次计算"
    
    # 第二次调用应该从缓存获取
    result2 = await manager.get_or_compute(compute_key, expensive_computation, ttl=60)
    logger.info(f"第二次结果: {result2}")
    assert compute_count == 1, "不应该再次计算"
    assert result1 == result2, "结果应该相同"
    logger.info("✅ 测试5通过")
    
    # 测试6: 文档缓存失效
    logger.info("\n测试6: 文档缓存失效")
    doc_id = "test_doc_123"
    
    # 设置一些文档相关的缓存
    await manager.cache_service.set(f"embeddings:{doc_id}", ["embedding1", "embedding2"], ttl=60)
    await manager.cache_service.set(f"chunks:{doc_id}:0", {"content": "chunk0"}, ttl=60)
    await manager.cache_service.set(f"metadata:{doc_id}", {"title": "Test Doc"}, ttl=60)
    
    # 使文档缓存失效
    cleared = await manager.invalidate_document_cache(doc_id)
    logger.info(f"清除了 {cleared} 个文档相关缓存")
    
    # 验证缓存已清除
    assert await manager.cache_service.get(f"embeddings:{doc_id}") is None
    assert await manager.cache_service.get(f"chunks:{doc_id}:0") is None
    assert await manager.cache_service.get(f"metadata:{doc_id}") is None
    logger.info("✅ 测试6通过")
    
    return True


async def test_cache_keys():
    """测试缓存键生成器"""
    logger.info("\n测试缓存键生成器...")
    
    # 测试各种键生成
    doc_id = "doc_456"
    project_id = "proj_789"
    user_id = "user_123"
    
    keys = {
        "embeddings": CacheKeys.document_embeddings(doc_id),
        "chunks": CacheKeys.document_chunks(doc_id),
        "metadata": CacheKeys.document_metadata(doc_id),
        "search": CacheKeys.search_results(project_id, "query_hash_abc"),
        "stats": CacheKeys.project_stats(project_id),
        "prefs": CacheKeys.user_preferences(user_id)
    }
    
    for key_type, key in keys.items():
        logger.info(f"{key_type}: {key}")
    
    # 验证键格式
    assert keys["embeddings"] == f"embeddings:{doc_id}"
    assert keys["chunks"] == f"chunks:{doc_id}"
    assert keys["metadata"] == f"metadata:{doc_id}"
    logger.info("✅ 缓存键生成测试通过")
    
    return True


async def main():
    """主测试函数"""
    try:
        # 运行所有测试
        await test_cache_service()
        await test_cache_manager()
        await test_cache_keys()
        
        logger.info("\n🎉 所有缓存测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)