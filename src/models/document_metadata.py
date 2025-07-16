"""
文档元数据扩展模型
支持增量更新和灵活的元数据管理
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .base import BaseEntity, Base


class DocumentSource(str, Enum):
    """文档来源枚举"""
    USER_UPLOAD = "user_upload"  # 用户上传
    AI_GENERATED = "ai_generated"  # AI生成
    ANALYSIS_GENERATED = "analysis_generated"  # 分析生成
    INTERNET_SEARCH = "internet_search"  # 网络检索
    ARCHIVE = "archive"  # 归档文档
    EXTERNAL_API = "external_api"  # 外部API


class ConfidenceLevel(str, Enum):
    """置信度等级"""
    AUTHORITATIVE = "authoritative"  # 权威
    MODERATE = "moderate"  # 中等
    REFERENCE_ONLY = "reference_only"  # 仅供参考
    UNDER_REVIEW = "under_review"  # 被评审中


class DocumentMetadata(BaseEntity):
    """增强的文档元数据表"""
    __tablename__ = "document_metadata"
    
    # 关联字段
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), unique=True, nullable=False)
    # document = relationship("Document", back_populates="document_metadata")
    
    # 基础元数据
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), index=True, comment="所属项目")
    directory_path = Column(String, comment="所在目录路径")
    
    # 引用关系 - 使用JSONB存储复杂关系
    upstream_references = Column(JSONB, default=list, comment="参考文献-上游")
    downstream_citations = Column(JSONB, default=list, comment="被引用文献-下游")
    
    # 文档来源
    source_type = Column(String(50), comment="文档来源类型")
    source_url = Column(Text, comment="原始URL（如果是网络来源）")
    source_metadata = Column(JSONB, default=dict, comment="来源相关元数据")
    
    # 文档置信度
    confidence_stars = Column(Integer, default=3, comment="置信度星级 1-5")
    confidence_level = Column(String(50), comment="置信度等级")
    confidence_notes = Column(Text, comment="置信度评级说明")
    
    # 文档时效性
    publication_date = Column(DateTime(timezone=True), comment="发表时间")
    publication_year_month = Column(String(20), comment="发表年月 YYYY-MM")
    expiry_date = Column(DateTime(timezone=True), comment="过期时间")
    is_outdated = Column(Boolean, default=False, comment="是否已过时")
    
    # 内容摘要
    abstract = Column(Text, comment="文档摘要")
    table_of_contents = Column(JSONB, default=list, comment="文档目录结构")
    key_points = Column(JSONB, default=list, comment="关键要点")
    
    # 增量更新追踪
    metadata_version = Column(Integer, default=1, comment="元数据版本")
    last_enriched_at = Column(DateTime(timezone=True), comment="最后丰富时间")
    enrichment_status = Column(JSONB, default=dict, comment="各字段填充状态")
    
    # 审计字段
    reviewed_by = Column(String, comment="审核人")
    reviewed_at = Column(DateTime(timezone=True), comment="审核时间")
    review_notes = Column(Text, comment="审核备注")
    
    # 处理相关元数据
    processing_history = Column(JSONB, default=list, comment="处理历史记录")
    summary_metadata = Column(JSONB, default=dict, comment="摘要生成元数据")
    index_metadata = Column(JSONB, default=dict, comment="索引创建元数据")
    analysis_metadata = Column(JSONB, default=dict, comment="分析结果元数据")


# 文档引用关系表（多对多）
document_references = Table(
    'document_references',
    Base.metadata,
    Column('citing_document_id', PG_UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('cited_document_id', PG_UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('reference_type', String, comment="引用类型"),
    Column('reference_context', Text, comment="引用上下文"),
    Column('created_at', DateTime(timezone=True), default=datetime.now)
)


class DocumentMetadataUpdate(BaseModel):
    """文档元数据更新模型（支持部分更新）"""
    project_id: Optional[str] = None
    directory_path: Optional[str] = None
    
    # 引用关系
    upstream_references: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="上游参考文献列表",
        example=[{"document_id": "doc123", "title": "参考文献标题", "type": "paper"}]
    )
    downstream_citations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="下游引用文献列表"
    )
    
    # 文档来源
    source_type: Optional[DocumentSource] = None
    source_url: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    
    # 置信度
    confidence_stars: Optional[int] = Field(None, ge=1, le=5)
    confidence_level: Optional[ConfidenceLevel] = None
    confidence_notes: Optional[str] = None
    
    # 时效性
    publication_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    
    # 内容
    abstract: Optional[str] = None
    table_of_contents: Optional[List[Dict[str, Any]]] = Field(
        None,
        example=[{"level": 1, "title": "第一章", "page": 1}]
    )
    key_points: Optional[List[str]] = None
    
    @validator('publication_date')
    def format_publication_year_month(cls, v, values):
        """自动生成年月格式"""
        if v:
            values['publication_year_month'] = v.strftime("%Y-%m")
        return v
    
    class Config:
        use_enum_values = True


class MetadataEnrichmentService:
    """元数据丰富服务"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    async def enrich_metadata(self, document_id: str, updates: DocumentMetadataUpdate):
        """增量更新文档元数据"""
        # 获取或创建元数据记录
        metadata = self.session.query(DocumentMetadata).filter_by(
            document_id=document_id
        ).first()
        
        if not metadata:
            metadata = DocumentMetadata(document_id=document_id)
            self.session.add(metadata)
        
        # 记录哪些字段被更新
        enrichment_status = metadata.enrichment_status or {}
        
        # 应用更新
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                setattr(metadata, field, value)
                enrichment_status[field] = {
                    "filled": True,
                    "last_updated": datetime.now().isoformat()
                }
        
        # 更新元数据版本和状态
        metadata.metadata_version += 1
        metadata.last_enriched_at = datetime.now()
        metadata.enrichment_status = enrichment_status
        
        await self.session.commit()
        return metadata
    
    async def extract_metadata_from_content(self, document_id: str, content: str):
        """从文档内容中提取元数据"""
        # 这里可以使用LLM来提取
        # 1. 提取摘要
        # 2. 生成目录
        # 3. 识别关键要点
        # 4. 判断文档类型和置信度
        pass
    
    async def update_references(self, citing_doc_id: str, cited_doc_ids: List[str]):
        """更新文档引用关系"""
        # 更新上游引用
        citing_metadata = await self._get_or_create_metadata(citing_doc_id)
        citing_metadata.upstream_references = [
            {"document_id": doc_id} for doc_id in cited_doc_ids
        ]
        
        # 更新下游被引用
        for cited_doc_id in cited_doc_ids:
            cited_metadata = await self._get_or_create_metadata(cited_doc_id)
            downstream = cited_metadata.downstream_citations or []
            if citing_doc_id not in [d.get("document_id") for d in downstream]:
                downstream.append({"document_id": citing_doc_id})
                cited_metadata.downstream_citations = downstream
        
        await self.session.commit()
    
    async def calculate_confidence_score(self, document_id: str) -> Dict[str, Any]:
        """计算文档置信度评分"""
        factors = {
            "source_reliability": 0,  # 来源可靠性
            "citation_count": 0,  # 被引用次数
            "review_status": 0,  # 审核状态
            "content_quality": 0,  # 内容质量
            "timeliness": 0  # 时效性
        }
        
        metadata = await self._get_metadata(document_id)
        if not metadata:
            return {"stars": 3, "level": ConfidenceLevel.REFERENCE_ONLY}
        
        # 根据来源类型评分
        source_scores = {
            DocumentSource.AUTHORITATIVE: 5,
            DocumentSource.USER_UPLOAD: 3,
            DocumentSource.AI_GENERATED: 2,
            DocumentSource.INTERNET_SEARCH: 2,
            DocumentSource.ANALYSIS_GENERATED: 4
        }
        factors["source_reliability"] = source_scores.get(metadata.source_type, 3)
        
        # 根据被引用次数评分
        citation_count = len(metadata.downstream_citations or [])
        factors["citation_count"] = min(5, citation_count + 1)
        
        # 计算总分
        total_score = sum(factors.values()) / len(factors)
        stars = round(total_score)
        
        # 确定置信度等级
        if stars >= 4:
            level = ConfidenceLevel.AUTHORITATIVE
        elif stars >= 3:
            level = ConfidenceLevel.MODERATE
        elif metadata.reviewed_by:
            level = ConfidenceLevel.UNDER_REVIEW
        else:
            level = ConfidenceLevel.REFERENCE_ONLY
        
        return {
            "stars": stars,
            "level": level,
            "factors": factors,
            "notes": self._generate_confidence_notes(factors)
        }
    
    def _generate_confidence_notes(self, factors: Dict[str, float]) -> str:
        """生成置信度说明"""
        notes = []
        if factors["source_reliability"] >= 4:
            notes.append("来源可靠")
        if factors["citation_count"] >= 3:
            notes.append("被广泛引用")
        if factors["timeliness"] <= 2:
            notes.append("可能已过时")
        
        return "；".join(notes) if notes else "标准文档"
    
    async def _get_or_create_metadata(self, document_id: str) -> DocumentMetadata:
        """获取或创建元数据记录"""
        metadata = self.session.query(DocumentMetadata).filter_by(
            document_id=document_id
        ).first()
        
        if not metadata:
            metadata = DocumentMetadata(document_id=document_id)
            self.session.add(metadata)
        
        return metadata
    
    async def _get_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """获取元数据记录"""
        return self.session.query(DocumentMetadata).filter_by(
            document_id=document_id
        ).first()


# 元数据查询辅助类
class MetadataQuery:
    """元数据查询辅助类"""
    
    @staticmethod
    def get_documents_by_confidence(session, project_id: str, min_stars: int = 4):
        """获取高置信度文档"""
        return session.query(DocumentMetadata).filter(
            DocumentMetadata.project_id == project_id,
            DocumentMetadata.confidence_stars >= min_stars
        ).order_by(DocumentMetadata.confidence_stars.desc())
    
    @staticmethod
    def get_recent_documents(session, project_id: str, months: int = 6):
        """获取最近发表的文档"""
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        return session.query(DocumentMetadata).filter(
            DocumentMetadata.project_id == project_id,
            DocumentMetadata.publication_date >= cutoff_date
        ).order_by(DocumentMetadata.publication_date.desc())
    
    @staticmethod
    def get_document_network(session, document_id: str, depth: int = 2):
        """获取文档引用网络"""
        # 递归查询引用关系，构建知识图谱
        # 这里需要使用图数据库或递归CTE
        pass