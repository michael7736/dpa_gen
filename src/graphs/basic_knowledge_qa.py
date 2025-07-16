"""
基础知识问答系统
简化版RAG实现，专注于稳定性和响应速度
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict
import numpy as np

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph, END

from ..core.simple_vectorstore import SimpleVectorStore
from ..services.cache_service import CacheService, CacheKeys, cache_result
from ..services.reranker import RerankerService
from ..services.optimized_retrieval import OptimizedVectorRetrieval, QueryOptimizer
from ..utils.logger import get_logger

logger = get_logger(__name__)


class QAState(TypedDict):
    """问答状态"""
    question: str
    project_id: str
    
    # 检索结果
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    
    # 答案
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    
    # 元信息
    response_time: float
    from_cache: bool


class BasicKnowledgeQA:
    """基础知识问答系统"""
    
    def __init__(self):
        # 配置向量存储
        from ..config.settings import get_settings
        settings = get_settings()
        
        # 使用配置中的API密钥
        import os
        if settings.ai_model.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.ai_model.openai_api_key
            
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # 使用简单的向量存储（临时方案）
        self.vector_store = SimpleVectorStore()
        self.cache_service = CacheService()
        self.reranker = RerankerService()
        self.optimized_retrieval = OptimizedVectorRetrieval()
        self.query_optimizer = QueryOptimizer()
        
        # 构建工作流
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """构建问答工作流"""
        graph = StateGraph(QAState)
        
        # 简化的三步流程
        graph.add_node("retrieve", self.retrieve_context)
        graph.add_node("rerank", self.rerank_results)
        graph.add_node("generate", self.generate_answer)
        
        # 线性流程
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "rerank")
        graph.add_edge("rerank", "generate")
        graph.add_edge("generate", END)
        
        return graph
    
    async def retrieve_context(self, state: QAState) -> QAState:
        """检索相关上下文"""
        start_time = datetime.now()
        
        try:
            # 优化查询
            query_suggestions = await self.query_optimizer.optimize_query(state["question"])
            
            # 使用优化的检索服务
            chunks = await self.optimized_retrieval.optimized_search(
                collection_name=f"project_{state['project_id']}",
                query=state["question"],
                top_k=20,
                filters=query_suggestions.get("filters"),
                search_strategy=query_suggestions.get("search_strategy", "hybrid")
            )
            
            state["retrieved_chunks"] = chunks
            state["from_cache"] = False  # 缓存已在optimized_search内部处理
            
            logger.info(f"Retrieved {len(chunks)} chunks using {query_suggestions.get('search_strategy')} strategy")
            
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            # 降级到基础检索
            try:
                # 使用LangChain向量存储进行检索
                results = await self.vector_store.similarity_search(
                    query=state["question"],
                    k=20,
                    filter_conditions={"project_id": state["project_id"]}
                )
                
                # 转换结果格式
                chunks = []
                for doc, score in results:
                    chunks.append({
                        "content": doc.page_content,
                        "score": score,
                        "metadata": doc.metadata,
                        "document_id": doc.metadata.get("document_id")
                    })
                
                state["retrieved_chunks"] = chunks
                state["from_cache"] = False
                logger.info(f"Fallback retrieval: {len(chunks)} chunks")
                
            except Exception as fallback_error:
                logger.error(f"Fallback retrieval error: {fallback_error}")
                state["retrieved_chunks"] = []
        
        finally:
            state["response_time"] = (datetime.now() - start_time).total_seconds()
        
        return state
    
    async def rerank_results(self, state: QAState) -> QAState:
        """重排序检索结果"""
        try:
            chunks = state.get("retrieved_chunks", [])
            if not chunks:
                state["reranked_chunks"] = []
                return state
            
            # 使用高级重排序服务
            reranked_chunks = await self.reranker.rerank(
                query=state["question"],
                chunks=chunks,
                strategy="hybrid",  # 使用混合策略
                top_k=5
            )
            
            state["reranked_chunks"] = reranked_chunks
            logger.info(f"Reranked to {len(reranked_chunks)} chunks using hybrid strategy")
            
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            state["reranked_chunks"] = state.get("retrieved_chunks", [])[:5]
        
        return state
    
    async def generate_answer(self, state: QAState) -> QAState:
        """生成答案"""
        try:
            chunks = state.get("reranked_chunks", [])
            
            if not chunks:
                state["answer"] = "抱歉，我没有找到相关的信息来回答您的问题。"
                state["confidence"] = 0.0
                state["sources"] = []
                return state
            
            # 构建上下文
            context = "\n\n---\n\n".join([
                f"[来源 {i+1}]\n{chunk['content']}"
                for i, chunk in enumerate(chunks)
            ])
            
            # 构建提示
            system_prompt = """你是一个专业的知识问答助手。基于提供的上下文信息回答用户问题。

要求：
1. 只使用提供的上下文信息回答
2. 如果上下文中没有相关信息，诚实说明
3. 回答要准确、简洁、专业
4. 在回答末尾标注使用了哪些来源（如[来源1,2]）"""
            
            user_prompt = f"""上下文信息：
{context}

用户问题：{state['question']}

请基于上述上下文回答问题。"""
            
            # 生成答案
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            state["answer"] = response.content
            
            # 提取来源信息
            sources = []
            for i, chunk in enumerate(chunks):
                sources.append({
                    "index": i + 1,
                    "document_id": chunk.get("document_id"),
                    "content_preview": chunk["content"][:200] + "...",
                    "score": chunk["score"]
                })
            
            state["sources"] = sources
            
            # 计算置信度（基于检索分数）
            avg_score = np.mean([chunk["score"] for chunk in chunks[:3]])
            state["confidence"] = min(avg_score, 1.0)
            
            logger.info(f"Generated answer with confidence: {state['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            state["answer"] = "抱歉，生成答案时出现错误。"
            state["confidence"] = 0.0
            state["sources"] = []
        
        return state
    
    async def answer_question(self, question: str, project_id: str) -> Dict[str, Any]:
        """回答问题的入口方法"""
        initial_state = QAState(
            question=question,
            project_id=project_id,
            retrieved_chunks=[],
            reranked_chunks=[],
            answer="",
            sources=[],
            confidence=0.0,
            response_time=0.0,
            from_cache=False
        )
        
        try:
            # 执行问答流程
            start_time = datetime.now()
            result = await self.app.ainvoke(initial_state)
            total_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "answer": result["answer"],
                "sources": result["sources"],
                "confidence": result["confidence"],
                "response_time": total_time,
                "from_cache": result["from_cache"]
            }
            
        except Exception as e:
            logger.error(f"QA pipeline error: {e}")
            return {
                "success": False,
                "answer": "抱歉，处理您的问题时出现错误。",
                "error": str(e)
            }
    
    async def batch_answer(self, questions: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """批量回答问题"""
        results = []
        
        for q in questions:
            result = await self.answer_question(
                question=q["question"],
                project_id=q["project_id"]
            )
            result["question_id"] = q.get("id")
            results.append(result)
        
        return results


# 问答服务的辅助函数
class QAEnhancer:
    """问答增强功能"""
    
    @staticmethod
    async def suggest_follow_ups(question: str, answer: str, llm: ChatOpenAI) -> List[str]:
        """生成后续问题建议"""
        prompt = f"""基于用户的问题和回答，生成3个相关的后续问题。

原始问题：{question}
回答：{answer}

生成3个用户可能想继续了解的问题，每个问题一行。"""
        
        try:
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            questions = [q.strip() for q in response.content.split('\n') if q.strip()]
            return questions[:3]
        except:
            return []
    
    @staticmethod
    def calculate_answer_quality(answer: str, sources: List[Dict]) -> Dict[str, Any]:
        """评估答案质量"""
        quality_metrics = {
            "has_sources": len(sources) > 0,
            "answer_length": len(answer),
            "avg_source_score": np.mean([s["score"] for s in sources]) if sources else 0,
            "source_diversity": len(set([s.get("document_id") for s in sources]))
        }
        
        # 综合评分
        score = 0
        if quality_metrics["has_sources"]:
            score += 0.4
        if quality_metrics["answer_length"] > 50:
            score += 0.2
        if quality_metrics["avg_source_score"] > 0.7:
            score += 0.2
        if quality_metrics["source_diversity"] > 1:
            score += 0.2
        
        return {
            "quality_score": score,
            "metrics": quality_metrics
        }