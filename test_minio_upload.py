"""测试MinIO上传功能"""
import io
from datetime import datetime
from minio import Minio
from minio.error import S3Error

# MinIO配置
MINIO_ENDPOINT = "rtx4080:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_SECURE = False
BUCKET_NAME = "dpa-documents"

def test_minio_upload():
    """测试MinIO上传"""
    try:
        # 创建MinIO客户端
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        print(f"连接到MinIO: {MINIO_ENDPOINT}")
        
        # 检查bucket是否存在
        if not client.bucket_exists(BUCKET_NAME):
            print(f"Bucket {BUCKET_NAME} 不存在，尝试创建...")
            client.make_bucket(BUCKET_NAME)
            print(f"Bucket {BUCKET_NAME} 创建成功")
        else:
            print(f"Bucket {BUCKET_NAME} 已存在")
        
        # 准备测试数据
        test_content = b"This is a test document for MinIO upload testing."
        test_filename = f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 构建对象路径
        object_name = f"u1/default/test123/original/{test_filename}"
        
        # 上传文件
        print(f"\n上传文件: {object_name}")
        client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=object_name,
            data=io.BytesIO(test_content),
            length=len(test_content),
            content_type="text/plain",
            metadata={
                "user_id": "u1",
                "project_id": "default",
                "document_id": "test123",
                "upload_time": datetime.utcnow().isoformat()
            }
        )
        
        print("上传成功!")
        
        # 验证文件是否存在
        try:
            stat = client.stat_object(BUCKET_NAME, object_name)
            print(f"\n文件信息:")
            print(f"- 大小: {stat.size} bytes")
            print(f"- 修改时间: {stat.last_modified}")
            print(f"- ETag: {stat.etag}")
        except S3Error as e:
            print(f"获取文件信息失败: {e}")
            
    except S3Error as e:
        print(f"\nMinIO错误: {e}")
        print(f"错误代码: {e.code}")
        print(f"错误消息: {e.message}")
    except Exception as e:
        print(f"\n其他错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_minio_upload()