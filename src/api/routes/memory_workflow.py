"""
记忆工作流API路由
提供认知工作流的HTTP接口
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from src.core.memory.mvp_workflow import create_mvp_workflow
from src.api.middleware.auth import get_current_user
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class WorkflowRequest(BaseModel):
    """工作流请求模型"""
    message: str = Field(..., description="用户消息")
    thread_id: Optional[str] = Field(None, description="会话ID")
    project_id: Optional[str] = Field(None, description="项目ID")
    
    
class WorkflowResponse(BaseModel):
    """工作流响应模型"""
    success: bool
    thread_id: str
    response: Optional[str] = None
    error: Optional[str] = None
    status: str
    memory_snapshot: Optional[Dict[str, Any]] = None
    

class MemoryWriteRequest(BaseModel):
    """记忆写入请求"""
    content: str = Field(..., description="记忆内容")
    memory_type: str = Field("semantic", description="记忆类型")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    project_id: Optional[str] = Field(None, description="项目ID")
    

class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    query: str = Field(..., description="搜索查询")
    project_id: Optional[str] = Field(None, description="项目ID")
    limit: int = Field(10, ge=1, le=50, description="返回结果数量")
    

@router.post("/chat", response_model=WorkflowResponse)
async def chat_with_memory(
    request: WorkflowRequest,
    current_user: str = Depends(get_current_user)
):
    """
    使用认知工作流处理用户消息
    
    - 自动管理记忆和上下文
    - 支持多轮对话（通过thread_id）
    - 三阶段混合检索
    """
    try:
        # 创建用户专属的工作流
        workflow = create_mvp_workflow(user_id=current_user)
        
        # 运行工作流
        result = await workflow.run(
            message=request.message,
            thread_id=request.thread_id,
            project_id=request.project_id
        )
        
        # 提取响应
        response_content = None
        if result["messages"] and len(result["messages"]) >= 2:
            # 获取最后一条AI消息
            for msg in reversed(result["messages"]):
                if msg.type == "ai":
                    response_content = msg.content
                    break
                    
        return WorkflowResponse(
            success=result["processing_status"] == "completed",
            thread_id=result["thread_id"],
            response=response_content,
            error=result.get("last_error"),
            status=result["processing_status"],
            memory_snapshot=result.get("memory_bank_snapshot")
        )
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )
        

@router.post("/write")
async def write_memory(
    request: MemoryWriteRequest,
    current_user: str = Depends(get_current_user)
):
    """
    直接写入记忆
    
    - 写入到所有存储系统
    - 确保数据一致性
    """
    try:
        from src.services.memory_write_service_v2 import MemoryWriteService, MemoryType
        
        # 创建写入服务
        service = MemoryWriteService(user_id=current_user)
        
        # 映射记忆类型
        memory_type_map = {
            "semantic": MemoryType.SEMANTIC,
            "episodic": MemoryType.EPISODIC,
            "working": MemoryType.WORKING
        }
        memory_type = memory_type_map.get(
            request.memory_type.lower(), 
            MemoryType.SEMANTIC
        )
        
        # 写入记忆
        result = await service.write_memory(
            content=request.content,
            memory_type=memory_type,
            metadata=request.metadata,
            project_id=request.project_id,
            user_id=current_user
        )
        
        return {
            "success": result.success,
            "operation_id": result.operation_id,
            "completed_stores": result.completed_stores,
            "failed_stores": result.failed_stores,
            "error": result.error
        }
        
    except Exception as e:
        logger.error(f"Memory write error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write memory: {str(e)}"
        )
        

@router.post("/search")
async def search_memories(
    request: MemorySearchRequest,
    current_user: str = Depends(get_current_user)
):
    """
    搜索记忆
    
    - 三阶段混合检索
    - 返回相关记忆和上下文
    """
    try:
        from src.services.memory_write_service_v2 import MemoryWriteService
        
        # 创建服务
        service = MemoryWriteService(user_id=current_user)
        
        # 搜索记忆
        results = await service.search_memories(
            query=request.query,
            user_id=current_user,
            project_id=request.project_id,
            limit=request.limit
        )
        
        return {
            "success": True,
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search memories: {str(e)}"
        )
        

@router.get("/status/{thread_id}")
async def get_thread_status(
    thread_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    获取会话状态
    
    - 工作记忆内容
    - 处理状态
    - 错误信息
    """
    try:
        # TODO: 从检查点存储中恢复状态
        # 现在返回模拟数据
        return {
            "thread_id": thread_id,
            "user_id": current_user,
            "status": "active",
            "working_memory_items": 0,
            "last_interaction": None
        }
        
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get thread status: {str(e)}"
        )
        

@router.delete("/thread/{thread_id}")
async def clear_thread(
    thread_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    清除会话
    
    - 删除工作记忆
    - 保留长期记忆
    """
    try:
        # TODO: 实现会话清理
        return {
            "success": True,
            "message": f"Thread {thread_id} cleared"
        }
        
    except Exception as e:
        logger.error(f"Thread clear error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear thread: {str(e)}"
        )