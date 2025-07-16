"""
DPA认知系统 - V3.0
基于认知科学的四层记忆模型和LangGraph工作流
"""

from .state import DPACognitiveState, StateManager
from .storage import CognitiveStorageManager, create_cognitive_storage
from .memory.memory_bank import MemoryBankManager, create_memory_bank_manager
from .workflow.cognitive_workflow import CognitiveWorkflow, create_cognitive_workflow
from .chunking.s2_semantic_chunker import S2SemanticChunker, create_s2_chunker
from .retrieval import HybridRetrievalSystem, create_hybrid_retrieval_system, hybrid_search
from .metacognition import MetacognitiveEngine, create_metacognitive_engine

__all__ = [
    "DPACognitiveState",
    "StateManager", 
    "CognitiveStorageManager",
    "create_cognitive_storage",
    "MemoryBankManager",
    "create_memory_bank_manager",
    "CognitiveWorkflow",
    "create_cognitive_workflow",
    "S2SemanticChunker",
    "create_s2_chunker",
    "HybridRetrievalSystem",
    "create_hybrid_retrieval_system",
    "hybrid_search",
    "MetacognitiveEngine",
    "create_metacognitive_engine"
]

__version__ = "3.0.0"