"""
文档深度分析API路由
提供高级文档分析功能的HTTP接口
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database.postgresql import get_db_session as get_db
from ...graphs.advanced_document_analyzer import (
    AdvancedDocumentAnalyzer,
    AnalysisDepth,
    AnalysisStage
)
from ...models.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusModel,
    AnalysisResult,
    QuickAnalysisRequest,
    AnalysisListResponse,
    DocumentAnalysis,
    AnalysisStatus
)
from ...models.document import Document
from ...services.cache_service import CacheService
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

# 全局分析器实例
analyzer = AdvancedDocumentAnalyzer()
cache_service = CacheService()

# 内存中的分析任务状态（生产环境应使用Redis）
analysis_tasks: Dict[str, Dict] = {}


@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Query(..., description="用户ID")
):
    """
    启动文档深度分析任务
    
    支持五种分析深度：
    - basic: 基础分析（元数据提取）
    - standard: 标准分析（结构+摘要）
    - deep: 深度分析（语义+主题）
    - expert: 专家分析（关系+洞察）
    - comprehensive: 全面分析（六阶段完整流程）
    """
    try:
        # 验证文档是否存在
        document = db.query(Document).filter(
            Document.id == request.document_id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # 创建分析记录
        analysis = DocumentAnalysis(
            id=uuid4(),
            document_id=request.document_id,
            project_id=request.project_id,
            user_id=user_id,
            analysis_depth=request.analysis_depth,
            analysis_goal=request.analysis_goal,
            status=AnalysisStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.add(analysis)
        db.commit()
        
        # 准备文档信息
        document_info = {
            "document_id": str(document.id),
            "project_id": str(request.project_id),
            "user_id": user_id,
            "file_path": document.file_path,
            "file_name": document.file_name,
            "analysis_depth": request.analysis_depth,
            "analysis_goal": request.analysis_goal
        }
        
        # 在后台启动分析任务
        background_tasks.add_task(
            run_analysis,
            str(analysis.id),
            document_info,
            db
        )
        
        # 估算处理时间
        estimated_time = estimate_processing_time(
            document.file_size,
            request.analysis_depth
        )
        
        # 缓存任务状态
        analysis_tasks[str(analysis.id)] = {
            "status": AnalysisStatus.PENDING,
            "started_at": datetime.utcnow(),
            "estimated_time": estimated_time
        }
        
        return AnalysisResponse(
            analysis_id=analysis.id,
            status=AnalysisStatus.PENDING,
            message=f"Analysis started for document {document.file_name}",
            estimated_time=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{analysis_id}", response_model=AnalysisStatusModel)
async def get_analysis_status(
    analysis_id: UUID,
    db: Session = Depends(get_db)
):
    """获取分析任务状态"""
    try:
        # 从数据库获取分析记录
        analysis = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # 获取实时进度
        progress_info = analyzer.get_analysis_progress(str(analysis.document_id))
        
        # 计算预计完成时间
        estimated_completion = None
        if analysis.started_at and progress_info.get("progress", 0) > 0:
            elapsed = (datetime.utcnow() - analysis.started_at).total_seconds()
            total_estimated = elapsed / (progress_info["progress"] / 100)
            remaining = total_estimated - elapsed
            estimated_completion = datetime.utcnow().timestamp() + remaining
        
        return AnalysisStatusModel(
            analysis_id=analysis.id,
            document_id=analysis.document_id,
            status=analysis.status,
            current_stage=analysis.current_stage,
            progress=progress_info.get("progress", 0.0),
            error_message=analysis.error_message,
            started_at=analysis.started_at,
            estimated_completion=datetime.fromtimestamp(estimated_completion) if estimated_completion else None
        )
        
    except Exception as e:
        logger.error(f"Failed to get analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{analysis_id}", response_model=AnalysisResult)
async def get_analysis_results(
    analysis_id: UUID,
    include_details: bool = Query(False, description="是否包含详细报告"),
    db: Session = Depends(get_db)
):
    """获取分析结果"""
    try:
        # 从数据库获取分析记录
        analysis = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis.status != AnalysisStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Analysis is {analysis.status}, not completed"
            )
        
        # 构建响应
        result = AnalysisResult(
            analysis_id=analysis.id,
            document_id=analysis.document_id,
            project_id=analysis.project_id,
            status=analysis.status,
            analysis_depth=analysis.analysis_depth,
            executive_summary=analysis.executive_summary,
            key_insights=analysis.key_insights or [],
            recommendations=analysis.recommendations or [],
            quality_score=analysis.quality_score,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
            processing_time_seconds=analysis.processing_time_seconds
        )
        
        # 如果请求详细信息
        if include_details:
            result.detailed_report = analysis.detailed_report
            result.visualization_data = analysis.visualization_data
            result.action_plan = analysis.action_plan
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get analysis results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-text", response_model=AnalysisResult)
async def analyze_text(
    request: QuickAnalysisRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="用户ID")
):
    """
    快速分析文本内容
    不需要先上传文档，直接分析提供的文本
    """
    try:
        # 创建临时文档信息
        temp_doc_id = str(uuid4())
        document_info = {
            "document_id": temp_doc_id,
            "project_id": "temp_project",
            "user_id": user_id,
            "file_path": "memory",
            "file_name": request.title,
            "content": request.content,
            "analysis_depth": request.analysis_depth,
            "analysis_goal": request.analysis_goal
        }
        
        # 直接执行分析（对于快速分析，同步执行）
        if request.analysis_depth == AnalysisDepth.BASIC:
            result = await analyzer.analyze_document(document_info)
            
            if result["success"]:
                return AnalysisResult(
                    analysis_id=uuid4(),
                    document_id=UUID(temp_doc_id),
                    project_id=UUID("00000000-0000-0000-0000-000000000000"),
                    status=AnalysisStatus.COMPLETED,
                    analysis_depth=request.analysis_depth,
                    executive_summary=result["results"].get("executive_summary"),
                    key_insights=result["results"].get("key_insights", []),
                    recommendations=result["results"].get("recommendations", []),
                    quality_score=result["results"].get("quality_score"),
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    processing_time_seconds=result.get("processing_time", 0)
                )
            else:
                raise HTTPException(status_code=500, detail=result.get("error"))
        else:
            # 对于更深度的分析，使用后台任务
            analysis_id = uuid4()
            background_tasks.add_task(
                run_quick_analysis,
                str(analysis_id),
                document_info
            )
            
            raise HTTPException(
                status_code=202,
                detail=f"Deep analysis started with ID: {analysis_id}"
            )
            
    except Exception as e:
        logger.error(f"Failed to analyze text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=AnalysisListResponse)
async def list_analyses(
    project_id: Optional[UUID] = Query(None, description="项目ID过滤"),
    status: Optional[AnalysisStatus] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    user_id: str = Query(..., description="用户ID")
):
    """列出分析任务"""
    try:
        # 构建查询
        query = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.user_id == user_id
        )
        
        if project_id:
            query = query.filter(DocumentAnalysis.project_id == project_id)
        
        if status:
            query = query.filter(DocumentAnalysis.status == status)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        analyses = query.order_by(
            DocumentAnalysis.created_at.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        # 构建响应
        analysis_list = []
        for analysis in analyses:
            progress_info = analyzer.get_analysis_progress(str(analysis.document_id))
            
            analysis_list.append(AnalysisStatusModel(
                analysis_id=analysis.id,
                document_id=analysis.document_id,
                status=analysis.status,
                current_stage=analysis.current_stage,
                progress=progress_info.get("progress", 0.0),
                error_message=analysis.error_message,
                started_at=analysis.started_at,
                estimated_completion=None  # 简化处理
            ))
        
        return AnalysisListResponse(
            analyses=analysis_list,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Failed to list analyses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_analysis(
    analysis_id: str,
    document_info: Dict,
    db: Session
):
    """后台运行分析任务"""
    try:
        # 更新状态为运行中
        analysis = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.id == UUID(analysis_id)
        ).first()
        
        if analysis:
            analysis.status = AnalysisStatus.RUNNING
            analysis.started_at = datetime.utcnow()
            db.commit()
        
        # 执行分析
        result = await analyzer.analyze_document(document_info)
        
        # 更新分析结果
        if analysis:
            if result["success"]:
                analysis.status = AnalysisStatus.COMPLETED
                analysis.completed_at = datetime.utcnow()
                analysis.processing_time_seconds = (
                    analysis.completed_at - analysis.started_at
                ).total_seconds()
                
                # 保存结果
                results = result["results"]
                analysis.executive_summary = results.get("executive_summary")
                analysis.key_insights = results.get("key_insights", [])
                analysis.recommendations = results.get("recommendations", [])
                analysis.quality_score = results.get("quality_score")
                analysis.detailed_report = results.get("detailed_report")
                analysis.visualization_data = results.get("visualization_data")
                analysis.action_plan = results.get("action_plan")
                analysis.current_stage = AnalysisStage.OUTPUT_GENERATION
                analysis.progress = 100.0
            else:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = result.get("error", "Unknown error")
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Analysis task failed: {str(e)}")
        if analysis:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            db.commit()


async def run_quick_analysis(
    analysis_id: str,
    document_info: Dict
):
    """运行快速分析任务"""
    try:
        # 执行分析
        result = await analyzer.analyze_document(document_info)
        
        # 缓存结果
        if result["success"]:
            await cache_service.set(
                f"quick_analysis_{analysis_id}",
                result,
                ttl=3600  # 1小时
            )
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {str(e)}")


def estimate_processing_time(file_size: int, depth: AnalysisDepth) -> int:
    """估算处理时间（秒）"""
    base_time = {
        AnalysisDepth.BASIC: 10,
        AnalysisDepth.STANDARD: 30,
        AnalysisDepth.DEEP: 60,
        AnalysisDepth.EXPERT: 120,
        AnalysisDepth.COMPREHENSIVE: 300
    }
    
    # 根据文件大小调整
    size_factor = 1 + (file_size / (1024 * 1024 * 10))  # 每10MB增加一倍时间
    
    return int(base_time.get(depth, 60) * size_factor)


# 保留原有的模板相关端点
@router.get("/templates")
async def get_analysis_templates():
    """获取预定义的分析模板"""
    return {
        "templates": [
            {
                "id": "academic_paper",
                "name": "学术论文分析",
                "description": "适用于分析学术论文，提取研究方法、结论和贡献",
                "analysis_depth": AnalysisDepth.EXPERT,
                "focus_areas": ["methodology", "findings", "contribution"],
                "output_formats": ["executive_summary", "detailed_report"]
            },
            {
                "id": "business_report",
                "name": "商业报告分析",
                "description": "适用于分析商业报告，关注市场洞察和行动建议",
                "analysis_depth": AnalysisDepth.DEEP,
                "focus_areas": ["market_analysis", "recommendations", "risks"],
                "output_formats": ["executive_summary", "action_plan"]
            },
            {
                "id": "technical_doc",
                "name": "技术文档分析",
                "description": "适用于分析技术文档，理解架构和实现细节",
                "analysis_depth": AnalysisDepth.COMPREHENSIVE,
                "focus_areas": ["architecture", "implementation", "best_practices"],
                "output_formats": ["detailed_report", "visualization"]
            },
            {
                "id": "policy_analysis",
                "name": "政策文件分析",
                "description": "适用于分析政策文件，评估影响和执行建议",
                "analysis_depth": AnalysisDepth.EXPERT,
                "focus_areas": ["stakeholders", "impact", "implementation"],
                "output_formats": ["executive_summary", "action_plan"]
            }
        ]
    }