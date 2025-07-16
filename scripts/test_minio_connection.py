#!/usr/bin/env python3
"""
测试MinIO连接
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from minio import Minio
from minio.error import S3Error

# MinIO配置
MINIO_ENDPOINT = "rtx4080:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin123"
MINIO_SECURE = False
BUCKET_NAME = "dpa-documents"

def test_minio_connection():
    """测试MinIO连接"""
    try:
        # 创建MinIO客户端
        client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        print(f"连接到MinIO: {MINIO_ENDPOINT}")
        
        # 列出所有桶
        buckets = client.list_buckets()
        print(f"\n现有的桶:")
        for bucket in buckets:
            print(f"  - {bucket.name} (创建时间: {bucket.creation_date})")
        
        # 检查目标桶是否存在
        if client.bucket_exists(BUCKET_NAME):
            print(f"\n✓ 桶 '{BUCKET_NAME}' 已存在")
        else:
            print(f"\n✗ 桶 '{BUCKET_NAME}' 不存在，正在创建...")
            client.make_bucket(BUCKET_NAME)
            print(f"✓ 桶 '{BUCKET_NAME}' 创建成功")
        
        # 测试上传
        test_content = b"Hello MinIO from DPA!"
        test_object = "test/hello.txt"
        
        from io import BytesIO
        client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=test_object,
            data=BytesIO(test_content),
            length=len(test_content)
        )
        print(f"\n✓ 测试上传成功: {test_object}")
        
        # 测试下载
        response = client.get_object(BUCKET_NAME, test_object)
        data = response.read()
        response.close()
        response.release_conn()
        
        if data == test_content:
            print(f"✓ 测试下载成功，内容匹配")
        else:
            print(f"✗ 下载内容不匹配")
        
        # 清理测试文件
        client.remove_object(BUCKET_NAME, test_object)
        print(f"✓ 测试文件已清理")
        
        print("\n✅ MinIO连接测试成功!")
        return True
        
    except S3Error as e:
        print(f"\n❌ MinIO S3错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 连接错误: {e}")
        print(f"   错误类型: {type(e).__name__}")
        return False


if __name__ == "__main__":
    test_minio_connection()