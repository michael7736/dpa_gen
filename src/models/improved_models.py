"""
改进版数据模型
添加了性能优化字段和更好的索引支持
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, JSON, Index, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseEntity


class ImprovedDocumentMixin:
    """文档模型改进混入类"""
    # 性能优化字段
    chunk_count = Column(Integer, default=0, comment="文档块数量", index=True)
    total_tokens = Column(Integer, default=0, comment="总token数")
    processing_time_seconds = Column(Float, comment="处理耗时（秒）")
    
    # 缓存字段
    cached_summary = Column(Text, comment="缓存的摘要")
    cached_keywords = Column(JSON, default=list, comment="缓存的关键词")
    cache_updated_at = Column(DateTime(timezone=True), comment="缓存更新时间")
    
    # 版本控制
    version = Column(Integer, default=1, comment="文档版本")
    is_latest = Column(Boolean, default=True, comment="是否最新版本")


class ImprovedProjectMixin:
    """项目模型改进混入类"""
    # 统计字段
    document_count = Column(Integer, default=0, comment="文档数量", index=True)
    total_chunks = Column(Integer, default=0, comment="总块数")
    total_tokens = Column(BigInteger, default=0, comment="总token数")
    last_accessed_at = Column(DateTime(timezone=True), comment="最后访问时间")
    
    # 配额管理
    storage_used_bytes = Column(BigInteger, default=0, comment="已用存储空间")
    api_calls_count = Column(Integer, default=0, comment="API调用次数")
    
    # 性能优化
    is_archived = Column(Boolean, default=False, index=True, comment="是否已归档")
    cache_enabled = Column(Boolean, default=True, comment="是否启用缓存")


class ImprovedUserMixin:
    """用户模型改进混入类"""
    # 使用统计
    project_count = Column(Integer, default=0, comment="项目数量")
    total_documents = Column(Integer, default=0, comment="文档总数")
    last_login_at = Column(DateTime(timezone=True), comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    
    # 配额管理
    storage_quota_bytes = Column(BigInteger, default=10737418240, comment="存储配额(10GB)")
    api_quota_monthly = Column(Integer, default=10000, comment="月度API配额")
    api_calls_this_month = Column(Integer, default=0, comment="本月API调用数")
    
    # 用户行为
    preferred_language = Column(String(10), default="zh", comment="首选语言")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区")
    
    # 功能开关（用户级）
    feature_flags = Column(JSON, default=dict, comment="用户级功能开关")


class ImprovedChunkMixin:
    """文档块模型改进混入类"""
    # 检索优化
    content_hash = Column(String(64), index=True, comment="内容哈希")
    quality_score = Column(Float, default=0.0, index=True, comment="质量评分")
    relevance_score = Column(Float, default=0.0, comment="相关性评分")
    
    # 使用统计
    access_count = Column(Integer, default=0, comment="访问次数")
    last_accessed_at = Column(DateTime(timezone=True), comment="最后访问时间")
    
    # 缓存优化
    is_cached = Column(Boolean, default=False, index=True, comment="是否已缓存")
    cache_priority = Column(Integer, default=0, comment="缓存优先级")


class ImprovedConversationMixin:
    """对话模型改进混入类"""
    # 统计信息
    message_count = Column(Integer, default=0, comment="消息数量")
    total_tokens_used = Column(Integer, default=0, comment="使用的token总数")
    
    # 性能优化
    is_pinned = Column(Boolean, default=False, index=True, comment="是否置顶")
    last_message_at = Column(DateTime(timezone=True), comment="最后消息时间")
    
    # AI反馈
    satisfaction_score = Column(Float, comment="满意度评分")
    feedback_count = Column(Integer, default=0, comment="反馈次数")


# 创建复合索引的辅助函数
def create_improved_indexes(metadata):
    """创建改进的复合索引"""
    
    # 文档表复合索引
    Index('idx_documents_project_status_type', 
          'documents.project_id', 'documents.processing_status', 'documents.document_type')
    
    Index('idx_documents_project_created', 
          'documents.project_id', 'documents.created_at')
    
    # 项目表复合索引
    Index('idx_projects_owner_archived_accessed',
          'projects.owner_id', 'projects.is_archived', 'projects.last_accessed_at')
    
    # 块表复合索引
    Index('idx_chunks_document_quality_cached',
          'chunks.document_id', 'chunks.quality_score', 'chunks.is_cached')
    
    # 对话表复合索引
    Index('idx_conversations_user_project_pinned',
          'conversations.user_id', 'conversations.project_id', 'conversations.is_pinned')


# 查询优化辅助类
class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def get_active_projects_query(session, user_id: int):
        """获取活跃项目的优化查询"""
        from .project import Project
        
        return session.query(Project).filter(
            Project.owner_id == user_id,
            Project.is_archived == False,
            Project.status == 'active'
        ).order_by(
            Project.last_accessed_at.desc()
        ).options(
            # 预加载常用关系
            selectinload(Project.documents),
            # 只加载需要的列
            load_only(Project.id, Project.name, Project.document_count, Project.last_accessed_at)
        )
    
    @staticmethod
    def get_recent_documents_query(session, project_id: int, limit: int = 10):
        """获取最近文档的优化查询"""
        from .document import Document
        
        return session.query(Document).filter(
            Document.project_id == project_id,
            Document.processing_status == 'completed'
        ).order_by(
            Document.created_at.desc()
        ).limit(limit).options(
            # 延迟加载大字段
            defer(Document.content),
            # 预加载统计信息
            undefer(Document.chunk_count),
            undefer(Document.total_tokens)
        )
    
    @staticmethod
    def search_chunks_optimized(session, project_id: int, query_embedding: List[float], limit: int = 10):
        """优化的向量搜索查询"""
        from .chunk import Chunk
        from sqlalchemy import text
        
        # 使用原生SQL进行向量搜索（PostgreSQL pgvector）
        sql = text("""
            SELECT c.*, 
                   1 - (c.embedding_vector <=> :query_embedding) as similarity
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.project_id = :project_id
              AND c.is_cached = true
              AND c.quality_score > 0.7
            ORDER BY c.embedding_vector <=> :query_embedding
            LIMIT :limit
        """)
        
        return session.execute(sql, {
            'project_id': project_id,
            'query_embedding': query_embedding,
            'limit': limit
        })


# 性能监控装饰器
def track_query_performance(query_name: str):
    """跟踪查询性能的装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                # 记录慢查询
                if duration > 1.0:
                    logger.warning(f"Slow query detected: {query_name} took {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Query failed: {query_name} after {duration:.2f}s - {str(e)}")
                raise
        
        return wrapper
    return decorator


# 缓存策略
class CacheStrategy:
    """缓存策略配置"""
    
    # 文档摘要缓存（1天）
    DOCUMENT_SUMMARY_TTL = 86400
    
    # 搜索结果缓存（1小时）
    SEARCH_RESULTS_TTL = 3600
    
    # 统计信息缓存（10分钟）
    STATISTICS_TTL = 600
    
    # 用户会话缓存（30分钟）
    SESSION_TTL = 1800
    
    @staticmethod
    def get_cache_key(prefix: str, *args) -> str:
        """生成缓存键"""
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)
    
    @staticmethod
    def should_cache(item_type: str, item: Any) -> bool:
        """判断是否应该缓存"""
        if item_type == "document":
            # 只缓存已完成处理的文档
            return item.processing_status == "completed"
        elif item_type == "chunk":
            # 只缓存高质量的块
            return item.quality_score > 0.8
        elif item_type == "search_result":
            # 只缓存有结果的搜索
            return len(item) > 0
        return True