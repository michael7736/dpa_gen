"""
文档处理智能体模块
根据功能开关选择使用改进版或原版
"""

from ..config.feature_flags import is_feature_enabled
from ..utils.logger import get_logger

logger = get_logger(__name__)

def get_document_processing_agent():
    """
    获取文档处理智能体实例
    根据功能开关决定使用哪个版本
    """
    use_improved = is_feature_enabled("use_improved_document_processor")
    
    if use_improved:
        logger.info("Using improved document processing agent")
        from .improved_document_processing_agent import ImprovedDocumentProcessingAgent
        return ImprovedDocumentProcessingAgent()
    else:
        logger.info("Using standard document processing agent")
        from .document_processing_agent import DocumentProcessingAgent
        return DocumentProcessingAgent()

def get_research_planning_agent():
    """获取研究规划智能体实例"""
    from .research_planning_agent import ResearchPlanningAgent
    return ResearchPlanningAgent()

__all__ = [
    'get_document_processing_agent',
    'get_research_planning_agent'
]