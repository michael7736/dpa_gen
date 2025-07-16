"""
智能句子边界分块器
基于句子边界进行智能文本分块，支持中英文混合文本
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import tiktoken
from pydantic import BaseModel, Field

from ...models.chunk import Chunk as DocumentChunk
from ...utils.logger import get_logger
from ..chunking import BaseChunker, ChunkingConfig

logger = get_logger(__name__)


class SentenceBasedConfig(ChunkingConfig):
    """句子分块配置"""
    max_tokens: int = Field(default=1000, ge=100, le=8000, description="最大token数")
    sentence_overlap: int = Field(default=2, ge=0, le=10, description="句子重叠数量")
    encoding_model: str = Field(default="cl100k_base", description="tiktoken编码模型")
    preserve_sentence_boundaries: bool = Field(default=True, description="保持句子完整性")
    min_sentences_per_chunk: int = Field(default=1, ge=1, description="每块最少句子数")


class SentenceBasedChunker(BaseChunker):
    """基于句子边界的智能分块器"""
    
    def __init__(self, config: SentenceBasedConfig):
        super().__init__(config)
        self.config: SentenceBasedConfig = config
        self.encoding = tiktoken.get_encoding(config.encoding_model)
        
        # 中文标点符号
        self.chinese_punctuation = r'[。！？；]'
        # 英文标点符号 (简化版，TODO: 使用nltk进行更准确的句子分割)
        self.english_punctuation = r'[.!?]'
        # 引号和括号
        self.quote_marks = r'[""\"\'()（）]'
    
    def _detect_language(self, text: str) -> str:
        """检测文本主要语言（简化版）"""
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文字符
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = chinese_chars + english_chars
        if total_chars == 0:
            return "mixed"
        
        chinese_ratio = chinese_chars / total_chars
        if chinese_ratio > 0.7:
            return "chinese"
        elif chinese_ratio < 0.3:
            return "english"
        else:
            return "mixed"
    
    def _split_chinese_sentences(self, text: str) -> List[str]:
        """分割中文句子"""
        sentences = []
        
        # 使用正则表达式分割，但保留标点符号
        pattern = f'({self.chinese_punctuation})'
        parts = re.split(pattern, text)
        
        current_sentence = ""
        for i, part in enumerate(parts):
            if re.match(self.chinese_punctuation, part):
                # 是标点符号，附加到当前句子
                current_sentence += part
                sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                current_sentence += part
        
        # 处理最后可能没有标点的部分
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return [s for s in sentences if s]
    
    def _split_english_sentences(self, text: str) -> List[str]:
        """分割英文句子（简化版）"""
        sentences = []
        
        # 简单的句子分割规则
        # TODO: 使用nltk.sent_tokenize进行更准确的分割
        pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        raw_sentences = re.split(pattern, text)
        
        for sentence in raw_sentences:
            sentence = sentence.strip()
            if sentence:
                # 确保句子以标点结尾
                if not re.search(r'[.!?]$', sentence):
                    # 查找下一个标点
                    next_punct = re.search(r'[.!?]', sentence)
                    if not next_punct and len(sentence) > 20:
                        sentence += '.'
                sentences.append(sentence)
        
        return sentences
    
    def _split_mixed_sentences(self, text: str) -> List[str]:
        """分割混合语言句子"""
        sentences = []
        
        # 结合中英文标点进行分割
        pattern = f'({self.chinese_punctuation}|{self.english_punctuation})'
        parts = re.split(pattern, text)
        
        current_sentence = ""
        for i, part in enumerate(parts):
            if re.match(pattern, part):
                current_sentence += part
                # 检查是否应该结束当前句子
                if self._should_end_sentence(current_sentence, i, parts):
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
            else:
                current_sentence += part
        
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return [s for s in sentences if s]
    
    def _should_end_sentence(self, current_sentence: str, punct_index: int, parts: List[str]) -> bool:
        """判断是否应该在此处结束句子"""
        # 检查标点后是否有空格或换行
        if punct_index + 1 < len(parts):
            next_part = parts[punct_index + 1]
            if next_part.startswith('\n') or next_part.startswith(' '):
                return True
            # 检查下一个字符是否是大写字母（英文句子开始）
            if re.match(r'^[A-Z]', next_part.strip()):
                return True
            # 检查是否是新的中文句子
            if re.match(r'^[\u4e00-\u9fff]', next_part.strip()):
                return True
        
        return True
    
    def _count_tokens(self, text: str) -> int:
        """计算文本的token数"""
        return len(self.encoding.encode(text))
    
    def _split_text_by_sentence(
        self,
        text: str,
        max_tokens: int,
        sentence_overlap: int = 2
    ) -> List[Tuple[str, int, int]]:
        """按句子分割文本，返回(内容, 开始位置, 结束位置)"""
        # 检测语言
        language = self._detect_language(text)
        
        # 根据语言选择分割方法
        if language == "chinese":
            sentences = self._split_chinese_sentences(text)
        elif language == "english":
            sentences = self._split_english_sentences(text)
        else:
            sentences = self._split_mixed_sentences(text)
        
        if not sentences:
            return []
        
        # 计算每个句子的位置
        sentence_positions = []
        current_pos = 0
        for sentence in sentences:
            start_pos = text.find(sentence, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(sentence)
            sentence_positions.append((sentence, start_pos, end_pos))
            current_pos = end_pos
        
        # 按token限制分组句子
        chunks = []
        current_chunk_sentences = []
        current_tokens = 0
        chunk_start_pos = 0
        
        for i, (sentence, start_pos, end_pos) in enumerate(sentence_positions):
            sentence_tokens = self._count_tokens(sentence)
            
            # 检查是否需要开始新块
            if current_tokens + sentence_tokens > max_tokens and current_chunk_sentences:
                # 创建当前块
                chunk_content = "".join([s[0] for s in current_chunk_sentences])
                chunk_end_pos = current_chunk_sentences[-1][2]
                chunks.append((chunk_content, chunk_start_pos, chunk_end_pos))
                
                # 准备下一块（包含重叠）
                if sentence_overlap > 0 and len(current_chunk_sentences) > sentence_overlap:
                    # 保留最后几个句子作为重叠
                    overlap_sentences = current_chunk_sentences[-sentence_overlap:]
                    current_chunk_sentences = overlap_sentences
                    current_tokens = sum(self._count_tokens(s[0]) for s in overlap_sentences)
                    chunk_start_pos = overlap_sentences[0][1]
                else:
                    current_chunk_sentences = []
                    current_tokens = 0
                    chunk_start_pos = start_pos
            
            # 添加当前句子
            current_chunk_sentences.append((sentence, start_pos, end_pos))
            current_tokens += sentence_tokens
        
        # 处理最后一块
        if current_chunk_sentences:
            chunk_content = "".join([s[0] for s in current_chunk_sentences])
            chunk_end_pos = current_chunk_sentences[-1][2]
            chunks.append((chunk_content, chunk_start_pos, chunk_end_pos))
        
        return chunks
    
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """执行句子分块"""
        text = self._clean_text(text)
        document_id = metadata.get("document_id", str(uuid4())) if metadata else str(uuid4())
        
        # 使用配置的参数进行分块
        chunk_tuples = self._split_text_by_sentence(
            text,
            max_tokens=self.config.max_tokens,
            sentence_overlap=self.config.sentence_overlap
        )
        
        # 创建文档块对象
        chunks = []
        for i, (content, start_pos, end_pos) in enumerate(chunk_tuples):
            # 添加分块元数据
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "token_count": self._count_tokens(content),
                "sentence_count": len(self._split_mixed_sentences(content)),
                "language": self._detect_language(content),
                "chunking_method": "sentence_based"
            })
            
            chunk = self._create_chunk(
                content=content,
                start_index=start_pos,
                end_index=end_pos,
                chunk_index=i,
                document_id=document_id,
                metadata=chunk_metadata
            )
            chunks.append(chunk)
        
        return self._post_process_chunks(chunks)
    
    def _clean_text(self, text: str) -> str:
        """清理文本，保留句子结构"""
        # 标准化换行符
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # 移除多余的空行，但保留段落结构
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        if self.config.remove_extra_whitespace:
            # 移除行内多余空格，但保留必要的空格
            text = re.sub(r'[ \t]+', ' ', text)
            # 移除行首行尾空格
            lines = text.split('\n')
            lines = [line.strip() for line in lines]
            text = '\n'.join(lines)
        
        return text.strip()


# 便捷函数
def create_sentence_chunker(
    max_tokens: int = 1000,
    sentence_overlap: int = 2,
    encoding_model: str = "cl100k_base",
    **kwargs
) -> SentenceBasedChunker:
    """创建句子分块器的便捷函数"""
    config = SentenceBasedConfig(
        max_tokens=max_tokens,
        sentence_overlap=sentence_overlap,
        encoding_model=encoding_model,
        **kwargs
    )
    return SentenceBasedChunker(config)


async def chunk_by_sentence(
    text: str,
    document_id: str,
    max_tokens: int = 1000,
    sentence_overlap: int = 2,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> List[DocumentChunk]:
    """按句子分块的便捷函数"""
    chunker = create_sentence_chunker(
        max_tokens=max_tokens,
        sentence_overlap=sentence_overlap,
        **kwargs
    )
    
    # 确保元数据包含document_id
    if metadata is None:
        metadata = {}
    metadata["document_id"] = document_id
    
    return await chunker.chunk_text(text, metadata)