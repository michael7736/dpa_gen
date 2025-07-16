"""调试V2上传MinIO问题"""
import sys
sys.path.append('.')

from src.services.minio_service import get_minio_service
from uuid import uuid4
from datetime import datetime

async def debug_upload():
    """调试上传功能"""
    try:
        # 获取MinIO服务
        minio_service = get_minio_service()
        print(f"MinIO endpoint: {minio_service.client._base_url}")
        print(f"Bucket: {minio_service.bucket_name}")
        
        # 准备测试数据
        test_content = b"Debug test content for V2 upload"
        document_id = str(uuid4())
        
        # 测试上传
        storage_path = await minio_service.upload_document(
            file_content=test_content,
            file_name="debug_test.txt",
            user_id="u1",
            project_id="test_project_id",
            document_id=document_id,
            content_type="text/plain",
            metadata={
                "test": "debug",
                "upload_time": datetime.utcnow().isoformat()
            }
        )
        
        print(f"上传成功！存储路径: {storage_path}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_upload())