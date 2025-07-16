"""
处理管道执行器
负责执行文档处理管道的各个阶段
"""

import asyncio
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.processing_pipeline import ProcessingPipeline, PipelineStage, StageStatus, ProcessingStage
from ..models.document import Document, ProcessingStatus
from ..services.minio_service import get_minio_service
from ..services.summary_service import SummaryService
from ..services.index_service import IndexService
from ..graphs.advanced_document_analyzer import AdvancedDocumentAnalyzer, AnalysisDepth
from ..utils.logger import get_logger
from ..api.websocket import get_progress_notifier

logger = get_logger(__name__)


class PipelineExecutor:
    """管道执行器"""
    
    def __init__(self):
        self.interrupt_flags: Dict[str, bool] = {}
        self.progress_callbacks: Dict[str, Callable] = {}
        
        # 阶段执行器映射
        self.stage_executors = {
            ProcessingStage.SUMMARY: self._execute_summary,
            ProcessingStage.INDEX: self._execute_index,
            ProcessingStage.ANALYSIS: self._execute_analysis
        }
    
    async def execute(self, pipeline_id: str, db: Session):
        """
        执行处理管道
        
        Args:
            pipeline_id: 管道ID
            db: 数据库会话
        """
        try:
            # 获取管道
            pipeline = db.query(ProcessingPipeline).filter(
                ProcessingPipeline.id == pipeline_id
            ).first()
            
            if not pipeline:
                logger.error(f"Pipeline not found: {pipeline_id}")
                return
            
            # 获取文档
            document = db.query(Document).filter(
                Document.id == pipeline.document_id
            ).first()
            
            if not document:
                logger.error(f"Document not found: {pipeline.document_id}")
                return
            
            # 获取所有待处理阶段
            stages = db.query(PipelineStage).filter(
                PipelineStage.pipeline_id == pipeline.id,
                PipelineStage.status.in_([StageStatus.PENDING, StageStatus.INTERRUPTED])
            ).order_by(PipelineStage.id).all()
            
            # 设置管道开始时间
            if not pipeline.started_at:
                pipeline.started_at = datetime.utcnow()
            
            # 执行每个阶段
            total_stages = len(stages)
            completed_stages = 0
            
            for stage in stages:
                # 检查中断标志
                if self._check_interrupt(pipeline_id):
                    pipeline.interrupted = True
                    logger.info(f"Pipeline {pipeline_id} interrupted")
                    break
                
                # 更新当前阶段
                pipeline.current_stage = stage.stage_type
                stage.status = StageStatus.PROCESSING
                stage.started_at = datetime.utcnow()
                stage.message = "正在处理..."
                db.commit()
                
                try:
                    # 执行阶段
                    logger.info(f"Executing stage {stage.stage_type} for pipeline {pipeline_id}")
                    
                    # 创建异步进度回调
                    async def progress_callback(progress: int, message: str):
                        try:
                            stage.progress = progress
                            stage.message = message
                            db.commit()
                            
                            # WebSocket实时通知
                            try:
                                notifier = get_progress_notifier()
                                await notifier.notify_stage_update(str(stage.id), db)
                            except Exception as ws_error:
                                logger.warning(f"WebSocket通知失败: {ws_error}")
                                
                        except Exception as e:
                            logger.error(f"Error updating stage progress: {e}")
                    
                    result = await self.stage_executors[stage.stage_type](
                        document=document,
                        stage=stage,
                        pipeline=pipeline,
                        db=db,
                        progress_callback=progress_callback
                    )
                    
                    # 更新阶段结果
                    stage.status = StageStatus.COMPLETED
                    stage.completed_at = datetime.utcnow()
                    stage.duration = (stage.completed_at - stage.started_at).total_seconds()
                    stage.progress = 100
                    stage.result = result
                    stage.message = "处理完成"
                    
                    completed_stages += 1
                    pipeline.overall_progress = (completed_stages / total_stages) * 100
                    
                    # 更新文档状态
                    self._update_document_status(document, stage.stage_type)
                    
                    db.commit()
                    logger.info(f"Stage {stage.stage_type} completed for pipeline {pipeline_id}")
                    
                    # WebSocket通知阶段完成
                    try:
                        notifier = get_progress_notifier()
                        await notifier.notify_pipeline_progress(pipeline_id, db)
                    except Exception as ws_error:
                        logger.warning(f"WebSocket通知失败: {ws_error}")
                    
                except Exception as e:
                    logger.error(f"Stage {stage.stage_type} failed for pipeline {pipeline_id}: {e}")
                    stage.status = StageStatus.FAILED
                    stage.error = str(e)
                    stage.error_details = {"exception": type(e).__name__}
                    stage.message = f"处理失败: {str(e)}"
                    db.commit()
                    break
            
            # 更新管道状态
            if not pipeline.interrupted and completed_stages == total_stages:
                pipeline.completed = True
                pipeline.completed_at = datetime.utcnow()
                document.processing_status = ProcessingStatus.COMPLETED
            
            db.commit()
            logger.info(f"Pipeline {pipeline_id} execution finished")
            
            # 发送最终完成通知
            try:
                notifier = get_progress_notifier()
                await notifier.notify_pipeline_progress(pipeline_id, db)
            except Exception as ws_error:
                logger.warning(f"WebSocket最终完成通知失败: {ws_error}")
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            db.rollback()
    
    def _check_interrupt(self, pipeline_id: str) -> bool:
        """检查是否需要中断"""
        return self.interrupt_flags.get(pipeline_id, False)
    
    def set_interrupt(self, pipeline_id: str):
        """设置中断标志"""
        self.interrupt_flags[pipeline_id] = True
    
    def clear_interrupt(self, pipeline_id: str):
        """清除中断标志"""
        self.interrupt_flags.pop(pipeline_id, None)
    
    def _update_stage_progress(self, db: Session, stage: PipelineStage, 
                             progress: int, message: str):
        """更新阶段进度"""
        try:
            stage.progress = progress
            stage.message = message
            db.commit()
        except Exception as e:
            logger.error(f"Error updating stage progress: {e}")
    
    def _update_document_status(self, document: Document, stage_type: ProcessingStage):
        """根据完成的阶段更新文档状态"""
        status_map = {
            ProcessingStage.SUMMARY: ProcessingStatus.SUMMARIZED,
            ProcessingStage.INDEX: ProcessingStatus.INDEXED,
            ProcessingStage.ANALYSIS: ProcessingStatus.ANALYZED
        }
        
        if stage_type in status_map:
            document.processing_status = status_map[stage_type]
    
    async def _execute_summary(self, document: Document, stage: PipelineStage,
                             pipeline: ProcessingPipeline, db: Session,
                             progress_callback: Callable) -> Dict[str, Any]:
        """执行摘要生成阶段"""
        try:
            await progress_callback(10, "正在获取文档内容...")
            
            # 获取文档内容
            minio_service = get_minio_service()
            
            # 解析存储路径
            storage_path = document.file_path
            if storage_path.startswith("s3://"):
                # 解析MinIO路径
                parts = storage_path.replace("s3://", "").split("/", 1)
                if len(parts) >= 2:
                    object_path = parts[1]
                    # 提取路径组件
                    path_parts = object_path.split("/")
                    if len(path_parts) >= 4:
                        user_id = path_parts[0]
                        project_id = path_parts[1]
                        document_id = path_parts[2]
                        file_name = "/".join(path_parts[4:])  # original/filename
                        
                        content = await minio_service.get_document(
                            user_id, project_id, str(document.id), file_name
                        )
            else:
                # 本地文件路径
                with open(document.file_path, 'rb') as f:
                    content = f.read()
            
            await progress_callback(30, "正在生成摘要...")
            
            # 使用摘要服务生成摘要
            summary_service = SummaryService()
            summary_result = await summary_service.generate_summary(
                document_id=str(document.id),
                content=content,
                file_type=document.document_type,
                progress_callback=progress_callback
            )
            
            # 保存摘要到文档
            document.summary = summary_result.summary
            if document.metadata_info is None:
                document.metadata_info = {}
            document.metadata_info["keywords"] = summary_result.keywords
            document.metadata_info["summary_info"] = {
                "document_type": summary_result.document_type,
                "complexity_level": summary_result.complexity_level,
                "estimated_read_time": summary_result.estimated_read_time,
                "key_sections": summary_result.key_sections,
                "recommendation": summary_result.recommendation
            }
            
            # 保存结果到MinIO
            await minio_service.save_processing_result(
                user_id=user_id,
                project_id=str(document.project_id),
                document_id=str(document.id),
                result_type="summary",
                content=summary_result.dict()
            )
            
            await progress_callback(100, "摘要生成完成")
            
            return {
                "summary_length": len(summary_result.summary),
                "keywords_count": len(summary_result.keywords),
                "recommendation": summary_result.recommendation
            }
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            raise
    
    async def _execute_index(self, document: Document, stage: PipelineStage,
                           pipeline: ProcessingPipeline, db: Session,
                           progress_callback: Callable) -> Dict[str, Any]:
        """执行索引创建阶段"""
        try:
            await progress_callback(10, "正在准备索引...")
            
            # 使用索引服务创建索引
            index_service = IndexService(db)
            result = await index_service.create_index(
                document=document,
                progress_callback=progress_callback
            )
            
            await progress_callback(100, "索引创建完成")
            
            return result
            
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            raise
    
    async def _execute_analysis(self, document: Document, stage: PipelineStage,
                              pipeline: ProcessingPipeline, db: Session,
                              progress_callback: Callable) -> Dict[str, Any]:
        """执行深度分析阶段"""
        try:
            await progress_callback(10, "正在准备深度分析...")
            
            # 获取文档内容
            minio_service = get_minio_service()
            content = None
            
            # 解析存储路径
            storage_path = document.file_path
            if storage_path.startswith("s3://"):
                # 解析MinIO路径
                parts = storage_path.replace("s3://", "").split("/", 1)
                if len(parts) >= 2:
                    object_path = parts[1]
                    # 提取路径组件
                    path_parts = object_path.split("/")
                    if len(path_parts) >= 4:
                        user_id = path_parts[0]
                        project_id = path_parts[1]
                        document_id = path_parts[2]
                        file_name = "/".join(path_parts[4:])  # original/filename
                        
                        content_bytes = await minio_service.get_document(
                            user_id, project_id, str(document.id), file_name
                        )
                        # 解码内容
                        content = content_bytes.decode('utf-8', errors='ignore')
            else:
                # 本地文件路径
                with open(document.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            await progress_callback(20, "正在初始化分析器...")
            
            # 使用高级文档分析器
            analyzer = AdvancedDocumentAnalyzer()
            
            # 获取分析深度配置
            depth = pipeline.processing_options.get("analysis_depth", AnalysisDepth.COMPREHENSIVE)
            
            # 构建分析参数，直接传递内容而不是文件路径
            analysis_params = {
                "document_id": str(document.id),
                "project_id": str(document.project_id),
                "file_path": document.file_path,  # 保留用于记录
                "file_name": document.filename,
                "content": content,  # 直接传递内容
                "analysis_depth": depth,
                "analysis_goal": pipeline.processing_options.get("analysis_goal", "深入理解文档内容")
            }
            
            await progress_callback(30, "正在执行深度分析...")
            
            # 执行分析
            result = await analyzer.analyze_document(analysis_params)
            
            # 保存分析结果
            if result["success"]:
                # 保存到MinIO
                minio_service = get_minio_service()
                storage_path = document.file_path
                if storage_path.startswith("s3://"):
                    parts = storage_path.replace("s3://", "").split("/", 1)
                    if len(parts) >= 2:
                        object_path = parts[1]
                        path_parts = object_path.split("/")
                        if len(path_parts) >= 4:
                            user_id = path_parts[0]
                            
                            await minio_service.save_processing_result(
                                user_id=user_id,
                                project_id=str(document.project_id),
                                document_id=str(document.id),
                                result_type="analysis",
                                content=result
                            )
            
            await progress_callback(100, "深度分析完成")
            
            return {
                "analysis_id": result.get("analysis_id"),
                "insights_count": len(result.get("insights", [])),
                "recommendations_count": len(result.get("action_items", []))
            }
            
        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            raise


# 全局执行器实例
_executor: Optional[PipelineExecutor] = None


def get_pipeline_executor() -> PipelineExecutor:
    """获取管道执行器实例"""
    global _executor
    if _executor is None:
        _executor = PipelineExecutor()
    return _executor