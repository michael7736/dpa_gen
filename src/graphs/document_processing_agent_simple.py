"""
简化的文档处理智能体
用于测试和基础功能
"""

from typing import Dict, Any, Optional


class DocumentProcessingAgent:
    """简化的文档处理智能体"""
    
    def __init__(self):
        self.name = "SimplifiedDocumentProcessingAgent"
        
    async def process_document(self, document_id: str, content: str) -> Dict[str, Any]:
        """处理文档（简化版）"""
        return {
            "status": "completed",
            "document_id": document_id,
            "chunks": len(content) // 1000 + 1,
            "message": "Document processed successfully"
        }


def get_document_processing_agent() -> DocumentProcessingAgent:
    """获取文档处理智能体实例"""
    return DocumentProcessingAgent()