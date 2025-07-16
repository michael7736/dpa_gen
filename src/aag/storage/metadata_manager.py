"""
Metadata Manager
文档元数据管理器
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
from sqlalchemy import text

from ...database.postgresql import get_session
from ...utils.logger import get_logger

logger = get_logger(__name__)


class MetadataManager:
    """文档元数据管理器"""
    
    async def create_metadata(
        self,
        document_id: str,
        skim_summary: Optional[Dict[str, Any]] = None,
        document_type: Optional[str] = None,
        quality_score: Optional[float] = None,
        target_audience: Optional[List[str]] = None
    ) -> str:
        """
        创建文档元数据
        
        Args:
            document_id: 文档ID
            skim_summary: 略读摘要
            document_type: 文档类型
            quality_score: 质量评分
            target_audience: 目标受众
            
        Returns:
            元数据ID
        """
        metadata_id = str(uuid4())
        
        async with get_session() as session:
            try:
                stmt = text("""
                    INSERT INTO document_metadata_v2 (
                        id, document_id, version,
                        skim_summary, document_type,
                        quality_score, target_audience
                    ) VALUES (
                        :id, :document_id, 1,
                        :skim_summary, :document_type,
                        :quality_score, :target_audience
                    )
                """)
                
                # 处理JSON字段
                skim_summary_json = None
                if skim_summary:
                    if isinstance(skim_summary, dict):
                        skim_summary_json = json.dumps(skim_summary, ensure_ascii=False)
                    elif isinstance(skim_summary, str):
                        skim_summary_json = skim_summary
                    else:
                        skim_summary_json = json.dumps(skim_summary, ensure_ascii=False)
                
                await session.execute(stmt, {
                    "id": metadata_id,
                    "document_id": document_id,
                    "skim_summary": skim_summary_json,
                    "document_type": document_type,
                    "quality_score": quality_score,
                    "target_audience": target_audience
                })
                
                await session.commit()
                logger.info(f"Created metadata {metadata_id} for document {document_id}")
                
                return metadata_id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create metadata: {str(e)}", exc_info=True)
                raise
    
    async def get_metadata(
        self,
        document_id: str,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档元数据
        
        Args:
            document_id: 文档ID
            version: 版本号（默认获取最新版本）
            
        Returns:
            元数据
        """
        async with get_session() as session:
            try:
                if version:
                    query = """
                        SELECT * FROM document_metadata_v2
                        WHERE document_id = :document_id AND version = :version
                    """
                    params = {"document_id": document_id, "version": version}
                else:
                    query = """
                        SELECT * FROM document_metadata_v2
                        WHERE document_id = :document_id
                        ORDER BY version DESC
                        LIMIT 1
                    """
                    params = {"document_id": document_id}
                
                result = await session.execute(text(query), params)
                row = result.fetchone()
                
                if not row:
                    return None
                
                # 将行转换为字典
                columns = result.keys()
                metadata = dict(zip(columns, row))
                
                # 解析JSON字段 - 安全处理
                for json_field in ["skim_summary", "analysis_plan", "ext"]:
                    if metadata.get(json_field):
                        field_value = metadata[json_field]
                        if isinstance(field_value, str):
                            try:
                                metadata[json_field] = json.loads(field_value)
                            except (json.JSONDecodeError, TypeError):
                                logger.warning(f"Failed to parse JSON field {json_field}, keeping as string")
                        elif isinstance(field_value, dict):
                            # 已经是字典格式，无需解析
                            pass
                        else:
                            logger.warning(f"Unexpected type for {json_field}: {type(field_value)}")
                
                # 转换UUID为字符串
                metadata["id"] = str(metadata["id"])
                metadata["document_id"] = str(metadata["document_id"])
                
                # 转换时间戳
                for field in ["created_at", "updated_at", "last_analysis_at"]:
                    if metadata.get(field):
                        metadata[field] = metadata[field].isoformat()
                
                return metadata
                
            except Exception as e:
                logger.error(f"Failed to get metadata: {str(e)}", exc_info=True)
                raise
    
    async def update_metadata(
        self,
        document_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        更新文档元数据
        
        Args:
            document_id: 文档ID
            updates: 更新内容
            
        Returns:
            是否成功
        """
        async with get_session() as session:
            try:
                # 构建更新语句
                set_clauses = []
                params = {"document_id": document_id}
                
                # 处理不同类型的字段
                json_fields = ["skim_summary", "analysis_plan", "ext"]
                array_fields = ["target_audience", "completed_steps"]
                
                for key, value in updates.items():
                    if key in json_fields and value is not None:
                        set_clauses.append(f"{key} = :{key}")
                        # 处理JSON字段 - 避免重复序列化
                        if isinstance(value, dict):
                            params[key] = json.dumps(value, ensure_ascii=False)
                        elif isinstance(value, str):
                            params[key] = value
                        else:
                            params[key] = json.dumps(value, ensure_ascii=False)
                    elif key in array_fields and value is not None:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                    else:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clauses:
                    return True
                
                # 添加更新时间
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                
                query = f"""
                    UPDATE document_metadata_v2
                    SET {', '.join(set_clauses)}
                    WHERE document_id = :document_id
                    AND version = (
                        SELECT MAX(version) FROM document_metadata_v2
                        WHERE document_id = :document_id
                    )
                """
                
                result = await session.execute(text(query), params)
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Updated metadata for document {document_id}")
                    return True
                else:
                    logger.warning(f"No metadata found to update for document {document_id}")
                    return False
                    
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update metadata: {str(e)}", exc_info=True)
                return False
    
    async def update_analysis_status(
        self,
        document_id: str,
        status: str,
        depth: Optional[str] = None
    ) -> bool:
        """
        更新分析状态
        
        Args:
            document_id: 文档ID
            status: 状态
            depth: 分析深度
            
        Returns:
            是否成功
        """
        updates = {
            "analysis_status": status
        }
        
        if depth:
            updates["analysis_depth"] = depth
            
        if status == "completed":
            updates["last_analysis_at"] = datetime.utcnow()
            
        return await self.update_metadata(document_id, updates)
    
    async def increment_counters(
        self,
        document_id: str,
        analyses: int = 0,
        artifacts: int = 0,
        tokens: int = 0
    ) -> bool:
        """
        增加计数器
        
        Args:
            document_id: 文档ID
            analyses: 分析次数增量
            artifacts: 物料数量增量
            tokens: Token使用量增量
            
        Returns:
            是否成功
        """
        async with get_session() as session:
            try:
                query = """
                    UPDATE document_metadata_v2
                    SET total_analyses = total_analyses + :analyses,
                        total_artifacts = total_artifacts + :artifacts,
                        total_tokens_used = total_tokens_used + :tokens,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = :document_id
                    AND version = (
                        SELECT MAX(version) FROM document_metadata_v2
                        WHERE document_id = :document_id
                    )
                """
                
                await session.execute(text(query), {
                    "document_id": document_id,
                    "analyses": analyses,
                    "artifacts": artifacts,
                    "tokens": tokens
                })
                
                await session.commit()
                logger.info(f"Updated counters for document {document_id}")
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update counters: {str(e)}", exc_info=True)
                return False
    
    async def add_completed_step(
        self,
        document_id: str,
        step: str
    ) -> bool:
        """
        添加已完成的步骤
        
        Args:
            document_id: 文档ID
            step: 步骤名称
            
        Returns:
            是否成功
        """
        async with get_session() as session:
            try:
                # 先获取当前的completed_steps
                metadata = await self.get_metadata(document_id)
                if not metadata:
                    logger.error(f"No metadata found for document {document_id}")
                    return False
                
                completed_steps = metadata.get("completed_steps", []) or []
                
                if step not in completed_steps:
                    completed_steps.append(step)
                    
                    return await self.update_metadata(document_id, {
                        "completed_steps": completed_steps
                    })
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to add completed step: {str(e)}", exc_info=True)
                return False