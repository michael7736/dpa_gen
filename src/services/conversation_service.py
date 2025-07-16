"""
对话历史持久化服务
提供对话的创建、存储、检索和管理功能
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database.postgresql import get_db_session
from ..models.conversation import Conversation, Message, MessageRole, MessageType
from ..services.cache_service import CacheService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConversationService:
    """对话服务类"""
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        初始化对话服务
        
        Args:
            db_session: 数据库会话（可选）
        """
        self.db = db_session
        self.cache_service = CacheService()
        self.cache_ttl = 3600  # 缓存1小时
    
    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self.db:
            return self.db
        return next(get_db_session())
    
    async def create_conversation(
        self,
        user_id: str,
        title: str,
        project_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        创建新对话
        
        Args:
            user_id: 用户ID
            title: 对话标题
            project_id: 项目ID（可选）
            settings: 对话设置（可选）
            
        Returns:
            创建的对话对象
        """
        try:
            db = self._get_db()
            
            conversation = Conversation(
                id=uuid4(),
                user_id=UUID(user_id),
                title=title,
                project_id=UUID(project_id) if project_id else None,
                settings=json.dumps(settings) if settings else None,
                message_count=0,
                total_tokens=0
            )
            
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"创建对话: {conversation.id}, 用户: {user_id}")
            
            # 缓存新对话
            await self._cache_conversation(conversation)
            
            return conversation
            
        except SQLAlchemyError as e:
            logger.error(f"创建对话失败: {str(e)}")
            if self.db is None:
                db.rollback()
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        sources: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        processing_time: Optional[float] = None,
        token_count: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        添加消息到对话
        
        Args:
            conversation_id: 对话ID
            role: 消息角色
            content: 消息内容
            message_type: 消息类型
            sources: 来源信息
            citations: 引用信息
            processing_time: 处理时间
            token_count: token数量
            metadata: 其他元数据
            
        Returns:
            创建的消息对象
        """
        try:
            db = self._get_db()
            
            # 获取对话
            conversation = db.query(Conversation).filter(
                Conversation.id == UUID(conversation_id)
            ).first()
            
            if not conversation:
                raise ValueError(f"对话不存在: {conversation_id}")
            
            # 获取下一个序号
            next_seq = conversation.message_count + 1
            
            # 创建消息
            message = Message(
                id=uuid4(),
                conversation_id=UUID(conversation_id),
                role=role,
                message_type=message_type,
                content=content,
                sequence_number=next_seq,
                processing_time=processing_time,
                token_count=token_count,
                sources=json.dumps(sources) if sources else None,
                citations=json.dumps(citations) if citations else None,
                message_metadata=json.dumps(metadata) if metadata else None
            )
            
            # 更新对话统计
            conversation.message_count = next_seq
            if token_count:
                conversation.total_tokens += token_count
            
            db.add(message)
            db.commit()
            db.refresh(message)
            
            logger.info(f"添加消息到对话 {conversation_id}: {role.value}, seq={next_seq}")
            
            # 清除缓存
            await self._invalidate_cache(conversation_id)
            
            return message
            
        except SQLAlchemyError as e:
            logger.error(f"添加消息失败: {str(e)}")
            if self.db is None:
                db.rollback()
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def get_conversation(
        self,
        conversation_id: str,
        include_messages: bool = False
    ) -> Optional[Conversation]:
        """
        获取对话
        
        Args:
            conversation_id: 对话ID
            include_messages: 是否包含消息
            
        Returns:
            对话对象或None
        """
        # 尝试从缓存获取
        cache_key = f"conversation:{conversation_id}"
        cached = await self.cache_service.get(cache_key)
        if cached and not include_messages:
            return cached
        
        try:
            db = self._get_db()
            
            query = db.query(Conversation).filter(
                Conversation.id == UUID(conversation_id)
            )
            
            conversation = query.first()
            
            if conversation and not include_messages:
                # 缓存对话信息
                await self._cache_conversation(conversation)
            
            return conversation
            
        except SQLAlchemyError as e:
            logger.error(f"获取对话失败: {str(e)}")
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        include_system: bool = True
    ) -> List[Message]:
        """
        获取对话消息
        
        Args:
            conversation_id: 对话ID
            limit: 限制数量
            offset: 偏移量
            include_system: 是否包含系统消息
            
        Returns:
            消息列表
        """
        try:
            db = self._get_db()
            
            query = db.query(Message).filter(
                Message.conversation_id == UUID(conversation_id)
            )
            
            if not include_system:
                query = query.filter(Message.role != MessageRole.SYSTEM)
            
            query = query.order_by(Message.sequence_number)
            
            if offset:
                query = query.offset(offset)
            
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"获取对话消息失败: {str(e)}")
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def get_user_conversations(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Conversation], int]:
        """
        获取用户的对话列表
        
        Args:
            user_id: 用户ID
            project_id: 项目ID（可选）
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            (对话列表, 总数)
        """
        try:
            db = self._get_db()
            
            # 构建查询
            query = db.query(Conversation).filter(
                Conversation.user_id == UUID(user_id)
            )
            
            if project_id:
                query = query.filter(Conversation.project_id == UUID(project_id))
            
            # 获取总数
            total = query.count()
            
            # 获取分页数据
            conversations = query.order_by(
                desc(Conversation.updated_at)
            ).offset(offset).limit(limit).all()
            
            return conversations, total
            
        except SQLAlchemyError as e:
            logger.error(f"获取用户对话列表失败: {str(e)}")
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        更新对话信息
        
        Args:
            conversation_id: 对话ID
            title: 新标题
            settings: 新设置
            
        Returns:
            更新后的对话对象
        """
        try:
            db = self._get_db()
            
            conversation = db.query(Conversation).filter(
                Conversation.id == UUID(conversation_id)
            ).first()
            
            if not conversation:
                raise ValueError(f"对话不存在: {conversation_id}")
            
            if title is not None:
                conversation.title = title
            
            if settings is not None:
                conversation.settings = json.dumps(settings)
            
            conversation.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(conversation)
            
            # 更新缓存
            await self._cache_conversation(conversation)
            
            return conversation
            
        except SQLAlchemyError as e:
            logger.error(f"更新对话失败: {str(e)}")
            if self.db is None:
                db.rollback()
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话（软删除）
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            是否成功
        """
        try:
            db = self._get_db()
            
            conversation = db.query(Conversation).filter(
                Conversation.id == UUID(conversation_id)
            ).first()
            
            if not conversation:
                return False
            
            # 软删除
            conversation.is_deleted = True
            conversation.deleted_at = datetime.utcnow()
            
            db.commit()
            
            # 清除缓存
            await self._invalidate_cache(conversation_id)
            
            logger.info(f"删除对话: {conversation_id}")
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"删除对话失败: {str(e)}")
            if self.db is None:
                db.rollback()
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def search_conversations(
        self,
        user_id: str,
        query: str,
        project_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Conversation]:
        """
        搜索对话
        
        Args:
            user_id: 用户ID
            query: 搜索查询
            project_id: 项目ID（可选）
            limit: 限制数量
            
        Returns:
            匹配的对话列表
        """
        try:
            db = self._get_db()
            
            # 构建搜索查询
            search_query = db.query(Conversation).filter(
                and_(
                    Conversation.user_id == UUID(user_id),
                    Conversation.title.ilike(f"%{query}%")
                )
            )
            
            if project_id:
                search_query = search_query.filter(
                    Conversation.project_id == UUID(project_id)
                )
            
            conversations = search_query.order_by(
                desc(Conversation.updated_at)
            ).limit(limit).all()
            
            return conversations
            
        except SQLAlchemyError as e:
            logger.error(f"搜索对话失败: {str(e)}")
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def get_conversation_context(
        self,
        conversation_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取对话上下文（用于AI回复）
        
        Args:
            conversation_id: 对话ID
            max_messages: 最大消息数
            
        Returns:
            格式化的消息列表
        """
        messages = await self.get_conversation_messages(
            conversation_id,
            limit=max_messages
        )
        
        # 格式化为AI可用的格式
        context = []
        for msg in messages:
            context_msg = {
                "role": msg.role.value,
                "content": msg.content
            }
            
            # 添加元数据（如果有）
            if msg.message_metadata:
                try:
                    metadata = json.loads(msg.message_metadata)
                    if isinstance(metadata, dict):
                        context_msg.update(metadata)
                except json.JSONDecodeError:
                    pass
            
            context.append(context_msg)
        
        return context
    
    async def get_conversation_summary(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        获取对话摘要
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话摘要信息
        """
        try:
            db = self._get_db()
            
            # 获取对话和统计信息
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"对话不存在: {conversation_id}")
            
            # 获取消息统计
            message_stats = db.query(
                func.count(Message.id).label("total"),
                func.count(Message.id).filter(Message.role == MessageRole.USER).label("user_messages"),
                func.count(Message.id).filter(Message.role == MessageRole.ASSISTANT).label("assistant_messages"),
                func.avg(Message.processing_time).label("avg_processing_time")
            ).filter(
                Message.conversation_id == UUID(conversation_id)
            ).first()
            
            # 获取最近的消息
            recent_messages = await self.get_conversation_messages(
                conversation_id,
                limit=5
            )
            
            summary = {
                "conversation_id": str(conversation.id),
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": conversation.message_count,
                "total_tokens": conversation.total_tokens,
                "user_messages": message_stats.user_messages or 0,
                "assistant_messages": message_stats.assistant_messages or 0,
                "avg_processing_time": float(message_stats.avg_processing_time or 0),
                "recent_messages": [
                    {
                        "role": msg.role.value,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "timestamp": msg.created_at.isoformat()
                    }
                    for msg in recent_messages[-3:]  # 最后3条
                ]
            }
            
            return summary
            
        except SQLAlchemyError as e:
            logger.error(f"获取对话摘要失败: {str(e)}")
            raise
        finally:
            if self.db is None:
                db.close()
    
    async def _cache_conversation(self, conversation: Conversation):
        """缓存对话信息"""
        cache_key = f"conversation:{conversation.id}"
        await self.cache_service.set(
            cache_key,
            conversation,
            ttl=self.cache_ttl
        )
    
    async def _invalidate_cache(self, conversation_id: str):
        """清除对话缓存"""
        cache_key = f"conversation:{conversation_id}"
        await self.cache_service.delete(cache_key)
    
    async def export_conversation(
        self,
        conversation_id: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        导出对话
        
        Args:
            conversation_id: 对话ID
            format: 导出格式（json, markdown）
            
        Returns:
            导出的数据
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        messages = await self.get_conversation_messages(conversation_id)
        
        if format == "json":
            return {
                "conversation": {
                    "id": str(conversation.id),
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "message_count": conversation.message_count,
                    "total_tokens": conversation.total_tokens
                },
                "messages": [
                    {
                        "id": str(msg.id),
                        "role": msg.role.value,
                        "content": msg.content,
                        "type": msg.message_type.value,
                        "timestamp": msg.created_at.isoformat(),
                        "sources": json.loads(msg.sources) if msg.sources else None,
                        "citations": json.loads(msg.citations) if msg.citations else None
                    }
                    for msg in messages
                ]
            }
        
        elif format == "markdown":
            md_content = f"# {conversation.title}\n\n"
            md_content += f"*创建时间: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            
            for msg in messages:
                role_emoji = "👤" if msg.role == MessageRole.USER else "🤖"
                md_content += f"## {role_emoji} {msg.role.value.title()}\n\n"
                md_content += f"{msg.content}\n\n"
                
                if msg.sources:
                    sources = json.loads(msg.sources)
                    if sources:
                        md_content += "**来源:**\n"
                        for source in sources:
                            md_content += f"- {source.get('title', 'Unknown')}\n"
                        md_content += "\n"
            
            return {"content": md_content, "filename": f"{conversation.title}.md"}
        
        else:
            raise ValueError(f"不支持的格式: {format}")


# 创建全局服务实例
conversation_service = ConversationService()