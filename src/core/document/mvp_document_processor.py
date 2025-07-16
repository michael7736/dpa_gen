"""
MVP文档处理器 - 简化的文档处理管道
支持PDF、TXT、MD等格式，使用基于token的智能分块算法
"""
import asyncio
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import aiofiles
import fitz  # PyMuPDF
import chardet
import tiktoken
import re
from dataclasses import dataclass, asdict

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader,
    PyPDFLoader
)

from src.services.memory_write_service_v2 import MemoryWriteService, MemoryType
from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 默认配置
DEFAULT_CHUNK_SIZE = 512  # 基于token的分块大小（适合研究性长文）
DEFAULT_CHUNK_OVERLAP = 128  # 25%的重叠能很好地承接上下文
DEFAULT_USER_ID = "u1"
SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.text', '.markdown'}

# 优化的分隔符顺序（优先保持语义完整性）
OPTIMIZED_SEPARATORS = [
    "\n\n",       # 1. 段落
    ".\n",        # 2. 英文句+换行
    "。\n",       # 3. 中文句+换行
    "\n",         # 4. 单独换行
    ". ",         # 5. 英文句号
    "。",         # 6. 中文句号
    "!", "！", "?", "？",  # 7. 其他句尾标点
    ";", "；",     # 8. 分号
    ",", "，",     # 9. 逗号
    " ",          # 10. 空格
    "",           # 11. 兜底
]


# 初始化tiktoken编码器（使用cl100k_base，适用于大多数新模型）
tokenizer = tiktoken.get_encoding("cl100k_base")

def tiktoken_len(text: str) -> int:
    """
    使用tiktoken计算文本的token数量
    这对于处理中英文混合文档至关重要，因为中文和英文的token比例差异很大
    """
    tokens = tokenizer.encode(text)
    return len(tokens)


def split_text_by_sentence(text: str, chunk_size: int = 512, overlap_sentences: int = 3) -> List[str]:
    """
    基于句子的智能分块（第二步优化）
    
    Args:
        text: 输入文本
        chunk_size: 每个块的最大token数
        overlap_sentences: 重叠句子数
    """
    # 步骤1: 使用正则表达式分句
    # 中文句子结束符：。！？；
    # 英文句子结束符：.!?
    # 保留标点符号在句子末尾
    sentences = re.split(r'(?<=[。！？；\.\?!])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]  # 移除空字符串
    
    if not sentences:
        return []
    
    chunks = []
    current_chunk_sentences = []
    current_chunk_tokens = 0
    
    # 步骤2: 组合句子
    for i, sentence in enumerate(sentences):
        sentence_tokens = tiktoken_len(sentence)
        
        # 如果单个句子就超过chunk_size，单独成块
        if sentence_tokens > chunk_size:
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_chunk_tokens = 0
            chunks.append(sentence)
            continue
        
        # 如果加上这个句子会超过限制，先保存当前块
        if current_chunk_tokens + sentence_tokens > chunk_size and current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            
            # 创建重叠：从前一个块的末尾取overlap_sentences个句子
            start_index = max(0, len(current_chunk_sentences) - overlap_sentences)
            current_chunk_sentences = current_chunk_sentences[start_index:]
            current_chunk_tokens = tiktoken_len(" ".join(current_chunk_sentences))
        
        current_chunk_sentences.append(sentence)
        current_chunk_tokens += sentence_tokens
    
    # 保存最后一个块
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))
    
    return chunks


@dataclass
class DocumentMetadata:
    """文档元数据"""
    document_id: str
    filename: str
    file_path: str
    file_size: int
    file_type: str
    created_at: str
    processed_at: Optional[str] = None
    chunk_count: int = 0
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    user_id: str = DEFAULT_USER_ID
    project_id: Optional[str] = None
    
    
@dataclass
class DocumentChunk:
    """文档块"""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class MVPDocumentProcessor:
    """
    MVP文档处理器
    简化的文档处理流程，支持多种分块策略
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID, use_sentence_chunking: bool = True):
        self.user_id = user_id
        self.use_sentence_chunking = use_sentence_chunking
        self.memory_service = MemoryWriteService(user_id=user_id)
        self.memory_bank_manager = create_memory_bank_manager(user_id=user_id)
        
        # 文本分割器 - 使用tiktoken进行准确的token计数
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            length_function=tiktoken_len,  # 关键改进：使用token计数而不是字符计数
            separators=OPTIMIZED_SEPARATORS,
            keep_separator=True,  # 保留分隔符，有助于语义完整
            is_separator_regex=False
        )
        
        # 嵌入模型
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",  # 使用小模型节省成本
            api_key=settings.ai_model.openai_api_key
        )
        
        # 处理状态缓存
        self._processing_status: Dict[str, DocumentMetadata] = {}
        
    async def process_document(
        self,
        file_path: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentMetadata:
        """
        处理单个文档
        
        Args:
            file_path: 文档路径
            project_id: 项目ID
            metadata: 额外的元数据
            
        Returns:
            DocumentMetadata: 处理结果
        """
        file_path = Path(file_path)
        
        # 验证文件
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
        # 生成文档ID
        document_id = self._generate_document_id(file_path)
        
        # 创建元数据
        doc_metadata = DocumentMetadata(
            document_id=document_id,
            filename=file_path.name,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            file_type=file_path.suffix.lower(),
            created_at=datetime.now().isoformat(),
            user_id=self.user_id,
            project_id=project_id
        )
        
        # 更新处理状态
        self._processing_status[document_id] = doc_metadata
        doc_metadata.status = "processing"
        
        try:
            # 1. 加载文档
            logger.info(f"Loading document: {file_path}")
            content = await self._load_document(file_path)
            
            # 2. 分块
            logger.info(f"Splitting document into chunks")
            chunks = self._split_text(content, doc_metadata)
            doc_metadata.chunk_count = len(chunks)
            
            # 3. 生成嵌入
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            chunks_with_embeddings = await self._generate_embeddings(chunks)
            
            # 4. 存储到记忆系统
            logger.info(f"Storing chunks to memory systems")
            await self._store_chunks(chunks_with_embeddings, doc_metadata)
            
            # 5. 更新Memory Bank
            if project_id:
                await self._update_memory_bank(project_id, doc_metadata, chunks[:5])
                
            # 更新状态
            doc_metadata.status = "completed"
            doc_metadata.processed_at = datetime.now().isoformat()
            
            logger.info(f"Document processed successfully: {document_id}")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            doc_metadata.status = "failed"
            doc_metadata.error_message = str(e)
            raise
            
        finally:
            # 清理处理状态
            if document_id in self._processing_status:
                del self._processing_status[document_id]
                
        return doc_metadata
        
    async def process_batch(
        self,
        file_paths: List[str],
        project_id: Optional[str] = None,
        max_concurrent: int = 3
    ) -> List[DocumentMetadata]:
        """批量处理文档"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_limit(file_path: str) -> DocumentMetadata:
            async with semaphore:
                try:
                    return await self.process_document(file_path, project_id)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    return DocumentMetadata(
                        document_id="error",
                        filename=Path(file_path).name,
                        file_path=file_path,
                        file_size=0,
                        file_type=Path(file_path).suffix,
                        created_at=datetime.now().isoformat(),
                        status="failed",
                        error_message=str(e)
                    )
                    
        tasks = [process_with_limit(fp) for fp in file_paths]
        return await asyncio.gather(*tasks)
        
    async def _load_document(self, file_path: Path) -> str:
        """加载文档内容"""
        if file_path.suffix.lower() == '.pdf':
            return await self._load_pdf(file_path)
        elif file_path.suffix.lower() in ['.md', '.markdown']:
            return await self._load_markdown(file_path)
        else:  # .txt and others
            return await self._load_text(file_path)
            
    async def _load_pdf(self, file_path: Path) -> str:
        """加载PDF文档"""
        try:
            # 使用PyMuPDF提取文本
            pdf_document = fitz.open(str(file_path))
            text_content = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append(f"[Page {page_num + 1}]\n{text}")
                    
            pdf_document.close()
            
            if not text_content:
                raise ValueError("No text content found in PDF")
                
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            # 降级到 PyPDFLoader
            try:
                loader = PyPDFLoader(str(file_path))
                documents = await asyncio.to_thread(loader.load)
                return "\n\n".join([doc.page_content for doc in documents])
            except Exception as e2:
                logger.error(f"PyPDFLoader also failed: {e2}")
                raise
                
    async def _load_markdown(self, file_path: Path) -> str:
        """加载Markdown文档"""
        try:
            # 先尝试直接读取
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except UnicodeDecodeError:
            # 检测编码
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                return await f.read()
                
    async def _load_text(self, file_path: Path) -> str:
        """加载文本文档"""
        try:
            # 先尝试UTF-8
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except UnicodeDecodeError:
            # 自动检测编码
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                return await f.read()
                
    def _split_text(self, content: str, metadata: DocumentMetadata) -> List[DocumentChunk]:
        """分割文本为块"""
        # 根据配置选择分块策略
        if self.use_sentence_chunking:
            # 使用第二步优化：基于句子的智能分块
            text_chunks = split_text_by_sentence(
                content, 
                chunk_size=DEFAULT_CHUNK_SIZE,
                overlap_sentences=3  # 3个句子的重叠
            )
        else:
            # 使用第一步优化：基于token的递归分块
            text_chunks = self.text_splitter.split_text(content)
        
        chunks = []
        current_position = 0
        
        for i, chunk_text in enumerate(text_chunks):
            # 查找块在原文中的位置
            start_pos = content.find(chunk_text, current_position)
            if start_pos == -1:
                start_pos = current_position
            end_pos = start_pos + len(chunk_text)
            
            # 创建块对象
            chunk = DocumentChunk(
                chunk_id=f"{metadata.document_id}_chunk_{i}",
                document_id=metadata.document_id,
                content=chunk_text,
                chunk_index=i,
                start_char=start_pos,
                end_char=end_pos,
                metadata={
                    "filename": metadata.filename,
                    "file_type": metadata.file_type,
                    "chunk_size": len(chunk_text),
                    "total_chunks": len(text_chunks),
                    "user_id": metadata.user_id,
                    "project_id": metadata.project_id
                }
            )
            chunks.append(chunk)
            current_position = end_pos
            
        return chunks
        
    async def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """生成嵌入向量"""
        # 提取文本
        texts = [chunk.content for chunk in chunks]
        
        # 批量生成嵌入
        batch_size = 20
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            try:
                embeddings = await self.embeddings.aembed_documents(batch_texts)
                all_embeddings.extend(embeddings)
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size}: {e}")
                # 为失败的批次生成空嵌入
                all_embeddings.extend([None] * len(batch_texts))
                
        # 更新块的嵌入
        for chunk, embedding in zip(chunks, all_embeddings):
            chunk.embedding = embedding
            
        return chunks
        
    async def _store_chunks(
        self, 
        chunks: List[DocumentChunk], 
        metadata: DocumentMetadata
    ):
        """存储文档块到记忆系统"""
        stored_count = 0
        failed_count = 0
        
        for chunk in chunks:
            try:
                # 写入到所有存储系统
                result = await self.memory_service.write_memory(
                    content=chunk.content,
                    memory_type=MemoryType.SEMANTIC,
                    metadata={
                        **chunk.metadata,
                        "chunk_id": chunk.chunk_id,
                        "chunk_index": chunk.chunk_index,
                        "document_id": chunk.document_id,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char
                    },
                    project_id=metadata.project_id,
                    user_id=metadata.user_id,
                    embedding=chunk.embedding
                )
                
                if result.success:
                    stored_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"Failed to store chunk {chunk.chunk_id}: {result.error}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error storing chunk {chunk.chunk_id}: {e}")
                
        logger.info(f"Stored {stored_count} chunks, {failed_count} failed")
        
        if failed_count > len(chunks) * 0.1:  # 如果超过10%失败
            raise Exception(f"Too many chunks failed to store: {failed_count}/{len(chunks)}")
            
    async def _update_memory_bank(
        self,
        project_id: str,
        metadata: DocumentMetadata,
        sample_chunks: List[DocumentChunk]
    ):
        """更新Memory Bank"""
        try:
            # 确保项目已初始化
            snapshot = await self.memory_bank_manager.get_snapshot(project_id)
            if not snapshot:
                await self.memory_bank_manager.initialize_project(project_id)
                
            # 更新上下文
            context_content = f"""
Document: {metadata.filename}
Type: {metadata.file_type}
Size: {metadata.file_size} bytes
Chunks: {metadata.chunk_count}
Processed: {metadata.processed_at}

Sample content:
{sample_chunks[0].content[:500] if sample_chunks else 'N/A'}
"""
            
            await self.memory_bank_manager.update_context(
                project_id=project_id,
                new_content=context_content,
                source=f"document:{metadata.filename}"
            )
            
            # 提取并添加概念（简单实现）
            concepts = self._extract_simple_concepts(sample_chunks)
            if concepts:
                await self.memory_bank_manager.add_concepts(
                    project_id=project_id,
                    new_concepts=concepts
                )
                
        except Exception as e:
            logger.error(f"Failed to update Memory Bank: {e}")
            # 不中断主流程
            
    def _extract_simple_concepts(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """简单的概念提取（基于关键词）"""
        concepts = []
        
        # 简单的基于词频的概念提取
        word_freq = {}
        for chunk in chunks:
            # 简单的中文分词（实际应使用jieba等）
            words = chunk.content.split()
            for word in words:
                if len(word) > 2:  # 过滤短词
                    word_freq[word] = word_freq.get(word, 0) + 1
                    
        # 选择高频词作为概念
        for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
            if freq > 1:
                concepts.append({
                    "name": word,
                    "category": "extracted",
                    "description": f"Frequency: {freq}",
                    "confidence": min(freq / 10, 1.0)
                })
                
        return concepts
        
    def _generate_document_id(self, file_path: Path) -> str:
        """生成文档ID"""
        # 基于文件路径和时间戳生成唯一ID
        unique_string = f"{file_path.absolute()}_{datetime.now().isoformat()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
        
    def get_processing_status(self, document_id: str) -> Optional[DocumentMetadata]:
        """获取处理状态"""
        return self._processing_status.get(document_id)
        
    def list_processing_documents(self) -> List[DocumentMetadata]:
        """列出正在处理的文档"""
        return list(self._processing_status.values())


# 工厂函数
def create_mvp_document_processor(user_id: str = DEFAULT_USER_ID, use_sentence_chunking: bool = True) -> MVPDocumentProcessor:
    """创建MVP文档处理器实例"""
    return MVPDocumentProcessor(user_id=user_id, use_sentence_chunking=use_sentence_chunking)