"""
优化的问答系统 - 专注于响应速度
目标：将响应时间从3秒优化到1秒以内
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate

from src.core.retrieval.mvp_hybrid_retriever import create_mvp_hybrid_retriever
from src.services.memory_write_service_v2 import MemoryWriteService, MemoryType
from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 优化配置
DEFAULT_USER_ID = "u1"
FAST_MODEL = "gpt-4o-mini"  # 使用更快的模型
SIMPLE_MODEL = "gpt-3.5-turbo"  # 备选快速模型

@dataclass
class OptimizedQAResult:
    """优化的问答结果"""
    question: str
    answer: str
    context_used: List[Dict[str, Any]]
    retrieval_breakdown: Dict[str, int]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]


class OptimizedQASystem:
    """
    优化的问答系统
    专注于速度优化，目标响应时间<1秒
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        self.retriever = create_mvp_hybrid_retriever(user_id=user_id)
        self.memory_service = MemoryWriteService(user_id=user_id)
        self.memory_bank_manager = create_memory_bank_manager(user_id=user_id)
        
        # 优化LLM配置 - 使用更快的模型和参数
        self.llm = ChatOpenAI(
            model=FAST_MODEL,
            temperature=0.1,
            max_tokens=1000,  # 减少最大token数
            api_key=settings.ai_model.openai_api_key,
            request_timeout=10,  # 添加超时
            max_retries=1  # 减少重试次数
        )
        
        # 简化的提示词模板
        self.fast_qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""基于以下上下文简洁回答问题：

{context}

问题：{question}

请提供准确、简洁的回答：
"""
        )
        
    async def fast_answer_question(
        self,
        question: str,
        project_id: Optional[str] = None,
        top_k: int = 5,  # 减少检索数量
        use_memory: bool = False  # 默认关闭Memory Bank
    ) -> OptimizedQAResult:
        """
        快速回答问题 - 优化版本
        
        优化策略：
        1. 简化检索流程
        2. 并行处理
        3. 减少LLM调用
        4. 异步保存记录
        """
        start_time = datetime.now()
        
        try:
            # 1. 快速检索 - 只使用向量检索，跳过复杂的混合检索
            retrieval_task = asyncio.create_task(
                self._fast_retrieve(question, project_id, top_k)
            )
            
            # 2. 并行获取Memory上下文（如果需要）
            memory_task = None
            if use_memory and project_id:
                memory_task = asyncio.create_task(
                    self._get_memory_context_fast(project_id)
                )
            
            # 3. 等待检索完成
            retrieval_result = await retrieval_task
            
            # 4. 准备上下文
            context = self._format_context_fast(retrieval_result["results"])
            
            # 5. 快速生成回答
            answer = await self._generate_answer_fast(question, context)
            
            # 6. 简化置信度计算
            confidence = self._calculate_confidence_fast(
                retrieval_result["results"],
                len(answer)
            )
            
            # 7. 异步保存记录（不阻塞响应）
            if project_id:
                asyncio.create_task(
                    self._save_interaction_async(project_id, question, answer)
                )
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return OptimizedQAResult(
                question=question,
                answer=answer,
                context_used=[
                    {
                        "doc_id": r.get("doc_id", "unknown"),
                        "content": r.get("content", "")[:100] + "...",  # 进一步缩短
                        "score": r.get("score", 0),
                        "source": r.get("source", "vector")
                    }
                    for r in retrieval_result["results"][:3]  # 只返回前3个
                ],
                retrieval_breakdown=retrieval_result["breakdown"],
                confidence_score=confidence,
                processing_time=processing_time,
                metadata={
                    "project_id": project_id,
                    "user_id": self.user_id,
                    "model": FAST_MODEL,
                    "optimization": "fast_mode"
                }
            )
            
        except Exception as e:
            logger.error(f"Fast QA error: {e}")
            # 快速回退策略
            return await self._fallback_answer(question, start_time)
            
    async def _fast_retrieve(
        self,
        query: str,
        project_id: Optional[str],
        top_k: int
    ) -> Dict[str, Any]:
        """简化的快速检索 - 使用混合检索但简化参数"""
        try:
            # 使用标准的混合检索器
            retrieval_result = await self.retriever.retrieve(
                query=query,
                project_id=project_id,
                top_k=top_k,
                score_threshold=0.7  # 提高阈值，减少结果
            )
            
            # 优先使用向量结果，减少后处理复杂度
            primary_results = retrieval_result.vector_results
            if not primary_results and retrieval_result.fused_results:
                primary_results = retrieval_result.fused_results[:top_k//2]  # 减少结果数量
            
            return {
                "results": primary_results,
                "breakdown": {
                    "vector": len(retrieval_result.vector_results),
                    "graph": len(retrieval_result.graph_results),
                    "memory": len(retrieval_result.memory_results)
                }
            }
        except Exception as e:
            logger.error(f"Fast retrieval error: {e}")
            return {"results": [], "breakdown": {"vector": 0, "graph": 0, "memory": 0}}
            
    async def _get_memory_context_fast(self, project_id: str) -> str:
        """快速获取Memory上下文"""
        try:
            # 简化的Memory查询，添加超时
            memory_snapshot = await asyncio.wait_for(
                self.memory_bank_manager.get_snapshot(project_id),
                timeout=0.5  # 500ms超时
            )
            
            if memory_snapshot and memory_snapshot.get("dynamic_summary"):
                return memory_snapshot["dynamic_summary"][:200]  # 限制长度
                
        except Exception as e:
            logger.warning(f"Memory context timeout or error: {e}")
            
        return ""
        
    def _format_context_fast(self, results: List) -> str:
        """快速格式化上下文"""
        if not results:
            return "未找到相关信息。"
            
        # 简化格式，只使用前3个结果
        context_parts = []
        for i, result in enumerate(results[:3]):
            content = result.content if hasattr(result, 'content') else str(result.get('content', ''))
            # 限制每个文档的长度
            content = content[:300] + "..." if len(content) > 300 else content
            context_parts.append(f"[文档{i+1}] {content}")
            
        return "\n\n".join(context_parts)
        
    async def _generate_answer_fast(self, question: str, context: str) -> str:
        """快速生成回答"""
        try:
            prompt = self.fast_qa_prompt.format(
                context=context,
                question=question
            )
            
            messages = [
                SystemMessage(content="你是一个专业的问答助手。请简洁准确地回答问题。"),
                HumanMessage(content=prompt)
            ]
            
            # 添加超时机制
            response = await asyncio.wait_for(
                self.llm.ainvoke(messages),
                timeout=15  # 15秒超时
            )
            
            return response.content
            
        except asyncio.TimeoutError:
            logger.warning("LLM response timeout")
            return "回答生成超时，请重试。"
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "抱歉，无法生成回答，请重试。"
            
    def _calculate_confidence_fast(self, results: List, answer_length: int) -> float:
        """快速置信度计算"""
        base_confidence = 0.5
        
        # 基于检索结果数量
        if results:
            base_confidence += min(len(results) * 0.1, 0.3)
            
        # 基于回答长度
        if answer_length > 50:
            base_confidence += 0.1
            
        # 基于最高分数（如果有）
        if results and hasattr(results[0], 'score'):
            top_score = results[0].score
            if top_score > 0.8:
                base_confidence += 0.1
                
        return min(base_confidence, 0.9)
        
    async def _save_interaction_async(
        self,
        project_id: str,
        question: str,
        answer: str
    ):
        """异步保存交互记录 - 不阻塞主流程"""
        try:
            # 简化保存逻辑
            interaction = f"Q: {question[:100]}\nA: {answer[:200]}"
            
            await self.memory_service.write_memory(
                content=interaction,
                memory_type=MemoryType.WORKING,
                metadata={
                    "type": "fast_qa",
                    "timestamp": datetime.now().isoformat()
                },
                project_id=project_id,
                user_id=self.user_id
            )
            
        except Exception as e:
            logger.error(f"Async save failed: {e}")
            # 静默失败，不影响用户体验
            
    async def _fallback_answer(
        self,
        question: str,
        start_time: datetime
    ) -> OptimizedQAResult:
        """快速回退策略"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return OptimizedQAResult(
            question=question,
            answer="抱歉，系统当前繁忙，请稍后重试。",
            context_used=[],
            retrieval_breakdown={"vector": 0, "graph": 0, "memory": 0},
            confidence_score=0.1,
            processing_time=processing_time,
            metadata={
                "user_id": self.user_id,
                "model": FAST_MODEL,
                "status": "fallback"
            }
        )
        
    async def batch_answer_fast(
        self,
        questions: List[str],
        project_id: Optional[str] = None,
        max_concurrent: int = 5  # 增加并发数
    ) -> List[OptimizedQAResult]:
        """快速批量回答"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def answer_with_limit(question: str) -> OptimizedQAResult:
            async with semaphore:
                return await self.fast_answer_question(
                    question, 
                    project_id,
                    top_k=3,  # 批量时进一步减少检索数量
                    use_memory=False  # 批量时关闭Memory
                )
                
        tasks = [answer_with_limit(q) for q in questions]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 工厂函数
def create_optimized_qa_system(user_id: str = DEFAULT_USER_ID) -> OptimizedQASystem:
    """创建优化的问答系统实例"""
    return OptimizedQASystem(user_id=user_id)


class HybridQASystem:
    """
    混合问答系统 - 智能选择策略
    根据问题复杂度自动选择快速或完整模式
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        self.fast_system = create_optimized_qa_system(user_id)
        # self.full_system = create_mvp_qa_system(user_id)  # 如需要可导入
        
    async def smart_answer(
        self,
        question: str,
        project_id: Optional[str] = None,
        priority: str = "fast"  # "fast" | "accurate" | "auto"
    ) -> OptimizedQAResult:
        """智能回答 - 根据优先级选择策略"""
        
        if priority == "fast":
            return await self.fast_system.fast_answer_question(
                question, project_id, use_memory=False
            )
        elif priority == "accurate":
            # 使用准确模式（需要时实现）
            return await self.fast_system.fast_answer_question(
                question, project_id, top_k=10, use_memory=True
            )
        else:  # auto mode
            # 简单的智能判断：短问题用快速模式，长问题用准确模式
            if len(question) < 50:
                return await self.fast_system.fast_answer_question(
                    question, project_id, use_memory=False
                )
            else:
                return await self.fast_system.fast_answer_question(
                    question, project_id, top_k=8, use_memory=True
                )


def create_hybrid_qa_system(user_id: str = DEFAULT_USER_ID) -> HybridQASystem:
    """创建混合问答系统"""
    return HybridQASystem(user_id=user_id)