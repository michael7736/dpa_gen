"""
文档分块系统
支持多种分块策略：固定大小、语义、结构化分块
"""

import asyncio
import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, Field

from ..config.settings import get_settings
from ..core.vectorization import VectorStore
from ..models.document import DocumentChunk
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ChunkingStrategy(str, Enum):
    """分块策略枚举"""
    FIXED_SIZE = "fixed_size"           # 固定大小分块
    SEMANTIC = "semantic"               # 语义分块
    STRUCTURAL = "structural"           # 结构化分块
    SLIDING_WINDOW = "sliding_window"   # 滑动窗口分块
    PARAGRAPH = "paragraph"             # 段落分块
    SENTENCE = "sentence"               # 句子分块


class ChunkingConfig(BaseModel):
    """分块配置"""
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC
    chunk_size: int = Field(default=1000, ge=100, le=8000, description="块大小（字符数）")
    chunk_overlap: int = Field(default=200, ge=0, le=2000, description="块重叠大小")
    min_chunk_size: int = Field(default=100, ge=50, le=500, description="最小块大小")
    max_chunk_size: int = Field(default=2000, ge=500, le=10000, description="最大块大小")
    
    # 语义分块特定参数
    semantic_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="语义相似度阈值")
    use_embeddings: bool = Field(default=True, description="是否使用嵌入向量进行语义分块")
    
    # 结构化分块参数
    respect_structure: bool = Field(default=True, description="是否尊重文档结构")
    section_aware: bool = Field(default=True, description="是否感知章节边界")
    
    # 文本处理参数
    preserve_formatting: bool = Field(default=False, description="是否保留格式")
    remove_extra_whitespace: bool = Field(default=True, description="是否移除多余空白")
    
    # 质量控制参数
    filter_short_chunks: bool = Field(default=True, description="是否过滤过短的块")
    merge_short_chunks: bool = Field(default=True, description="是否合并过短的块")


class BaseChunker(ABC):
    """分块器基类"""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """分块文本"""
        pass
    
    def _create_chunk(
        self,
        content: str,
        start_index: int,
        end_index: int,
        chunk_index: int,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentChunk:
        """创建文档块"""
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata.update({
            "chunk_index": chunk_index,
            "chunk_size": len(content),
            "chunk_strategy": self.config.strategy.value,
            "created_at": datetime.now().isoformat()
        })
        
        return DocumentChunk(
            id=str(uuid4()),
            document_id=document_id,
            content=content.strip(),
            start_index=start_index,
            end_index=end_index,
            chunk_index=chunk_index,
            metadata=chunk_metadata,
            embedding=None  # 将在后续步骤中生成
        )
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if self.config.remove_extra_whitespace:
            # 移除多余的空白字符
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _is_valid_chunk(self, content: str) -> bool:
        """验证块是否有效"""
        content = content.strip()
        
        if len(content) < self.config.min_chunk_size:
            return False
        
        if len(content) > self.config.max_chunk_size:
            return False
        
        # 检查内容质量
        if len(content.split()) < 5:  # 至少5个单词
            return False
        
        return True
    
    def _post_process_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """后处理块"""
        if not chunks:
            return chunks
        
        processed_chunks = []
        
        for chunk in chunks:
            # 过滤过短的块
            if self.config.filter_short_chunks and not self._is_valid_chunk(chunk.content):
                continue
            
            processed_chunks.append(chunk)
        
        # 合并过短的块
        if self.config.merge_short_chunks:
            processed_chunks = self._merge_short_chunks(processed_chunks)
        
        # 重新编号
        for i, chunk in enumerate(processed_chunks):
            chunk.chunk_index = i
        
        return processed_chunks
    
    def _merge_short_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """合并过短的块"""
        if not chunks:
            return chunks
        
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if len(chunk.content) < self.config.min_chunk_size and current_chunk:
                # 合并到前一个块
                current_chunk.content += "\n\n" + chunk.content
                current_chunk.end_index = chunk.end_index
                
                # 更新元数据
                current_chunk.metadata["merged_chunks"] = current_chunk.metadata.get("merged_chunks", []) + [chunk.id]
                current_chunk.metadata["chunk_size"] = len(current_chunk.content)
            else:
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        return merged_chunks


class FixedSizeChunker(BaseChunker):
    """固定大小分块器"""
    
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """固定大小分块"""
        text = self._clean_text(text)
        chunks = []
        
        document_id = metadata.get("document_id", str(uuid4())) if metadata else str(uuid4())
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # 计算结束位置
            end = min(start + self.config.chunk_size, len(text))
            
            # 如果不是最后一个块，尝试在单词边界分割
            if end < len(text):
                # 向后查找单词边界
                word_end = text.rfind(' ', start, end)
                sentence_end = text.rfind('。', start, end)
                
                if sentence_end > start + self.config.chunk_size // 2:
                    end = sentence_end + 1
                elif word_end > start + self.config.chunk_size // 2:
                    end = word_end
            
            # 提取内容
            content = text[start:end]
            
            if content.strip():
                chunk = self._create_chunk(
                    content=content,
                    start_index=start,
                    end_index=end,
                    chunk_index=chunk_index,
                    document_id=document_id,
                    metadata=metadata
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # 计算下一个开始位置（考虑重叠）
            next_start = end - self.config.chunk_overlap
            start = max(next_start, start + 1)  # 确保前进
        
        return self._post_process_chunks(chunks)


class SemanticChunker(BaseChunker):
    """语义分块器"""
    
    def __init__(self, config: ChunkingConfig):
        super().__init__(config)
        self.vector_store = VectorStore() if config.use_embeddings else None
    
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """语义分块"""
        text = self._clean_text(text)
        document_id = metadata.get("document_id", str(uuid4())) if metadata else str(uuid4())
        
        # 首先进行句子分割
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        # 如果使用嵌入向量进行语义分块
        if self.vector_store and len(sentences) > 1:
            chunks = await self._semantic_chunk_with_embeddings(sentences, document_id, metadata)
        else:
            chunks = await self._semantic_chunk_without_embeddings(sentences, document_id, metadata)
        
        return self._post_process_chunks(chunks)
    
    def _split_into_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        """分割成句子，返回(句子, 开始位置, 结束位置)"""
        sentences = []
        
        # 中文句子分割
        sentence_pattern = r'[。！？；\n]+'
        
        start = 0
        for match in re.finditer(sentence_pattern, text):
            end = match.end()
            sentence = text[start:end].strip()
            
            if sentence:
                sentences.append((sentence, start, end))
            
            start = end
        
        # 处理最后一个句子
        if start < len(text):
            sentence = text[start:].strip()
            if sentence:
                sentences.append((sentence, start, len(text)))
        
        return sentences
    
    async def _semantic_chunk_with_embeddings(
        self,
        sentences: List[Tuple[str, int, int]],
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """使用嵌入向量进行语义分块"""
        if len(sentences) <= 1:
            sentence, start, end = sentences[0]
            return [self._create_chunk(sentence, start, end, 0, document_id, metadata)]
        
        # 生成句子嵌入向量
        sentence_texts = [sent[0] for sent in sentences]
        embeddings = await self.vector_store.embed_texts(sentence_texts)
        
        # 计算相邻句子的相似度
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)
        
        # 找到分割点（相似度低于阈值的位置）
        split_points = [0]  # 总是从第一个句子开始
        
        for i, sim in enumerate(similarities):
            if sim < self.config.semantic_threshold:
                split_points.append(i + 1)
        
        split_points.append(len(sentences))  # 总是在最后结束
        
        # 创建块
        chunks = []
        chunk_index = 0
        
        for i in range(len(split_points) - 1):
            start_idx = split_points[i]
            end_idx = split_points[i + 1]
            
            # 合并句子
            chunk_sentences = sentences[start_idx:end_idx]
            content = " ".join([sent[0] for sent in chunk_sentences])
            start_pos = chunk_sentences[0][1]
            end_pos = chunk_sentences[-1][2]
            
            # 检查块大小，如果太大则进一步分割
            if len(content) > self.config.max_chunk_size:
                sub_chunks = await self._split_large_chunk(
                    content, start_pos, chunk_index, document_id, metadata
                )
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
            else:
                chunk = self._create_chunk(
                    content=content,
                    start_index=start_pos,
                    end_index=end_pos,
                    chunk_index=chunk_index,
                    document_id=document_id,
                    metadata=metadata
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    async def _semantic_chunk_without_embeddings(
        self,
        sentences: List[Tuple[str, int, int]],
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """不使用嵌入向量的语义分块（基于规则）"""
        chunks = []
        current_chunk_sentences = []
        current_size = 0
        chunk_index = 0
        
        for sentence, start, end in sentences:
            sentence_size = len(sentence)
            
            # 检查是否应该开始新块
            if (current_size + sentence_size > self.config.chunk_size and 
                current_chunk_sentences and 
                current_size >= self.config.min_chunk_size):
                
                # 创建当前块
                content = " ".join([s[0] for s in current_chunk_sentences])
                start_pos = current_chunk_sentences[0][1]
                end_pos = current_chunk_sentences[-1][2]
                
                chunk = self._create_chunk(
                    content=content,
                    start_index=start_pos,
                    end_index=end_pos,
                    chunk_index=chunk_index,
                    document_id=document_id,
                    metadata=metadata
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 重置当前块（保留重叠）
                if self.config.chunk_overlap > 0:
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk_sentences, self.config.chunk_overlap
                    )
                    current_chunk_sentences = overlap_sentences
                    current_size = sum(len(s[0]) for s in overlap_sentences)
                else:
                    current_chunk_sentences = []
                    current_size = 0
            
            # 添加当前句子
            current_chunk_sentences.append((sentence, start, end))
            current_size += sentence_size
        
        # 处理最后一块
        if current_chunk_sentences:
            content = " ".join([s[0] for s in current_chunk_sentences])
            start_pos = current_chunk_sentences[0][1]
            end_pos = current_chunk_sentences[-1][2]
            
            chunk = self._create_chunk(
                content=content,
                start_index=start_pos,
                end_index=end_pos,
                chunk_index=chunk_index,
                document_id=document_id,
                metadata=metadata
            )
            chunks.append(chunk)
        
        return chunks
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0
    
    def _get_overlap_sentences(
        self,
        sentences: List[Tuple[str, int, int]],
        overlap_size: int
    ) -> List[Tuple[str, int, int]]:
        """获取重叠的句子"""
        if not sentences:
            return []
        
        overlap_sentences = []
        current_size = 0
        
        # 从后向前添加句子直到达到重叠大小
        for sentence, start, end in reversed(sentences):
            sentence_size = len(sentence)
            if current_size + sentence_size <= overlap_size:
                overlap_sentences.insert(0, (sentence, start, end))
                current_size += sentence_size
            else:
                break
        
        return overlap_sentences
    
    async def _split_large_chunk(
        self,
        content: str,
        start_pos: int,
        base_chunk_index: int,
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """分割过大的块"""
        # 使用固定大小分块器分割
        fixed_chunker = FixedSizeChunker(self.config)
        sub_chunks = await fixed_chunker.chunk_text(content, metadata)
        
        # 调整位置和索引
        adjusted_chunks = []
        for i, chunk in enumerate(sub_chunks):
            chunk.start_index += start_pos
            chunk.end_index += start_pos
            chunk.chunk_index = base_chunk_index + i
            adjusted_chunks.append(chunk)
        
        return adjusted_chunks


class StructuralChunker(BaseChunker):
    """结构化分块器"""
    
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """结构化分块"""
        text = self._clean_text(text)
        document_id = metadata.get("document_id", str(uuid4())) if metadata else str(uuid4())
        
        # 检查是否有结构信息
        structure = metadata.get("structure", {}) if metadata else {}
        sections = structure.get("sections", [])
        
        if sections and self.config.section_aware:
            return await self._chunk_by_sections(text, sections, document_id, metadata)
        else:
            return await self._chunk_by_paragraphs(text, document_id, metadata)
    
    async def _chunk_by_sections(
        self,
        text: str,
        sections: List[Dict[str, Any]],
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """按章节分块"""
        chunks = []
        chunk_index = 0
        
        for section in sections:
            section_content = section.get("content", "")
            section_title = section.get("title", "")
            
            if not section_content:
                continue
            
            # 如果章节内容太长，进一步分块
            if len(section_content) > self.config.max_chunk_size:
                # 使用语义分块器处理长章节
                semantic_chunker = SemanticChunker(self.config)
                section_chunks = await semantic_chunker.chunk_text(section_content, metadata)
                
                # 为每个块添加章节信息
                for chunk in section_chunks:
                    chunk.chunk_index = chunk_index
                    chunk.metadata["section_title"] = section_title
                    chunk.metadata["section_level"] = section.get("level", 1)
                    chunks.append(chunk)
                    chunk_index += 1
            else:
                # 创建单个章节块
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "section_title": section_title,
                    "section_level": section.get("level", 1),
                    "section_number": section.get("section_number", "")
                })
                
                chunk = self._create_chunk(
                    content=section_content,
                    start_index=0,  # TODO: 计算实际位置
                    end_index=len(section_content),
                    chunk_index=chunk_index,
                    document_id=document_id,
                    metadata=chunk_metadata
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return self._post_process_chunks(chunks)
    
    async def _chunk_by_paragraphs(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """按段落分块"""
        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        
        current_chunk_content = []
        current_size = 0
        chunk_index = 0
        start_pos = 0
        
        for para_content, para_start, para_end in paragraphs:
            para_size = len(para_content)
            
            # 检查是否应该开始新块
            if (current_size + para_size > self.config.chunk_size and 
                current_chunk_content and 
                current_size >= self.config.min_chunk_size):
                
                # 创建当前块
                content = "\n\n".join(current_chunk_content)
                chunk = self._create_chunk(
                    content=content,
                    start_index=start_pos,
                    end_index=start_pos + len(content),
                    chunk_index=chunk_index,
                    document_id=document_id,
                    metadata=metadata
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 重置
                current_chunk_content = []
                current_size = 0
                start_pos = para_start
            
            # 添加当前段落
            current_chunk_content.append(para_content)
            current_size += para_size
        
        # 处理最后一块
        if current_chunk_content:
            content = "\n\n".join(current_chunk_content)
            chunk = self._create_chunk(
                content=content,
                start_index=start_pos,
                end_index=start_pos + len(content),
                chunk_index=chunk_index,
                document_id=document_id,
                metadata=metadata
            )
            chunks.append(chunk)
        
        return self._post_process_chunks(chunks)
    
    def _split_into_paragraphs(self, text: str) -> List[Tuple[str, int, int]]:
        """分割成段落"""
        paragraphs = []
        
        # 按双换行符分割段落
        para_pattern = r'\n\s*\n'
        
        start = 0
        for match in re.finditer(para_pattern, text):
            end = match.start()
            paragraph = text[start:end].strip()
            
            if paragraph:
                paragraphs.append((paragraph, start, end))
            
            start = match.end()
        
        # 处理最后一个段落
        if start < len(text):
            paragraph = text[start:].strip()
            if paragraph:
                paragraphs.append((paragraph, start, len(text)))
        
        return paragraphs


class ParagraphChunker(BaseChunker):
    """段落分块器"""
    
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """按段落分块"""
        text = self._clean_text(text)
        document_id = metadata.get("document_id", str(uuid4())) if metadata else str(uuid4())
        
        paragraphs = text.split('\n\n')
        chunks = []
        chunk_index = 0
        
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 计算位置
            start_pos = text.find(paragraph)
            end_pos = start_pos + len(paragraph)
            
            chunk = self._create_chunk(
                content=paragraph,
                start_index=start_pos,
                end_index=end_pos,
                chunk_index=chunk_index,
                document_id=document_id,
                metadata=metadata
            )
            chunks.append(chunk)
            chunk_index += 1
        
        return self._post_process_chunks(chunks)


class DocumentChunker:
    """文档分块器主类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._chunkers = {}
    
    def _get_chunker(self, config: ChunkingConfig) -> BaseChunker:
        """获取分块器实例"""
        strategy = config.strategy
        
        if strategy not in self._chunkers:
            if strategy == ChunkingStrategy.FIXED_SIZE:
                self._chunkers[strategy] = FixedSizeChunker(config)
            elif strategy == ChunkingStrategy.SEMANTIC:
                self._chunkers[strategy] = SemanticChunker(config)
            elif strategy == ChunkingStrategy.STRUCTURAL:
                self._chunkers[strategy] = StructuralChunker(config)
            elif strategy == ChunkingStrategy.PARAGRAPH:
                self._chunkers[strategy] = ParagraphChunker(config)
            else:
                # 默认使用固定大小分块
                self._chunkers[strategy] = FixedSizeChunker(config)
        
        return self._chunkers[strategy]
    
    async def chunk_document(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        **kwargs
    ) -> List[DocumentChunk]:
        """分块文档"""
        try:
            # 创建配置
            config_dict = {
                "strategy": strategy,
                **kwargs
            }
            config = ChunkingConfig(**config_dict)
            
            # 准备元数据
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["document_id"] = document_id
            
            # 获取分块器并执行分块
            chunker = self._get_chunker(config)
            chunks = await chunker.chunk_text(text, chunk_metadata)
            
            self.logger.info(f"文档分块完成: {len(chunks)} 个块, 策略: {strategy.value}")
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"文档分块失败: {str(e)}")
            raise
    
    async def chunk_texts(
        self,
        texts: List[str],
        document_ids: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        **kwargs
    ) -> List[List[DocumentChunk]]:
        """批量分块文档"""
        if len(texts) != len(document_ids):
            raise ValueError("texts和document_ids长度必须相同")
        
        if metadata_list and len(metadata_list) != len(texts):
            raise ValueError("metadata_list长度必须与texts相同")
        
        tasks = []
        for i, (text, doc_id) in enumerate(zip(texts, document_ids)):
            metadata = metadata_list[i] if metadata_list else None
            task = self.chunk_document(text, doc_id, metadata, strategy, **kwargs)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"文档 {document_ids[i]} 分块失败: {str(result)}")
                processed_results.append([])
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_supported_strategies(self) -> List[ChunkingStrategy]:
        """获取支持的分块策略"""
        return list(ChunkingStrategy)
    
    def estimate_chunk_count(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> int:
        """估算分块数量"""
        text_length = len(text)
        
        if strategy == ChunkingStrategy.PARAGRAPH:
            # 按段落估算
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            return paragraph_count
        else:
            # 按大小估算
            effective_chunk_size = chunk_size - chunk_overlap
            if effective_chunk_size <= 0:
                effective_chunk_size = chunk_size
            
            estimated_count = max(1, (text_length + effective_chunk_size - 1) // effective_chunk_size)
            return estimated_count


# 全局分块器实例
document_chunker = DocumentChunker()


# 便捷函数
async def chunk_document(
    text: str,
    document_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
    **kwargs
) -> List[DocumentChunk]:
    """分块文档的便捷函数"""
    return await document_chunker.chunk_document(
        text, document_id, metadata, strategy, **kwargs
    )


async def chunk_texts(
    texts: List[str],
    document_ids: List[str],
    metadata_list: Optional[List[Dict[str, Any]]] = None,
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
    **kwargs
) -> List[List[DocumentChunk]]:
    """批量分块文档的便捷函数"""
    return await document_chunker.chunk_texts(
        texts, document_ids, metadata_list, strategy, **kwargs
    )


def get_supported_strategies() -> List[ChunkingStrategy]:
    """获取支持的分块策略"""
    return document_chunker.get_supported_strategies()


def estimate_chunk_count(
    text: str,
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> int:
    """估算分块数量"""
    return document_chunker.estimate_chunk_count(text, strategy, chunk_size, chunk_overlap) 