"""
Memory Bank API路由
提供Memory Bank的HTTP接口
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from src.core.memory.memory_bank_manager import create_memory_bank_manager, Concept
from src.api.middleware.auth import get_current_user
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/memory-bank", tags=["memory-bank"])


class InitProjectRequest(BaseModel):
    """初始化项目请求"""
    project_id: str = Field(..., description="项目ID")


class UpdateContextRequest(BaseModel):
    """更新上下文请求"""
    project_id: str = Field(..., description="项目ID")
    content: str = Field(..., description="新的上下文内容")
    source: Optional[str] = Field(None, description="内容来源")


class AddConceptsRequest(BaseModel):
    """添加概念请求"""
    project_id: str = Field(..., description="项目ID")
    concepts: List[Dict[str, Any]] = Field(..., description="概念列表")


class SearchConceptsRequest(BaseModel):
    """搜索概念请求"""
    project_id: str = Field(..., description="项目ID")
    query: str = Field(..., description="搜索查询")
    category: Optional[str] = Field(None, description="概念类别")


class UpdateSummaryRequest(BaseModel):
    """更新摘要请求"""
    project_id: str = Field(..., description="项目ID")
    force_regenerate: bool = Field(False, description="强制重新生成")


@router.post("/init")
async def initialize_project(
    request: InitProjectRequest,
    current_user: str = Depends(get_current_user)
):
    """
    初始化项目Memory Bank
    
    创建项目的持久化记忆存储结构
    """
    try:
        manager = create_memory_bank_manager(user_id=current_user)
        success = await manager.initialize_project(request.project_id)
        
        if success:
            return {
                "success": True,
                "message": f"Project {request.project_id} initialized successfully",
                "project_id": request.project_id,
                "user_id": current_user
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize project"
            )
            
    except Exception as e:
        logger.error(f"Project initialization error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize project: {str(e)}"
        )


@router.post("/context/update")
async def update_context(
    request: UpdateContextRequest,
    current_user: str = Depends(get_current_user)
):
    """
    更新项目上下文
    
    添加新内容到项目上下文，自动管理大小限制
    """
    try:
        manager = create_memory_bank_manager(user_id=current_user)
        success = await manager.update_context(
            project_id=request.project_id,
            new_content=request.content,
            source=request.source
        )
        
        if success:
            return {
                "success": True,
                "message": "Context updated successfully",
                "content_length": len(request.content)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update context"
            )
            
    except Exception as e:
        logger.error(f"Context update error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update context: {str(e)}"
        )


@router.post("/concepts/add")
async def add_concepts(
    request: AddConceptsRequest,
    current_user: str = Depends(get_current_user)
):
    """
    添加概念
    
    添加新概念或更新现有概念的频率
    """
    try:
        manager = create_memory_bank_manager(user_id=current_user)
        added_count = await manager.add_concepts(
            project_id=request.project_id,
            new_concepts=request.concepts
        )
        
        return {
            "success": True,
            "added_count": added_count,
            "total_concepts": len(request.concepts)
        }
        
    except Exception as e:
        logger.error(f"Add concepts error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add concepts: {str(e)}"
        )


@router.post("/concepts/search")
async def search_concepts(
    request: SearchConceptsRequest,
    current_user: str = Depends(get_current_user)
):
    """
    搜索概念
    
    根据名称或描述搜索概念
    """
    try:
        manager = create_memory_bank_manager(user_id=current_user)
        results = await manager.search_concepts(
            project_id=request.project_id,
            query=request.query,
            category=request.category
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search concepts error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search concepts: {str(e)}"
        )


@router.post("/summary/update")
async def update_summary(
    request: UpdateSummaryRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    更新项目摘要
    
    基于当前上下文和概念智能生成摘要
    """
    try:
        manager = create_memory_bank_manager(user_id=current_user)
        
        # 异步更新摘要
        async def update_task():
            await manager.update_summary(
                project_id=request.project_id,
                force_regenerate=request.force_regenerate
            )
            
        background_tasks.add_task(update_task)
        
        return {
            "success": True,
            "message": "Summary update initiated",
            "project_id": request.project_id
        }
        
    except Exception as e:
        logger.error(f"Update summary error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update summary: {str(e)}"
        )


@router.get("/snapshot/{project_id}")
async def get_snapshot(
    project_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    获取项目快照
    
    获取项目的完整记忆状态
    """
    try:
        manager = create_memory_bank_manager(user_id=current_user)
        snapshot = await manager.get_snapshot(project_id)
        
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
            
        return {
            "success": True,
            "snapshot": snapshot
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get snapshot error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get snapshot: {str(e)}"
        )


@router.get("/export/{project_id}")
async def export_memory(
    project_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    导出项目记忆
    
    导出项目的完整记忆数据
    """
    try:
        manager = create_memory_bank_manager(user_id=current_user)
        export_data = await manager.export_memory(project_id)
        
        if not export_data:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
            
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export memory error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export memory: {str(e)}"
        )


@router.get("/projects")
async def list_projects(
    current_user: str = Depends(get_current_user)
):
    """
    列出用户的所有项目
    
    扫描Memory Bank获取项目列表
    """
    try:
        from pathlib import Path
        from src.config.settings import settings
        
        base_path = Path(settings.paths.memory_bank)
        
        # 根据用户ID确定路径
        if current_user == "u1":
            search_path = base_path
        else:
            search_path = base_path / current_user
            
        if not search_path.exists():
            return {
                "success": True,
                "projects": [],
                "count": 0
            }
            
        # 查找所有项目目录
        projects = []
        for project_dir in search_path.glob("project_*"):
            if project_dir.is_dir():
                project_id = project_dir.name.replace("project_", "")
                
                # 尝试读取元数据
                metadata_file = project_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        import json
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            
                        projects.append({
                            "project_id": project_id,
                            "created_at": metadata.get("created_at"),
                            "updated_at": metadata.get("updated_at"),
                            "stats": metadata.get("stats", {})
                        })
                    except:
                        projects.append({
                            "project_id": project_id,
                            "error": "Failed to read metadata"
                        })
                        
        # 按更新时间排序
        projects.sort(
            key=lambda p: p.get("updated_at", ""), 
            reverse=True
        )
        
        return {
            "success": True,
            "projects": projects,
            "count": len(projects),
            "user_id": current_user
        }
        
    except Exception as e:
        logger.error(f"List projects error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    删除项目Memory Bank
    
    永久删除项目的所有记忆数据
    """
    try:
        from pathlib import Path
        from src.config.settings import settings
        import shutil
        
        manager = create_memory_bank_manager(user_id=current_user)
        project_path = manager._get_project_path(project_id)
        
        if not project_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
            
        # 备份到临时目录（可选）
        backup_path = Path(settings.paths.memory_bank) / "deleted" / f"{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path.parent.mkdir(exist_ok=True)
        shutil.move(str(project_path), str(backup_path))
        
        return {
            "success": True,
            "message": f"Project {project_id} deleted successfully",
            "backup_path": str(backup_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete project error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete project: {str(e)}"
        )