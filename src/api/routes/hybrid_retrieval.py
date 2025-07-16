"""
混合检索API路由
提供三阶段混合检索服务
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from src.core.retrieval.mvp_hybrid_retriever import (
    create_mvp_hybrid_retriever,
    HybridRetrievalResult,
    RetrievalResult
)
from src.api.middleware.auth import get_current_user
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])


class RetrievalRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本")
    project_id: Optional[str] = Field(None, description="项目ID")
    top_k: int = Field(10, ge=1, le=50, description="返回结果数量")
    score_threshold: float = Field(0.6, ge=0.0, le=1.0, description="分数阈值")
    filters: Optional[Dict[str, Any]] = Field(None, description="额外过滤条件")


class RetrievalResultResponse(BaseModel):
    """检索结果响应"""
    doc_id: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]


class HybridRetrievalResponse(BaseModel):
    """混合检索响应"""
    query: str
    total_results: int
    results: List[RetrievalResultResponse]
    breakdown: Dict[str, int]
    retrieval_time: float
    metadata: Dict[str, Any]


@router.post("/hybrid", response_model=HybridRetrievalResponse)
async def hybrid_retrieval(
    request: RetrievalRequest,
    current_user: str = Depends(get_current_user)
):
    """
    执行三阶段混合检索
    
    包括：
    1. 向量搜索 (Qdrant)
    2. 图谱扩展 (Neo4j)
    3. Memory Bank增强
    """
    try:
        # 创建检索器
        retriever = create_mvp_hybrid_retriever(user_id=current_user)
        
        # 执行检索
        result = await retriever.retrieve(
            query=request.query,
            project_id=request.project_id,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            filters=request.filters
        )
        
        # 转换响应格式
        response_results = [
            RetrievalResultResponse(
                doc_id=r.doc_id,
                content=r.content,
                score=r.score,
                source=r.source,
                metadata=r.metadata
            )
            for r in result.fused_results
        ]
        
        # 统计各来源结果数量
        breakdown = {
            "vector": len(result.vector_results),
            "graph": len(result.graph_results),
            "memory": len(result.memory_results)
        }
        
        return HybridRetrievalResponse(
            query=result.query,
            total_results=result.total_results,
            results=response_results,
            breakdown=breakdown,
            retrieval_time=result.retrieval_time,
            metadata=result.metadata
        )
        
    except Exception as e:
        logger.error(f"Hybrid retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )


@router.post("/vector-only")
async def vector_retrieval(
    request: RetrievalRequest,
    current_user: str = Depends(get_current_user)
):
    """
    仅执行向量检索
    
    用于对比测试
    """
    try:
        retriever = create_mvp_hybrid_retriever(user_id=current_user)
        
        # 生成查询向量
        query_embedding = await retriever.embeddings.aembed_query(request.query)
        
        # 仅执行向量搜索
        vector_results = await retriever._vector_search(
            query_embedding=query_embedding,
            project_id=request.project_id,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            filters=request.filters
        )
        
        return {
            "query": request.query,
            "total_results": len(vector_results),
            "results": [
                {
                    "doc_id": r.doc_id,
                    "content": r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in vector_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Vector retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Vector retrieval failed: {str(e)}"
        )


@router.post("/graph-only")
async def graph_retrieval(
    request: RetrievalRequest,
    current_user: str = Depends(get_current_user)
):
    """
    仅执行图谱检索
    
    用于对比测试
    """
    try:
        retriever = create_mvp_hybrid_retriever(user_id=current_user)
        
        # 仅执行图谱搜索
        graph_results = await retriever._graph_search(
            query=request.query,
            project_id=request.project_id,
            top_k=request.top_k
        )
        
        return {
            "query": request.query,
            "total_results": len(graph_results),
            "results": [
                {
                    "doc_id": r.doc_id,
                    "content": r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in graph_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Graph retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Graph retrieval failed: {str(e)}"
        )


@router.post("/memory-only")
async def memory_retrieval(
    request: RetrievalRequest,
    current_user: str = Depends(get_current_user)
):
    """
    仅执行Memory Bank检索
    
    用于对比测试
    """
    try:
        if not request.project_id:
            raise HTTPException(
                status_code=400,
                detail="Project ID is required for memory retrieval"
            )
            
        retriever = create_mvp_hybrid_retriever(user_id=current_user)
        
        # 仅执行Memory Bank搜索
        memory_results = await retriever._memory_bank_search(
            query=request.query,
            project_id=request.project_id
        )
        
        return {
            "query": request.query,
            "total_results": len(memory_results),
            "results": [
                {
                    "doc_id": r.doc_id,
                    "content": r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in memory_results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Memory retrieval failed: {str(e)}"
        )


@router.get("/test-connection")
async def test_retrieval_connections(
    current_user: str = Depends(get_current_user)
):
    """
    测试检索系统各组件连接状态
    """
    try:
        retriever = create_mvp_hybrid_retriever(user_id=current_user)
        
        status = {
            "qdrant": "unknown",
            "neo4j": "unknown",
            "memory_bank": "unknown"
        }
        
        # 测试Qdrant
        try:
            collections = await retriever.qdrant_manager.list_collections()
            status["qdrant"] = "connected" if collections else "no_collections"
        except Exception as e:
            status["qdrant"] = f"error: {str(e)}"
            
        # 测试Neo4j
        try:
            result = await retriever.neo4j_manager.execute_query("RETURN 1 as test")
            status["neo4j"] = "connected" if result else "error"
        except Exception as e:
            status["neo4j"] = f"error: {str(e)}"
            
        # 测试Memory Bank
        try:
            test_project = "test_connection"
            snapshot = await retriever.memory_bank_manager.get_snapshot(test_project)
            status["memory_bank"] = "connected"
        except Exception as e:
            status["memory_bank"] = f"error: {str(e)}"
            
        return {
            "status": "ok" if all(v.startswith("connected") for v in status.values()) else "degraded",
            "components": status,
            "user_id": current_user
        }
        
    except Exception as e:
        logger.error(f"Connection test error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )