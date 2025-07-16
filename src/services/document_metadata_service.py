"""
文档元数据服务
用于管理和更新文档的处理元数据
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import json

from sqlalchemy.orm import Session

from ..models.document import Document, ProcessingStatus
from ..models.document_metadata import DocumentMetadata
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DocumentMetadataService:
    """文档元数据服务类"""
    
    @staticmethod
    def update_processing_metadata(
        db: Session,
        document_id: UUID,
        processing_type: str,
        result_data: Dict[str, Any],
        processing_duration: Optional[float] = None
    ) -> DocumentMetadata:
        """
        更新文档的处理元数据
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            processing_type: 处理类型 (summary, index, analysis)
            result_data: 处理结果数据
            processing_duration: 处理耗时（秒）
            
        Returns:
            更新后的元数据对象
        """
        try:
            # 获取或创建文档元数据
            metadata = db.query(DocumentMetadata).filter(
                DocumentMetadata.document_id == document_id
            ).first()
            
            if not metadata:
                metadata = DocumentMetadata(
                    document_id=document_id,
                    processing_history=[]
                )
                db.add(metadata)
            
            # 构建处理记录
            processing_record = {
                "type": processing_type,
                "timestamp": datetime.utcnow().isoformat(),
                "duration": processing_duration,
                "result": result_data
            }
            
            # 更新处理历史
            if not metadata.processing_history:
                metadata.processing_history = []
            metadata.processing_history.append(processing_record)
            
            # 更新特定字段
            if processing_type == "summary":
                metadata.summary_metadata = {
                    "generated_at": datetime.utcnow().isoformat(),
                    "summary_length": len(result_data.get("summary", "")),
                    "key_points": result_data.get("key_points", []),
                    "model_used": result_data.get("model", "unknown")
                }
                
                # 更新文档的摘要字段
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.summary = result_data.get("summary", "")
                    document.processing_status = ProcessingStatus.SUMMARIZED
                    
            elif processing_type == "index":
                metadata.index_metadata = {
                    "indexed_at": datetime.utcnow().isoformat(),
                    "chunk_count": result_data.get("chunk_count", 0),
                    "vector_count": result_data.get("vector_count", 0),
                    "index_type": result_data.get("index_type", "vector"),
                    "embedding_model": result_data.get("embedding_model", "unknown")
                }
                
                # 更新文档状态
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.processing_status = ProcessingStatus.INDEXED
                    
            elif processing_type == "analysis":
                # 分析可以多次进行，保存所有分析历史
                if not metadata.analysis_metadata:
                    metadata.analysis_metadata = {"analyses": []}
                    
                analysis_record = {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "analysis_id": result_data.get("analysis_id"),
                    "depth_level": result_data.get("depth_level", "standard"),
                    "analysis_goal": result_data.get("analysis_goal"),
                    "key_insights_count": len(result_data.get("key_insights", [])),
                    "action_items_count": len(result_data.get("action_items", []))
                }
                
                metadata.analysis_metadata["analyses"].append(analysis_record)
                metadata.analysis_metadata["latest_analysis_id"] = result_data.get("analysis_id")
                
                # 更新文档状态
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.processing_status = ProcessingStatus.ANALYZED
            
            # 提交更改
            db.commit()
            db.refresh(metadata)
            
            logger.info(f"成功更新文档 {document_id} 的 {processing_type} 元数据")
            return metadata
            
        except Exception as e:
            logger.error(f"更新文档元数据失败: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_processing_history(
        db: Session,
        document_id: UUID,
        processing_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取文档的处理历史
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            processing_type: 筛选的处理类型（可选）
            
        Returns:
            处理历史记录列表
        """
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
        ).first()
        
        if not metadata or not metadata.processing_history:
            return []
        
        history = metadata.processing_history
        
        # 如果指定了处理类型，进行筛选
        if processing_type:
            history = [h for h in history if h.get("type") == processing_type]
        
        # 按时间倒序排列
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return history
    
    @staticmethod
    def get_latest_analysis(
        db: Session,
        document_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档的最新分析结果
        
        Args:
            db: 数据库会话
            document_id: 文档ID
            
        Returns:
            最新的分析结果，如果没有则返回None
        """
        metadata = db.query(DocumentMetadata).filter(
            DocumentMetadata.document_id == document_id
        ).first()
        
        if not metadata or not metadata.analysis_metadata:
            return None
        
        latest_analysis_id = metadata.analysis_metadata.get("latest_analysis_id")
        if not latest_analysis_id:
            return None
        
        # 从分析表中获取详细结果
        from ..models.analysis import DocumentAnalysis
        analysis = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.id == latest_analysis_id
        ).first()
        
        if analysis:
            return {
                "analysis_id": str(analysis.id),
                "depth_level": analysis.depth_level,
                "executive_summary": analysis.executive_summary,
                "key_insights": analysis.key_insights,
                "action_items": analysis.action_items,
                "created_at": analysis.created_at.isoformat()
            }
        
        return None
    
    @staticmethod
    def mark_processing_complete(
        db: Session,
        document_id: UUID
    ):
        """
        标记文档处理完成
        
        Args:
            db: 数据库会话
            document_id: 文档ID
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processing_status = ProcessingStatus.COMPLETED
            
            # 更新元数据中的完成时间
            metadata = db.query(DocumentMetadata).filter(
                DocumentMetadata.document_id == document_id
            ).first()
            
            if metadata:
                if not metadata.metadata_info:
                    metadata.metadata_info = {}
                metadata.metadata_info["completed_at"] = datetime.utcnow().isoformat()
            
            db.commit()
            logger.info(f"文档 {document_id} 标记为处理完成")