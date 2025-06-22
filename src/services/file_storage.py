"""
本地文件存储服务
使用操作系统自带的文件系统进行文档存储和管理
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import aiofiles
import aiofiles.os
from pydantic import BaseModel

class FileMetadata(BaseModel):
    """文件元数据"""
    file_id: str
    original_name: str
    file_path: str
    file_size: int
    mime_type: str
    content_hash: str
    created_at: datetime
    project_id: Optional[str] = None

class LocalFileStorage:
    """本地文件存储服务"""
    
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            "uploads/documents",
            "uploads/images", 
            "processed/chunks",
            "processed/embeddings",
            "processed/extracted",
            "projects",
            "temp",
            "backups"
        ]
        
        for directory in directories:
            (self.base_path / directory).mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(
        self, 
        file_content: bytes, 
        original_filename: str,
        project_id: Optional[str] = None
    ) -> FileMetadata:
        """保存上传的文件"""
        
        # 生成文件ID和哈希
        content_hash = hashlib.sha256(file_content).hexdigest()
        file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash[:8]}"
        
        # 获取文件扩展名和MIME类型
        file_extension = Path(original_filename).suffix
        mime_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"
        
        # 构建文件路径
        relative_path = f"uploads/documents/{file_id}{file_extension}"
        file_path = self.base_path / relative_path
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # 创建元数据
        metadata = FileMetadata(
            file_id=file_id,
            original_name=original_filename,
            file_path=str(relative_path),
            file_size=len(file_content),
            mime_type=mime_type,
            content_hash=content_hash,
            created_at=datetime.now(),
            project_id=project_id
        )
        
        return metadata
    
    async def get_file_content(self, file_path: str) -> bytes:
        """获取文件内容"""
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()
    
    async def get_file_stream(self, file_path: str):
        """获取文件流（用于大文件下载）"""
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return aiofiles.open(full_path, 'rb')
    
    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        full_path = self.base_path / file_path
        
        try:
            if full_path.exists():
                await aiofiles.os.remove(full_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    async def move_to_processed(self, file_path: str, processed_type: str) -> str:
        """将文件移动到处理后的目录"""
        source_path = self.base_path / file_path
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        # 构建目标路径
        filename = source_path.name
        target_relative = f"processed/{processed_type}/{filename}"
        target_path = self.base_path / target_relative
        
        # 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 移动文件
        shutil.move(str(source_path), str(target_path))
        
        return target_relative
    
    async def save_processed_data(
        self, 
        data: Any, 
        filename: str, 
        data_type: str = "chunks"
    ) -> str:
        """保存处理后的数据（JSON格式）"""
        import json
        
        target_path = self.base_path / f"processed/{data_type}/{filename}"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果是字典或列表，转换为JSON
        if isinstance(data, (dict, list)):
            content = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            content = str(data)
        
        async with aiofiles.open(target_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        return f"processed/{data_type}/{filename}"
    
    async def load_processed_data(self, file_path: str) -> Any:
        """加载处理后的数据"""
        import json
        
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Processed data not found: {file_path}")
        
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # 尝试解析JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    
    async def create_project_directory(self, project_id: str) -> str:
        """为项目创建专用目录"""
        project_path = self.base_path / f"projects/{project_id}"
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        subdirs = ["exports", "cache", "temp"]
        for subdir in subdirs:
            (project_path / subdir).mkdir(exist_ok=True)
        
        return f"projects/{project_id}"
    
    async def save_project_export(
        self, 
        project_id: str, 
        export_data: Any, 
        export_name: str
    ) -> str:
        """保存项目导出数据"""
        export_path = f"projects/{project_id}/exports/{export_name}"
        return await self.save_processed_data(export_data, export_name, f"../projects/{project_id}/exports")
    
    async def cleanup_temp_files(self, older_than_hours: int = 24):
        """清理临时文件"""
        import time
        
        temp_path = self.base_path / "temp"
        current_time = time.time()
        cutoff_time = current_time - (older_than_hours * 3600)
        
        if not temp_path.exists():
            return
        
        for file_path in temp_path.rglob("*"):
            if file_path.is_file():
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f"Error deleting temp file {file_path}: {e}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_type": {},
            "by_directory": {}
        }
        
        for directory in ["uploads", "processed", "projects"]:
            dir_path = self.base_path / directory
            if not dir_path.exists():
                continue
            
            dir_stats = {"files": 0, "size": 0}
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    file_ext = file_path.suffix.lower()
                    
                    stats["total_files"] += 1
                    stats["total_size"] += file_size
                    
                    dir_stats["files"] += 1
                    dir_stats["size"] += file_size
                    
                    # 按文件类型统计
                    if file_ext not in stats["by_type"]:
                        stats["by_type"][file_ext] = {"files": 0, "size": 0}
                    stats["by_type"][file_ext]["files"] += 1
                    stats["by_type"][file_ext]["size"] += file_size
            
            stats["by_directory"][directory] = dir_stats
        
        return stats
    
    def get_absolute_path(self, relative_path: str) -> str:
        """获取文件的绝对路径"""
        return str(self.base_path / relative_path)
    
    async def backup_file(self, file_path: str) -> str:
        """备份文件"""
        source_path = self.base_path / file_path
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        # 构建备份路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
        backup_relative = f"backups/{backup_name}"
        backup_path = self.base_path / backup_relative
        
        # 确保备份目录存在
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        shutil.copy2(str(source_path), str(backup_path))
        
        return backup_relative


# 全局文件存储实例
file_storage = LocalFileStorage()


# 使用示例
async def example_usage():
    """使用示例"""
    
    # 保存上传的文件
    with open("example.pdf", "rb") as f:
        file_content = f.read()
    
    metadata = await file_storage.save_uploaded_file(
        file_content=file_content,
        original_filename="research_paper.pdf",
        project_id="project_123"
    )
    
    print(f"File saved: {metadata.file_path}")
    
    # 获取文件内容
    content = await file_storage.get_file_content(metadata.file_path)
    print(f"File size: {len(content)} bytes")
    
    # 保存处理后的数据
    processed_data = {
        "chunks": ["chunk1", "chunk2"],
        "metadata": {"pages": 10}
    }
    
    processed_path = await file_storage.save_processed_data(
        data=processed_data,
        filename="processed_data.json",
        data_type="chunks"
    )
    
    # 获取存储统计
    stats = await file_storage.get_storage_stats()
    print(f"Storage stats: {stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage()) 