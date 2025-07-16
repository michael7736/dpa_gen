#!/usr/bin/env python3
"""
测试Qdrant连接
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import get_settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

settings = get_settings()


def test_qdrant_connection():
    """测试Qdrant连接"""
    print(f"🔍 测试Qdrant连接...")
    print(f"   URL: {settings.qdrant.url}")
    print(f"   Host: {settings.qdrant.host}")
    print(f"   Port: {settings.qdrant.port}")
    
    try:
        # 创建客户端
        client = QdrantClient(
            host=settings.qdrant.host,
            port=settings.qdrant.port,
            timeout=5
        )
        
        # 测试连接
        collections = client.get_collections()
        print(f"✅ 连接成功！")
        print(f"   现有集合数: {len(collections.collections)}")
        
        # 列出集合
        if collections.collections:
            print("   集合列表:")
            for coll in collections.collections:
                print(f"   - {coll.name}")
        
        # 尝试创建测试集合
        test_collection = "dpa_test_collection"
        try:
            client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"✅ 创建测试集合成功: {test_collection}")
            
            # 删除测试集合
            client.delete_collection(test_collection)
            print(f"✅ 删除测试集合成功")
            
        except Exception as e:
            print(f"⚠️  测试集合操作失败: {e}")
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n可能的原因:")
        print("1. Qdrant服务未启动")
        print("2. 网络连接问题")
        print("3. 防火墙阻止")
        print("\n解决方案:")
        print("1. 确保Qdrant服务正在运行")
        print("2. 检查rtx4080服务器是否可访问")
        print("3. 验证端口6333是否开放")
        
        # 尝试本地连接
        print("\n尝试本地连接...")
        try:
            local_client = QdrantClient(host="localhost", port=6333, timeout=5)
            local_collections = local_client.get_collections()
            print("✅ 本地连接成功！建议修改配置使用localhost")
        except:
            print("❌ 本地连接也失败，请确保Qdrant服务已启动")


def main():
    """主函数"""
    test_qdrant_connection()


if __name__ == "__main__":
    main()