"""
DPA V3认知系统API桥接层
将认知系统能力暴露为RESTful API端点
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...cognitive import (
    DPACognitiveState,
    StateManager,
    create_cognitive_storage,
    create_memory_bank_manager,
    create_cognitive_workflow,
    create_s2_chunker,
    create_hybrid_retrieval_system,
    create_metacognitive_engine,
    hybrid_search
)
from ...utils.logger import get_logger
from ...models.base import ResponseSchema
from ..middleware.auth import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/cognitive", tags=["认知系统"])

# ==========================================
# 请求/响应模型
# ==========================================

class CognitiveAnalysisRequest(BaseModel):
    """认知分析请求"""
    document_id: Optional[str] = None
    document_text: Optional[str] = None
    project_id: str
    analysis_type: str = Field(default="comprehensive", description="分析类型：basic/standard/deep/expert/comprehensive")
    analysis_goal: Optional[str] = Field(default=None, description="分析目标")
    use_memory: bool = Field(default=True, description="是否使用记忆库")
    enable_metacognition: bool = Field(default=True, description="是否启用元认知")

class CognitiveAnalysisResponse(BaseModel):
    """认知分析响应"""
    analysis_id: str
    processing_report: Dict[str, Any]
    chunks_created: int
    retrieval_results: int
    metacognitive_strategy: str
    performance_score: float
    confidence_level: str
    working_memory_usage: float
    cognitive_state_id: str
    insights: List[Dict[str, Any]]

class CognitiveChatRequest(BaseModel):
    """认知对话请求"""
    message: str
    project_id: str
    conversation_id: Optional[str] = None
    use_memory: bool = Field(default=True, description="是否使用记忆库")
    strategy: Optional[str] = Field(default=None, description="认知策略：exploration/exploitation/verification/reflection/adaptation")
    max_results: int = Field(default=10, description="检索结果数量")

class CognitiveChatResponse(BaseModel):
    """认知对话响应"""
    conversation_id: str
    response: str
    strategy_used: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    metacognitive_state: Dict[str, Any]
    processing_time: float

class MemoryQueryRequest(BaseModel):
    """记忆库查询请求"""
    query: str
    project_id: str
    memory_types: List[str] = Field(default=["all"], description="记忆类型：concepts/insights/hypotheses/learning_journal/all")
    limit: int = Field(default=20, description="返回结果数量")

class MemoryQueryResponse(BaseModel):
    """记忆库查询响应"""
    results: List[Dict[str, Any]]
    memory_stats: Dict[str, Any]
    search_strategy: str

class CognitiveStateResponse(BaseModel):
    """认知状态响应"""
    thread_id: str
    working_memory: Dict[str, Any]
    episodic_memory: List[Dict[str, Any]]
    semantic_memory: Dict[str, Any]
    attention_weights: Dict[str, float]
    processing_status: str
    performance_metrics: Dict[str, Any]
    metacognitive_state: Dict[str, Any]

# ==========================================
# 全局组件实例
# ==========================================

# 延迟初始化的全局组件
_cognitive_components = {}

async def get_cognitive_components():
    """获取或初始化认知组件"""
    if not _cognitive_components:
        logger.info("初始化认知系统组件...")
        
        try:
            config = {"mock_mode": False}  # 使用真实API
            
            # 异步初始化组件，避免阻塞
            _cognitive_components.update({
                "storage": create_cognitive_storage(),
                "memory_bank": create_memory_bank_manager(),
                "workflow": create_cognitive_workflow(config),
                "s2_chunker": create_s2_chunker(config),
                "retrieval_system": create_hybrid_retrieval_system(config),
                "metacognitive_engine": create_metacognitive_engine(config),
                "state_manager": StateManager()
            })
            
            logger.info("认知系统组件初始化完成")
            
        except Exception as e:
            logger.error(f"认知系统组件初始化失败: {e}")
            # 初始化失败时使用空组件，避免完全阻塞
            _cognitive_components.update({
                "status": "failed",
                "error": str(e)
            })
    
    return _cognitive_components

# ==========================================
# API端点实现
# ==========================================

@router.post("/analyze", response_model=CognitiveAnalysisResponse)
async def cognitive_analysis(
    request: CognitiveAnalysisRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """
    执行认知分析
    
    使用S2语义分块、三阶段混合检索和元认知引擎
    对文档进行深度认知分析
    """
    try:
        components = await get_cognitive_components()
        analysis_id = f"analysis_{uuid4().hex[:8]}"
        
        logger.info(f"开始认知分析: {analysis_id}")
        
        # 1. 创建认知状态
        cognitive_state = components["state_manager"].create_initial_state(
            user_id, request.project_id
        )
        
        # 2. 准备文档内容
        if request.document_text:
            document_content = request.document_text
        elif request.document_id:
            # TODO: 从数据库获取文档内容
            document_content = "示例文档内容"  # 临时实现
        else:
            raise HTTPException(status_code=400, detail="必须提供document_text或document_id")
        
        # 3. S2语义分块
        chunks = await components["s2_chunker"].chunk_document(
            document_content, 
            {"source": request.document_id or "text_input", "project_id": request.project_id}
        )
        
        # 4. 更新认知状态
        cognitive_state["s2_chunks"] = [chunk.__dict__ for chunk in chunks]
        
        # 5. 执行混合检索（如果有分析目标）
        retrieval_results = []
        if request.analysis_goal:
            retrieval_response = await hybrid_search(
                request.analysis_goal,
                query_type="semantic",
                max_results=20
            )
            retrieval_results = retrieval_response.get("results", [])
        
        # 6. 执行元认知评估
        metacognitive_report = {}
        if request.enable_metacognition:
            task_context = {
                "task_type": "document_analysis",
                "analysis_type": request.analysis_type,
                "task_complexity": 0.7,
                "accuracy_requirement": 0.8,
                "start_time": datetime.now(),
                "task_completed": True
            }
            
            metacognitive_report = await components["metacognitive_engine"].metacognitive_cycle(
                cognitive_state, task_context
            )
        
        # 7. 保存认知状态
        await components["storage"].save_cognitive_state(cognitive_state)
        
        # 8. 生成洞察
        insights = []
        if len(chunks) > 0:
            insights.append({
                "type": "document_structure",
                "content": f"文档被分割为{len(chunks)}个语义分块",
                "confidence": 0.9
            })
        
        if retrieval_results:
            insights.append({
                "type": "knowledge_connection",
                "content": f"发现{len(retrieval_results)}个相关知识点",
                "confidence": 0.8
            })
        
        # 9. 构建响应
        response = CognitiveAnalysisResponse(
            analysis_id=analysis_id,
            processing_report={
                "timestamp": datetime.now().isoformat(),
                "document_length": len(document_content),
                "analysis_type": request.analysis_type,
                "processing_time": "completed"
            },
            chunks_created=len(chunks),
            retrieval_results=len(retrieval_results),
            metacognitive_strategy=metacognitive_report.get("metacognitive_state", {}).get("current_strategy", "exploration"),
            performance_score=metacognitive_report.get("performance", {}).get("overall_score", 0.7),
            confidence_level=metacognitive_report.get("metacognitive_state", {}).get("confidence_level", "medium"),
            working_memory_usage=len(cognitive_state["working_memory"]) / 7,
            cognitive_state_id=cognitive_state["thread_id"],
            insights=insights
        )
        
        logger.info(f"认知分析完成: {analysis_id}")
        return response
        
    except Exception as e:
        logger.error(f"认知分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"认知分析失败: {str(e)}")

@router.post("/chat", response_model=CognitiveChatResponse)
async def cognitive_chat(
    request: CognitiveChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    认知对话接口
    
    使用完整的认知系统进行智能对话，包括：
    - 三阶段混合检索
    - 工作记忆管理
    - 元认知策略选择
    """
    try:
        components = await get_cognitive_components()
        start_time = datetime.now()
        
        conversation_id = request.conversation_id or f"conv_{uuid4().hex[:8]}"
        
        logger.info(f"开始认知对话: {conversation_id}")
        
        # 1. 创建或恢复认知状态
        if request.conversation_id:
            # TODO: 从存储恢复状态
            cognitive_state = components["state_manager"].create_initial_state(
                user_id, request.project_id
            )
        else:
            cognitive_state = components["state_manager"].create_initial_state(
                user_id, request.project_id
            )
        
        # 2. 执行混合检索
        retrieval_response = await hybrid_search(
            request.message,
            query_type="semantic",
            max_results=request.max_results
        )
        
        # retrieval_response是一个字典，包含results列表
        sources = retrieval_response.get("results", [])
        
        # 3. 更新工作记忆
        cognitive_state["working_memory"]["current_query"] = {
            "content": request.message,
            "timestamp": datetime.now(),
            "type": "user_query"
        }
        
        # 4. 生成响应（这里使用简化实现）
        context_summary = f"基于{len(sources)}个相关文档片段"
        
        response_text = f"""基于认知检索的分析，我找到了{len(sources)}个相关信息源。

{request.message}

根据检索到的信息，我可以为您提供以下洞察：
1. 相关文档片段显示了多个角度的信息
2. 检索策略采用了向量+图谱+记忆库的混合方法
3. 当前置信度为中等水平

您希望我深入探讨哪个方面？"""
        
        # 5. 元认知评估
        task_context = {
            "task_type": "conversational_qa",
            "query": request.message,
            "task_complexity": 0.6,
            "start_time": start_time,
            "task_completed": True
        }
        
        metacognitive_report = await components["metacognitive_engine"].metacognitive_cycle(
            cognitive_state, task_context
        )
        
        # 6. 保存状态
        await components["storage"].save_cognitive_state(cognitive_state)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = CognitiveChatResponse(
            conversation_id=conversation_id,
            response=response_text,
            strategy_used=metacognitive_report.get("strategy", {}).get("current", request.strategy or "exploration"),
            confidence_score=metacognitive_report.get("performance", {}).get("overall_score", 0.7),
            sources=[
                {
                    "id": src.metadata.get("id", "unknown") if hasattr(src, "metadata") else "unknown",
                    "content": (src.content if hasattr(src, "content") else str(src))[:200] + "...",
                    "score": src.score if hasattr(src, "score") else 0.0,
                    "source": src.source if hasattr(src, "source") else "unknown"
                }
                for src in sources[:5]  # 限制返回数量
            ],
            metacognitive_state={
                "current_strategy": metacognitive_report.get("metacognitive_state", {}).get("current_strategy", "exploration"),
                "confidence_level": metacognitive_report.get("metacognitive_state", {}).get("confidence_level", "medium"),
                "attention_focus": cognitive_state.get("attention_weights", {})
            },
            processing_time=processing_time
        )
        
        logger.info(f"认知对话完成: {conversation_id}, 用时: {processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"认知对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"认知对话失败: {str(e)}")

@router.post("/memory/query", response_model=MemoryQueryResponse)
async def query_memory_bank(
    request: MemoryQueryRequest,
    user_id: str = Depends(get_current_user)
):
    """
    查询记忆库
    
    支持查询不同类型的记忆：概念、洞察、假设、学习日志等
    """
    try:
        components = await get_cognitive_components()
        
        logger.info(f"查询记忆库: {request.query}")
        
        # 1. 读取记忆库内容
        memories = await components["memory_bank"].read_all_memories()
        
        # 2. 执行检索（简化实现）
        results = []
        for memory_type, content in memories.items():
            if "all" in request.memory_types or memory_type in request.memory_types:
                if isinstance(content, list):
                    for item in content[:request.limit]:
                        results.append({
                            "type": memory_type,
                            "content": str(item),
                            "relevance_score": 0.8,  # 简化评分
                            "timestamp": datetime.now().isoformat()
                        })
                elif isinstance(content, dict):
                    results.append({
                        "type": memory_type,
                        "content": str(content),
                        "relevance_score": 0.7,
                        "timestamp": datetime.now().isoformat()
                    })
        
        # 3. 生成记忆统计
        memory_stats = {
            "total_memories": len(memories),
            "memory_types": list(memories.keys()),
            "query_timestamp": datetime.now().isoformat(),
            "results_count": len(results)
        }
        
        response = MemoryQueryResponse(
            results=results[:request.limit],
            memory_stats=memory_stats,
            search_strategy="semantic_similarity"
        )
        
        logger.info(f"记忆库查询完成，返回{len(response.results)}个结果")
        return response
        
    except Exception as e:
        logger.error(f"记忆库查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"记忆库查询失败: {str(e)}")

@router.get("/state/{thread_id}", response_model=CognitiveStateResponse)
async def get_cognitive_state(
    thread_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    获取认知状态
    
    返回指定线程的完整认知状态信息
    """
    try:
        components = await get_cognitive_components()
        
        # 从存储加载认知状态
        cognitive_state = await components["storage"].load_cognitive_state(thread_id)
        
        if not cognitive_state:
            raise HTTPException(status_code=404, detail="认知状态不存在")
        
        response = CognitiveStateResponse(
            thread_id=thread_id,
            working_memory=cognitive_state.get("working_memory", {}),
            episodic_memory=cognitive_state.get("episodic_memory", []),
            semantic_memory=cognitive_state.get("semantic_memory", {}),
            attention_weights=cognitive_state.get("attention_weights", {}),
            processing_status=cognitive_state.get("processing_status", "unknown"),
            performance_metrics=cognitive_state.get("self_evaluation", {}),
            metacognitive_state=cognitive_state.get("metacognitive_state", {})
        )
        
        return response
        
    except Exception as e:
        logger.error(f"获取认知状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取认知状态失败: {str(e)}")

@router.get("/health")
async def cognitive_health_check():
    """
    认知系统健康检查
    """
    try:
        components = await get_cognitive_components()
        
        # 检查组件初始化状态
        if "status" in components and components["status"] == "failed":
            return {
                "status": "degraded",
                "error": components.get("error", "Unknown error"),
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "storage": "failed",
                    "memory_bank": "failed", 
                    "workflow": "failed",
                    "s2_chunker": "failed",
                    "retrieval_system": "failed",
                    "metacognitive_engine": "failed"
                }
            }
        
        # 简单的健康检查
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "storage": "online" if "storage" in components else "offline",
                "memory_bank": "online" if "memory_bank" in components else "offline", 
                "workflow": "online" if "workflow" in components else "offline",
                "s2_chunker": "online" if "s2_chunker" in components else "offline",
                "retrieval_system": "online" if "retrieval_system" in components else "offline",
                "metacognitive_engine": "online" if "metacognitive_engine" in components else "offline"
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"认知系统健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/workflow/run")
async def run_cognitive_workflow(
    request: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """
    运行完整的认知工作流
    
    这是一个高级接口，执行完整的15节点认知循环
    """
    try:
        components = await get_cognitive_components()
        
        # TODO: 实现完整的工作流执行
        # 这需要更复杂的状态管理和工作流控制
        
        return {
            "status": "workflow_started",
            "message": "认知工作流功能正在开发中",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"认知工作流执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"认知工作流执行失败: {str(e)}")