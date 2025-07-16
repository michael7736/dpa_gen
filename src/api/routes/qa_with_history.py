"""
带对话历史的问答API端点
集成对话管理系统，支持上下文感知的问答
"""

from typing import List, Optional
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...graphs.basic_knowledge_qa import BasicKnowledgeQA
from ...services.conversation_service import ConversationService
from ...services.project_service import ProjectService
from ...models.conversation import MessageRole, MessageType
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/qa-history", tags=["qa-with-history"])


class QuestionWithHistoryRequest(BaseModel):
    """带历史的问题请求模型"""
    question: str = Field(..., description="用户问题")
    project_id: Optional[str] = Field(None, description="项目ID，如果未提供则使用默认项目")
    conversation_id: Optional[str] = Field(None, description="对话ID，如果为空则创建新对话")
    use_conversation_context: bool = Field(True, description="是否使用对话历史作为上下文")
    max_history_messages: int = Field(10, description="使用的历史消息数量")
    include_sources: bool = Field(True, description="是否返回来源信息")


class QuestionWithHistoryResponse(BaseModel):
    """带历史的问题响应模型"""
    answer: str
    confidence: float
    sources: Optional[List[dict]] = None
    conversation_id: str
    message_id: str
    response_time: float
    from_cache: bool
    context_used: Optional[List[dict]] = None


# 创建全局实例
qa_system = BasicKnowledgeQA()


@router.post("/answer", response_model=QuestionWithHistoryResponse)
async def answer_with_history(
    request: QuestionWithHistoryRequest,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db_session)
):
    """
    带对话历史的问答
    
    特性：
    - 自动管理对话历史
    - 使用历史上下文增强回答
    - 保存问答记录便于后续查询
    """
    try:
        conversation_service = ConversationService(db)
        
        # 如果没有提供项目ID，使用用户的默认项目
        if not request.project_id:
            project_service = ProjectService(db)
            default_project = await project_service.get_or_create_default_project(uuid.UUID(user_id))
            project_id = str(default_project.id)
            logger.info(f"使用用户 {user_id} 的默认项目: {project_id}")
        else:
            project_id = request.project_id
        
        # 1. 获取或创建对话
        if request.conversation_id:
            conversation = await conversation_service.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话不存在")
            if str(conversation.user_id) != user_id:
                raise HTTPException(status_code=403, detail="无权访问此对话")
        else:
            # 创建新对话
            conversation = await conversation_service.create_conversation(
                user_id=user_id,
                title=request.question[:50] + "..." if len(request.question) > 50 else request.question,
                project_id=project_id
            )
        
        # 2. 获取对话历史上下文
        context_messages = []
        if request.use_conversation_context and request.conversation_id:
            history = await conversation_service.get_conversation_context(
                conversation_id=str(conversation.id),
                max_messages=request.max_history_messages
            )
            context_messages = history
        
        # 3. 保存用户问题
        user_message = await conversation_service.add_message(
            conversation_id=str(conversation.id),
            role=MessageRole.USER,
            content=request.question,
            message_type=MessageType.QUERY
        )
        
        # 4. 构建增强的问题（包含历史上下文）
        enhanced_question = request.question
        if context_messages:
            # 构建上下文提示
            context_prompt = "基于以下对话历史：\n"
            for msg in context_messages[-5:]:  # 只使用最近5条消息
                role = "用户" if msg["role"] == "user" else "助手"
                context_prompt += f"{role}: {msg['content']}\n"
            context_prompt += f"\n当前问题: {request.question}"
            enhanced_question = context_prompt
        
        # 5. 调用QA系统回答问题
        result = await qa_system.answer_question(
            question=enhanced_question,
            project_id=project_id
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        # 6. 保存助手回答
        assistant_message = await conversation_service.add_message(
            conversation_id=str(conversation.id),
            role=MessageRole.ASSISTANT,
            content=result["answer"],
            message_type=MessageType.TEXT,
            sources=result["sources"] if request.include_sources else None,
            processing_time=result["response_time"],
            metadata={
                "confidence": result["confidence"],
                "from_cache": result.get("from_cache", False)
            }
        )
        
        # 7. 构建响应
        response = QuestionWithHistoryResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            sources=result["sources"] if request.include_sources else None,
            conversation_id=str(conversation.id),
            message_id=str(assistant_message.id),
            response_time=result["response_time"],
            from_cache=result.get("from_cache", False),
            context_used=context_messages if request.use_conversation_context else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in answer_with_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/continue")
async def continue_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db_session)
):
    """
    继续现有对话
    
    返回对话历史和建议的后续问题
    """
    try:
        conversation_service = ConversationService(db)
        
        # 验证对话权限
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 获取对话历史
        messages = await conversation_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=20
        )
        
        # 获取对话摘要
        summary = await conversation_service.get_conversation_summary(conversation_id)
        
        # 基于历史生成建议问题
        suggested_questions = []
        if messages:
            last_answer = None
            for msg in reversed(messages):
                if msg.role == MessageRole.ASSISTANT:
                    last_answer = msg.content
                    break
            
            if last_answer:
                # 这里可以调用LLM生成建议问题
                # 暂时返回固定的建议
                suggested_questions = [
                    "能详细解释一下这个观点吗？",
                    "有什么相关的例子吗？",
                    "这个结论的依据是什么？"
                ]
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "summary": summary,
            "recent_messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in messages[-10:]  # 最近10条
            ],
            "suggested_questions": suggested_questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error continuing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/summarize")
async def summarize_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db_session)
):
    """
    总结对话内容
    
    使用LLM生成对话摘要
    """
    try:
        conversation_service = ConversationService(db)
        
        # 验证权限
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        if str(conversation.user_id) != user_id:
            raise HTTPException(status_code=403, detail="无权访问此对话")
        
        # 获取所有消息
        messages = await conversation_service.get_conversation_messages(conversation_id)
        
        if not messages:
            return {
                "success": True,
                "summary": "对话中暂无内容"
            }
        
        # 构建对话文本
        conversation_text = ""
        for msg in messages:
            role = "用户" if msg.role == MessageRole.USER else "助手"
            conversation_text += f"{role}: {msg.content}\n\n"
        
        # 使用QA系统的LLM生成摘要
        from langchain_core.messages import SystemMessage, HumanMessage
        
        summary_prompt = f"""请总结以下对话的主要内容，包括：
1. 讨论的主要话题
2. 得出的关键结论
3. 未解决的问题（如果有）

对话内容：
{conversation_text[:3000]}  # 限制长度

请用简洁的语言总结，不超过200字。"""
        
        response = await qa_system.llm.ainvoke([
            SystemMessage(content="你是一个专业的对话总结助手。"),
            HumanMessage(content=summary_prompt)
        ])
        
        # 更新对话标题（使用摘要的第一句）
        summary_text = response.content
        first_sentence = summary_text.split("。")[0] + "。"
        if len(first_sentence) < 50:
            await conversation_service.update_conversation(
                conversation_id=conversation_id,
                title=first_sentence
            )
        
        return {
            "success": True,
            "summary": summary_text,
            "message_count": len(messages),
            "updated_title": first_sentence if len(first_sentence) < 50 else None
        }
        
    except Exception as e:
        logger.error(f"Error summarizing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 健康检查端点
@router.get("/health")
async def health_check():
    """QA历史系统健康检查"""
    return {
        "status": "healthy",
        "service": "qa-with-history",
        "features": [
            "conversation_management",
            "context_aware_qa",
            "conversation_summary"
        ]
    }