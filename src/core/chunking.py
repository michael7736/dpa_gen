"""
智能分块处理模块
实现层次化文档分块，支持语义感知的文档切分
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)

class ChunkType(Enum):
    """分块类型枚举"""
    TITLE = "title"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CODE = "code"
    FORMULA = "formula"

@dataclass
class ChunkMetadata:
    """分块元数据"""
    chunk_id: str
    chunk_type: ChunkType
    level: int  # 层次级别 (1-6)
    parent_id: Optional[str] = None
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    position: Optional[int] = None
    token_count: Optional[int] = None
    
class HierarchicalChunker:
    """层次化分块器"""
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        chunk_overlap: int = 200,
        model_name: str = "gpt-3.5-turbo"
    ):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model(model_name)
        
        # 标题模式匹配
        self.title_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown标题
            r'^第[一二三四五六七八九十\d]+[章节部分]\s*(.*)$',  # 中文章节
            r'^Chapter\s+\d+\s*(.*)$',  # 英文章节
            r'^Section\s+\d+\s*(.*)$',  # 英文节
            r'^\d+\.\s+(.+)$',  # 数字编号标题
            r'^\d+\.\d+\s+(.+)$',  # 二级数字编号
        ]
        
        # 列表模式匹配
        self.list_patterns = [
            r'^[-*+]\s+(.+)$',  # 无序列表
            r'^\d+\.\s+(.+)$',  # 有序列表
            r'^[a-zA-Z]\.\s+(.+)$',  # 字母列表
        ]
        
        # 代码块模式
        self.code_patterns = [
            r'```[\s\S]*?```',  # Markdown代码块
            r'`[^`]+`',  # 行内代码
        ]
        
        # 公式模式
        self.formula_patterns = [
            r'\$\$[\s\S]*?\$\$',  # 块级公式
            r'\$[^$]+\$',  # 行内公式
        ]

    def count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token计数失败: {e}")
            return len(text) // 4  # 粗略估算

    def detect_chunk_type(self, text: str) -> ChunkType:
        """检测文本块类型"""
        text = text.strip()
        
        # 检测标题
        for pattern in self.title_patterns:
            if re.match(pattern, text, re.MULTILINE):
                return ChunkType.TITLE
        
        # 检测列表项
        for pattern in self.list_patterns:
            if re.match(pattern, text):
                return ChunkType.LIST_ITEM
        
        # 检测代码块
        for pattern in self.code_patterns:
            if re.search(pattern, text):
                return ChunkType.CODE
        
        # 检测公式
        for pattern in self.formula_patterns:
            if re.search(pattern, text):
                return ChunkType.FORMULA
        
        # 检测表格
        if '|' in text and text.count('|') >= 4:
            return ChunkType.TABLE
        
        # 默认为段落
        return ChunkType.PARAGRAPH

    def extract_title_level(self, text: str) -> int:
        """提取标题级别"""
        text = text.strip()
        
        # Markdown标题
        if text.startswith('#'):
            return min(text.count('#'), 6)
        
        # 中文章节
        if re.match(r'^第[一二三四五六七八九十\d]+章', text):
            return 1
        if re.match(r'^第[一二三四五六七八九十\d]+节', text):
            return 2
        if re.match(r'^第[一二三四五六七八九十\d]+部分', text):
            return 3
        
        # 数字编号
        if re.match(r'^\d+\.\s+', text):
            return 2
        if re.match(r'^\d+\.\d+\s+', text):
            return 3
        if re.match(r'^\d+\.\d+\.\d+\s+', text):
            return 4
        
        return 1

    def split_by_structure(self, text: str) -> List[Dict[str, Any]]:
        """基于文档结构进行分割"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_metadata = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                if current_chunk:
                    current_chunk.append('')
                continue
            
            chunk_type = self.detect_chunk_type(line)
            
            # 如果遇到新的标题，保存当前块并开始新块
            if chunk_type == ChunkType.TITLE:
                if current_chunk:
                    chunks.append({
                        'text': '\n'.join(current_chunk).strip(),
                        'metadata': current_metadata
                    })
                
                level = self.extract_title_level(line)
                current_metadata = ChunkMetadata(
                    chunk_id=f"chunk_{len(chunks)}",
                    chunk_type=chunk_type,
                    level=level,
                    section_title=line,
                    position=i
                )
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        # 添加最后一个块
        if current_chunk:
            chunks.append({
                'text': '\n'.join(current_chunk).strip(),
                'metadata': current_metadata or ChunkMetadata(
                    chunk_id=f"chunk_{len(chunks)}",
                    chunk_type=ChunkType.PARAGRAPH,
                    level=1,
                    position=len(lines)
                )
            })
        
        return chunks

    def split_large_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分割过大的文本块"""
        result = []
        
        for chunk in chunks:
            text = chunk['text']
            metadata = chunk['metadata']
            
            token_count = self.count_tokens(text)
            
            if token_count <= self.max_chunk_size:
                metadata.token_count = token_count
                result.append(chunk)
            else:
                # 使用递归字符分割器进一步分割
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.max_chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    length_function=self.count_tokens,
                    separators=["\n\n", "\n", "。", ".", " ", ""]
                )
                
                sub_texts = splitter.split_text(text)
                
                for j, sub_text in enumerate(sub_texts):
                    sub_metadata = ChunkMetadata(
                        chunk_id=f"{metadata.chunk_id}_sub_{j}",
                        chunk_type=metadata.chunk_type,
                        level=metadata.level,
                        parent_id=metadata.chunk_id,
                        section_title=metadata.section_title,
                        page_number=metadata.page_number,
                        position=metadata.position,
                        token_count=self.count_tokens(sub_text)
                    )
                    
                    result.append({
                        'text': sub_text,
                        'metadata': sub_metadata
                    })
        
        return result

    def build_hierarchy(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建层次关系"""
        hierarchy_stack = []  # 存储各级别的父节点
        
        for chunk in chunks:
            metadata = chunk['metadata']
            
            if metadata.chunk_type == ChunkType.TITLE:
                level = metadata.level
                
                # 清理比当前级别高的栈项
                hierarchy_stack = [item for item in hierarchy_stack if item['level'] < level]
                
                # 设置父节点
                if hierarchy_stack:
                    metadata.parent_id = hierarchy_stack[-1]['chunk_id']
                
                # 添加到栈中
                hierarchy_stack.append({
                    'chunk_id': metadata.chunk_id,
                    'level': level
                })
            else:
                # 非标题块，设置最近的标题为父节点
                if hierarchy_stack:
                    metadata.parent_id = hierarchy_stack[-1]['chunk_id']
        
        return chunks

    def chunk_document(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """对文档进行层次化分块"""
        logger.info(f"开始对文档 {document_id} 进行层次化分块")
        
        # 1. 基于结构分割
        chunks = self.split_by_structure(text)
        logger.debug(f"结构分割得到 {len(chunks)} 个初始块")
        
        # 2. 分割过大的块
        chunks = self.split_large_chunks(chunks)
        logger.debug(f"大小分割后得到 {len(chunks)} 个块")
        
        # 3. 构建层次关系
        chunks = self.build_hierarchy(chunks)
        logger.debug("完成层次关系构建")
        
        # 4. 转换为LangChain Document格式
        documents = []
        for chunk in chunks:
            chunk_metadata = chunk['metadata']
            
            # 合并元数据
            doc_metadata = {
                'document_id': document_id,
                'chunk_id': chunk_metadata.chunk_id,
                'chunk_type': chunk_metadata.chunk_type.value,
                'level': chunk_metadata.level,
                'parent_id': chunk_metadata.parent_id,
                'section_title': chunk_metadata.section_title,
                'page_number': chunk_metadata.page_number,
                'position': chunk_metadata.position,
                'token_count': chunk_metadata.token_count,
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            documents.append(Document(
                page_content=chunk['text'],
                metadata=doc_metadata
            ))
        
        logger.info(f"文档 {document_id} 分块完成，共生成 {len(documents)} 个文档块")
        return documents

class SemanticChunker:
    """语义感知分块器"""
    
    def __init__(self, embedding_model=None, similarity_threshold: float = 0.7):
        self.embedding_model = embedding_model
        self.similarity_threshold = similarity_threshold
    
    def semantic_split(self, text: str, base_chunks: List[str]) -> List[str]:
        """基于语义相似度进行分块优化"""
        if not self.embedding_model:
            return base_chunks
        
        # TODO: 实现语义分块逻辑
        # 1. 计算相邻块的语义相似度
        # 2. 合并相似度高的块
        # 3. 分割相似度低的块
        
        return base_chunks

def create_chunker(
    chunker_type: str = "hierarchical",
    **kwargs
) -> HierarchicalChunker:
    """创建分块器工厂函数"""
    if chunker_type == "hierarchical":
        return HierarchicalChunker(**kwargs)
    elif chunker_type == "semantic":
        return SemanticChunker(**kwargs)
    else:
        raise ValueError(f"不支持的分块器类型: {chunker_type}") 