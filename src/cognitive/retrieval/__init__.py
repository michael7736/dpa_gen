"""
三阶段混合检索模块

这个模块实现了DPA认知系统的核心检索功能：
- 第一阶段：向量检索（Vector Retrieval）
- 第二阶段：图谱增强（Graph Enhancement）  
- 第三阶段：记忆库协同（Memory Bank Collaboration）

主要组件：
- HybridRetrievalSystem: 主控制器
- VectorRetriever: 向量检索器
- GraphEnhancer: 图谱增强器
- MemoryBankRetriever: 记忆库检索器
"""

from .hybrid_retrieval import (
    # 核心类
    HybridRetrievalSystem,
    VectorRetriever,
    GraphEnhancer,
    MemoryBankRetriever,
    
    # 数据结构
    HybridQuery,
    RetrievalResult,
    
    # 工厂函数
    create_hybrid_retrieval_system,
    
    # 便捷函数
    hybrid_search
)

__all__ = [
    # 核心类
    "HybridRetrievalSystem",
    "VectorRetriever", 
    "GraphEnhancer",
    "MemoryBankRetriever",
    
    # 数据结构
    "HybridQuery",
    "RetrievalResult",
    
    # 工厂函数
    "create_hybrid_retrieval_system",
    
    # 便捷函数
    "hybrid_search"
]