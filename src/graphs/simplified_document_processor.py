"""
简化版文档处理器
专注于稳定性和成功率，移除实验性功能
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
import aiofiles

from ..config.settings import get_settings
from ..core.vectorization import VectorStore
from ..services.cache_service import CacheService
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ProcessingMode(str, Enum):
    """处理模式"""
    STANDARD = "standard"  # 标准处理
    FAST = "fast"  # 快速处理


class SimplifiedDocumentState(TypedDict):
    """简化的文档处理状态"""
    # 基础信息
    document_id: str
    project_id: str
    file_path: str
    file_name: str
    mode: ProcessingMode
    
    # 处理状态
    status: str  # pending, processing, completed, error
    progress: float
    error_message: Optional[str]
    
    # 处理结果
    content: Optional[str]
    chunks: List[Dict[str, Any]]
    embeddings: List[List[float]]
    metadata: Dict[str, Any]
    
    # 性能指标
    start_time: datetime
    end_time: Optional[datetime]
    processing_time_seconds: Optional[float]


class SimplifiedDocumentProcessor:
    """简化版文档处理器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # 使用更快的模型
        self.vector_store = VectorStore()
        self.cache_service = CacheService()
        
        # 文本分割器配置
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""]
        )
        
        # 构建工作流
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """构建简化的处理流程"""
        graph = StateGraph(SimplifiedDocumentState)
        
        # 简化的处理步骤
        graph.add_node("parse", self.parse_document)
        graph.add_node("chunk", self.chunk_document)
        graph.add_node("embed", self.embed_chunks)
        graph.add_node("store", self.store_results)
        graph.add_node("complete", self.complete_processing)
        
        # 线性流程，减少复杂性
        graph.set_entry_point("parse")
        graph.add_edge("parse", "chunk")
        graph.add_edge("chunk", "embed")
        graph.add_edge("embed", "store")
        graph.add_edge("store", "complete")
        graph.add_edge("complete", END)
        
        return graph
    
    async def parse_document(self, state: SimplifiedDocumentState) -> SimplifiedDocumentState:
        """解析文档 - 简化版"""
        state["status"] = "processing"
        state["progress"] = 20.0
        
        try:
            file_path = Path(state["file_path"])
            
            # 根据文件类型选择加载器
            if file_path.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                loader = Docx2txtLoader(str(file_path))
            elif file_path.suffix.lower() in ['.txt', '.md']:
                loader = TextLoader(str(file_path))
            else:
                # 尝试作为文本文件处理
                loader = TextLoader(str(file_path))
            
            # 加载文档
            documents = loader.load()
            
            # 合并内容
            content = "\n\n".join([doc.page_content for doc in documents])
            state["content"] = content
            
            # 提取基础元数据
            state["metadata"] = {
                "file_name": state["file_name"],
                "file_size": file_path.stat().st_size,
                "pages": len(documents),
                "parsed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully parsed document: {state['file_name']}")
            
        except Exception as e:
            state["status"] = "error"
            state["error_message"] = f"Failed to parse document: {str(e)}"
            self.logger.error(f"Document parsing error: {e}")
            raise
        
        return state
    
    async def chunk_document(self, state: SimplifiedDocumentState) -> SimplifiedDocumentState:
        """文档分块 - 使用标准方法"""
        state["progress"] = 40.0
        
        try:
            content = state.get("content", "")
            if not content:
                raise ValueError("No content to chunk")
            
            # 根据模式调整分块大小
            if state["mode"] == ProcessingMode.FAST:
                self.text_splitter.chunk_size = 1500
                self.text_splitter.chunk_overlap = 100
            else:
                self.text_splitter.chunk_size = 1000
                self.text_splitter.chunk_overlap = 200
            
            # 执行分块
            chunks = self.text_splitter.split_text(content)
            
            # 构建块对象
            state["chunks"] = [
                {
                    "content": chunk,
                    "index": i,
                    "metadata": {
                        "document_id": state["document_id"],
                        "chunk_size": len(chunk),
                        "position": i / len(chunks)  # 相对位置
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
            
            self.logger.info(f"Created {len(chunks)} chunks for document")
            
        except Exception as e:
            state["status"] = "error"
            state["error_message"] = f"Failed to chunk document: {str(e)}"
            self.logger.error(f"Chunking error: {e}")
            raise
        
        return state
    
    async def embed_chunks(self, state: SimplifiedDocumentState) -> SimplifiedDocumentState:
        """生成嵌入向量 - 批量处理"""
        state["progress"] = 60.0
        
        try:
            chunks = state.get("chunks", [])
            if not chunks:
                raise ValueError("No chunks to embed")
            
            # 检查缓存
            cache_key = f"embeddings:{state['document_id']}"
            cached_embeddings = await self.cache_service.get(cache_key)
            
            if cached_embeddings:
                state["embeddings"] = cached_embeddings
                self.logger.info("Using cached embeddings")
            else:
                # 批量生成嵌入
                texts = [chunk["content"] for chunk in chunks]
                batch_size = 20  # OpenAI建议的批量大小
                all_embeddings = []
                
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    embeddings = await self.embeddings_model.aembed_documents(batch)
                    all_embeddings.extend(embeddings)
                    
                    # 更新进度
                    progress = 60 + (i / len(texts)) * 20
                    state["progress"] = min(progress, 80.0)
                
                state["embeddings"] = all_embeddings
                
                # 缓存结果
                await self.cache_service.set(cache_key, all_embeddings, ttl=86400)  # 24小时
            
            self.logger.info(f"Generated {len(state['embeddings'])} embeddings")
            
        except Exception as e:
            state["status"] = "error"
            state["error_message"] = f"Failed to generate embeddings: {str(e)}"
            self.logger.error(f"Embedding error: {e}")
            raise
        
        return state
    
    async def store_results(self, state: SimplifiedDocumentState) -> SimplifiedDocumentState:
        """存储结果到向量数据库"""
        state["progress"] = 90.0
        
        try:
            chunks = state.get("chunks", [])
            embeddings = state.get("embeddings", [])
            
            if len(chunks) != len(embeddings):
                raise ValueError("Chunks and embeddings count mismatch")
            
            # 批量存储到向量数据库
            stored_ids = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk_id = await self.vector_store.add(
                    collection_name=f"project_{state['project_id']}",
                    document={
                        "id": f"{state['document_id']}_{chunk['index']}",
                        "content": chunk["content"],
                        "embedding": embedding,
                        "metadata": {
                            **chunk["metadata"],
                            **state["metadata"]
                        }
                    }
                )
                stored_ids.append(chunk_id)
            
            # 更新文档元数据
            state["metadata"]["chunk_count"] = len(chunks)
            state["metadata"]["stored_ids"] = stored_ids
            
            self.logger.info(f"Stored {len(stored_ids)} chunks to vector database")
            
        except Exception as e:
            state["status"] = "error"
            state["error_message"] = f"Failed to store results: {str(e)}"
            self.logger.error(f"Storage error: {e}")
            raise
        
        return state
    
    async def complete_processing(self, state: SimplifiedDocumentState) -> SimplifiedDocumentState:
        """完成处理"""
        state["status"] = "completed"
        state["progress"] = 100.0
        state["end_time"] = datetime.now()
        
        # 计算处理时间
        if state.get("start_time"):
            state["processing_time_seconds"] = (
                state["end_time"] - state["start_time"]
            ).total_seconds()
        
        # 生成摘要（可选）
        if state["mode"] == ProcessingMode.STANDARD and state.get("content"):
            try:
                summary = await self._generate_summary(state["content"][:2000])
                state["metadata"]["summary"] = summary
            except:
                # 摘要生成失败不影响整体流程
                pass
        
        self.logger.info(
            f"Document processing completed: {state['file_name']} "
            f"in {state.get('processing_time_seconds', 0):.2f}s"
        )
        
        return state
    
    async def _generate_summary(self, content: str) -> str:
        """生成文档摘要"""
        prompt = f"请用100字以内总结以下文档的主要内容：\n\n{content}"
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
    
    async def process_document(self, document_info: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个文档的入口方法"""
        initial_state = SimplifiedDocumentState(
            document_id=document_info["document_id"],
            project_id=document_info["project_id"],
            file_path=document_info["file_path"],
            file_name=document_info["file_name"],
            mode=document_info.get("mode", ProcessingMode.STANDARD),
            status="pending",
            progress=0.0,
            error_message=None,
            content=None,
            chunks=[],
            embeddings=[],
            metadata={},
            start_time=datetime.now(),
            end_time=None,
            processing_time_seconds=None
        )
        
        try:
            # 执行处理流程
            result = await self.app.ainvoke(initial_state)
            return {
                "success": True,
                "document_id": result["document_id"],
                "status": result["status"],
                "metadata": result["metadata"],
                "processing_time": result.get("processing_time_seconds")
            }
        except Exception as e:
            return {
                "success": False,
                "document_id": document_info["document_id"],
                "error": str(e)
            }
    
    async def process_batch(self, documents: List[Dict[str, Any]], 
                          max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """批量处理文档"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_limit(doc):
            async with semaphore:
                return await self.process_document(doc)
        
        results = await asyncio.gather(
            *[process_with_limit(doc) for doc in documents],
            return_exceptions=True
        )
        
        return [
            result if not isinstance(result, Exception) 
            else {"success": False, "error": str(result)}
            for result in results
        ]