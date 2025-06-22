"""
基础数据模型定义
包含所有实体的基类和通用字段
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_mixin
from pydantic import BaseModel, Field, ConfigDict

# SQLAlchemy基类
Base = declarative_base()


@declarative_mixin
class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


@declarative_mixin
class UUIDMixin:
    """UUID主键混入类"""
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)


@declarative_mixin
class SoftDeleteMixin:
    """软删除混入类"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class BaseEntity(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """基础实体类"""
    __abstract__ = True
    
    # 实体元数据
    metadata_info = Column(JSON, default=dict, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# Pydantic基础模型
class BaseSchema(BaseModel):
    """Pydantic基础模型"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )


class TimestampSchema(BaseSchema):
    """时间戳模式"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UUIDSchema(BaseSchema):
    """UUID模式"""
    id: Optional[UUID] = Field(default_factory=uuid4)


class BaseEntitySchema(UUIDSchema, TimestampSchema):
    """基础实体模式"""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    metadata_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


# 响应模式
class ResponseSchema(BaseSchema):
    """通用响应模式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    error: Optional[str] = None


class PaginationSchema(BaseSchema):
    """分页模式"""
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)
    total: Optional[int] = None
    total_pages: Optional[int] = None


class PaginatedResponseSchema(ResponseSchema):
    """分页响应模式"""
    pagination: Optional[PaginationSchema] = None 