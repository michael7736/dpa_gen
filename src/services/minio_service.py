"""
MinIO对象存储服务
处理文档的存储、检索和管理
"""

import io
import json
import urllib.parse
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path

from minio import Minio
from minio.error import S3Error
from minio.commonconfig import Tags
from minio.datatypes import Object

from ..config.settings import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MinIOService:
    """MinIO对象存储服务类"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.client = Minio(
            endpoint=settings.minio.endpoint,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            secure=settings.minio.secure
        )
        self.bucket_name = settings.minio.bucket_name
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
                
                # 设置桶策略允许读取
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": ["*"]},
                            "Action": ["s3:GetBucketLocation"],
                            "Resource": [f"arn:aws:s3:::{self.bucket_name}"]
                        }
                    ]
                }
                self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
        except S3Error as e:
            logger.error(f"Error ensuring bucket: {e}")
            raise
    
    @staticmethod
    def encode_filename(filename: str) -> str:
        """编码文件名以支持非ASCII字符"""
        return urllib.parse.quote(filename, safe='')
    
    @staticmethod
    def decode_filename(encoded_filename: str) -> str:
        """解码文件名"""
        return urllib.parse.unquote(encoded_filename)
    
    def _get_document_path(self, user_id: str, project_id: str, document_id: str, 
                          path_type: str = "original") -> str:
        """
        获取文档存储路径
        
        Args:
            user_id: 用户ID
            project_id: 项目ID  
            document_id: 文档ID
            path_type: 路径类型 (original, processed, temp)
            
        Returns:
            文档路径
        """
        return f"{user_id}/{project_id}/{document_id}/{path_type}/"
    
    async def upload_document(self, 
                            file_content: bytes,
                            file_name: str,
                            user_id: str,
                            project_id: str,
                            document_id: str,
                            content_type: Optional[str] = None,
                            metadata: Optional[Dict[str, str]] = None) -> str:
        """
        上传文档到MinIO
        
        Args:
            file_content: 文件内容
            file_name: 文件名
            user_id: 用户ID
            project_id: 项目ID
            document_id: 文档ID
            content_type: 内容类型
            metadata: 元数据
            
        Returns:
            文档存储路径
        """
        try:
            # 构建存储路径
            object_name = self._get_document_path(user_id, project_id, document_id, "original") + file_name
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            
            # 对文件名进行 URL 编码以支持非 ASCII 字符
            encoded_filename = self.encode_filename(file_name)
            
            metadata.update({
                "user_id": user_id,
                "project_id": project_id,
                "document_id": document_id,
                "upload_time": datetime.utcnow().isoformat(),
                "original_name": encoded_filename  # 使用编码后的文件名
            })
            
            # 上传文件
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type=content_type or "application/octet-stream",
                metadata=metadata
            )
            
            logger.info(f"Document uploaded successfully: {object_name}")
            return f"s3://{self.bucket_name}/{object_name}"
            
        except S3Error as e:
            logger.error(f"Error uploading document: {e}")
            raise
    
    async def get_document(self, 
                         user_id: str,
                         project_id: str,
                         document_id: str,
                         file_name: str,
                         path_type: str = "original") -> bytes:
        """
        从MinIO获取文档
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            document_id: 文档ID
            file_name: 文件名
            path_type: 路径类型
            
        Returns:
            文档内容
        """
        try:
            object_name = self._get_document_path(user_id, project_id, document_id, path_type) + file_name
            
            response = self.client.get_object(self.bucket_name, object_name)
            content = response.read()
            response.close()
            response.release_conn()
            
            return content
            
        except S3Error as e:
            logger.error(f"Error getting document: {e}")
            raise
    
    async def delete_document(self,
                            user_id: str,
                            project_id: str,
                            document_id: str) -> bool:
        """
        删除文档及其所有相关文件
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            document_id: 文档ID
            
        Returns:
            是否成功删除
        """
        try:
            # 获取文档前缀
            prefix = f"{user_id}/{project_id}/{document_id}/"
            
            # 列出所有相关对象
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            # 删除所有对象
            delete_list = [obj.object_name for obj in objects]
            if delete_list:
                errors = self.client.remove_objects(self.bucket_name, delete_list)
                for error in errors:
                    logger.error(f"Error deleting object: {error}")
                    
            logger.info(f"Document deleted: {document_id}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def get_document_url(self,
                             user_id: str,
                             project_id: str,
                             document_id: str,
                             file_name: str,
                             expiry: int = 3600) -> str:
        """
        获取文档的临时访问URL
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            document_id: 文档ID
            file_name: 文件名
            expiry: URL有效期（秒）
            
        Returns:
            临时访问URL
        """
        try:
            object_name = self._get_document_path(user_id, project_id, document_id, "original") + file_name
            
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expiry)
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    async def save_processing_result(self,
                                   user_id: str,
                                   project_id: str,
                                   document_id: str,
                                   result_type: str,
                                   content: Any,
                                   format: str = "json") -> str:
        """
        保存处理结果
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            document_id: 文档ID
            result_type: 结果类型 (summary, index, analysis)
            content: 结果内容
            format: 保存格式
            
        Returns:
            结果存储路径
        """
        try:
            # 构建路径
            file_name = f"{result_type}.{format}"
            object_name = self._get_document_path(
                user_id, project_id, document_id, "processed"
            ) + file_name
            
            # 序列化内容
            if format == "json":
                content_bytes = json.dumps(content, ensure_ascii=False, indent=2).encode('utf-8')
                content_type = "application/json"
            else:
                content_bytes = str(content).encode('utf-8')
                content_type = "text/plain"
            
            # 上传结果
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(content_bytes),
                length=len(content_bytes),
                content_type=content_type,
                metadata={
                    "result_type": result_type,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Processing result saved: {object_name}")
            return f"s3://{self.bucket_name}/{object_name}"
            
        except Exception as e:
            logger.error(f"Error saving processing result: {e}")
            raise
    
    async def get_processing_result(self,
                                  user_id: str,
                                  project_id: str,
                                  document_id: str,
                                  result_type: str,
                                  format: str = "json") -> Optional[Any]:
        """
        获取处理结果
        
        Args:
            user_id: 用户ID
            project_id: 项目ID
            document_id: 文档ID
            result_type: 结果类型
            format: 结果格式
            
        Returns:
            处理结果
        """
        try:
            file_name = f"{result_type}.{format}"
            content = await self.get_document(
                user_id, project_id, document_id, file_name, "processed"
            )
            
            if format == "json":
                return json.loads(content.decode('utf-8'))
            else:
                return content.decode('utf-8')
                
        except S3Error as e:
            if e.code == "NoSuchKey":
                return None
            logger.error(f"Error getting processing result: {e}")
            raise


# 全局实例
_minio_service: Optional[MinIOService] = None


def get_minio_service() -> MinIOService:
    """获取MinIO服务实例"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service