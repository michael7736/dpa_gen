"""
文档深度分析API端点
提供基于大语言模型的六阶段文档分析服务
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session
from ...graphs.document_analysis_workflow import DocumentAnalysisWorkflow, AnalysisStage
from ...templates.analysis_prompts import AnalysisPrompts
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    """文档分析请求"""
    document_id: str = Field(..., description="文档ID")
    project_id: str = Field(..., description="项目ID")
    user_id: str = Field(..., description="用户ID")
    analysis_goal: str = Field(..., description="分析目标")
    analysis_type: str = Field(
        "comprehensive", 
        description="分析类型：comprehensive/quick/focused"
    )
    focus_areas: Optional[List[str]] = Field(
        None,
        description="重点关注领域"
    )
    output_formats: List[str] = Field(
        ["executive_summary"],
        description="输出格式：executive_summary/detailed_report/action_plan/visualization"
    )


class AnalysisResponse(BaseModel):
    """文档分析响应"""
    analysis_id: str
    status: str
    message: str
    preview: Optional[Dict[str, Any]] = None


class AnalysisStatusResponse(BaseModel):
    """分析状态响应"""
    analysis_id: str
    status: str
    current_stage: Optional[str] = None
    progress: float
    results: Optional[Dict[str, Any]] = None
    errors: List[str] = []


# 存储运行中的分析任务
running_analyses = {}


@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """
    启动文档深度分析
    
    分析流程：
    1. 准备与预处理
    2. 宏观理解
    3. 深度探索
    4. 批判性分析
    5. 知识整合
    6. 成果输出
    """
    try:
        # 生成分析ID
        import uuid
        analysis_id = str(uuid.uuid4())
        
        # 获取文档内容（这里需要从数据库或存储中获取）
        # document_content = await get_document_content(request.document_id)
        document_content = "示例文档内容..."  # 临时示例
        
        # 初始化分析状态
        initial_state = {
            "document_id": request.document_id,
            "project_id": request.project_id,
            "user_id": request.user_id,
            "analysis_goal": request.analysis_goal,
            "document_content": document_content,
            "structured_summary": {},
            "knowledge_graph": {},
            "deep_insights": [],
            "critical_findings": [],
            "integrated_knowledge": {},
            "final_output": {},
            "current_stage": AnalysisStage.PREPARATION,
            "stage_results": {},
            "errors": [],
            "warnings": [],
            "start_time": None,
            "end_time": None,
            "total_tokens_used": 0
        }
        
        # 存储初始状态
        running_analyses[analysis_id] = {
            "status": "running",
            "state": initial_state,
            "progress": 0.0
        }
        
        # 在后台启动分析
        background_tasks.add_task(
            run_analysis_workflow,
            analysis_id,
            initial_state,
            db
        )
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message=f"Analysis started for document {request.document_id}",
            preview={
                "estimated_time": "10-15 minutes",
                "stages": 6,
                "analysis_type": request.analysis_type
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_analysis_workflow(analysis_id: str, initial_state: Dict, db: Session):
    """运行分析工作流（后台任务）"""
    try:
        workflow = DocumentAnalysisWorkflow(db)
        
        # 更新进度回调
        def update_progress(stage: str, progress: float):
            if analysis_id in running_analyses:
                running_analyses[analysis_id]["progress"] = progress
                running_analyses[analysis_id]["current_stage"] = stage
        
        # 运行工作流
        result = await workflow.app.ainvoke(initial_state)
        
        # 更新最终状态
        running_analyses[analysis_id] = {
            "status": "completed",
            "state": result,
            "progress": 100.0,
            "current_stage": "completed"
        }
        
    except Exception as e:
        logger.error(f"Analysis workflow error: {e}")
        if analysis_id in running_analyses:
            running_analyses[analysis_id]["status"] = "failed"
            running_analyses[analysis_id]["state"]["errors"].append(str(e))


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str):
    """
    获取分析状态
    
    返回当前分析进度和部分结果
    """
    if analysis_id not in running_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = running_analyses[analysis_id]
    state = analysis.get("state", {})
    
    # 根据状态准备响应
    response = AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=analysis["status"],
        current_stage=state.get("current_stage"),
        progress=analysis.get("progress", 0.0),
        errors=state.get("errors", [])
    )
    
    # 如果完成，返回结果
    if analysis["status"] == "completed":
        response.results = {
            "summary": state.get("structured_summary"),
            "key_insights": state.get("integrated_knowledge", {}).get("novel_insights", [])[:5],
            "output": state.get("final_output")
        }
    
    return response


@router.get("/results/{analysis_id}")
async def get_analysis_results(
    analysis_id: str,
    include_details: bool = False
):
    """
    获取完整分析结果
    
    参数：
    - include_details: 是否包含所有中间结果
    """
    if analysis_id not in running_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = running_analyses[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Analysis is still {analysis['status']}"
        )
    
    state = analysis["state"]
    
    # 基础结果
    results = {
        "analysis_id": analysis_id,
        "document_id": state["document_id"],
        "analysis_goal": state["analysis_goal"],
        "executive_summary": state.get("final_output", {}).get("executive_summary"),
        "key_findings": state.get("integrated_knowledge", {}).get("novel_insights", []),
        "recommendations": state.get("integrated_knowledge", {}).get("actionable_recommendations", []),
        "knowledge_graph": state.get("knowledge_graph"),
        "analysis_time": (
            state["end_time"] - state["start_time"]
        ).total_seconds() if state.get("end_time") and state.get("start_time") else None
    }
    
    # 详细结果
    if include_details:
        results["detailed_results"] = {
            "structured_summary": state.get("structured_summary"),
            "deep_insights": state.get("deep_insights"),
            "critical_findings": state.get("critical_findings"),
            "stage_results": state.get("stage_results"),
            "warnings": state.get("warnings")
        }
    
    return results


@router.post("/analyze-text")
async def analyze_text_directly(
    text: str,
    analysis_type: str = "quick",
    user_id: str = "anonymous",
    db: Session = Depends(get_db_session)
):
    """
    直接分析文本（无需先上传文档）
    
    适用于快速分析场景
    """
    try:
        workflow = DocumentAnalysisWorkflow(db)
        
        # 简化的状态
        state = {
            "document_id": "text_analysis",
            "project_id": "default",
            "user_id": user_id,
            "analysis_goal": "Quick text analysis",
            "document_content": text,
            "structured_summary": {},
            "knowledge_graph": {},
            "deep_insights": [],
            "critical_findings": [],
            "integrated_knowledge": {},
            "final_output": {},
            "current_stage": AnalysisStage.PREPARATION,
            "stage_results": {},
            "errors": [],
            "warnings": [],
            "start_time": None,
            "end_time": None,
            "total_tokens_used": 0
        }
        
        # 根据分析类型选择执行的阶段
        if analysis_type == "quick":
            # 只执行宏观理解
            state = await workflow.prepare_document(state)
            state = await workflow.macro_understanding(state)
            
            return {
                "summary": state.get("structured_summary"),
                "knowledge_graph": state.get("knowledge_graph"),
                "key_concepts": list(state.get("knowledge_graph", {}).get("entities", {}).keys())[:10]
            }
        else:
            # 执行完整流程
            result = await workflow.app.ainvoke(state)
            return {
                "summary": result.get("final_output", {}).get("executive_summary"),
                "insights": result.get("integrated_knowledge", {}).get("novel_insights", [])[:5]
            }
            
    except Exception as e:
        logger.error(f"Text analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{category}")
async def get_analysis_prompts(
    category: str,
    prompt_name: Optional[str] = None
):
    """
    获取分析提示词模板
    
    类别：
    - preparation: 准备阶段
    - macro_understanding: 宏观理解
    - deep_exploration: 深度探索
    - critical_analysis: 批判分析
    - knowledge_integration: 知识整合
    - output_generation: 成果输出
    """
    try:
        if prompt_name:
            prompt = AnalysisPrompts.get_prompt(category, prompt_name)
            return {
                "category": category,
                "name": prompt_name,
                "prompt": prompt
            }
        else:
            prompts = AnalysisPrompts.get_all_prompts(category)
            return {
                "category": category,
                "prompts": prompts
            }
    except AttributeError:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category}' not found"
        )


@router.post("/custom-prompt")
async def execute_custom_prompt(
    document_id: str,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db_session)
):
    """
    使用自定义提示词分析文档
    
    允许用户提供自己的分析提示词
    """
    try:
        # 获取文档内容
        # document_content = await get_document_content(document_id)
        document_content = "示例文档内容..."  # 临时示例
        
        # 构建完整提示
        full_prompt = prompt
        if context:
            full_prompt = f"{prompt}\n\n上下文信息：{context}"
        
        # 使用LLM分析
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response = await llm.ainvoke([
            HumanMessage(content=f"{full_prompt}\n\n文档内容：\n{document_content[:5000]}")
        ])
        
        return {
            "document_id": document_id,
            "prompt": prompt,
            "analysis": response.content
        }
        
    except Exception as e:
        logger.error(f"Custom prompt analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_analysis_templates():
    """获取预定义的分析模板"""
    return {
        "templates": [
            {
                "id": "academic_paper",
                "name": "学术论文分析",
                "description": "适用于分析学术论文，提取研究方法、结论和贡献",
                "focus_areas": ["methodology", "findings", "contribution"],
                "output_formats": ["executive_summary", "detailed_report"]
            },
            {
                "id": "business_report",
                "name": "商业报告分析",
                "description": "适用于分析商业报告，关注市场洞察和行动建议",
                "focus_areas": ["market_analysis", "recommendations", "risks"],
                "output_formats": ["executive_summary", "action_plan"]
            },
            {
                "id": "technical_doc",
                "name": "技术文档分析",
                "description": "适用于分析技术文档，理解架构和实现细节",
                "focus_areas": ["architecture", "implementation", "best_practices"],
                "output_formats": ["detailed_report", "visualization"]
            },
            {
                "id": "policy_analysis",
                "name": "政策文件分析",
                "description": "适用于分析政策文件，评估影响和执行建议",
                "focus_areas": ["stakeholders", "impact", "implementation"],
                "output_formats": ["executive_summary", "action_plan"]
            }
        ]
    }