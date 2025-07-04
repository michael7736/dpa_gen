"""
文档处理智能体
负责文档的解析、分块、向量化和索引
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Union
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from ..config.settings import get_settings
from ..core.chunking import DocumentChunker, ChunkingStrategy
from ..core.vectorization import VectorStore
from ..core.knowledge_index import KnowledgeIndexer
from ..database.qdrant_client import QdrantClient
from ..models.document import Document, DocumentType, ProcessingStatus, DocumentChunk
from ..models.project import Project
from ..services.document_parser import parse_document, DocumentContent
from ..services.file_storage import FileStorageService
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DocumentProcessingState(TypedDict):
    """文档处理状态"""
    # 输入信息
    project_id: str
    document_id: str
    file_path: str
    file_name: str
    processing_options: Dict[str, Any]
    
    # 处理过程状态
    current_step: str
    progress: float
    status: ProcessingStatus
    error_message: Optional[str]
    
    # 处理结果
    parsed_content: Optional[DocumentContent]
    chunks: List[DocumentChunk]
    embeddings: List[List[float]]
    indexed: bool
    
    # 元数据
    processing_start_time: datetime
    processing_end_time: Optional[datetime]
    processing_duration: Optional[float]
    
    # 消息历史
    messages: List[BaseMessage]


class DocumentProcessingConfig(BaseModel):
    """文档处理配置"""
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    chunk_size: int = Field(default=1000, ge=100, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    enable_ocr: bool = False
    extract_tables: bool = True
    extract_images: bool = True
    enable_summarization: bool = True
    quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class DocumentProcessingAgent:
    """文档处理智能体"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.file_storage = FileStorageService()
        self.chunker = DocumentChunker()
        self.vector_store = VectorStore()
        self.knowledge_index = KnowledgeIndex()
        self.qdrant_client = QdrantClient()
        
        # 构建状态图
        self.graph = self._build_graph()
        
        # 设置检查点
        self.checkpointer = MemorySaver()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
    
    def _build_graph(self) -> StateGraph:
        """构建文档处理状态图"""
        graph = StateGraph(DocumentProcessingState)
        
        # 添加节点
        graph.add_node("initialize", self._initialize_processing)
        graph.add_node("parse_document", self._parse_document)
        graph.add_node("validate_content", self._validate_content)
        graph.add_node("chunk_content", self._chunk_content)
        graph.add_node("generate_embeddings", self._generate_embeddings)
        graph.add_node("index_content", self._index_content)
        graph.add_node("finalize", self._finalize_processing)
        graph.add_node("handle_error", self._handle_error)
        
        # 设置入口点
        graph.set_entry_point("initialize")
        
        # 添加边
        graph.add_edge("initialize", "parse_document")
        
        # 条件路由：解析后的验证
        graph.add_conditional_edges(
            "parse_document",
            self._should_validate_content,
            {
                "validate": "validate_content",
                "error": "handle_error"
            }
        )
        
        # 条件路由：内容验证后
        graph.add_conditional_edges(
            "validate_content",
            self._should_proceed_to_chunking,
            {
                "chunk": "chunk_content",
                "error": "handle_error"
            }
        )
        
        graph.add_edge("chunk_content", "generate_embeddings")
        
        # 条件路由：嵌入生成后
        graph.add_conditional_edges(
            "generate_embeddings",
            self._should_index_content,
            {
                "index": "index_content",
                "error": "handle_error"
            }
        )
        
        graph.add_edge("index_content", "finalize")
        graph.add_edge("finalize", END)
        graph.add_edge("handle_error", END)
        
        return graph
    
    async def process_document(
        self,
        project_id: str,
        document_id: str,
        file_path: str,
        config: Optional[DocumentProcessingConfig] = None
    ) -> DocumentProcessingState:
        """处理文档"""
        if config is None:
            config = DocumentProcessingConfig()
        
        # 初始化状态
        initial_state = DocumentProcessingState(
            project_id=project_id,
            document_id=document_id,
            file_path=file_path,
            file_name=Path(file_path).name,
            processing_options=config.dict(),
            current_step="initialize",
            progress=0.0,
            status=ProcessingStatus.PROCESSING,
            error_message=None,
            parsed_content=None,
            chunks=[],
            embeddings=[],
            indexed=False,
            processing_start_time=datetime.now(),
            processing_end_time=None,
            processing_duration=None,
            messages=[
                SystemMessage(content="开始文档处理流程"),
                HumanMessage(content=f"处理文档: {Path(file_path).name}")
            ]
        )
        
        # 运行图
        config_dict = {
            "configurable": {
                "thread_id": f"doc_processing_{document_id}",
                "checkpoint_ns": f"project_{project_id}"
            }
        }
        
        try:
            result = await self.compiled_graph.ainvoke(
                initial_state,
                config=RunnableConfig(**config_dict)
            )
            return result
        except Exception as e:
            self.logger.error(f"文档处理失败: {str(e)}")
            # 返回错误状态
            initial_state["status"] = ProcessingStatus.FAILED
            initial_state["error_message"] = str(e)
            initial_state["processing_end_time"] = datetime.now()
            return initial_state
    
    async def _initialize_processing(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """初始化处理"""
        self.logger.info(f"开始处理文档: {state['file_name']}")
        
        state["current_step"] = "initialize"
        state["progress"] = 0.1
        
        # 验证文件存在
        if not Path(state["file_path"]).exists():
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = f"文件不存在: {state['file_path']}"
            return state
        
        # 验证项目存在
        # TODO: 添加项目验证逻辑
        
        state["messages"].append(
            SystemMessage(content=f"初始化完成，开始解析文档: {state['file_name']}")
        )
        
        return state
    
    async def _parse_document(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """解析文档"""
        self.logger.info(f"解析文档: {state['file_name']}")
        
        state["current_step"] = "parse_document"
        state["progress"] = 0.2
        
        try:
            # 解析文档
            parsed_content = await parse_document(
                state["file_path"],
                **state["processing_options"]
            )
            
            state["parsed_content"] = parsed_content
            state["messages"].append(
                SystemMessage(content=f"文档解析完成，提取文本长度: {len(parsed_content.text)} 字符")
            )
            
            self.logger.info(f"文档解析完成: {state['file_name']}, 文本长度: {len(parsed_content.text)}")
            
        except Exception as e:
            self.logger.error(f"文档解析失败: {str(e)}")
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = f"文档解析失败: {str(e)}"
        
        return state
    
    async def _validate_content(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """验证内容质量"""
        self.logger.info(f"验证文档内容: {state['file_name']}")
        
        state["current_step"] = "validate_content"
        state["progress"] = 0.3
        
        if not state["parsed_content"]:
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = "没有解析内容可供验证"
            return state
        
        try:
            content = state["parsed_content"]
            quality_score = await self._calculate_content_quality(content)
            
            quality_threshold = state["processing_options"].get("quality_threshold", 0.8)
            
            if quality_score < quality_threshold:
                state["status"] = ProcessingStatus.FAILED
                state["error_message"] = f"内容质量不达标: {quality_score:.2f} < {quality_threshold}"
                return state
            
            state["messages"].append(
                SystemMessage(content=f"内容质量验证通过，质量分数: {quality_score:.2f}")
            )
            
            self.logger.info(f"内容质量验证通过: {state['file_name']}, 质量分数: {quality_score:.2f}")
            
        except Exception as e:
            self.logger.error(f"内容验证失败: {str(e)}")
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = f"内容验证失败: {str(e)}"
        
        return state
    
    async def _chunk_content(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """分块内容"""
        self.logger.info(f"分块文档内容: {state['file_name']}")
        
        state["current_step"] = "chunk_content"
        state["progress"] = 0.5
        
        if not state["parsed_content"]:
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = "没有内容可供分块"
            return state
        
        try:
            content = state["parsed_content"]
            
            # 配置分块参数
            chunking_config = {
                "strategy": ChunkingStrategy(state["processing_options"].get("chunking_strategy", "semantic")),
                "chunk_size": state["processing_options"].get("chunk_size", 1000),
                "chunk_overlap": state["processing_options"].get("chunk_overlap", 200)
            }
            
            # 执行分块
            chunks = await self.chunker.chunk_document(
                content.text,
                document_id=state["document_id"],
                metadata=content.metadata,
                **chunking_config
            )
            
            state["chunks"] = chunks
            state["messages"].append(
                SystemMessage(content=f"内容分块完成，生成 {len(chunks)} 个块")
            )
            
            self.logger.info(f"内容分块完成: {state['file_name']}, 生成 {len(chunks)} 个块")
            
        except Exception as e:
            self.logger.error(f"内容分块失败: {str(e)}")
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = f"内容分块失败: {str(e)}"
        
        return state
    
    async def _generate_embeddings(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """生成嵌入向量"""
        self.logger.info(f"生成嵌入向量: {state['file_name']}")
        
        state["current_step"] = "generate_embeddings"
        state["progress"] = 0.7
        
        if not state["chunks"]:
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = "没有块可供向量化"
            return state
        
        try:
            # 提取文本内容
            texts = [chunk.content for chunk in state["chunks"]]
            
            # 生成嵌入向量
            embeddings = await self.vector_store.embed_texts(texts)
            
            # 更新块的嵌入向量
            for chunk, embedding in zip(state["chunks"], embeddings):
                chunk.embedding = embedding
            
            state["embeddings"] = embeddings
            state["messages"].append(
                SystemMessage(content=f"嵌入向量生成完成，处理 {len(embeddings)} 个向量")
            )
            
            self.logger.info(f"嵌入向量生成完成: {state['file_name']}, 处理 {len(embeddings)} 个向量")
            
        except Exception as e:
            self.logger.error(f"嵌入向量生成失败: {str(e)}")
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = f"嵌入向量生成失败: {str(e)}"
        
        return state
    
    async def _index_content(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """索引内容"""
        self.logger.info(f"索引文档内容: {state['file_name']}")
        
        state["current_step"] = "index_content"
        state["progress"] = 0.9
        
        if not state["chunks"] or not state["embeddings"]:
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = "没有内容或嵌入向量可供索引"
            return state
        
        try:
            # 索引到向量数据库
            collection_name = f"project_{state['project_id']}"
            
            # 准备向量数据
            points = []
            for i, (chunk, embedding) in enumerate(zip(state["chunks"], state["embeddings"])):
                point = {
                    "id": chunk.id,
                    "vector": embedding,
                    "payload": {
                        "document_id": state["document_id"],
                        "project_id": state["project_id"],
                        "chunk_index": i,
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "start_index": chunk.start_index,
                        "end_index": chunk.end_index
                    }
                }
                points.append(point)
            
            # 批量插入向量
            await self.qdrant_client.upsert_vectors(collection_name, points)
            
            # 更新知识索引
            await self.knowledge_index.index_document_chunks(
                state["project_id"],
                state["document_id"],
                state["chunks"]
            )
            
            state["indexed"] = True
            state["messages"].append(
                SystemMessage(content=f"内容索引完成，索引 {len(points)} 个向量")
            )
            
            self.logger.info(f"内容索引完成: {state['file_name']}, 索引 {len(points)} 个向量")
            
        except Exception as e:
            self.logger.error(f"内容索引失败: {str(e)}")
            state["status"] = ProcessingStatus.FAILED
            state["error_message"] = f"内容索引失败: {str(e)}"
        
        return state
    
    async def _finalize_processing(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """完成处理"""
        self.logger.info(f"完成文档处理: {state['file_name']}")
        
        state["current_step"] = "finalize"
        state["progress"] = 1.0
        state["status"] = ProcessingStatus.COMPLETED
        state["processing_end_time"] = datetime.now()
        
        # 计算处理时长
        duration = (state["processing_end_time"] - state["processing_start_time"]).total_seconds()
        state["processing_duration"] = duration
        
        state["messages"].append(
            SystemMessage(content=f"文档处理完成，耗时 {duration:.2f} 秒")
        )
        
        # TODO: 更新数据库中的文档状态
        await self._update_document_status(state)
        
        self.logger.info(f"文档处理完成: {state['file_name']}, 耗时 {duration:.2f} 秒")
        
        return state
    
    async def _handle_error(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """处理错误"""
        self.logger.error(f"文档处理出错: {state['file_name']}, 错误: {state.get('error_message', '未知错误')}")
        
        state["current_step"] = "handle_error"
        state["status"] = ProcessingStatus.FAILED
        state["processing_end_time"] = datetime.now()
        
        if state["processing_start_time"]:
            duration = (state["processing_end_time"] - state["processing_start_time"]).total_seconds()
            state["processing_duration"] = duration
        
        state["messages"].append(
            SystemMessage(content=f"文档处理失败: {state.get('error_message', '未知错误')}")
        )
        
        # TODO: 更新数据库中的文档状态
        await self._update_document_status(state)
        
        return state
    
    # 条件判断函数
    def _should_validate_content(self, state: DocumentProcessingState) -> str:
        """判断是否应该验证内容"""
        if state["status"] == ProcessingStatus.FAILED:
            return "error"
        if state["parsed_content"] is None:
            return "error"
        return "validate"
    
    def _should_proceed_to_chunking(self, state: DocumentProcessingState) -> str:
        """判断是否应该进行分块"""
        if state["status"] == ProcessingStatus.FAILED:
            return "error"
        return "chunk"
    
    def _should_index_content(self, state: DocumentProcessingState) -> str:
        """判断是否应该索引内容"""
        if state["status"] == ProcessingStatus.FAILED:
            return "error"
        if not state["embeddings"]:
            return "error"
        return "index"
    
    # 辅助方法
    async def _calculate_content_quality(self, content: DocumentContent) -> float:
        """计算内容质量分数"""
        try:
            score = 0.0
            
            # 文本长度检查 (30%)
            text_length = len(content.text.strip())
            if text_length > 100:
                score += 0.3
            elif text_length > 50:
                score += 0.15
            
            # 结构化程度检查 (25%)
            if content.structure.get("sections"):
                score += 0.25
            elif content.structure.get("paragraph_count", 0) > 1:
                score += 0.1
            
            # 元数据完整性检查 (20%)
            metadata_fields = ["title", "author", "creation_date", "file_size"]
            filled_fields = sum(1 for field in metadata_fields if content.metadata.get(field))
            score += (filled_fields / len(metadata_fields)) * 0.2
            
            # 内容可读性检查 (25%)
            # 简单检查：字母数字比例
            text = content.text
            alphanumeric_chars = sum(1 for c in text if c.isalnum())
            if len(text) > 0:
                readability_ratio = alphanumeric_chars / len(text)
                if readability_ratio > 0.7:
                    score += 0.25
                elif readability_ratio > 0.5:
                    score += 0.15
            
            return min(score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"质量评分计算失败: {str(e)}")
            return 0.5  # 默认中等质量
    
    async def _update_document_status(self, state: DocumentProcessingState):
        """更新文档状态到数据库"""
        try:
            # TODO: 实现数据库更新逻辑
            # 这里应该更新Document模型的状态
            pass
        except Exception as e:
            self.logger.error(f"更新文档状态失败: {str(e)}")
    
    async def get_processing_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取处理状态"""
        try:
            # TODO: 从检查点存储中获取状态
            # 这需要根据document_id查找对应的线程ID
            return None
        except Exception as e:
            self.logger.error(f"获取处理状态失败: {str(e)}")
            return None
    
    async def cancel_processing(self, document_id: str) -> bool:
        """取消处理"""
        try:
            # TODO: 实现处理取消逻辑
            return False
        except Exception as e:
            self.logger.error(f"取消处理失败: {str(e)}")
            return False


# 全局实例
document_processing_agent = DocumentProcessingAgent()


# 便捷函数
async def process_document(
    project_id: str,
    document_id: str,
    file_path: str,
    config: Optional[DocumentProcessingConfig] = None
) -> DocumentProcessingState:
    """处理文档的便捷函数"""
    return await document_processing_agent.process_document(
        project_id, document_id, file_path, config
    )


async def get_processing_status(document_id: str) -> Optional[Dict[str, Any]]:
    """获取处理状态的便捷函数"""
    return await document_processing_agent.get_processing_status(document_id)


async def cancel_processing(document_id: str) -> bool:
    """取消处理的便捷函数"""
    return await document_processing_agent.cancel_processing(document_id) 