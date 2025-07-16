"""
Analysis Artifact Store
分析物料存储管理
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from sqlalchemy import text, select, and_
from sqlalchemy.dialects.postgresql import insert

from ...database.postgresql import get_session
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactStore:
    """分析物料存储管理器"""
    
    async def save_artifact(
        self,
        document_id: str,
        analysis_type: str,
        content: Dict[str, Any],
        depth_level: Optional[str] = None,
        execution_time_seconds: Optional[int] = None,
        token_usage: Optional[int] = None,
        model_used: Optional[str] = None,
        created_by: Optional[str] = "system"
    ) -> str:
        """
        保存分析物料
        
        Args:
            document_id: 文档ID
            analysis_type: 分析类型
            content: 分析内容
            depth_level: 深度级别
            execution_time_seconds: 执行时间
            token_usage: Token使用量
            model_used: 使用的模型
            created_by: 创建者
            
        Returns:
            物料ID
        """
        artifact_id = str(uuid4())
        
        async with get_session() as session:
            try:
                # 创建摘要
                summary = self._generate_summary(analysis_type, content)
                
                # 插入数据
                stmt = text("""
                    INSERT INTO analysis_artifacts (
                        id, document_id, analysis_type, depth_level,
                        content, summary, execution_time_seconds,
                        token_usage, model_used, created_by
                    ) VALUES (
                        :id, :document_id, :analysis_type, :depth_level,
                        :content, :summary, :execution_time_seconds,
                        :token_usage, :model_used, :created_by
                    )
                """)
                
                await session.execute(stmt, {
                    "id": artifact_id,
                    "document_id": document_id,
                    "analysis_type": analysis_type,
                    "depth_level": depth_level,
                    "content": json.dumps(content, ensure_ascii=False),
                    "summary": summary,
                    "execution_time_seconds": execution_time_seconds,
                    "token_usage": token_usage,
                    "model_used": model_used,
                    "created_by": created_by
                })
                
                await session.commit()
                logger.info(f"Saved artifact {artifact_id} for document {document_id}")
                
                return artifact_id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save artifact: {str(e)}", exc_info=True)
                raise
    
    async def get_artifact(
        self,
        artifact_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取分析物料
        
        Args:
            artifact_id: 物料ID
            
        Returns:
            物料内容
        """
        async with get_session() as session:
            try:
                stmt = text("""
                    SELECT id, document_id, analysis_type, depth_level,
                           content, summary, execution_time_seconds,
                           token_usage, model_used, created_at, created_by,
                           user_corrections, is_user_approved, version
                    FROM analysis_artifacts
                    WHERE id = :id
                """)
                
                result = await session.execute(stmt, {"id": artifact_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                return {
                    "id": str(row[0]),
                    "document_id": str(row[1]),
                    "analysis_type": row[2],
                    "depth_level": row[3],
                    "content": json.loads(row[4]) if row[4] else {},
                    "summary": row[5],
                    "execution_time_seconds": row[6],
                    "token_usage": row[7],
                    "model_used": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                    "created_by": row[10],
                    "user_corrections": json.loads(row[11]) if row[11] else [],
                    "is_user_approved": row[12],
                    "version": row[13]
                }
                
            except Exception as e:
                logger.error(f"Failed to get artifact: {str(e)}", exc_info=True)
                raise
    
    async def get_document_artifacts(
        self,
        document_id: str,
        analysis_type: Optional[str] = None,
        depth_level: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取文档的所有分析物料
        
        Args:
            document_id: 文档ID
            analysis_type: 分析类型过滤
            depth_level: 深度级别过滤
            limit: 返回数量限制
            
        Returns:
            物料列表
        """
        async with get_session() as session:
            try:
                query = """
                    SELECT id, document_id, analysis_type, depth_level,
                           content, summary, execution_time_seconds,
                           token_usage, model_used, created_at, created_by,
                           user_corrections, is_user_approved, version
                    FROM analysis_artifacts
                    WHERE document_id = :document_id
                """
                
                params = {"document_id": document_id}
                
                if analysis_type:
                    query += " AND analysis_type = :analysis_type"
                    params["analysis_type"] = analysis_type
                
                if depth_level:
                    query += " AND depth_level = :depth_level"
                    params["depth_level"] = depth_level
                
                query += " ORDER BY created_at DESC LIMIT :limit"
                params["limit"] = limit
                
                result = await session.execute(text(query), params)
                
                artifacts = []
                for row in result:
                    artifacts.append({
                        "id": str(row[0]),
                        "document_id": str(row[1]),
                        "analysis_type": row[2],
                        "depth_level": row[3],
                        "content": json.loads(row[4]) if row[4] else {},
                        "summary": row[5],
                        "execution_time_seconds": row[6],
                        "token_usage": row[7],
                        "model_used": row[8],
                        "created_at": row[9].isoformat() if row[9] else None,
                        "created_by": row[10],
                        "user_corrections": json.loads(row[11]) if row[11] else [],
                        "is_user_approved": row[12],
                        "version": row[13]
                    })
                
                return artifacts
                
            except Exception as e:
                logger.error(f"Failed to get document artifacts: {str(e)}", exc_info=True)
                raise
    
    async def update_artifact_corrections(
        self,
        artifact_id: str,
        corrections: List[Dict[str, Any]],
        is_approved: bool = False
    ) -> bool:
        """
        更新物料的用户纠正
        
        Args:
            artifact_id: 物料ID
            corrections: 纠正列表
            is_approved: 是否用户批准
            
        Returns:
            是否成功
        """
        async with get_session() as session:
            try:
                stmt = text("""
                    UPDATE analysis_artifacts
                    SET user_corrections = :corrections,
                        is_user_approved = :is_approved,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """)
                
                await session.execute(stmt, {
                    "id": artifact_id,
                    "corrections": json.dumps(corrections, ensure_ascii=False),
                    "is_approved": is_approved
                })
                
                await session.commit()
                logger.info(f"Updated corrections for artifact {artifact_id}")
                
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update artifact corrections: {str(e)}", exc_info=True)
                return False
    
    def _generate_summary(
        self,
        analysis_type: str,
        content: Dict[str, Any]
    ) -> str:
        """
        根据分析类型生成摘要
        
        Args:
            analysis_type: 分析类型
            content: 内容
            
        Returns:
            摘要文本
        """
        if analysis_type == "skim":
            return content.get("core_topic", "文档快速略读结果")
        elif analysis_type == "summary":
            # 取第一级摘要
            if "level_1" in content:
                return content["level_1"]
            return "文档摘要"
        elif analysis_type == "outline":
            return "文档大纲分析"
        elif analysis_type == "knowledge_graph":
            entity_count = len(content.get("entities", []))
            relation_count = len(content.get("relations", []))
            return f"知识图谱：{entity_count}个实体，{relation_count}个关系"
        elif analysis_type == "evidence_chain":
            return f"证据链分析：{content.get('claim', '核心论点')}"
        else:
            return f"{analysis_type}分析结果"