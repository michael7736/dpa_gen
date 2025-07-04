"""
文档块数据模型
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from .base import BaseEntity


class Chunk(BaseEntity):
    """文档块模型"""
    __tablename__ = "chunks"
    
    # 关联文档
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # 块信息
    chunk_index = Column(Integer, nullable=False, index=True)  # 在文档中的序号
    content = Column(Text, nullable=False)  # 块内容
    content_hash = Column(String(64), nullable=False, index=True)  # 内容哈希
    
    # 位置信息
    start_page = Column(Integer, nullable=True)  # 起始页码
    end_page = Column(Integer, nullable=True)  # 结束页码
    start_char = Column(Integer, nullable=True)  # 起始字符位置
    end_char = Column(Integer, nullable=True)  # 结束字符位置
    
    # 向量信息
    vector_id = Column(String(100), nullable=True, index=True)  # Qdrant中的向量ID
    embedding_model = Column(String(100), nullable=True)  # 使用的嵌入模型
    
    # 块特征
    token_count = Column(Integer, nullable=True)  # token数量
    char_count = Column(Integer, nullable=False)  # 字符数量
    
    # 语义信息
    keywords = Column(Text, nullable=True)  # JSON格式的关键词
    entities = Column(Text, nullable=True)  # JSON格式的实体信息
    
    # 质量评分
    quality_score = Column(Float, nullable=True)  # 块质量评分
    relevance_score = Column(Float, nullable=True)  # 相关性评分
    
    # 标记
    is_title = Column(Boolean, default=False, nullable=False)  # 是否是标题
    is_table = Column(Boolean, default=False, nullable=False)  # 是否是表格
    is_list = Column(Boolean, default=False, nullable=False)  # 是否是列表
    
    # 关系
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index}, chars={self.char_count})>" 