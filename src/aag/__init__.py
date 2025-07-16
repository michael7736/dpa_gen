"""
DPA-AAG: Analysis-Augmented Generation Module
基于分析增强生成的智能文档处理系统
"""

__version__ = "0.1.0"

from .agents import (
    SkimmerAgent,
    ProgressiveSummaryAgent,
    SummaryLevel,
    KnowledgeGraphAgent,
    EntityType,
    RelationType,
    OutlineAgent,
    OutlineDimension,
    EvidenceChainAnalyzer,
    CrossReferenceAnalyzer,
    CriticalThinkingAnalyzer,
    DeepAnalyzer,
    AnalysisType,
    PlannerAgent,
    AnalysisGoal,
    DocumentCategory
)

# TODO: 实现其他模块
# from .engines import (
#     AnalysisEngine,
#     ExecutionEngine,
#     OrchestrationEngine
# )

from .storage import (
    ArtifactStore,
    MetadataManager
)

__all__ = [
    "SkimmerAgent",
    "ProgressiveSummaryAgent",
    "SummaryLevel",
    "KnowledgeGraphAgent",
    "EntityType",
    "RelationType",
    "OutlineAgent",
    "OutlineDimension",
    "EvidenceChainAnalyzer",
    "CrossReferenceAnalyzer",
    "CriticalThinkingAnalyzer",
    "DeepAnalyzer",
    "AnalysisType",
    "PlannerAgent",
    "AnalysisGoal",
    "DocumentCategory",
    "ArtifactStore",
    "MetadataManager"
]