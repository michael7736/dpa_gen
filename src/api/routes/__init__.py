"""
API路由模块
包含所有API端点的路由定义
"""

from . import documents, projects, research, knowledge, health

__all__ = [
    "documents",
    "projects", 
    "research",
    "knowledge",
    "health"
] 