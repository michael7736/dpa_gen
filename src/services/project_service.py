"""
项目管理服务
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.project import (
    Project, Task, TaskSnapshot, ProjectMemory, Deliverable,
    ProjectType, ProjectStatus, TaskType, TaskStatus
)
from ..models.user import User
from ..utils.logger import get_logger
from sqlalchemy import or_
from datetime import timedelta

logger = get_logger(__name__)


class ProjectService:
    """项目管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_or_create_default_project(self, user_id: UUID) -> Project:
        """获取或创建用户的默认项目"""
        try:
            # 查找用户的默认项目
            default_project = self.db.query(Project).filter(
                and_(
                    Project.user_id == user_id,
                    Project.is_default == True
                )
            ).first()
            
            if default_project:
                return default_project
            
            # 获取用户信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"用户不存在: {user_id}")
            
            # 创建默认项目
            default_project = Project(
                name=f"{user.username}的默认项目",
                description="系统自动创建的默认项目，用于存储所有文档和对话",
                type=ProjectType.CUSTOM,
                status=ProjectStatus.DRAFT,
                is_default=True,
                user_id=user_id,
                config={
                    "auto_created": True,
                    "creation_time": datetime.utcnow().isoformat()
                },
                context={
                    "created_by": "system",
                    "creation_method": "auto_default"
                }
            )
            
            self.db.add(default_project)
            self.db.commit()
            self.db.refresh(default_project)
            
            logger.info(f"Created default project for user {user.username}: {default_project.id}")
            
            return default_project
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating default project: {e}")
            raise
    
    async def create_project(
        self,
        name: str,
        description: Optional[str],
        project_type: ProjectType,
        user_id: UUID,
        config: Optional[Dict[str, Any]] = None,
        objectives: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None
    ) -> Project:
        """创建新项目"""
        try:
            # 检查项目名是否已存在
            existing = self.db.query(Project).filter(
                and_(
                    Project.name == name,
                    Project.user_id == user_id
                )
            ).first()
            
            if existing:
                raise ValueError(f"项目名称 '{name}' 已存在")
            
            # 创建项目
            project = Project(
                name=name,
                description=description,
                type=project_type,
                status=ProjectStatus.DRAFT,
                user_id=user_id,
                config=config or {},
                objectives=objectives or [],
                constraints=constraints or [],
                context={
                    "created_by": "user",
                    "creation_method": "manual"
                }
            )
            
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            
            logger.info(f"Created project: {project.id} - {project.name}")
            
            return project
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating project: {e}")
            raise
    
    async def get_project(self, project_id: UUID, user_id: UUID) -> Optional[Project]:
        """获取项目详情"""
        project = self.db.query(Project).filter(
            and_(
                Project.id == project_id,
                Project.user_id == user_id
            )
        ).first()
        
        return project
    
    async def list_projects(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ProjectStatus] = None,
        project_type: Optional[ProjectType] = None
    ) -> List[Project]:
        """获取项目列表"""
        query = self.db.query(Project).filter(Project.user_id == user_id)
        
        if status:
            query = query.filter(Project.status == status)
        
        if project_type:
            query = query.filter(Project.type == project_type)
        
        projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
        
        return projects
    
    async def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        **update_data
    ) -> Optional[Project]:
        """更新项目"""
        project = await self.get_project(project_id, user_id)
        
        if not project:
            return None
        
        try:
            # 更新字段
            for field, value in update_data.items():
                if hasattr(project, field) and value is not None:
                    setattr(project, field, value)
            
            project.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(project)
            
            logger.info(f"Updated project: {project_id}")
            
            return project
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating project: {e}")
            raise
    
    async def delete_project(self, project_id: UUID, user_id: UUID) -> bool:
        """删除项目"""
        project = await self.get_project(project_id, user_id)
        
        if not project:
            return False
        
        try:
            # 删除相关数据（由于设置了cascade，会自动删除）
            self.db.delete(project)
            self.db.commit()
            
            logger.info(f"Deleted project: {project_id}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting project: {e}")
            raise
    
    # 任务管理
    
    async def create_task(
        self,
        project_id: UUID,
        title: str,
        description: Optional[str],
        task_type: TaskType,
        priority: int = 0,
        parent_id: Optional[UUID] = None,
        dependencies: Optional[List[UUID]] = None,
        estimated_time: Optional[int] = None
    ) -> Task:
        """创建任务"""
        try:
            # 获取当前最大order
            max_order = self.db.query(Task).filter(
                Task.project_id == project_id
            ).count()
            
            task = Task(
                project_id=project_id,
                parent_id=parent_id,
                title=title,
                description=description,
                type=task_type,
                status=TaskStatus.PENDING,
                priority=priority,
                order=max_order,
                dependencies=dependencies or [],
                estimated_time=estimated_time,
                plan={}
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Created task: {task.id} - {task.title}")
            
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating task: {e}")
            raise
    
    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """获取任务详情"""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    async def list_tasks(self, project_id: UUID) -> List[Task]:
        """获取项目任务列表"""
        tasks = self.db.query(Task).filter(
            Task.project_id == project_id
        ).order_by(Task.order, Task.created_at).all()
        
        return tasks
    
    async def update_task(self, task_id: UUID, **update_data) -> Optional[Task]:
        """更新任务"""
        task = await self.get_task(task_id)
        
        if not task:
            return None
        
        try:
            # 更新字段
            for field, value in update_data.items():
                if hasattr(task, field) and value is not None:
                    setattr(task, field, value)
            
            # 如果状态变为开始，记录开始时间
            if update_data.get("status") == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = datetime.utcnow()
            
            # 如果状态变为完成，记录完成时间
            if update_data.get("status") == TaskStatus.COMPLETED and not task.completed_at:
                task.completed_at = datetime.utcnow()
                if task.started_at:
                    task.actual_time = int((task.completed_at - task.started_at).total_seconds() / 60)
            
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"Updated task: {task_id}")
            
            return task
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating task: {e}")
            raise
    
    async def create_task_snapshot(
        self,
        task_id: UUID,
        status: TaskStatus,
        progress: float,
        context: Dict[str, Any],
        decisions: List[Dict[str, Any]] = None,
        intermediate_results: Dict[str, Any] = None
    ) -> TaskSnapshot:
        """创建任务快照"""
        try:
            snapshot = TaskSnapshot(
                task_id=task_id,
                status=status,
                progress=progress,
                context=context,
                decisions=decisions or [],
                intermediate_results=intermediate_results or {}
            )
            
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            
            return snapshot
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating task snapshot: {e}")
            raise
    
    # 项目记忆管理
    
    async def save_project_memory(
        self,
        project_id: UUID,
        memory_type: str,
        content: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> ProjectMemory:
        """保存项目记忆"""
        try:
            # 检查是否已存在同类型记忆
            existing = self.db.query(ProjectMemory).filter(
                and_(
                    ProjectMemory.project_id == project_id,
                    ProjectMemory.memory_type == memory_type
                )
            ).first()
            
            if existing:
                # 更新现有记忆
                existing.content = content
                existing.updated_at = datetime.utcnow()
                if ttl:
                    existing.ttl = ttl
                    existing.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                
                self.db.commit()
                self.db.refresh(existing)
                return existing
            else:
                # 创建新记忆
                memory = ProjectMemory(
                    project_id=project_id,
                    memory_type=memory_type,
                    content=content,
                    ttl=ttl
                )
                
                if ttl:
                    memory.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                
                self.db.add(memory)
                self.db.commit()
                self.db.refresh(memory)
                return memory
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving project memory: {e}")
            raise
    
    async def get_project_memory(
        self,
        project_id: UUID,
        memory_type: Optional[str] = None
    ) -> List[ProjectMemory]:
        """获取项目记忆"""
        query = self.db.query(ProjectMemory).filter(
            ProjectMemory.project_id == project_id
        )
        
        if memory_type:
            query = query.filter(ProjectMemory.memory_type == memory_type)
        
        # 过滤已过期的记忆
        query = query.filter(
            or_(
                ProjectMemory.expires_at.is_(None),
                ProjectMemory.expires_at > datetime.utcnow()
            )
        )
        
        memories = query.all()
        return memories
    
    # 可交付成果管理
    
    async def create_deliverable(
        self,
        project_id: UUID,
        name: str,
        deliverable_type: str,
        content: Dict[str, Any],
        format: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Deliverable:
        """创建可交付成果"""
        try:
            deliverable = Deliverable(
                project_id=project_id,
                name=name,
                type=deliverable_type,
                format=format,
                content=content,
                file_path=file_path
            )
            
            self.db.add(deliverable)
            self.db.commit()
            self.db.refresh(deliverable)
            
            logger.info(f"Created deliverable: {deliverable.id} - {deliverable.name}")
            
            return deliverable
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating deliverable: {e}")
            raise
    
    async def list_deliverables(self, project_id: UUID) -> List[Deliverable]:
        """获取项目可交付成果列表"""
        deliverables = self.db.query(Deliverable).filter(
            Deliverable.project_id == project_id
        ).order_by(Deliverable.created_at.desc()).all()
        
        return deliverables