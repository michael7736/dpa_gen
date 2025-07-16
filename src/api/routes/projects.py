"""
项目管理API路由
提供项目的CRUD操作和管理功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.postgresql import get_db_session
from ...models.project import Project
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/projects")


class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type: Optional[str] = None  # 项目类型
    metadata: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: Optional[str]
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    user_id: str
    document_count: int = 0
    
    class Config:
        from_attributes = True


class PaginatedProjectResponse(BaseModel):
    """分页项目响应"""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db_session)
):
    """创建新项目"""
    try:
        # 检查项目名是否已存在
        existing = db.query(Project).filter(Project.name == project.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"项目名称 '{project.name}' 已存在"
            )
        
        # 创建项目
        # TODO: 实现用户认证后，从请求中获取用户ID
        # 暂时使用默认用户
        from ...models.user import User
        default_user = db.query(User).filter(User.email == "default@dpa.ai").first()
        if not default_user:
            raise HTTPException(status_code=500, detail="默认用户不存在")
        
        # 处理项目类型
        from ...models.project import ProjectType
        project_type = None
        if project.type:
            try:
                # 根据名称或值匹配枚举
                if project.type.upper() in [e.name for e in ProjectType]:
                    # 通过名称匹配（大写）
                    project_type = ProjectType[project.type.upper()]
                else:
                    # 通过值匹配（小写）
                    project_type = ProjectType(project.type.lower())
                logger.info(f"项目类型: {project.type} -> {project_type.name}")
            except (ValueError, KeyError):
                # 如果无效的类型，使用默认值
                project_type = ProjectType.RESEARCH
                logger.warning(f"无效的项目类型: {project.type}, 使用默认值: {project_type.name}")
        
        db_project = Project(
            name=project.name,
            description=project.description,
            type=project_type or ProjectType.RESEARCH,
            metadata=project.metadata or {},
            user_id=default_user.id
        )
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        logger.info(f"创建项目成功: {db_project.id} - {db_project.name}")
        
        return ProjectResponse(
            id=str(db_project.id),
            name=db_project.name,
            description=db_project.description,
            status=db_project.status.value if hasattr(db_project.status, 'value') else db_project.status,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at,
            user_id=str(db_project.user_id),
            document_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建项目失败: {e}")
        raise HTTPException(status_code=500, detail="创建项目失败")


@router.get("", response_model=PaginatedProjectResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """获取项目列表"""
    try:
        query = db.query(Project)
        
        # 过滤条件
        if is_active is not None:
            # TODO: 根据 status 字段过滤
            pass
        
        if search:
            query = query.filter(
                Project.name.ilike(f"%{search}%") |
                Project.description.ilike(f"%{search}%")
            )
        
        # 获取总数
        total = query.count()
        
        # 计算分页
        skip = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        # 排序和分页
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(page_size).all()
        
        # 转换响应
        result = []
        for project in projects:
            # 获取文档数量
            from ...models.document import Document
            doc_count = db.query(Document).filter(
                Document.project_id == project.id,
                Document.is_deleted == False
            ).count()
            
            result.append(ProjectResponse(
                id=str(project.id),
                name=project.name,
                description=project.description,
                status=project.status.value if hasattr(project.status, 'value') else project.status,
                created_at=project.created_at,
                updated_at=project.updated_at,
                user_id=str(project.user_id),
                document_count=doc_count
            ))
        
        return PaginatedProjectResponse(
            items=result,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取项目列表失败")


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """获取项目详情"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取文档数量
        from ...models.document import Document
        doc_count = db.query(Document).filter(
            Document.project_id == project.id,
            Document.is_deleted == False
        ).count()
        
        return ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            status=project.status.value if hasattr(project.status, 'value') else project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            user_id=str(project.user_id),
            document_count=doc_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取项目详情失败")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db_session)
):
    """更新项目"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 更新字段
        update_data = project_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(project)
        
        logger.info(f"更新项目成功: {project.id}")
        
        # 获取文档数量
        from ...models.document import Document
        doc_count = db.query(Document).filter(
            Document.project_id == project.id,
            Document.is_deleted == False
        ).count()
        
        return ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            status=project.status.value if hasattr(project.status, 'value') else project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            user_id=str(project.user_id),
            document_count=doc_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新项目失败: {e}")
        raise HTTPException(status_code=500, detail="更新项目失败")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    force: bool = Query(False, description="强制删除，包括所有相关数据"),
    db: Session = Depends(get_db_session)
):
    """删除项目"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 检查是否有关联文档
        from ...models.document import Document
        doc_count = db.query(Document).filter(
            Document.project_id == project.id,
            Document.is_deleted == False
        ).count()
        
        if doc_count > 0 and not force:
            raise HTTPException(
                status_code=400,
                detail=f"项目包含 {doc_count} 个文档，请先删除文档或使用强制删除"
            )
        
        if force:
            # 软删除所有文档
            db.query(Document).filter(
                Document.project_id == project.id
            ).update({"is_deleted": True})
        
        # 软删除项目
        project.is_active = False
        project.metadata = project.metadata or {}
        project.metadata["deleted_at"] = datetime.utcnow().isoformat()
        
        db.commit()
        
        logger.info(f"删除项目成功: {project.id}")
        
        return {"message": "项目删除成功", "project_id": project_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除项目失败: {e}")
        raise HTTPException(status_code=500, detail="删除项目失败")


@router.get("/{project_id}/statistics")
async def get_project_statistics(
    project_id: str,
    db: Session = Depends(get_db_session)
):
    """获取项目统计信息"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取统计数据
        from ...models.document import Document
        from ...models.chunk import Chunk
        from ...models.memory import Memory, ProjectMemory
        from sqlalchemy import func
        
        # 文档统计
        doc_stats = db.query(
            func.count(Document.id).label("total"),
            func.sum(func.cast(Document.status == "completed", int)).label("completed"),
            func.sum(func.cast(Document.status == "processing", int)).label("processing"),
            func.sum(func.cast(Document.status == "failed", int)).label("failed")
        ).filter(
            Document.project_id == project.id,
            Document.is_deleted == False
        ).first()
        
        # 分块统计
        chunk_count = db.query(func.count(Chunk.id)).join(Document).filter(
            Document.project_id == project.id,
            Document.is_deleted == False
        ).scalar() or 0
        
        # 记忆统计
        memory_count = db.query(func.count(Memory.id)).filter(
            Memory.project_id == project.id
        ).scalar() or 0
        
        # 项目记忆
        project_memory = db.query(ProjectMemory).filter(
            ProjectMemory.project_id == project.id
        ).first()
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "documents": {
                "total": doc_stats.total or 0,
                "completed": doc_stats.completed or 0,
                "processing": doc_stats.processing or 0,
                "failed": doc_stats.failed or 0
            },
            "chunks": {
                "total": chunk_count
            },
            "memories": {
                "total": memory_count,
                "has_project_memory": project_memory is not None
            },
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "is_active": project.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取项目统计失败")