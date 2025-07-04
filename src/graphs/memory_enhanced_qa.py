"""
记忆增强的问答系统
集成项目记忆和用户偏好，提供个性化的问答体验
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..graphs.basic_knowledge_qa import BasicKnowledgeQA, QAState
from ..services.memory_service import (
    ProjectMemoryService, UserMemoryService, 
    ConversationMemoryService, MemoryService
)
from ..models.memory import MemoryCreate, MemoryType, MemoryScope
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MemoryEnhancedQA(BasicKnowledgeQA):
    """记忆增强的问答系统"""
    
    def __init__(self, db_session):
        super().__init__()
        self.db_session = db_session
        self.project_memory_service = ProjectMemoryService(db_session)
        self.user_memory_service = UserMemoryService(db_session)
        self.conversation_memory_service = ConversationMemoryService(db_session)
        self.memory_service = MemoryService(db_session)
    
    async def answer_with_memory(
        self,
        question: str,
        project_id: str,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用记忆增强的问答"""
        
        # 1. 获取用户上下文
        user_context = await self.user_memory_service.get_user_context(user_id)
        
        # 2. 获取项目记忆
        project_memory = await self.project_memory_service.get_or_create_project_memory(project_id)
        
        # 3. 获取对话上下文（如果有）
        conversation_context = []
        if conversation_id:
            conversation_context = await self.conversation_memory_service.get_conversation_context(
                conversation_id, last_n_turns=3
            )
        
        # 4. 增强问题（加入上下文）
        enhanced_question = await self._enhance_question_with_context(
            question, user_context, project_memory, conversation_context
        )
        
        # 5. 执行基础问答
        result = await self.answer_question(enhanced_question, project_id)
        
        # 6. 个性化调整答案
        if result["success"]:
            result["answer"] = await self._personalize_answer(
                result["answer"],
                user_context,
                result.get("sources", [])
            )
            
            # 7. 记录到记忆系统
            await self._record_qa_to_memory(
                question, result["answer"], project_id, user_id, 
                conversation_id, result.get("confidence", 0)
            )
            
            # 8. 更新项目记忆
            await self._update_project_memory_from_qa(
                project_id, question, result["answer"], result.get("confidence", 0)
            )
            
            # 9. 记录用户活动
            await self.user_memory_service.record_user_activity(
                user_id, "query", {
                    "query": question,
                    "project_id": project_id,
                    "success": True,
                    "confidence": result.get("confidence", 0)
                }
            )
        
        return result
    
    async def _enhance_question_with_context(
        self,
        question: str,
        user_context: Dict[str, Any],
        project_memory: Any,
        conversation_context: List[Dict[str, Any]]
    ) -> str:
        """使用上下文增强问题"""
        
        # 构建上下文提示
        context_parts = []
        
        # 添加项目上下文
        if project_memory.context_summary:
            context_parts.append(f"项目背景：{project_memory.context_summary}")
        
        if project_memory.key_concepts:
            context_parts.append(f"关键概念：{', '.join(project_memory.key_concepts[:5])}")
        
        # 添加对话历史
        if conversation_context:
            recent_topics = []
            for turn in conversation_context[-2:]:
                if turn.get("topics"):
                    recent_topics.extend(turn["topics"])
            if recent_topics:
                context_parts.append(f"最近讨论的主题：{', '.join(set(recent_topics))}")
        
        # 如果有上下文，增强问题
        if context_parts:
            enhanced = f"{question}\n\n相关上下文：\n" + "\n".join(context_parts)
            return enhanced
        
        return question
    
    async def _personalize_answer(
        self,
        answer: str,
        user_context: Dict[str, Any],
        sources: List[Dict[str, Any]]
    ) -> str:
        """根据用户偏好个性化答案"""
        
        # 根据用户偏好调整答案风格
        style = user_context.get("style", "balanced")
        expertise = user_context.get("expertise", "intermediate")
        
        if style == "concise" and len(answer) > 500:
            # 生成简洁版本
            prompt = f"请将以下答案简化为100字以内的核心要点：\n{answer}"
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            answer = response.content
        
        elif style == "detailed" and len(answer) < 200:
            # 扩展答案
            if sources:
                answer += "\n\n详细信息：\n"
                for i, source in enumerate(sources[:3]):
                    answer += f"\n{i+1}. {source.get('content_preview', '')}"
        
        # 根据专业水平调整术语
        if expertise == "beginner":
            # 可以添加术语解释
            pass
        elif expertise == "expert":
            # 可以使用更专业的表述
            pass
        
        # 添加自定义提示词
        custom_prompts = user_context.get("custom_prompts", {})
        if "answer_suffix" in custom_prompts:
            answer += f"\n\n{custom_prompts['answer_suffix']}"
        
        return answer
    
    async def _record_qa_to_memory(
        self,
        question: str,
        answer: str,
        project_id: str,
        user_id: str,
        conversation_id: Optional[str],
        confidence: float
    ):
        """记录问答到记忆系统"""
        
        # 创建问答记忆
        await self.memory_service.create_memory(MemoryCreate(
            memory_type=MemoryType.LEARNED_KNOWLEDGE,
            scope=MemoryScope.PROJECT,
            project_id=project_id,
            user_id=user_id,
            key=f"qa_{datetime.now().isoformat()}",
            content={
                "question": question,
                "answer": answer,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            },
            summary=question[:100],
            importance=confidence,
            expires_in_hours=24 * 30  # 30天
        ))
        
        # 如果有对话ID，记录到对话记忆
        if conversation_id:
            # 提取主题和实体（简化版）
            topics = []
            if "?" in question:
                topics.append("question")
            
            await self.conversation_memory_service.record_conversation_turn(
                conversation_id=conversation_id,
                turn_number=int(datetime.now().timestamp()),  # 简化的轮次号
                user_message=question,
                assistant_response=answer,
                metadata={
                    "topics": topics,
                    "confidence": confidence,
                    "importance_score": confidence
                }
            )
    
    async def _update_project_memory_from_qa(
        self,
        project_id: str,
        question: str,
        answer: str,
        confidence: float
    ):
        """从问答中更新项目记忆"""
        
        # 记录查询
        await self.project_memory_service.record_query(
            project_id, question, success=confidence > 0.5
        )
        
        # 如果是高置信度的答案，提取学习到的事实
        if confidence > 0.7 and len(answer) > 50:
            # 简化版的事实提取
            fact = f"关于'{question[:50]}...'的答案：{answer[:100]}..."
            await self.project_memory_service.add_learned_fact(
                project_id, fact, confidence, "qa_system"
            )
    
    async def get_memory_enhanced_context(
        self,
        project_id: str,
        user_id: str,
        query: str
    ) -> Dict[str, Any]:
        """获取记忆增强的上下文"""
        
        # 查询相关记忆
        from ..models.memory import MemoryQuery
        
        relevant_memories = await self.memory_service.query_memories(MemoryQuery(
            memory_types=[MemoryType.LEARNED_KNOWLEDGE, MemoryType.PROJECT_CONTEXT],
            project_id=project_id,
            key_pattern=query[:20],  # 使用查询的前20个字符
            min_importance=0.5,
            limit=10
        ))
        
        # 获取项目的常见查询
        project_memory = await self.project_memory_service.get_or_create_project_memory(project_id)
        frequent_queries = project_memory.frequent_queries or []
        
        # 获取用户的查询模式
        user_memory = await self.user_memory_service.get_or_create_user_memory(user_id)
        query_patterns = user_memory.query_patterns or []
        
        return {
            "relevant_memories": [
                {
                    "content": m.content,
                    "importance": m.importance,
                    "created_at": m.created_at
                }
                for m in relevant_memories
            ],
            "frequent_queries": frequent_queries[:5],
            "user_patterns": query_patterns[-5:],
            "project_context": {
                "summary": project_memory.context_summary,
                "key_concepts": project_memory.key_concepts,
                "total_queries": project_memory.total_queries
            }
        }


class MemoryBasedRecommender:
    """基于记忆的推荐系统"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.memory_service = MemoryService(db_session)
        self.project_memory_service = ProjectMemoryService(db_session)
        self.user_memory_service = UserMemoryService(db_session)
    
    async def recommend_next_queries(
        self,
        project_id: str,
        user_id: str,
        current_query: str
    ) -> List[str]:
        """推荐下一步查询"""
        
        # 获取项目的常见查询
        project_memory = await self.project_memory_service.get_or_create_project_memory(project_id)
        frequent_queries = project_memory.frequent_queries or []
        
        # 获取用户兴趣
        user_memory = await self.user_memory_service.get_or_create_user_memory(user_id)
        interests = user_memory.interests or []
        
        # 简单的推荐逻辑
        recommendations = []
        
        # 1. 基于常见查询推荐
        for fq in frequent_queries[:3]:
            if fq["query"] != current_query:
                recommendations.append(fq["query"])
        
        # 2. 基于用户兴趣推荐
        for interest in interests[:2]:
            if interest.lower() not in current_query.lower():
                recommendations.append(f"{current_query} 关于{interest}")
        
        # 3. 基于项目关键概念推荐
        if project_memory.key_concepts:
            for concept in project_memory.key_concepts[:2]:
                if concept.lower() not in current_query.lower():
                    recommendations.append(f"{concept}相关的内容")
        
        return recommendations[:5]
    
    async def recommend_documents(
        self,
        project_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """推荐相关文档"""
        
        # 获取项目记忆中的重要文档
        project_memory = await self.project_memory_service.get_or_create_project_memory(project_id)
        important_docs = project_memory.important_documents or []
        
        # 获取用户最近查看的文档（从记忆中）
        from ..models.memory import MemoryQuery
        recent_memories = await self.memory_service.query_memories(MemoryQuery(
            memory_types=[MemoryType.LEARNED_KNOWLEDGE],
            user_id=user_id,
            project_id=project_id,
            limit=20
        ))
        
        # 提取文档ID
        recent_doc_ids = []
        for memory in recent_memories:
            if "document_id" in memory.content:
                recent_doc_ids.append(memory.content["document_id"])
        
        # 组合推荐
        recommendations = []
        
        # 添加重要文档
        for doc_id in important_docs[:5]:
            if doc_id not in recent_doc_ids:
                recommendations.append({
                    "document_id": doc_id,
                    "reason": "项目重要文档",
                    "score": 0.9
                })
        
        return recommendations