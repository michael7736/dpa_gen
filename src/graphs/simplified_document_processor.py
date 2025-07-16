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
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
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
        
        # 导入VectorConfig
        from ..core.vectorization import VectorConfig
        vector_config = VectorConfig(
            model_name="text-embedding-3-large",
            dimension=3072,  # text-embedding-3-large的维度
            distance_metric="cosine",
            batch_size=100
        )
        # 从配置获取Qdrant URL
        from ..config.settings import get_settings
        settings = get_settings()
        self.qdrant_url = f"http://{settings.qdrant.host}:{settings.qdrant.port}"
        # 注意：不在这里初始化vector_store，因为collection_name需要根据项目动态确定
        self.vector_config = vector_config
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
        """解析文档 - 优化版，提高成功率"""
        state["status"] = "processing"
        state["progress"] = 20.0
        
        try:
            file_path = Path(state["file_path"])
            
            # 检查文件是否存在
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size == 0:
                raise ValueError("File is empty")
            
            # 根据文件类型选择加载器
            file_extension = file_path.suffix.lower()
            content = ""
            documents = []
            
            try:
                if file_extension == '.pdf':
                    loader = PyPDFLoader(str(file_path))
                    documents = loader.load()
                elif file_extension in ['.docx', '.doc']:
                    loader = Docx2txtLoader(str(file_path))
                    documents = loader.load()
                elif file_extension in ['.txt', '.md', '.py', '.js', '.json', '.yaml', '.yml']:
                    # 处理文本文件，支持多种编码
                    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin-1']
                    for encoding in encodings:
                        try:
                            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                                content = await f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # 如果所有编码都失败，使用二进制模式读取并忽略错误
                        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = await f.read()
                    
                    # 创建文档对象
                    from langchain.schema import Document
                    documents = [Document(page_content=content, metadata={"source": str(file_path)})]
                else:
                    # 尝试作为文本文件处理
                    self.logger.warning(f"Unknown file type: {file_extension}, attempting text processing")
                    loader = TextLoader(str(file_path), encoding='utf-8')
                    try:
                        documents = loader.load()
                    except Exception:
                        # 如果失败，尝试其他编码
                        loader = TextLoader(str(file_path), encoding='gbk')
                        documents = loader.load()
            
            except Exception as load_error:
                self.logger.warning(f"Primary loader failed: {load_error}, attempting fallback")
                # 最后的尝试：直接读取文件内容
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = await f.read()
                    from langchain.schema import Document
                    documents = [Document(page_content=content, metadata={"source": str(file_path)})]
                except Exception as fallback_error:
                    raise Exception(f"All parsing attempts failed: {fallback_error}")
            
            # 合并内容
            if not content and documents:
                content = "\n\n".join([doc.page_content for doc in documents])
            
            # 清理内容
            content = self._clean_content(content)
            
            # 验证内容
            if not content or len(content.strip()) < 10:
                raise ValueError("Document content is too short or empty after parsing")
            
            state["content"] = content
            
            # 提取基础元数据
            state["metadata"] = {
                "file_name": state["file_name"],
                "file_size": file_size,
                "pages": len(documents),
                "content_length": len(content),
                "parsed_at": datetime.now().isoformat(),
                "file_type": file_extension
            }
            
            self.logger.info(f"Successfully parsed document: {state['file_name']} ({len(content)} chars)")
            
        except Exception as e:
            state["status"] = "error"
            state["error_message"] = f"Failed to parse document: {str(e)}"
            self.logger.error(f"Document parsing error for {state.get('file_name', 'unknown')}: {e}")
            raise
        
        return state
    
    def _clean_content(self, content: str) -> str:
        """清理文档内容"""
        # 移除过多的空白
        content = ' '.join(content.split())
        
        # 移除控制字符
        import re
        content = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', content)
        
        # 确保段落之间有适当的分隔
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
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
    
    def store_results(self, state: SimplifiedDocumentState) -> SimplifiedDocumentState:
        """存储结果到向量数据库"""
        state["progress"] = 90.0
        
        try:
            chunks = state.get("chunks", [])
            embeddings = state.get("embeddings", [])
            
            if len(chunks) != len(embeddings):
                raise ValueError("Chunks and embeddings count mismatch")
            
            # 准备文档格式
            from langchain.schema import Document as LangchainDocument
            documents = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                doc = LangchainDocument(
                    page_content=chunk["content"],
                    metadata={
                        **chunk["metadata"],
                        **state["metadata"],
                        "chunk_index": i,
                        "document_id": state["document_id"]
                    }
                )
                documents.append(doc)
            
            # 批量存储到向量数据库
            # 使用同步的方式直接存储到Qdrant
            from qdrant_client.models import PointStruct
            import uuid
            
            points = []
            stored_ids = []
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                point_id = str(uuid.uuid4())
                stored_ids.append(point_id)
                
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": doc.page_content,
                        **doc.metadata
                    }
                ))
            
            # 创建项目特定的向量存储
            collection_name = f"project_{state['project_id']}"
            from ..core.vectorization import VectorStore
            vector_store = VectorStore(
                config=self.vector_config,
                qdrant_url=self.qdrant_url,
                collection_name=collection_name
            )
            
            # 直接使用Qdrant客户端
            vector_store.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
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
    
    def complete_processing(self, state: SimplifiedDocumentState) -> SimplifiedDocumentState:
        """完成处理并评估文档质量"""
        state["status"] = "completed"
        state["progress"] = 100.0
        state["end_time"] = datetime.now()
        
        # 计算处理时间
        if state.get("start_time"):
            state["processing_time_seconds"] = (
                state["end_time"] - state["start_time"]
            ).total_seconds()
        
        # 执行文档质量评估
        quality_assessment = self._assess_document_quality(state)
        state["metadata"]["quality_assessment"] = quality_assessment
        
        # 根据质量评估添加标记
        if quality_assessment["overall_score"] < 0.5:
            self.logger.warning(
                f"Low quality document detected: {state['file_name']} "
                f"(score: {quality_assessment['overall_score']:.2f})"
            )
        
        self.logger.info(
            f"Document processing completed: {state['file_name']} "
            f"in {state.get('processing_time_seconds', 0):.2f}s "
            f"(quality score: {quality_assessment['overall_score']:.2f})"
        )
        
        return state
    
    def _assess_document_quality(self, state: SimplifiedDocumentState) -> Dict[str, Any]:
        """评估文档质量"""
        quality_metrics = {
            "content_length": 0.0,
            "chunk_uniformity": 0.0,
            "text_density": 0.0,
            "readability": 0.0,
            "overall_score": 0.0
        }
        
        content = state.get("content", "")
        chunks = state.get("chunks", [])
        
        if not content or not chunks:
            return quality_metrics
        
        # 1. 内容长度评分（太短或太长都不好）
        content_length = len(content)
        if content_length < 100:
            quality_metrics["content_length"] = 0.2
        elif content_length < 500:
            quality_metrics["content_length"] = 0.5
        elif content_length < 50000:
            quality_metrics["content_length"] = 1.0
        elif content_length < 100000:
            quality_metrics["content_length"] = 0.8
        else:
            quality_metrics["content_length"] = 0.6
        
        # 2. 分块均匀性评分
        if len(chunks) > 1:
            chunk_sizes = [len(chunk["content"]) for chunk in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes)
            variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
            std_dev = variance ** 0.5
            
            # 变异系数（标准差/平均值）
            cv = std_dev / avg_size if avg_size > 0 else 1.0
            # CV越小，均匀性越好
            quality_metrics["chunk_uniformity"] = max(0, 1 - cv)
        else:
            quality_metrics["chunk_uniformity"] = 1.0
        
        # 3. 文本密度评分（非空白字符比例）
        non_whitespace = len(content.replace(" ", "").replace("\n", "").replace("\t", ""))
        text_density = non_whitespace / content_length if content_length > 0 else 0
        quality_metrics["text_density"] = min(text_density * 1.5, 1.0)  # 调整到0-1范围
        
        # 4. 可读性评分（基于平均句子长度和词汇多样性）
        sentences = content.split('.')
        avg_sentence_length = len(content) / len(sentences) if sentences else 0
        
        # 理想句子长度在15-25个词之间
        if 15 <= avg_sentence_length / 5 <= 25:  # 假设平均每个词5个字符
            quality_metrics["readability"] = 1.0
        elif 10 <= avg_sentence_length / 5 <= 30:
            quality_metrics["readability"] = 0.8
        else:
            quality_metrics["readability"] = 0.5
        
        # 计算总体评分（加权平均）
        weights = {
            "content_length": 0.2,
            "chunk_uniformity": 0.3,
            "text_density": 0.2,
            "readability": 0.3
        }
        
        quality_metrics["overall_score"] = sum(
            quality_metrics[metric] * weight 
            for metric, weight in weights.items()
        )
        
        # 添加其他有用的元数据
        quality_metrics["chunk_count"] = len(chunks)
        quality_metrics["avg_chunk_size"] = sum(len(c["content"]) for c in chunks) / len(chunks) if chunks else 0
        quality_metrics["content_type"] = self._detect_content_type(content)
        
        return quality_metrics
    
    def _detect_content_type(self, content: str) -> str:
        """检测文档内容类型"""
        # 简单的启发式检测
        lower_content = content.lower()
        
        if any(keyword in lower_content for keyword in ['abstract', 'introduction', 'conclusion', 'references']):
            return "academic"
        elif any(keyword in lower_content for keyword in ['function', 'class', 'def', 'import', 'return']):
            return "code"
        elif any(keyword in lower_content for keyword in ['chapter', 'section', 'subsection']):
            return "book"
        elif any(keyword in lower_content for keyword in ['dear', 'sincerely', 'regards']):
            return "correspondence"
        else:
            return "general"
    
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