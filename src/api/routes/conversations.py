"""
对话管理API路由
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session as get_db
from ...models.conversation import MessageRole, MessageType
from ...services.conversation_service import ConversationService
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


# Pydantic模型
class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    title: str = Field(..., min_length=1, max_length=200, description="对话标题")
    project_id: Optional[str] = Field(None, description="关联的项目ID")
    settings: Optional[Dict] = Field(None, description="对话设置")


class ConversationResponse(BaseModel):
    """对话响应"""
    id: str
    title: str
    user_id: str
    project_id: Optional[str]
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    settings: Optional[Dict] = None


class AddMessageRequest(BaseModel):
    """添加消息请求"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, description="消息内容")
    message_type: MessageType = Field(MessageType.TEXT, description="消息类型")
    sources: Optional[List[Dict]] = Field(None, description="来源信息")
    citations: Optional[List[Dict]] = Field(None, description="引用信息")
    metadata: Optional[Dict] = Field(None, description="元数据")


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    conversation_id: str
    role: MessageRole
    message_type: MessageType
    content: str
    sequence_number: int
    created_at: datetime
    processing_time: Optional[float] = None
    token_count: Optional[int] = None
    sources: Optional[List[Dict]] = None
    citations: Optional[List[Dict]] = None


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    per_page: int


class ConversationContextResponse(BaseModel):
    """对话上下文响应"""
    conversation_id: str
    messages: List[Dict]
    total_messages: int


class ConversationSummaryResponse(BaseModel):
    """对话摘要响应"""
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    total_tokens: int
    user_messages: int
    assistant_messages: int
    avg_processing_time: float
    recent_messages: List[Dict]


class UpdateConversationRequest(BaseModel):
    """更新对话请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    settings: Optional[Dict] = None


class ExportConversationResponse(BaseModel):
    """导出对话响应"""
    format: str
    data: Optional[Dict] = None
    content: Optional[str] = None
    filename: Optional[str] = None


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """创建新对话"""
    try:
        service = ConversationService(db)
        conversation = await service.create_conversation(
            user_id=user_id,
            title=request.title,
            project_id=request.project_id,
            settings=request.settings
        )
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            user_id=str(conversation.user_id),
            project_id=str(conversation.project_id) if conversation.project_id else None,
            message_count=conversation.message_count,
            total_tokens=conversation.total_tokens,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            settings=request.settings
        )
        
    except Exception as e:
        logger.error(f"创建对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    user_id: str = Query(..., description="用户ID"),
    project_id: Optional[str] = Query(None, description="项目ID"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取用户的对话列表"""
    try:
        service = ConversationService(db)
        offset = (page - 1) * per_page
        
        conversations, total = await service.get_user_conversations(
            user_id=user_id,
            project_id=project_id,
            limit=per_page,
            offset=offset
        )
        
        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    id=str(conv.id),
                    title=conv.title,
                    user_id=str(conv.user_id),
                    project_id=str(conv.project_id) if conv.project_id else None,
                    message_count=conv.message_count,
                    total_tokens=conv.total_tokens,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at
                )
                for conv in conversations
            ],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """获取对话详情"""
    try:
        service = ConversationService(db)
        conversation = await service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 验证用户权限
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            user_id=str(conversation.user_id),
            project_id=str(conversation.project_id) if conversation.project_id else None,
            message_count=conversation.message_count,
            total_tokens=conversation.total_tokens,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    user_id: str = Query(..., description="用户ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """添加消息到对话"""
    try:
        service = ConversationService(db)
        
        # 验证对话存在且用户有权限
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 添加消息
        message = await service.add_message(
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            message_type=request.message_type,
            sources=request.sources,
            citations=request.citations,
            metadata=request.metadata
        )
        
        # 如果需要，可以在后台处理一些任务
        # background_tasks.add_task(process_message, message.id)
        
        return MessageResponse(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            role=message.role,
            message_type=message.message_type,
            content=message.content,
            sequence_number=message.sequence_number,
            created_at=message.created_at,
            processing_time=message.processing_time,
            token_count=message.token_count,
            sources=request.sources,
            citations=request.citations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    user_id: str = Query(..., description="用户ID"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="限制数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    include_system: bool = Query(True, description="是否包含系统消息"),
    db: Session = Depends(get_db)
):
    """获取对话消息列表"""
    try:
        service = ConversationService(db)
        
        # 验证权限
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 获取消息
        messages = await service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
            include_system=include_system
        )
        
        return [
            MessageResponse(
                id=str(msg.id),
                conversation_id=str(msg.conversation_id),
                role=msg.role,
                message_type=msg.message_type,
                content=msg.content,
                sequence_number=msg.sequence_number,
                created_at=msg.created_at,
                processing_time=msg.processing_time,
                token_count=msg.token_count,
                sources=json.loads(msg.sources) if msg.sources else None,
                citations=json.loads(msg.citations) if msg.citations else None
            )
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取消息列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/context", response_model=ConversationContextResponse)
async def get_conversation_context(
    conversation_id: str,
    user_id: str = Query(..., description="用户ID"),
    max_messages: int = Query(10, ge=1, le=50, description="最大消息数"),
    db: Session = Depends(get_db)
):
    """获取对话上下文（用于AI回复）"""
    try:
        service = ConversationService(db)
        
        # 验证权限
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 获取上下文
        context = await service.get_conversation_context(
            conversation_id=conversation_id,
            max_messages=max_messages
        )
        
        return ConversationContextResponse(
            conversation_id=conversation_id,
            messages=context,
            total_messages=conversation.message_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话上下文失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/summary", response_model=ConversationSummaryResponse)
async def get_conversation_summary(
    conversation_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """获取对话摘要"""
    try:
        service = ConversationService(db)
        
        # 验证权限
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 获取摘要
        summary = await service.get_conversation_summary(conversation_id)
        
        return ConversationSummaryResponse(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """更新对话信息"""
    try:
        service = ConversationService(db)
        
        # 验证权限
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权修改此对话")
        
        # 更新对话
        updated_conversation = await service.update_conversation(
            conversation_id=conversation_id,
            title=request.title,
            settings=request.settings
        )
        
        return ConversationResponse(
            id=str(updated_conversation.id),
            title=updated_conversation.title,
            user_id=str(updated_conversation.user_id),
            project_id=str(updated_conversation.project_id) if updated_conversation.project_id else None,
            message_count=updated_conversation.message_count,
            total_tokens=updated_conversation.total_tokens,
            created_at=updated_conversation.created_at,
            updated_at=updated_conversation.updated_at,
            settings=request.settings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """删除对话"""
    try:
        service = ConversationService(db)
        
        # 验证权限
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权删除此对话")
        
        # 删除对话
        success = await service.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="删除失败")
        
        return {"message": "对话已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[ConversationResponse])
async def search_conversations(
    q: str = Query(..., min_length=1, description="搜索查询"),
    user_id: str = Query(..., description="用户ID"),
    project_id: Optional[str] = Query(None, description="项目ID"),
    limit: int = Query(10, ge=1, le=50, description="限制数量"),
    db: Session = Depends(get_db)
):
    """搜索对话"""
    try:
        service = ConversationService(db)
        
        conversations = await service.search_conversations(
            user_id=user_id,
            query=q,
            project_id=project_id,
            limit=limit
        )
        
        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                user_id=str(conv.user_id),
                project_id=str(conv.project_id) if conv.project_id else None,
                message_count=conv.message_count,
                total_tokens=conv.total_tokens,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"搜索对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/export", response_model=ExportConversationResponse)
async def export_conversation(
    conversation_id: str,
    format: str = Query("json", regex="^(json|markdown)$", description="导出格式"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """导出对话"""
    try:
        service = ConversationService(db)
        
        # 验证权限
        conversation = await service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权导出此对话")
        
        # 导出对话
        export_data = await service.export_conversation(
            conversation_id=conversation_id,
            format=format
        )
        
        if format == "json":
            return ExportConversationResponse(
                format=format,
                data=export_data
            )
        else:  # markdown
            return ExportConversationResponse(
                format=format,
                content=export_data["content"],
                filename=export_data["filename"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))