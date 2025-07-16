"""
AAG (Analysis-Augmented Generation) API Routes
基于分析增强生成的API端点
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, Header
from pydantic import BaseModel, Field
from datetime import datetime
import time

from ...aag.agents import (
    SkimmerAgent, ProgressiveSummaryAgent, SummaryLevel, 
    KnowledgeGraphAgent, OutlineAgent, DeepAnalyzer, AnalysisType,
    PlannerAgent, AnalysisGoal
)
from ...aag.storage import ArtifactStore, MetadataManager
from ...aag.engines import (
    OrchestrationEngine, WorkflowNode, WorkflowEdge,
    ExecutionMode
)
from ...database.postgresql import get_session
from ..middleware.auth import get_current_user
from ...utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/aag", tags=["AAG分析"])


class SkimRequest(BaseModel):
    """快速略读请求"""
    document_id: str = Field(..., description="文档ID")
    document_content: str = Field(..., description="文档内容")
    document_type: Optional[str] = Field(None, description="文档类型")


class SkimResponse(BaseModel):
    """快速略读响应"""
    success: bool
    document_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisTaskRequest(BaseModel):
    """分析任务请求"""
    document_id: str = Field(..., description="文档ID")
    analysis_type: str = Field(..., description="分析类型")
    analysis_depth: Optional[str] = Field("standard", description="分析深度")
    analysis_goals: Optional[List[str]] = Field(None, description="分析目标")
    execution_mode: Optional[str] = Field("async", description="执行模式: async|sync")


class AnalysisTaskResponse(BaseModel):
    """分析任务响应"""
    task_id: str
    document_id: str
    status: str
    estimated_time: Optional[int] = None
    estimated_cost: Optional[float] = None


class ProgressiveSummaryRequest(BaseModel):
    """渐进式摘要请求"""
    document_id: str = Field(..., description="文档ID")
    document_content: str = Field(..., description="文档内容")
    summary_level: str = Field("level_2", description="摘要级别：level_1到level_5")
    previous_summaries: Optional[Dict[str, str]] = Field(None, description="之前级别的摘要")


class ProgressiveSummaryResponse(BaseModel):
    """渐进式摘要响应"""
    success: bool
    document_id: str
    summary_level: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class KnowledgeGraphRequest(BaseModel):
    """知识图谱构建请求"""
    document_id: str = Field(..., description="文档ID")
    document_content: str = Field(..., description="文档内容")
    extraction_mode: str = Field("comprehensive", description="提取模式：quick|focused|comprehensive")
    focus_types: Optional[List[str]] = Field(None, description="聚焦提取的实体类型")


class KnowledgeGraphResponse(BaseModel):
    """知识图谱构建响应"""
    success: bool
    document_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OutlineRequest(BaseModel):
    """多维大纲提取请求"""
    document_id: str = Field(..., description="文档ID")
    document_content: str = Field(..., description="文档内容")
    dimension: str = Field("all", description="大纲维度：logical|thematic|temporal|causal|all")


class OutlineResponse(BaseModel):
    """多维大纲提取响应"""
    success: bool
    document_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeepAnalysisRequest(BaseModel):
    """深度分析请求"""
    document_id: str = Field(..., description="文档ID")
    document_content: str = Field(..., description="文档内容")
    analysis_types: Optional[List[str]] = Field(None, description="要执行的分析类型列表")
    focus_claims: Optional[List[str]] = Field(None, description="证据链分析的聚焦声明")
    reference_docs: Optional[List[str]] = Field(None, description="交叉引用分析的参考文档")
    analysis_depth: Optional[str] = Field("deep", description="批判性思维分析深度")


class DeepAnalysisResponse(BaseModel):
    """深度分析响应"""
    success: bool
    document_id: str
    analyses: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisPlanRequest(BaseModel):
    """分析规划请求"""
    document_id: str = Field(..., description="文档ID")
    document_content: str = Field(..., description="文档内容")
    analysis_goal: Optional[str] = Field("deep_understanding", description="分析目标")
    user_requirements: Optional[str] = Field(None, description="用户特定需求")
    time_budget: Optional[int] = Field(300, description="时间预算（秒）")
    cost_budget: Optional[float] = Field(1.0, description="成本预算（美元）")


class AnalysisPlanResponse(BaseModel):
    """分析规划响应"""
    success: bool
    document_id: str
    plan: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PlanProgressRequest(BaseModel):
    """计划进度请求"""
    document_id: str = Field(..., description="文档ID")
    plan: Dict[str, Any] = Field(..., description="原始分析计划")
    completed_analyses: List[str] = Field(..., description="已完成的分析列表")


@router.post("/skim", response_model=SkimResponse)
async def quick_skim(
    skim_request: SkimRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    对文档进行快速略读
    
    - 快速提取文档核心信息
    - 评估文档质量
    - 推荐后续分析方向
    """
    try:
        # 初始化Agent和存储
        skimmer = SkimmerAgent()
        artifact_store = ArtifactStore()
        metadata_manager = MetadataManager()
        
        # 执行略读
        result = await skimmer.process({
            "document_content": skim_request.document_content,
            "document_type": skim_request.document_type
        })
        
        if result["success"]:
            # 保存略读结果到物料库
            artifact_id = await artifact_store.save_artifact(
                document_id=skim_request.document_id,
                analysis_type="skim",
                content=result["result"],
                execution_time_seconds=int(result["metadata"]["duration"]),
                token_usage=result["metadata"]["tokens_used"],
                model_used=skimmer.model_name,
                created_by=current_user
            )
            
            # 创建或更新元数据
            existing_metadata = await metadata_manager.get_metadata(skim_request.document_id)
            
            if not existing_metadata:
                # 创建新的元数据
                target_audience = result["result"].get("target_audience", [])
                # 确保target_audience是列表格式
                if isinstance(target_audience, str):
                    target_audience = [audience.strip() for audience in target_audience.split("、") if audience.strip()]
                elif not isinstance(target_audience, list):
                    target_audience = []
                    
                await metadata_manager.create_metadata(
                    document_id=skim_request.document_id,
                    skim_summary=result["result"],
                    document_type=result["result"].get("document_type"),
                    quality_score=_calculate_quality_score(result["result"]),
                    target_audience=target_audience
                )
            else:
                # 更新现有元数据
                target_audience = result["result"].get("target_audience", [])
                # 确保target_audience是列表格式
                if isinstance(target_audience, str):
                    target_audience = [audience.strip() for audience in target_audience.split("、") if audience.strip()]
                elif not isinstance(target_audience, list):
                    target_audience = []
                    
                await metadata_manager.update_metadata(
                    document_id=skim_request.document_id,
                    updates={
                        "skim_summary": result["result"],
                        "document_type": result["result"].get("document_type"),
                        "quality_score": _calculate_quality_score(result["result"]),
                        "target_audience": target_audience
                    }
                )
            
            # 更新文档标记
            background_tasks.add_task(
                _update_document_flags,
                skim_request.document_id,
                has_skim_summary=True
            )
            
            # 增加计数器
            await metadata_manager.increment_counters(
                document_id=skim_request.document_id,
                analyses=1,
                artifacts=1,
                tokens=result["metadata"]["tokens_used"]
            )
            
            return SkimResponse(
                success=True,
                document_id=skim_request.document_id,
                result=result["result"],
                metadata={
                    "artifact_id": artifact_id,
                    "duration": result["metadata"]["duration"],
                    "tokens_used": result["metadata"]["tokens_used"]
                }
            )
        else:
            return SkimResponse(
                success=False,
                document_id=skim_request.document_id,
                error=result.get("error", "略读失败")
            )
            
    except Exception as e:
        logger.error(f"Skim failed for document {skim_request.document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"略读失败: {str(e)}"
        )


@router.post("/summary", response_model=ProgressiveSummaryResponse)
async def progressive_summary(
    summary_request: ProgressiveSummaryRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    生成渐进式摘要
    
    - 支持5个级别：从50字到2000字
    - 可以提供之前级别的摘要作为参考
    - 结果会保存到分析物料库
    """
    try:
        # 初始化Agent和存储
        summarizer = ProgressiveSummaryAgent()
        artifact_store = ArtifactStore()
        metadata_manager = MetadataManager()
        
        # 执行摘要生成
        result = await summarizer.process({
            "document_content": summary_request.document_content,
            "document_id": summary_request.document_id,
            "summary_level": summary_request.summary_level,
            "previous_summaries": summary_request.previous_summaries or {}
        })
        
        if result["success"]:
            # 保存摘要结果到物料库
            artifact_id = await artifact_store.save_artifact(
                document_id=summary_request.document_id,
                analysis_type="progressive_summary",
                content=result["result"],
                depth_level=summary_request.summary_level,
                execution_time_seconds=int(result["metadata"]["duration"]),
                token_usage=result["metadata"]["tokens_used"],
                model_used=summarizer.model_name,
                created_by=current_user
            )
            
            # 更新元数据
            await metadata_manager.update_metadata(
                document_id=summary_request.document_id,
                updates={
                    f"summary_{summary_request.summary_level}": result["result"]["summary"],
                    "last_summary_level": summary_request.summary_level
                }
            )
            
            # 增加计数器
            await metadata_manager.increment_counters(
                document_id=summary_request.document_id,
                analyses=1,
                artifacts=1,
                tokens=result["metadata"]["tokens_used"]
            )
            
            return ProgressiveSummaryResponse(
                success=True,
                document_id=summary_request.document_id,
                summary_level=summary_request.summary_level,
                result=result["result"],
                metadata={
                    "artifact_id": artifact_id,
                    "duration": result["metadata"]["duration"],
                    "tokens_used": result["metadata"]["tokens_used"],
                    "from_cache": result["metadata"].get("from_cache", False)
                }
            )
        else:
            return ProgressiveSummaryResponse(
                success=False,
                document_id=summary_request.document_id,
                summary_level=summary_request.summary_level,
                error=result.get("error", "摘要生成失败")
            )
            
    except Exception as e:
        logger.error(f"Summary failed for document {summary_request.document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"摘要生成失败: {str(e)}"
        )


@router.post("/summary/all", response_model=Dict[str, ProgressiveSummaryResponse])
async def generate_all_summaries(
    summary_request: ProgressiveSummaryRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    生成所有级别的摘要
    
    - 从Level 1到Level 5依次生成
    - 每个级别会参考之前的摘要
    - 返回所有级别的摘要结果
    """
    try:
        summarizer = ProgressiveSummaryAgent()
        all_summaries = await summarizer.generate_all_levels(
            document_content=summary_request.document_content,
            document_id=summary_request.document_id
        )
        
        # 构建响应
        responses = {}
        for level, summary_result in all_summaries.items():
            responses[level] = ProgressiveSummaryResponse(
                success=True,
                document_id=summary_request.document_id,
                summary_level=level,
                result=summary_result,
                metadata={
                    "word_count": summary_result.get("word_count", 0)
                }
            )
        
        return responses
        
    except Exception as e:
        logger.error(f"Generate all summaries failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成全部摘要失败: {str(e)}"
        )


@router.get("/artifacts/{document_id}")
async def get_document_artifacts(
    document_id: str,
    analysis_type: Optional[str] = None,
    depth_level: Optional[str] = None,
    limit: int = 50,
    current_user: str = Depends(get_current_user)
):
    """
    获取文档的分析物料
    
    - 支持按类型和深度过滤
    - 返回最新的分析结果
    """
    try:
        artifact_store = ArtifactStore()
        artifacts = await artifact_store.get_document_artifacts(
            document_id=document_id,
            analysis_type=analysis_type,
            depth_level=depth_level,
            limit=limit
        )
        
        return {
            "document_id": document_id,
            "total": len(artifacts),
            "artifacts": artifacts
        }
        
    except Exception as e:
        logger.error(f"Failed to get artifacts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取物料失败: {str(e)}"
        )


@router.get("/metadata/{document_id}")
async def get_document_metadata(
    document_id: str,
    version: Optional[int] = None,
    current_user: str = Depends(get_current_user)
):
    """
    获取文档元数据
    
    - 包含略读摘要、质量评分等
    - 支持版本查询
    """
    try:
        metadata_manager = MetadataManager()
        metadata = await metadata_manager.get_metadata(
            document_id=document_id,
            version=version
        )
        
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="元数据不存在"
            )
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取元数据失败: {str(e)}"
        )


@router.post("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def build_knowledge_graph(
    graph_request: KnowledgeGraphRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    构建知识图谱
    
    - 提取实体和关系
    - 支持三种模式：quick（快速）、focused（聚焦）、comprehensive（全面）
    - 结果保存到分析物料库
    """
    try:
        # 初始化Agent和存储
        kg_agent = KnowledgeGraphAgent()
        artifact_store = ArtifactStore()
        metadata_manager = MetadataManager()
        
        # 构建输入数据
        input_data = {
            "document_content": graph_request.document_content,
            "document_id": graph_request.document_id,
            "extraction_mode": graph_request.extraction_mode
        }
        
        if graph_request.focus_types:
            input_data["focus_types"] = graph_request.focus_types
        
        # 执行知识图谱构建
        result = await kg_agent.process(input_data)
        
        if result["success"]:
            # 保存结果到物料库
            artifact_id = await artifact_store.save_artifact(
                document_id=graph_request.document_id,
                analysis_type="knowledge_graph",
                content=result["result"],
                depth_level=graph_request.extraction_mode,
                execution_time_seconds=int(result["metadata"]["duration"]),
                token_usage=result["metadata"]["tokens_used"],
                model_used=kg_agent.model_name,
                created_by=current_user
            )
            
            # 更新元数据
            kg_stats = result["result"]["statistics"]
            await metadata_manager.update_metadata(
                document_id=graph_request.document_id,
                updates={
                    "has_knowledge_graph": True,
                    "entity_count": kg_stats["total_entities"],
                    "relation_count": kg_stats["total_relations"],
                    "core_entities": kg_stats.get("core_entities", [])
                }
            )
            
            # 增加计数器
            await metadata_manager.increment_counters(
                document_id=graph_request.document_id,
                analyses=1,
                artifacts=1,
                tokens=result["metadata"]["tokens_used"]
            )
            
            return KnowledgeGraphResponse(
                success=True,
                document_id=graph_request.document_id,
                result=result["result"],
                metadata={
                    "artifact_id": artifact_id,
                    "duration": result["metadata"]["duration"],
                    "tokens_used": result["metadata"]["tokens_used"],
                    "extraction_mode": graph_request.extraction_mode,
                    "from_cache": result["metadata"].get("from_cache", False)
                }
            )
        else:
            return KnowledgeGraphResponse(
                success=False,
                document_id=graph_request.document_id,
                error=result.get("error", "知识图谱构建失败")
            )
            
    except Exception as e:
        logger.error(f"Knowledge graph failed for document {graph_request.document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识图谱构建失败: {str(e)}"
        )


@router.post("/knowledge-graph/export")
async def export_knowledge_graph(
    document_id: str,
    export_format: str = "neo4j",
    current_user: str = Depends(get_current_user)
):
    """
    导出知识图谱
    
    - 支持导出格式：neo4j（Cypher语句）、json、graphml
    """
    try:
        artifact_store = ArtifactStore()
        
        # 获取最新的知识图谱物料
        artifacts = await artifact_store.get_document_artifacts(
            document_id=document_id,
            analysis_type="knowledge_graph",
            limit=1
        )
        
        if not artifacts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该文档尚未构建知识图谱"
            )
        
        kg_data = artifacts[0]["content"]
        entities = kg_data.get("entities", [])
        relations = kg_data.get("relations", [])
        
        if export_format == "neo4j":
            # 导出为Neo4j Cypher语句
            kg_agent = KnowledgeGraphAgent()
            export_data = await kg_agent.export_to_neo4j_format(entities, relations)
            
            return {
                "format": "neo4j",
                "document_id": document_id,
                "data": export_data
            }
        elif export_format == "json":
            # 直接返回JSON格式
            return {
                "format": "json",
                "document_id": document_id,
                "data": {
                    "entities": entities,
                    "relations": relations,
                    "statistics": kg_data.get("statistics", {})
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的导出格式: {export_format}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export knowledge graph failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出知识图谱失败: {str(e)}"
        )


@router.post("/outline", response_model=OutlineResponse)
async def extract_outline(
    outline_request: OutlineRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    提取多维度文档大纲
    
    - 支持四个维度：逻辑、主题、时间、因果
    - 可单独提取某个维度或同时提取所有维度
    - 结果保存到分析物料库
    """
    try:
        # 初始化Agent和存储
        outline_agent = OutlineAgent()
        artifact_store = ArtifactStore()
        metadata_manager = MetadataManager()
        
        # 执行大纲提取
        result = await outline_agent.process({
            "document_content": outline_request.document_content,
            "document_id": outline_request.document_id,
            "dimension": outline_request.dimension
        })
        
        if result["success"]:
            # 保存结果到物料库
            artifact_id = await artifact_store.save_artifact(
                document_id=outline_request.document_id,
                analysis_type="multi_dimensional_outline",
                content=result["result"],
                depth_level=outline_request.dimension,
                execution_time_seconds=int(result["metadata"]["duration"]),
                token_usage=result["metadata"]["tokens_used"],
                model_used=outline_agent.model_name,
                created_by=current_user
            )
            
            # 更新元数据
            outline_summary = result["result"].get("summary", "多维度大纲提取完成")
            await metadata_manager.update_metadata(
                document_id=outline_request.document_id,
                updates={
                    "has_outline": True,
                    "outline_dimension": outline_request.dimension,
                    "outline_summary": outline_summary
                }
            )
            
            # 增加计数器
            await metadata_manager.increment_counters(
                document_id=outline_request.document_id,
                analyses=1,
                artifacts=1,
                tokens=result["metadata"]["tokens_used"]
            )
            
            return OutlineResponse(
                success=True,
                document_id=outline_request.document_id,
                result=result["result"],
                metadata={
                    "artifact_id": artifact_id,
                    "duration": result["metadata"]["duration"],
                    "tokens_used": result["metadata"]["tokens_used"],
                    "dimension": outline_request.dimension,
                    "from_cache": result["metadata"].get("from_cache", False)
                }
            )
        else:
            return OutlineResponse(
                success=False,
                document_id=outline_request.document_id,
                error=result.get("error", "大纲提取失败")
            )
            
    except Exception as e:
        logger.error(f"Outline extraction failed for document {outline_request.document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"大纲提取失败: {str(e)}"
        )


@router.post("/outline/structure-analysis")
async def analyze_structure(
    document_id: str,
    document_content: str,
    current_user: str = Depends(get_current_user)
):
    """
    执行完整的文档结构分析
    
    - 提取所有维度的大纲
    - 分析大纲间的关系
    - 生成结构洞察和建议
    """
    try:
        outline_agent = OutlineAgent()
        
        # 执行结构分析
        result = await outline_agent.analyze_document_structure(
            document_content=document_content,
            document_id=document_id
        )
        
        if result["success"]:
            return {
                "success": True,
                "document_id": document_id,
                "analysis": result["result"],
                "metadata": result["metadata"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "结构分析失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Structure analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"结构分析失败: {str(e)}"
        )


@router.post("/analyze", response_model=AnalysisTaskResponse)
async def create_analysis_task(
    request: AnalysisTaskRequest,
    current_user: str = Depends(get_current_user)
):
    """
    创建分析任务
    
    - 支持多种分析类型
    - 可选同步或异步执行
    """
    # TODO: 实现完整的分析任务创建逻辑
    # 这里先返回一个模拟响应
    return AnalysisTaskResponse(
        task_id="task_" + str(datetime.now().timestamp()),
        document_id=request.document_id,
        status="pending",
        estimated_time=300,
        estimated_cost=0.05
    )


@router.post("/deep-analysis", response_model=DeepAnalysisResponse)
async def deep_analysis(
    analysis_request: DeepAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    执行深度分析
    
    - 支持三种分析类型：证据链、交叉引用、批判性思维
    - 可以选择执行部分或全部分析
    - 结果保存到分析物料库
    """
    try:
        # 初始化深度分析器
        deep_analyzer = DeepAnalyzer()
        metadata_manager = MetadataManager()
        
        # 执行深度分析
        result = await deep_analyzer.analyze(
            document_content=analysis_request.document_content,
            document_id=analysis_request.document_id,
            analysis_types=analysis_request.analysis_types,
            focus_claims=analysis_request.focus_claims,
            reference_docs=analysis_request.reference_docs,
            analysis_depth=analysis_request.analysis_depth
        )
        
        if result["success"]:
            # 更新元数据
            await metadata_manager.update_metadata(
                document_id=analysis_request.document_id,
                updates={
                    "has_deep_analysis": True,
                    "deep_analysis_types": list(result["analyses"].keys()),
                    "deep_analysis_count": result["metadata"]["analysis_count"]
                }
            )
            
            # 增加计数器
            await metadata_manager.increment_counters(
                document_id=analysis_request.document_id,
                analyses=result["metadata"]["analysis_count"],
                artifacts=result["metadata"]["analysis_count"],
                tokens=result["metadata"]["total_tokens"]
            )
            
            return DeepAnalysisResponse(
                success=True,
                document_id=analysis_request.document_id,
                analyses=result["analyses"],
                metadata={
                    "duration": result["metadata"]["total_duration"],
                    "tokens_used": result["metadata"]["total_tokens"],
                    "analysis_count": result["metadata"]["analysis_count"]
                }
            )
        else:
            return DeepAnalysisResponse(
                success=False,
                document_id=analysis_request.document_id,
                error="深度分析失败"
            )
            
    except Exception as e:
        logger.error(f"Deep analysis failed for document {analysis_request.document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"深度分析失败: {str(e)}"
        )


@router.post("/deep-analysis/evidence-chain", response_model=DeepAnalysisResponse)
async def evidence_chain_analysis(
    document_id: str,
    document_content: str,
    focus_claims: Optional[List[str]] = None,
    current_user: str = Depends(get_current_user)
):
    """
    执行证据链跟踪分析
    
    - 分析文档中的声明和证据
    - 评估证据的强度和完整性
    - 识别证据链中的薄弱环节
    """
    try:
        from ...aag.agents.analyzer import EvidenceChainAnalyzer
        
        analyzer = EvidenceChainAnalyzer()
        result = await analyzer.process({
            "document_content": document_content,
            "document_id": document_id,
            "focus_claims": focus_claims or []
        })
        
        if result["success"]:
            return DeepAnalysisResponse(
                success=True,
                document_id=document_id,
                analyses={"evidence_chain": result["result"]},
                metadata=result["metadata"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "证据链分析失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evidence chain analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"证据链分析失败: {str(e)}"
        )


@router.post("/deep-analysis/cross-reference", response_model=DeepAnalysisResponse)
async def cross_reference_analysis(
    document_id: str,
    document_content: str,
    reference_docs: Optional[List[str]] = None,
    current_user: str = Depends(get_current_user)
):
    """
    执行交叉引用分析
    
    - 分析文档内部引用关系
    - 检查概念一致性
    - 评估引用网络结构
    """
    try:
        from ...aag.agents.analyzer import CrossReferenceAnalyzer
        
        analyzer = CrossReferenceAnalyzer()
        result = await analyzer.process({
            "document_content": document_content,
            "document_id": document_id,
            "reference_docs": reference_docs or []
        })
        
        if result["success"]:
            return DeepAnalysisResponse(
                success=True,
                document_id=document_id,
                analyses={"cross_reference": result["result"]},
                metadata=result["metadata"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "交叉引用分析失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cross reference analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"交叉引用分析失败: {str(e)}"
        )


@router.post("/deep-analysis/critical-thinking", response_model=DeepAnalysisResponse)
async def critical_thinking_analysis(
    document_id: str,
    document_content: str,
    analysis_depth: str = "deep",
    current_user: str = Depends(get_current_user)
):
    """
    执行批判性思维分析
    
    - 评估论证逻辑
    - 识别假设和偏见
    - 提供替代视角
    """
    try:
        from ...aag.agents.analyzer import CriticalThinkingAnalyzer
        
        analyzer = CriticalThinkingAnalyzer()
        result = await analyzer.process({
            "document_content": document_content,
            "document_id": document_id,
            "analysis_depth": analysis_depth
        })
        
        if result["success"]:
            return DeepAnalysisResponse(
                success=True,
                document_id=document_id,
                analyses={"critical_thinking": result["result"]},
                metadata=result["metadata"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "批判性思维分析失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical thinking analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批判性思维分析失败: {str(e)}"
        )


@router.post("/plan", response_model=AnalysisPlanResponse)
async def create_analysis_plan(
    plan_request: AnalysisPlanRequest,
    current_user: str = Depends(get_current_user)
):
    """
    创建文档分析计划
    
    - 基于文档特征评估
    - 根据目标推荐分析方案
    - 考虑时间和成本预算
    - 提供替代方案
    """
    try:
        # 初始化PlannerAgent
        planner = PlannerAgent()
        
        # 制定分析计划
        result = await planner.process({
            "document_content": plan_request.document_content,
            "document_id": plan_request.document_id,
            "analysis_goal": plan_request.analysis_goal,
            "user_requirements": plan_request.user_requirements,
            "time_budget": plan_request.time_budget,
            "cost_budget": plan_request.cost_budget
        })
        
        if result["success"]:
            return AnalysisPlanResponse(
                success=True,
                document_id=plan_request.document_id,
                plan=result["result"],
                metadata=result["metadata"]
            )
        else:
            return AnalysisPlanResponse(
                success=False,
                document_id=plan_request.document_id,
                error=result.get("error", "分析规划失败")
            )
            
    except Exception as e:
        logger.error(f"Analysis planning failed for document {plan_request.document_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析规划失败: {str(e)}"
        )


@router.post("/plan/progress")
async def evaluate_plan_progress(
    progress_request: PlanProgressRequest,
    current_user: str = Depends(get_current_user)
):
    """
    评估分析计划执行进度
    
    - 计算完成率
    - 识别未完成任务
    - 提供调整建议
    """
    try:
        planner = PlannerAgent()
        
        result = await planner.evaluate_progress(
            document_id=progress_request.document_id,
            plan=progress_request.plan,
            completed_analyses=progress_request.completed_analyses
        )
        
        if result["success"]:
            return {
                "success": True,
                "document_id": progress_request.document_id,
                "progress": result["result"],
                "metadata": result.get("metadata", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "进度评估失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Progress evaluation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"进度评估失败: {str(e)}"
        )


@router.get("/plan/goals")
async def get_analysis_goals(
    current_user: str = Depends(get_current_user)
):
    """
    获取支持的分析目标列表
    """
    return {
        "goals": [
            {
                "value": AnalysisGoal.QUICK_OVERVIEW.value,
                "name": "快速概览",
                "description": "快速了解文档核心内容",
                "typical_time": "1-2分钟",
                "typical_cost": "$0.05-0.10"
            },
            {
                "value": AnalysisGoal.DEEP_UNDERSTANDING.value,
                "name": "深度理解",
                "description": "全面深入分析文档",
                "typical_time": "5-10分钟",
                "typical_cost": "$0.50-1.00"
            },
            {
                "value": AnalysisGoal.CRITICAL_REVIEW.value,
                "name": "批判性审查",
                "description": "评估论证质量和逻辑严密性",
                "typical_time": "3-5分钟",
                "typical_cost": "$0.20-0.40"
            },
            {
                "value": AnalysisGoal.KNOWLEDGE_EXTRACTION.value,
                "name": "知识提取",
                "description": "提取实体、关系和核心概念",
                "typical_time": "2-4分钟",
                "typical_cost": "$0.15-0.30"
            },
            {
                "value": AnalysisGoal.RESEARCH_PLANNING.value,
                "name": "研究规划",
                "description": "为后续研究制定方向",
                "typical_time": "3-5分钟",
                "typical_cost": "$0.20-0.40"
            },
            {
                "value": AnalysisGoal.CUSTOM.value,
                "name": "自定义",
                "description": "根据特定需求定制分析",
                "typical_time": "视需求而定",
                "typical_cost": "视需求而定"
            }
        ]
    }


# 初始化编排引擎
orchestrator = OrchestrationEngine()


# ==================== 编排引擎端点 ====================

@router.post("/workflow/create")
async def create_workflow(
    workflow_id: str,
    name: str,
    description: str,
    user_id: str = Header(..., alias="X-USER-ID")
):
    """
    创建新的分析工作流
    
    Args:
        workflow_id: 工作流ID
        name: 工作流名称  
        description: 工作流描述
        user_id: 用户ID
        
    Returns:
        工作流创建结果
    """
    try:
        workflow_id = orchestrator.create_workflow(
            workflow_id=workflow_id,
            name=name,
            description=description
        )
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": f"工作流 {name} 创建成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建工作流失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建工作流失败")


@router.post("/workflow/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    document_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Header(..., alias="X-USER-ID"),
    initial_state: Optional[Dict[str, Any]] = None
):
    """
    执行分析工作流
    
    Args:
        workflow_id: 工作流ID
        document_id: 文档ID
        user_id: 用户ID
        initial_state: 初始状态
        
    Returns:
        执行结果或任务ID
    """
    # 获取文档内容
    conn = await get_db_connection()
    try:
        document = await conn.fetchrow(
            """
            SELECT d.content, d.file_name, d.project_id
            FROM documents d
            JOIN projects p ON d.project_id = p.id
            WHERE d.id = $1 AND p.user_id = $2
            """,
            document_id, user_id
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
            
        document_content = document["content"]
        
        # 如果文档较大，使用后台任务
        if len(document_content) > 10000:
            task_id = f"workflow_{workflow_id}_{document_id}_{int(time.time())}"
            
            async def run_workflow():
                result = await orchestrator.execute_workflow(
                    workflow_id=workflow_id,
                    document_id=document_id,
                    document_content=document_content,
                    initial_state=initial_state
                )
                # 可以将结果保存到缓存或数据库
                
            background_tasks.add_task(run_workflow)
            
            return {
                "success": True,
                "task_id": task_id,
                "message": "工作流已提交到后台执行"
            }
        else:
            # 小文档直接执行
            result = await orchestrator.execute_workflow(
                workflow_id=workflow_id,
                document_id=document_id,
                document_content=document_content,
                initial_state=initial_state
            )
            return result
            
    finally:
        await return_db_connection(conn)


@router.get("/workflow/templates")
async def get_workflow_templates(
    user_id: str = Header(..., alias="X-USER-ID")
):
    """
    获取预定义的工作流模板
    
    Returns:
        工作流模板列表
    """
    templates = [
        {
            "id": "standard_analysis",
            "name": "标准文档分析",
            "description": "包含略读、摘要、知识图谱的标准分析流程",
            "estimated_time": "3-5分钟",
            "components": ["略读", "摘要生成", "知识图谱", "大纲提取"]
        },
        {
            "id": "critical_review",
            "name": "批判性审查",
            "description": "深度分析文档的论证质量和逻辑严密性",
            "estimated_time": "5-10分钟",
            "components": ["略读", "证据链分析", "批判性思维分析", "交叉引用分析"]
        },
        {
            "id": "adaptive_analysis",
            "name": "自适应分析",
            "description": "根据文档质量动态调整分析深度",
            "estimated_time": "2-8分钟",
            "components": ["略读", "动态摘要", "动态知识图谱"]
        }
    ]
    
    return {"templates": templates}


@router.post("/workflow/template/{template_id}/create")
async def create_workflow_from_template(
    template_id: str,
    user_id: str = Header(..., alias="X-USER-ID")
):
    """
    基于模板创建工作流
    
    Args:
        template_id: 模板ID
        user_id: 用户ID
        
    Returns:
        创建结果
    """
    try:
        if template_id == "standard_analysis":
            workflow_id = orchestrator.create_standard_analysis_workflow()
        elif template_id == "critical_review":
            workflow_id = orchestrator.create_critical_review_workflow()
        elif template_id == "adaptive_analysis":
            workflow_id = orchestrator.create_adaptive_workflow()
        else:
            raise HTTPException(status_code=404, detail="模板不存在")
            
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": f"基于模板 {template_id} 创建工作流成功"
        }
    except Exception as e:
        logger.error(f"基于模板创建工作流失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="创建工作流失败")


def _calculate_quality_score(skim_result: Dict[str, Any]) -> float:
    """
    计算文档质量评分
    
    Args:
        skim_result: 略读结果
        
    Returns:
        质量评分 (0-1)
    """
    quality_assessment = skim_result.get("quality_assessment", {})
    level = quality_assessment.get("level", "中")
    
    score_map = {
        "高": 0.9,
        "中": 0.7,
        "低": 0.4
    }
    
    return score_map.get(level, 0.5)


async def _update_document_flags(document_id: str, **flags):
    """更新文档标记"""
    async with get_session() as session:
        try:
            set_clauses = []
            params = {"document_id": document_id}
            
            for key, value in flags.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
            
            if set_clauses:
                from sqlalchemy import text
                query = f"""
                    UPDATE documents
                    SET {', '.join(set_clauses)}
                    WHERE id = :document_id
                """
                await session.execute(text(query), params)
                await session.commit()
                
        except Exception as e:
            logger.error(f"Failed to update document flags: {str(e)}", exc_info=True)