"""
文档索引服务
负责创建文档的向量索引以支持搜索和问答
"""

import os
import tempfile
from typing import Dict, Any, List, Callable
from sqlalchemy.orm import Session

from ..models.document import Document
from ..graphs.simplified_document_processor import SimplifiedDocumentProcessor
from ..services.minio_service import get_minio_service
from ..utils.logger import get_logger

logger = get_logger(__name__)


class IndexService:
    """索引服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.processor = SimplifiedDocumentProcessor()
    
    async def create_index(
        self,
        document: Document,
        progress_callback: Callable
    ) -> Dict[str, Any]:
        """
        为文档创建索引
        
        Args:
            document: 文档对象
            progress_callback: 进度回调函数
            
        Returns:
            索引结果
        """
        try:
            await progress_callback(5, "正在准备文档...")
            
            # 获取文档内容
            temp_file_path = None
            
            if document.file_path.startswith("s3://"):
                # 从MinIO获取文件内容
                minio_service = get_minio_service()
                
                # 解析MinIO路径
                storage_path = document.file_path
                parts = storage_path.replace("s3://", "").split("/", 1)
                if len(parts) >= 2:
                    object_path = parts[1]
                    path_parts = object_path.split("/")
                    if len(path_parts) >= 4:
                        user_id = path_parts[0]
                        project_id = path_parts[1]
                        document_id = path_parts[2]
                        file_name = "/".join(path_parts[4:])  # original/filename
                        
                        # 获取文件内容
                        content = await minio_service.get_document(
                            user_id, project_id, str(document.id), file_name
                        )
                        
                        # 创建临时文件
                        file_extension = os.path.splitext(document.filename)[1]
                        with tempfile.NamedTemporaryFile(mode='wb', suffix=file_extension, delete=False) as temp_file:
                            temp_file.write(content)
                            temp_file_path = temp_file.name
                        
                        actual_file_path = temp_file_path
            else:
                # 本地文件路径
                actual_file_path = document.file_path
            
            await progress_callback(10, "正在准备索引...")
            
            # 准备文档信息
            document_info = {
                "document_id": str(document.id),
                "project_id": str(document.project_id),
                "file_path": actual_file_path,
                "file_name": document.filename,
                "mode": "standard"
            }
            
            # 使用简化文档处理器的部分功能
            # 创建一个包装的进度回调
            def wrapped_callback(state):
                # 将处理器的进度映射到我们的进度
                progress = state.get("progress", 0)
                if progress <= 20:  # 解析阶段
                    actual_progress = int(progress * 0.5)  # 0-10%
                    message = "正在解析文档..."
                elif progress <= 40:  # 分块阶段
                    actual_progress = int(10 + (progress - 20) * 2)  # 10-50%
                    message = "正在分块处理..."
                elif progress <= 60:  # 向量化阶段
                    actual_progress = int(50 + (progress - 40) * 2)  # 50-90%
                    message = "正在生成向量..."
                else:  # 存储阶段
                    actual_progress = int(90 + (progress - 60) * 0.25)  # 90-100%
                    message = "正在存储索引..."
                
                # 同步调用异步回调
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(progress_callback(actual_progress, message))
                except RuntimeError:
                    # 如果没有事件循环，创建一个新的
                    asyncio.run(progress_callback(actual_progress, message))
                
                return state
            
            # 处理文档（仅执行向量化和存储步骤）
            result = await self.processor.process_document(document_info)
            
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.info(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")
            
            if result.get("success"):
                # 更新文档的块数信息
                if document.metadata_info is None:
                    document.metadata_info = {}
                document.metadata_info["chunks_count"] = result.get("metadata", {}).get("chunk_count", 0)
                document.metadata_info["index_info"] = {
                    "indexed_at": result.get("metadata", {}).get("indexed_at"),
                    "vector_dimension": result.get("metadata", {}).get("vector_dimension", 3072),
                    "collection": result.get("metadata", {}).get("collection_name", "chunks")
                }
                
                await progress_callback(100, "索引创建完成")
                
                return {
                    "success": True,
                    "chunks_count": result.get("metadata", {}).get("chunk_count", 0),
                    "processing_time": result.get("metadata", {}).get("processing_time", 0),
                    "collection_name": result.get("metadata", {}).get("collection_name", "chunks")
                }
            else:
                raise Exception(result.get("error", "索引创建失败"))
                
        except Exception as e:
            # 确保清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            logger.error(f"Index creation failed for document {document.id}: {e}")
            raise