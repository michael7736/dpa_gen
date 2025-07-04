"""
改进版文档处理智能体
包含完善的错误处理、降级策略和性能优化
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Union, Callable
from uuid import uuid4
from enum import Enum
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import aiofiles

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

from ..config.settings import get_settings
from ..core.chunking import DocumentChunker, ChunkingStrategy
from ..core.vectorization import VectorStore
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ProcessingStrategy(str, Enum):
    """处理策略枚举"""
    FULL = "full"  # 完整处理（包括语义分块）
    STANDARD = "standard"  # 标准处理（传统分块）
    FAST = "fast"  # 快速处理（简化流程）
    FALLBACK = "fallback"  # 降级处理


class DocumentProcessingState(TypedDict):
    """文档处理状态 - 增强版"""
    # 输入信息
    project_id: str
    document_id: str
    file_path: str
    file_name: str
    processing_strategy: ProcessingStrategy
    
    # 处理过程状态
    current_step: str
    progress: float
    status: str
    errors: List[Dict[str, Any]]  # 错误记录
    warnings: List[str]  # 警告信息
    
    # 处理结果
    parsed_content: Optional[Dict[str, Any]]
    chunks: List[Dict[str, Any]]
    embeddings: List[List[float]]
    indexed: bool
    
    # 文档元数据
    metadata: Dict[str, Any]  # 标题、作者、创建时间等
    quality_score: float  # 文档质量评分
    extended_metadata: Dict[str, Any]  # 扩展元数据（引用、置信度等）
    
    # 性能指标
    processing_start_time: datetime
    processing_end_time: Optional[datetime]
    step_durations: Dict[str, float]  # 各步骤耗时
    
    # 重试和降级
    retry_count: int
    max_retries: int
    fallback_triggered: bool
    
    # 缓存相关
    document_hash: str  # 文档哈希值
    use_cache: bool  # 是否使用缓存


class ImprovedDocumentProcessingAgent:
    """改进版文档处理智能体"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.logger = get_logger(__name__)
        self.chunker = DocumentChunker()
        self.vector_store = VectorStore()
        self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # 构建状态图
        self.graph = self._build_graph()
        
        # 设置检查点
        self.checkpointer = MemorySaver()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        
        # 性能监控
        self.metrics = {
            "total_processed": 0,
            "success_count": 0,
            "error_count": 0,
            "fallback_count": 0,
            "cache_hits": 0
        }
        
        # 进度回调
        self.progress_callback = progress_callback
        
        # 并发控制
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.processing_lock = asyncio.Lock()
        
        # 缓存配置
        self.cache_dir = Path("data/cache/documents")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _build_graph(self) -> StateGraph:
        """构建改进的文档处理状态图"""
        graph = StateGraph(DocumentProcessingState)
        
        # 添加节点
        graph.add_node("initialize", self._initialize_processing)
        graph.add_node("check_cache", self._check_cache)
        graph.add_node("validate_input", self._validate_input)
        graph.add_node("parse_document", self._parse_document_with_retry)
        graph.add_node("extract_metadata", self._extract_metadata)
        graph.add_node("assess_quality", self._assess_document_quality)
        graph.add_node("chunk_document", self._chunk_document_with_fallback)
        graph.add_node("generate_embeddings", self._generate_embeddings_batch)
        graph.add_node("store_results", self._store_results_with_validation)
        graph.add_node("update_cache", self._update_cache)
        graph.add_node("handle_error", self._handle_error)
        graph.add_node("finalize", self._finalize_processing)
        
        # 定义工作流
        graph.set_entry_point("initialize")
        
        # 条件路由
        graph.add_conditional_edges(
            "initialize",
            self._should_continue,
            {
                "continue": "check_cache",
                "error": "handle_error"
            }
        )
        
        graph.add_conditional_edges(
            "check_cache",
            self._check_cache_result,
            {
                "hit": "finalize",
                "miss": "validate_input"
            }
        )
        
        graph.add_edge("validate_input", "parse_document")
        
        graph.add_conditional_edges(
            "parse_document",
            self._check_parsing_result,
            {
                "success": "extract_metadata",
                "retry": "parse_document",
                "error": "handle_error"
            }
        )
        
        graph.add_edge("extract_metadata", "assess_quality")
        graph.add_edge("assess_quality", "chunk_document")
        
        graph.add_conditional_edges(
            "chunk_document",
            self._check_chunking_result,
            {
                "success": "generate_embeddings",
                "fallback": "chunk_document",
                "error": "handle_error"
            }
        )
        
        graph.add_edge("generate_embeddings", "store_results")
        graph.add_edge("store_results", "update_cache")
        graph.add_edge("update_cache", "finalize")
        graph.add_edge("handle_error", "finalize")
        graph.add_edge("finalize", END)
        
        return graph
    
    async def _initialize_processing(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """初始化处理状态"""
        state["processing_start_time"] = datetime.now()
        state["current_step"] = "initialize"
        state["progress"] = 0.0
        state["status"] = "processing"
        state["errors"] = []
        state["warnings"] = []
        state["step_durations"] = {}
        state["retry_count"] = 0
        state["max_retries"] = 3
        state["fallback_triggered"] = False
        state["metadata"] = {}
        state["quality_score"] = 0.0
        state["extended_metadata"] = {}
        state["use_cache"] = True
        
        # 计算文档哈希
        state["document_hash"] = await self._calculate_document_hash(state["file_path"])
        
        # 根据文件大小选择处理策略
        file_size = Path(state["file_path"]).stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50MB
            state["processing_strategy"] = ProcessingStrategy.FAST
            state["warnings"].append("Large file detected, using fast processing strategy")
        
        self.logger.info(f"Initialized processing for document: {state['file_name']}")
        
        # 触发进度回调
        if self.progress_callback:
            await self.progress_callback({
                "document_id": state["document_id"],
                "step": "initialize",
                "progress": state["progress"],
                "status": state["status"]
            })
        
        return state
    
    def _should_continue(self, state: DocumentProcessingState) -> str:
        """判断是否继续处理"""
        if state.get("errors"):
            return "error"
        return "continue"
    
    async def _validate_input(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """验证输入文件"""
        start_time = datetime.now()
        state["current_step"] = "validate_input"
        state["progress"] = 10.0
        
        try:
            file_path = Path(state["file_path"])
            
            # 检查文件是否存在
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # 检查文件类型
            supported_types = ['.pdf', '.docx', '.txt', '.md']
            if file_path.suffix.lower() not in supported_types:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # 检查文件大小
            max_size = 100 * 1024 * 1024  # 100MB
            if file_path.stat().st_size > max_size:
                raise ValueError(f"File too large: {file_path.stat().st_size / 1024 / 1024:.1f}MB")
            
            self.logger.info(f"Input validation passed for: {state['file_name']}")
            
        except Exception as e:
            state["errors"].append({
                "step": "validate_input",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            state["status"] = "error"
            self.logger.error(f"Input validation failed: {e}")
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            state["step_durations"]["validate_input"] = duration
        
        return state
    
    async def _parse_document_with_retry(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """解析文档（带重试机制）"""
        start_time = datetime.now()
        state["current_step"] = "parse_document"
        state["progress"] = 30.0
        
        try:
            # 根据策略选择解析器
            if state["processing_strategy"] == ProcessingStrategy.FAST:
                content = await self._fast_parse(state["file_path"])
            else:
                content = await self._standard_parse(state["file_path"])
            
            state["parsed_content"] = content
            state["retry_count"] = 0  # 重置重试计数
            self.logger.info(f"Document parsed successfully: {state['file_name']}")
            
        except Exception as e:
            state["retry_count"] += 1
            error_msg = f"Parse attempt {state['retry_count']} failed: {str(e)}"
            state["errors"].append({
                "step": "parse_document",
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "retry_count": state["retry_count"]
            })
            self.logger.warning(error_msg)
            
            # 如果还有重试机会，继续重试
            if state["retry_count"] < state["max_retries"]:
                await asyncio.sleep(2 ** state["retry_count"])  # 指数退避
            else:
                state["status"] = "error"
                self.logger.error(f"Document parsing failed after {state['retry_count']} attempts")
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            state["step_durations"]["parse_document"] = duration
        
        return state
    
    def _check_parsing_result(self, state: DocumentProcessingState) -> str:
        """检查解析结果"""
        if state.get("parsed_content"):
            return "success"
        elif state["retry_count"] < state["max_retries"]:
            return "retry"
        else:
            return "error"
    
    async def _chunk_document_with_fallback(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """文档分块（带降级策略）"""
        start_time = datetime.now()
        state["current_step"] = "chunk_document"
        state["progress"] = 50.0
        
        try:
            content = state.get("parsed_content", {}).get("text", "")
            
            if not content:
                raise ValueError("No content to chunk")
            
            # 尝试语义分块
            if (state["processing_strategy"] == ProcessingStrategy.FULL and 
                not state["fallback_triggered"]):
                try:
                    chunks = await self._semantic_chunking(content)
                    state["chunks"] = chunks
                    self.logger.info("Semantic chunking completed successfully")
                except Exception as e:
                    state["warnings"].append(f"Semantic chunking failed: {e}, falling back to standard chunking")
                    state["fallback_triggered"] = True
                    raise e
            else:
                # 使用标准分块
                chunks = await self._standard_chunking(content)
                state["chunks"] = chunks
                self.logger.info("Standard chunking completed successfully")
            
        except Exception as e:
            if not state["fallback_triggered"] and state["processing_strategy"] == ProcessingStrategy.FULL:
                # 触发降级
                state["fallback_triggered"] = True
                state["processing_strategy"] = ProcessingStrategy.STANDARD
                self.metrics["fallback_count"] += 1
                self.logger.warning(f"Triggering fallback strategy: {e}")
            else:
                # 降级也失败了
                state["errors"].append({
                    "step": "chunk_document",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                state["status"] = "error"
                self.logger.error(f"Document chunking failed: {e}")
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            state["step_durations"]["chunk_document"] = duration
        
        return state
    
    def _check_chunking_result(self, state: DocumentProcessingState) -> str:
        """检查分块结果"""
        if state.get("chunks"):
            return "success"
        elif state["fallback_triggered"] and not state.get("chunks"):
            return "fallback"
        else:
            return "error"
    
    async def _generate_embeddings_batch(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """批量生成嵌入向量"""
        start_time = datetime.now()
        state["current_step"] = "generate_embeddings"
        state["progress"] = 70.0
        
        try:
            chunks = state.get("chunks", [])
            if not chunks:
                raise ValueError("No chunks to embed")
            
            # 批量处理，避免超时
            batch_size = 10
            all_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_texts = [chunk["content"] for chunk in batch]
                
                # 生成嵌入
                embeddings = await self.vector_store.embed_batch(batch_texts)
                all_embeddings.extend(embeddings)
                
                # 更新进度
                progress = 70 + (i / len(chunks)) * 20
                state["progress"] = min(progress, 90.0)
            
            state["embeddings"] = all_embeddings
            self.logger.info(f"Generated {len(all_embeddings)} embeddings")
            
        except Exception as e:
            state["errors"].append({
                "step": "generate_embeddings",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            state["status"] = "error"
            self.logger.error(f"Embedding generation failed: {e}")
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            state["step_durations"]["generate_embeddings"] = duration
        
        return state
    
    async def _store_results_with_validation(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """存储结果（带验证）"""
        start_time = datetime.now()
        state["current_step"] = "store_results"
        state["progress"] = 90.0
        
        try:
            # 验证数据完整性
            chunks = state.get("chunks", [])
            embeddings = state.get("embeddings", [])
            
            if len(chunks) != len(embeddings):
                raise ValueError(f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch")
            
            # 存储到向量数据库
            stored_count = 0
            for chunk, embedding in zip(chunks, embeddings):
                try:
                    await self.vector_store.store(
                        document_id=state["document_id"],
                        chunk=chunk,
                        embedding=embedding,
                        metadata={
                            "project_id": state["project_id"],
                            "processing_strategy": state["processing_strategy"]
                        }
                    )
                    stored_count += 1
                except Exception as e:
                    state["warnings"].append(f"Failed to store chunk {chunk.get('index')}: {e}")
            
            state["indexed"] = stored_count > 0
            
            if stored_count < len(chunks):
                state["warnings"].append(f"Only {stored_count}/{len(chunks)} chunks were stored successfully")
            
            self.logger.info(f"Stored {stored_count} chunks to vector database")
            
        except Exception as e:
            state["errors"].append({
                "step": "store_results",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            state["status"] = "error"
            self.logger.error(f"Results storage failed: {e}")
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            state["step_durations"]["store_results"] = duration
        
        return state
    
    async def _handle_error(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """集中错误处理"""
        state["current_step"] = "error_handling"
        state["status"] = "error"
        
        # 记录错误到监控系统
        for error in state["errors"]:
            self.logger.error(f"Error in {error['step']}: {error['error']}")
        
        # 清理临时资源
        try:
            await self._cleanup_resources(state)
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
        
        # 更新指标
        self.metrics["error_count"] += 1
        
        return state
    
    async def _finalize_processing(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """完成处理"""
        state["processing_end_time"] = datetime.now()
        state["progress"] = 100.0
        
        # 计算总耗时
        total_duration = (state["processing_end_time"] - state["processing_start_time"]).total_seconds()
        
        # 更新指标
        self.metrics["total_processed"] += 1
        if state["status"] != "error":
            state["status"] = "completed"
            self.metrics["success_count"] += 1
        
        # 记录性能日志
        self.logger.info(f"""
        Document processing completed:
        - Document: {state['file_name']}
        - Status: {state['status']}
        - Total duration: {total_duration:.2f}s
        - Chunks created: {len(state.get('chunks', []))}
        - Warnings: {len(state['warnings'])}
        - Errors: {len(state['errors'])}
        - Strategy: {state['processing_strategy']}
        - Fallback triggered: {state['fallback_triggered']}
        """)
        
        return state
    
    # 辅助方法
    async def _calculate_document_hash(self, file_path: str) -> str:
        """计算文档哈希值"""
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            return hashlib.sha256(content).hexdigest()
    
    async def _check_cache(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """检查缓存"""
        state["current_step"] = "check_cache"
        
        if not state["use_cache"]:
            return state
        
        cache_file = self.cache_dir / f"{state['document_hash']}.json"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r') as f:
                    cached_data = json.loads(await f.read())
                    
                # 恢复缓存的数据
                state["chunks"] = cached_data["chunks"]
                state["embeddings"] = cached_data["embeddings"]
                state["metadata"] = cached_data["metadata"]
                state["extended_metadata"] = cached_data.get("extended_metadata", {})
                state["quality_score"] = cached_data["quality_score"]
                state["indexed"] = True
                state["status"] = "cached"
                
                self.metrics["cache_hits"] += 1
                self.logger.info(f"Cache hit for document: {state['file_name']}")
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")
        
        return state
    
    def _check_cache_result(self, state: DocumentProcessingState) -> str:
        """检查缓存结果"""
        if state.get("status") == "cached":
            return "hit"
        return "miss"
    
    async def _fast_parse(self, file_path: str) -> Dict[str, Any]:
        """快速解析（简化版）"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.txt':
            loader = TextLoader(file_path)
        elif file_ext == '.md':
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            # 默认使用文本加载器
            loader = TextLoader(file_path)
        
        documents = loader.load()
        return {
            "text": "\n".join([doc.page_content for doc in documents]),
            "pages": len(documents)
        }
    
    async def _standard_parse(self, file_path: str) -> Dict[str, Any]:
        """标准解析"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_ext == '.docx':
            loader = Docx2txtLoader(file_path)
        elif file_ext == '.txt':
            loader = TextLoader(file_path)
        elif file_ext == '.md':
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        documents = loader.load()
        
        # 提取文本和元数据
        text = "\n".join([doc.page_content for doc in documents])
        metadata = documents[0].metadata if documents else {}
        
        return {
            "text": text,
            "pages": len(documents),
            "metadata": metadata
        }
    
    async def _extract_metadata(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """提取文档元数据"""
        start_time = datetime.now()
        state["current_step"] = "extract_metadata"
        state["progress"] = 35.0
        
        try:
            parsed_content = state.get("parsed_content", {})
            
            # 基础元数据
            state["metadata"]["file_name"] = state["file_name"]
            state["metadata"]["file_size"] = Path(state["file_path"]).stat().st_size
            state["metadata"]["pages"] = parsed_content.get("pages", 1)
            
            # 从解析内容中提取的元数据
            if "metadata" in parsed_content:
                state["metadata"].update(parsed_content["metadata"])
            
            # 使用LLM提取额外元数据
            if state["processing_strategy"] != ProcessingStrategy.FAST:
                text_sample = parsed_content.get("text", "")[:3000]
                if text_sample:
                    extracted = await self._extract_metadata_with_llm(text_sample)
                    state["metadata"].update(extracted["basic_metadata"])
                    state["extended_metadata"] = extracted["extended_metadata"]
            
            self.logger.info(f"Metadata extracted for: {state['file_name']}")
            
        except Exception as e:
            state["warnings"].append(f"Metadata extraction warning: {e}")
            self.logger.warning(f"Metadata extraction error: {e}")
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            state["step_durations"]["extract_metadata"] = duration
        
        return state
    
    async def _assess_document_quality(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """评估文档质量"""
        start_time = datetime.now()
        state["current_step"] = "assess_quality"
        state["progress"] = 40.0
        
        try:
            content = state.get("parsed_content", {}).get("text", "")
            extended_metadata = state.get("extended_metadata", {})
            
            # 基础质量指标
            quality_factors = {
                "length": min(len(content) / 10000, 1.0),  # 文档长度
                "structure": 0.5,  # 默认结构分数
                "readability": 0.5,  # 默认可读性分数
                "professional": 0.5,  # 专业程度
            }
            
            # 检查文档结构
            if "\n\n" in content:  # 有段落
                quality_factors["structure"] += 0.2
            if any(marker in content for marker in ["#", "##", "###", "1.", "2.", "3."]):  # 有标题或列表
                quality_factors["structure"] += 0.3
            
            # 使用LLM提取的专业程度评分
            if "professional_level" in extended_metadata:
                quality_factors["professional"] = extended_metadata["professional_level"] / 5.0
            
            # 计算总分
            state["quality_score"] = sum(quality_factors.values()) / len(quality_factors)
            
            # 将质量评分映射到置信度星级
            confidence_stars = round(state["quality_score"] * 5)
            confidence_stars = max(1, min(5, confidence_stars))
            
            # 更新扩展元数据
            state["extended_metadata"]["confidence_stars"] = confidence_stars
            state["extended_metadata"]["quality_factors"] = quality_factors
            
            # 确定置信度等级
            if confidence_stars >= 4:
                state["extended_metadata"]["confidence_level"] = "authoritative"
            elif confidence_stars >= 3:
                state["extended_metadata"]["confidence_level"] = "moderate"
            else:
                state["extended_metadata"]["confidence_level"] = "reference_only"
            
            # 根据质量分数调整处理策略
            if state["quality_score"] < 0.3:
                state["warnings"].append("Low quality document detected")
                if state["processing_strategy"] == ProcessingStrategy.FULL:
                    state["processing_strategy"] = ProcessingStrategy.STANDARD
            
            self.logger.info(f"Document quality score: {state['quality_score']:.2f}, confidence: {confidence_stars} stars")
            
        except Exception as e:
            state["warnings"].append(f"Quality assessment warning: {e}")
            state["quality_score"] = 0.5  # 默认中等质量
        
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            state["step_durations"]["assess_quality"] = duration
        
        return state
    
    async def _semantic_chunking(self, content: str) -> List[Dict[str, Any]]:
        """语义分块"""
        # 使用实验性的语义分块器
        semantic_chunker = SemanticChunker(
            embeddings=self.embeddings_model,
            breakpoint_threshold_type="standard_deviation"
        )
        
        chunks = semantic_chunker.split_text(content)
        
        return [
            {
                "content": chunk,
                "index": i,
                "metadata": {
                    "chunk_size": len(chunk),
                    "chunking_method": "semantic"
                }
            }
            for i, chunk in enumerate(chunks)
        ]
    
    async def _standard_chunking(self, content: str) -> List[Dict[str, Any]]:
        """标准分块"""
        # 使用RecursiveCharacterTextSplitter
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        chunks = splitter.split_text(content)
        
        return [
            {
                "content": chunk,
                "index": i,
                "metadata": {
                    "chunk_size": len(chunk),
                    "chunking_method": "recursive_character"
                }
            }
            for i, chunk in enumerate(chunks)
        ]
    
    async def _update_cache(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """更新缓存"""
        if not state["use_cache"] or state["status"] == "error":
            return state
        
        try:
            cache_data = {
                "chunks": state.get("chunks", []),
                "embeddings": state.get("embeddings", []),
                "metadata": state.get("metadata", {}),
                "extended_metadata": state.get("extended_metadata", {}),
                "quality_score": state.get("quality_score", 0.0),
                "timestamp": datetime.now().isoformat(),
            }
            
            cache_file = self.cache_dir / f"{state['document_hash']}.json"
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
            
            self.logger.info(f"Cache updated for document: {state['file_name']}")
            
        except Exception as e:
            self.logger.warning(f"Failed to update cache: {e}")
        
        return state
    
    async def _cleanup_resources(self, state: DocumentProcessingState):
        """清理临时资源"""
        # 清理临时文件
        temp_files = state.get("temp_files", [])
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {temp_file}: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        success_rate = (
            self.metrics["success_count"] / self.metrics["total_processed"]
            if self.metrics["total_processed"] > 0
            else 0
        )
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "fallback_rate": self.metrics["fallback_count"] / max(self.metrics["total_processed"], 1),
            "cache_hit_rate": self.metrics["cache_hits"] / max(self.metrics["total_processed"], 1)
        }
    
    async def process_document_batch(self, documents: List[Dict[str, Any]], 
                                   max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """批量处理文档（并发控制）"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(doc):
            async with semaphore:
                return await self.compiled_graph.ainvoke(doc)
        
        results = await asyncio.gather(
            *[process_with_semaphore(doc) for doc in documents],
            return_exceptions=True
        )
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch processing error for document {i}: {result}")
                processed_results.append({
                    "document_id": documents[i].get("document_id"),
                    "status": "error",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _extract_metadata_with_llm(self, text_sample: str) -> Dict[str, Any]:
        """使用LLM提取文档元数据"""
        prompt = f"""
分析以下文档内容，提取元数据信息。

文档内容：
{text_sample}

请提取以下信息（如果无法确定，请返回null）：
1. 文档标题
2. 摘要（100-200字）
3. 主要关键点（最多5个）
4. 文档类型（论文/报告/文档/代码等）
5. 可能的发表时间
6. 是否包含引用文献
7. 文档的专业程度（1-5分）

请以JSON格式返回结果。
"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            result = json.loads(response.content)
            
            # 分离基础元数据和扩展元数据
            basic_metadata = {
                "title": result.get("title"),
                "document_type": result.get("document_type", "unknown")
            }
            
            extended_metadata = {
                "abstract": result.get("abstract"),
                "key_points": result.get("key_points", []),
                "publication_date_estimate": result.get("publication_date"),
                "has_references": result.get("has_references", False),
                "professional_level": result.get("professional_level", 3),
                "extracted_at": datetime.now().isoformat()
            }
            
            return {
                "basic_metadata": basic_metadata,
                "extended_metadata": extended_metadata
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to extract metadata with LLM: {e}")
            return {
                "basic_metadata": {},
                "extended_metadata": {}
            }