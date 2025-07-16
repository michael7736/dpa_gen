"""
混合智能分块器
结合多种分块策略优化检索命中率
"""

import asyncio
import hashlib
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import numpy as np
import tiktoken
from pydantic import BaseModel, Field

from ...config.settings import get_settings
from ...core.vectorization import VectorStore
from ...models.chunk import Chunk as DocumentChunk
from ...utils.logger import get_logger
from ..chunking import BaseChunker, ChunkingConfig, ChunkingStrategy

logger = get_logger(__name__)
settings = get_settings()


class HybridChunkingConfig(ChunkingConfig):
    """混合分块配置"""
    # 基础参数
    primary_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.SEMANTIC,
        description="主要分块策略"
    )
    secondary_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.SENTENCE_BASED,
        description="次要分块策略"
    )
    
    # 检索优化参数
    enable_context_windows: bool = Field(default=True, description="启用上下文窗口")
    context_window_size: int = Field(default=200, ge=50, le=500, description="上下文窗口大小（字符）")
    enable_sliding_windows: bool = Field(default=True, description="启用滑动窗口")
    sliding_window_step: float = Field(default=0.5, ge=0.1, le=0.9, description="滑动窗口步长比例")
    
    # 语义增强参数
    enable_semantic_clustering: bool = Field(default=True, description="启用语义聚类")
    semantic_diversity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="语义多样性阈值")
    
    # 关键信息识别
    enable_key_info_extraction: bool = Field(default=True, description="启用关键信息提取")
    key_info_patterns: List[str] = Field(
        default_factory=lambda: [
            r"(?:结论|总结|概述|摘要)[:：]",
            r"(?:关键|重要|核心|主要)(?:观点|发现|结果)",
            r"(?:第[一二三四五六七八九十]+|[\d]+)[\.、]\s*",
            r"(?:首先|其次|然后|最后|综上所述)",
        ],
        description="关键信息模式"
    )
    
    # 质量优化参数
    enable_chunk_refinement: bool = Field(default=True, description="启用块优化")
    min_semantic_density: float = Field(default=0.6, ge=0.0, le=1.0, description="最小语义密度")
    max_redundancy_ratio: float = Field(default=0.3, ge=0.0, le=1.0, description="最大冗余比例")
    
    # 性能参数
    batch_size: int = Field(default=10, ge=1, le=50, description="批处理大小")
    use_cache: bool = Field(default=True, description="使用缓存")


class HybridChunker(BaseChunker):
    """混合智能分块器"""
    
    def __init__(self, config: HybridChunkingConfig):
        super().__init__(config)
        self.config: HybridChunkingConfig = config
        
        # 初始化向量存储（如果需要）
        if config.use_embeddings:
            from ..vectorization import EmbeddingService, VectorConfig
            vector_config = VectorConfig()
            self.embedding_service = EmbeddingService(vector_config)
        else:
            self.embedding_service = None
            
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self._cache = {} if config.use_cache else None
        
        # 编译关键信息模式
        self.key_info_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in config.key_info_patterns
        ]
    
    async def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """执行混合分块"""
        text = self._clean_text(text)
        document_id = metadata.get("document_id", str(uuid4())) if metadata else str(uuid4())
        
        # 检查缓存
        if self._cache is not None:
            cache_key = self._generate_cache_key(text, document_id)
            if cache_key in self._cache:
                logger.info(f"从缓存返回分块结果: {cache_key}")
                return self._cache[cache_key]
        
        try:
            # 1. 执行主要分块策略
            primary_chunks = await self._apply_primary_strategy(text, document_id, metadata)
            
            # 2. 分析文本特征
            text_features = self._analyze_text_features(text)
            
            # 3. 应用优化策略
            optimized_chunks = await self._optimize_chunks(
                primary_chunks, text, text_features, document_id, metadata
            )
            
            # 4. 添加上下文窗口
            if self.config.enable_context_windows:
                optimized_chunks = self._add_context_windows(optimized_chunks, text)
            
            # 5. 创建滑动窗口块
            if self.config.enable_sliding_windows:
                sliding_chunks = self._create_sliding_windows(text, document_id, metadata)
                optimized_chunks.extend(sliding_chunks)
            
            # 6. 语义聚类和去重
            if self.config.enable_semantic_clustering and self.vector_store:
                optimized_chunks = await self._semantic_clustering(optimized_chunks)
            
            # 7. 最终优化和排序
            final_chunks = self._finalize_chunks(optimized_chunks)
            
            # 缓存结果
            if self._cache is not None:
                self._cache[cache_key] = final_chunks
            
            logger.info(f"混合分块完成: {len(final_chunks)} 个块")
            return final_chunks
            
        except Exception as e:
            logger.error(f"混合分块失败: {str(e)}")
            raise
    
    def _generate_cache_key(self, text: str, document_id: str) -> str:
        """生成缓存键"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        config_hash = hashlib.md5(str(self.config.dict()).encode()).hexdigest()
        return f"{document_id}_{text_hash}_{config_hash}"
    
    async def _apply_primary_strategy(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """应用主要分块策略"""
        from ..chunking import (
            FixedSizeChunker, SemanticChunker, StructuralChunker,
            ParagraphChunker, document_chunker
        )
        
        # 创建主策略分块器
        if self.config.primary_strategy == ChunkingStrategy.SEMANTIC:
            chunker = SemanticChunker(self.config)
        elif self.config.primary_strategy == ChunkingStrategy.STRUCTURAL:
            chunker = StructuralChunker(self.config)
        elif self.config.primary_strategy == ChunkingStrategy.PARAGRAPH:
            chunker = ParagraphChunker(self.config)
        elif self.config.primary_strategy == ChunkingStrategy.SENTENCE_BASED:
            from .sentence_based_chunker import SentenceBasedChunker, SentenceBasedConfig
            sentence_config = SentenceBasedConfig(
                max_tokens=self.config.chunk_size,
                sentence_overlap=2
            )
            chunker = SentenceBasedChunker(sentence_config)
        else:
            chunker = FixedSizeChunker(self.config)
        
        # 准备元数据
        chunk_metadata = metadata.copy() if metadata else {}
        chunk_metadata["document_id"] = document_id
        
        return await chunker.chunk_text(text, chunk_metadata)
    
    def _analyze_text_features(self, text: str) -> Dict[str, Any]:
        """分析文本特征"""
        features = {
            "length": len(text),
            "token_count": len(self.encoding.encode(text)),
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
            "sentence_count": len(re.findall(r'[。！？.!?]+', text)),
            "has_structure": bool(re.search(r'^#+\s+|\n#+\s+', text, re.MULTILINE)),
            "has_lists": bool(re.search(r'^\s*[-*•]\s+|\n\s*[-*•]\s+', text, re.MULTILINE)),
            "has_code": bool(re.search(r'```[\s\S]*?```|`[^`]+`', text)),
            "language": self._detect_language(text),
            "key_sections": self._identify_key_sections(text),
            "density_score": self._calculate_text_density(text)
        }
        
        return features
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = chinese_chars + english_chars
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        if chinese_ratio > 0.7:
            return "chinese"
        elif chinese_ratio < 0.3:
            return "english"
        else:
            return "mixed"
    
    def _identify_key_sections(self, text: str) -> List[Tuple[int, int, str]]:
        """识别关键章节"""
        key_sections = []
        
        for pattern in self.key_info_patterns:
            for match in pattern.finditer(text):
                start = match.start()
                end = min(match.end() + 500, len(text))  # 包含后续500字符
                section_type = self._classify_section(match.group())
                key_sections.append((start, end, section_type))
        
        # 合并重叠的章节
        key_sections = self._merge_overlapping_sections(key_sections)
        
        return key_sections
    
    def _classify_section(self, matched_text: str) -> str:
        """分类章节类型"""
        if re.search(r'结论|总结|概述|摘要', matched_text):
            return "summary"
        elif re.search(r'关键|重要|核心|主要', matched_text):
            return "key_point"
        elif re.search(r'第[一二三四五六七八九十]+|[\d]+', matched_text):
            return "numbered_point"
        else:
            return "transition"
    
    def _merge_overlapping_sections(
        self,
        sections: List[Tuple[int, int, str]]
    ) -> List[Tuple[int, int, str]]:
        """合并重叠的章节"""
        if not sections:
            return sections
        
        sections.sort(key=lambda x: x[0])
        merged = [sections[0]]
        
        for current in sections[1:]:
            last = merged[-1]
            if current[0] <= last[1]:
                # 重叠，合并
                merged[-1] = (last[0], max(last[1], current[1]), last[2])
            else:
                merged.append(current)
        
        return merged
    
    def _calculate_text_density(self, text: str) -> float:
        """计算文本密度（信息密度）"""
        if not text:
            return 0.0
        
        # 计算各种指标
        tokens = self.encoding.encode(text)
        unique_tokens = len(set(tokens))
        
        # 词汇多样性
        diversity = unique_tokens / len(tokens) if tokens else 0
        
        # 句子平均长度
        sentences = re.split(r'[。！？.!?]+', text)
        avg_sentence_length = np.mean([len(s) for s in sentences if s.strip()])
        
        # 关键词密度
        keywords = re.findall(r'\b(?:重要|关键|核心|主要|必须|应该|需要)\b', text)
        keyword_density = len(keywords) / len(text.split()) if text.split() else 0
        
        # 综合密度分数
        density = (diversity * 0.4 + 
                  min(avg_sentence_length / 100, 1.0) * 0.3 + 
                  min(keyword_density * 10, 1.0) * 0.3)
        
        return density
    
    async def _optimize_chunks(
        self,
        chunks: List[DocumentChunk],
        full_text: str,
        text_features: Dict[str, Any],
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """优化分块"""
        optimized_chunks = []
        
        for chunk in chunks:
            # 1. 检查是否包含关键信息
            is_key_chunk = self._contains_key_info(chunk.content, text_features)
            
            # 2. 计算块的质量分数
            quality_score = self._calculate_chunk_quality(chunk, text_features)
            
            # 3. 根据质量决定优化策略
            if quality_score < self.config.min_semantic_density and not is_key_chunk:
                # 尝试与相邻块合并
                continue  # 暂时跳过低质量块
            
            # 4. 增强块的元数据
            enhanced_chunk = self._enhance_chunk_metadata(
                chunk, text_features, is_key_chunk, quality_score
            )
            
            optimized_chunks.append(enhanced_chunk)
        
        # 5. 处理被跳过的块（尝试合并）
        optimized_chunks = self._merge_low_quality_chunks(optimized_chunks, chunks)
        
        return optimized_chunks
    
    def _contains_key_info(self, content: str, text_features: Dict[str, Any]) -> bool:
        """检查块是否包含关键信息"""
        # 检查是否匹配关键信息模式
        for pattern in self.key_info_patterns:
            if pattern.search(content):
                return True
        
        # 检查是否在关键章节中
        for start, end, section_type in text_features.get("key_sections", []):
            if section_type in ["summary", "key_point"]:
                return True
        
        return False
    
    def _calculate_chunk_quality(
        self,
        chunk: DocumentChunk,
        text_features: Dict[str, Any]
    ) -> float:
        """计算块质量分数"""
        content = chunk.content
        
        # 长度分数
        length_score = min(len(content) / self.config.chunk_size, 1.0)
        
        # 完整性分数（是否包含完整的句子）
        completeness_score = 1.0
        if not re.search(r'[。！？.!?]$', content.strip()):
            completeness_score = 0.7
        
        # 信息密度分数
        density_score = self._calculate_text_density(content)
        
        # 结构分数（是否有清晰的结构）
        structure_score = 0.5
        if re.search(r'^\s*[-*•\d]\s+', content, re.MULTILINE):
            structure_score = 0.8
        if re.search(r'^#+\s+', content, re.MULTILINE):
            structure_score = 0.9
        
        # 综合质量分数
        quality = (
            length_score * 0.2 +
            completeness_score * 0.3 +
            density_score * 0.3 +
            structure_score * 0.2
        )
        
        return quality
    
    def _enhance_chunk_metadata(
        self,
        chunk: DocumentChunk,
        text_features: Dict[str, Any],
        is_key_chunk: bool,
        quality_score: float
    ) -> DocumentChunk:
        """增强块的元数据"""
        # 复制原始块
        enhanced_chunk = DocumentChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            content=chunk.content,
            content_hash=chunk.content_hash,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            chunk_index=chunk.chunk_index,
            char_count=chunk.char_count
        )
        
        # 添加增强元数据
        enhanced_metadata = {
            "quality_score": quality_score,
            "is_key_chunk": is_key_chunk,
            "chunk_type": self._determine_chunk_type(chunk.content),
            "language": text_features.get("language", "unknown"),
            "token_count": len(self.encoding.encode(chunk.content)),
            "sentence_count": len(re.findall(r'[。！？.!?]+', chunk.content)),
            "has_structure": bool(re.search(r'^#+\s+|\n#+\s+', chunk.content, re.MULTILINE)),
            "optimization_method": "hybrid_chunking"
        }
        
        # 如果是关键块，添加额外信息
        if is_key_chunk:
            enhanced_metadata["key_info_types"] = self._identify_key_info_types(chunk.content)
            enhanced_metadata["importance_score"] = min(quality_score * 1.5, 1.0)
        
        # 合并元数据
        if hasattr(chunk, 'metadata') and isinstance(chunk.metadata, dict):
            enhanced_metadata.update(chunk.metadata)
        
        # 设置元数据
        if hasattr(enhanced_chunk, 'metadata'):
            enhanced_chunk.metadata = enhanced_metadata
        
        return enhanced_chunk
    
    def _determine_chunk_type(self, content: str) -> str:
        """确定块类型"""
        if re.search(r'```[\s\S]*?```', content):
            return "code"
        elif re.search(r'^\s*[-*•]\s+', content, re.MULTILINE):
            return "list"
        elif re.search(r'^#+\s+', content, re.MULTILINE):
            return "section"
        elif re.search(r'\|.*\|.*\|', content):
            return "table"
        elif len(content.split('\n\n')) > 3:
            return "multi_paragraph"
        else:
            return "paragraph"
    
    def _identify_key_info_types(self, content: str) -> List[str]:
        """识别关键信息类型"""
        types = []
        
        if re.search(r'结论|总结|概述', content):
            types.append("summary")
        if re.search(r'定义|概念|含义', content):
            types.append("definition")
        if re.search(r'步骤|流程|过程', content):
            types.append("process")
        if re.search(r'优点|缺点|利弊', content):
            types.append("comparison")
        if re.search(r'建议|推荐|应该', content):
            types.append("recommendation")
        
        return types
    
    def _merge_low_quality_chunks(
        self,
        optimized_chunks: List[DocumentChunk],
        original_chunks: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        """合并低质量块"""
        # 这里简化处理，实际实现需要更复杂的逻辑
        return optimized_chunks
    
    def _add_context_windows(
        self,
        chunks: List[DocumentChunk],
        full_text: str
    ) -> List[DocumentChunk]:
        """添加上下文窗口"""
        enhanced_chunks = []
        
        for chunk in chunks:
            # 添加前后文
            context_start = max(0, chunk.start_char - self.config.context_window_size)
            context_end = min(len(full_text), chunk.end_char + self.config.context_window_size)
            
            # 提取上下文
            pre_context = full_text[context_start:chunk.start_char].strip()
            post_context = full_text[chunk.end_char:context_end].strip()
            
            # 创建增强块
            enhanced_chunk = DocumentChunk(
                id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                content_hash=chunk.content_hash,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                chunk_index=chunk.chunk_index,
                char_count=chunk.char_count
            )
            
            # 添加上下文到元数据
            if hasattr(chunk, 'metadata') and isinstance(chunk.metadata, dict):
                enhanced_metadata = chunk.metadata.copy()
            else:
                enhanced_metadata = {}
            
            enhanced_metadata.update({
                "pre_context": pre_context[-100:] if pre_context else "",  # 限制长度
                "post_context": post_context[:100] if post_context else "",
                "has_context": True
            })
            
            if hasattr(enhanced_chunk, 'metadata'):
                enhanced_chunk.metadata = enhanced_metadata
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _create_sliding_windows(
        self,
        text: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """创建滑动窗口块"""
        sliding_chunks = []
        
        window_size = self.config.chunk_size
        step_size = int(window_size * self.config.sliding_window_step)
        
        for i in range(0, len(text) - window_size + 1, step_size):
            window_content = text[i:i + window_size]
            
            # 调整到句子边界
            if i + window_size < len(text):
                # 尝试在句子结束处断开
                last_period = window_content.rfind('。')
                last_period_en = window_content.rfind('.')
                last_break = max(last_period, last_period_en)
                
                if last_break > window_size * 0.8:
                    window_content = window_content[:last_break + 1]
            
            # 创建滑动窗口块
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_type": "sliding_window",
                "window_size": len(window_content),
                "overlap_ratio": self.config.sliding_window_step
            })
            
            chunk = self._create_chunk(
                content=window_content,
                start_index=i,
                end_index=i + len(window_content),
                chunk_index=len(sliding_chunks),
                document_id=document_id,
                metadata=chunk_metadata
            )
            
            sliding_chunks.append(chunk)
        
        return sliding_chunks
    
    async def _semantic_clustering(
        self,
        chunks: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        """语义聚类和去重"""
        if not chunks or not self.embedding_service:
            return chunks
        
        # 批量生成嵌入向量
        contents = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.embed_documents(contents)
        
        # 计算相似度矩阵
        similarity_matrix = self._compute_similarity_matrix(embeddings)
        
        # 识别高度相似的块
        clusters = self._cluster_similar_chunks(similarity_matrix)
        
        # 从每个聚类中选择最佳块
        selected_indices = self._select_best_from_clusters(chunks, clusters)
        
        # 返回选中的块
        return [chunks[i] for i in sorted(selected_indices)]
    
    def _compute_similarity_matrix(self, embeddings: List[List[float]]) -> np.ndarray:
        """计算相似度矩阵"""
        n = len(embeddings)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity
        
        return similarity_matrix
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _cluster_similar_chunks(self, similarity_matrix: np.ndarray) -> List[Set[int]]:
        """聚类相似块"""
        n = len(similarity_matrix)
        clusters = []
        visited = set()
        
        threshold = 1.0 - self.config.semantic_diversity_threshold
        
        for i in range(n):
            if i in visited:
                continue
            
            cluster = {i}
            visited.add(i)
            
            for j in range(i + 1, n):
                if j not in visited and similarity_matrix[i, j] > threshold:
                    cluster.add(j)
                    visited.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _select_best_from_clusters(
        self,
        chunks: List[DocumentChunk],
        clusters: List[Set[int]]
    ) -> Set[int]:
        """从每个聚类中选择最佳块"""
        selected = set()
        
        for cluster in clusters:
            if len(cluster) == 1:
                selected.update(cluster)
                continue
            
            # 选择质量最高的块
            best_idx = None
            best_score = -1
            
            for idx in cluster:
                chunk = chunks[idx]
                # 计算综合分数
                score = 0.0
                
                # 考虑元数据中的质量分数
                if hasattr(chunk, 'metadata') and isinstance(chunk.metadata, dict):
                    score += chunk.metadata.get('quality_score', 0.5)
                    if chunk.metadata.get('is_key_chunk', False):
                        score += 0.3
                
                # 考虑长度
                score += min(chunk.char_count / self.config.chunk_size, 1.0) * 0.2
                
                if score > best_score:
                    best_score = score
                    best_idx = idx
            
            if best_idx is not None:
                selected.add(best_idx)
        
        return selected
    
    def _finalize_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """最终优化和排序块"""
        # 重新编号
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
        
        # 按位置排序
        chunks.sort(key=lambda x: x.start_char)
        
        # 添加最终元数据
        for chunk in chunks:
            if hasattr(chunk, 'metadata') and isinstance(chunk.metadata, dict):
                chunk.metadata['total_chunks'] = len(chunks)
                chunk.metadata['final_optimization'] = True
        
        return chunks


# 便捷函数
def create_hybrid_chunker(**kwargs) -> HybridChunker:
    """创建混合分块器"""
    config = HybridChunkingConfig(**kwargs)
    return HybridChunker(config)


async def hybrid_chunk_text(
    text: str,
    document_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> List[DocumentChunk]:
    """使用混合策略分块文本"""
    chunker = create_hybrid_chunker(**kwargs)
    
    if metadata is None:
        metadata = {}
    metadata["document_id"] = document_id
    
    return await chunker.chunk_text(text, metadata)