"""
S2语义分块算法 - 支持500K+ token的超长文档处理
基于语义边界和动态大小的智能分块策略
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from ...utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class S2Chunk:
    """S2语义分块"""
    id: str
    content: str
    start_char: int
    end_char: int
    start_token: int
    end_token: int
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    semantic_density: float = 0.0
    coherence_score: float = 0.0
    boundary_confidence: float = 0.0


class S2SemanticChunker:
    """S2语义分块器 - 支持超长文档"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 分块参数
        self.min_chunk_size = self.config.get("min_chunk_size", 500)
        self.max_chunk_size = self.config.get("max_chunk_size", 2000)
        self.target_chunk_size = self.config.get("target_chunk_size", 1000)
        self.overlap_size = self.config.get("overlap_size", 200)
        
        # 语义参数
        self.semantic_threshold = self.config.get("semantic_threshold", 0.7)
        self.boundary_window = self.config.get("boundary_window", 100)
        
        # 初始化模型
        try:
            from ...config.settings import get_settings
            settings = get_settings()
            
            if settings.ai_model.openai_api_key:
                self.embeddings = OpenAIEmbeddings(
                    model="text-embedding-3-small",
                    openai_api_key=settings.ai_model.openai_api_key,
                    openai_api_base=settings.ai_model.openai_base_url
                )
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0,
                    openai_api_key=settings.ai_model.openai_api_key,
                    openai_api_base=settings.ai_model.openai_base_url
                )
                logger.info("S2 Chunker models initialized successfully")
            else:
                raise ValueError("OpenAI API key not found")
                
        except Exception as e:
            logger.warning(f"Failed to initialize S2 Chunker models: {e}")
            # 使用模拟模式
            self.embeddings = None
            self.llm = None
        
        # 缓存
        self._embedding_cache = {}
        self._boundary_cache = {}
    
    async def chunk_document(
        self,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[S2Chunk]:
        """
        对文档进行S2语义分块
        
        Args:
            document: 文档内容
            metadata: 文档元数据
            
        Returns:
            S2分块列表
        """
        logger.info(f"开始S2语义分块，文档长度: {len(document)} 字符")
        
        # 1. 预处理和初步分割
        segments = self._preliminary_segmentation(document)
        logger.info(f"初步分割完成，得到 {len(segments)} 个段落")
        
        # 2. 语义边界检测
        boundaries = await self._detect_semantic_boundaries(segments)
        logger.info(f"检测到 {len(boundaries)} 个语义边界")
        
        # 3. 动态分块
        chunks = await self._create_dynamic_chunks(document, segments, boundaries)
        logger.info(f"创建了 {len(chunks)} 个初始分块")
        
        # 4. 分块优化
        optimized_chunks = await self._optimize_chunks(chunks)
        logger.info(f"优化后得到 {len(optimized_chunks)} 个分块")
        
        # 5. 添加重叠窗口
        final_chunks = self._add_overlap_windows(optimized_chunks, document)
        
        # 6. 计算分块质量指标
        for chunk in final_chunks:
            chunk.semantic_density = await self._calculate_semantic_density(chunk.content)
            chunk.coherence_score = await self._calculate_coherence(chunk.content)
        
        # 7. 添加元数据
        doc_metadata = metadata or {}
        for i, chunk in enumerate(final_chunks):
            chunk.metadata.update({
                "chunk_index": i,
                "total_chunks": len(final_chunks),
                "document_metadata": doc_metadata,
                "chunking_method": "s2_semantic",
                "created_at": datetime.now().isoformat()
            })
        
        logger.info(f"S2语义分块完成，最终得到 {len(final_chunks)} 个分块")
        return final_chunks
    
    def _preliminary_segmentation(self, document: str) -> List[Dict[str, Any]]:
        """初步分割 - 基于段落和标点"""
        segments = []
        
        # 1. 按双换行符分割段落
        paragraphs = re.split(r'\n\n+', document)
        
        current_pos = 0
        for para in paragraphs:
            if not para.strip():
                continue
                
            # 2. 检查段落是否需要进一步分割
            if len(para) > self.max_chunk_size:
                # 按句子分割
                sentences = self._split_sentences(para)
                
                sub_segments = []
                current_segment = ""
                
                for sent in sentences:
                    if len(current_segment) + len(sent) > self.max_chunk_size:
                        if current_segment:
                            sub_segments.append(current_segment)
                        current_segment = sent
                    else:
                        current_segment += " " + sent if current_segment else sent
                
                if current_segment:
                    sub_segments.append(current_segment)
                
                # 添加子段落
                for sub in sub_segments:
                    start = document.find(sub, current_pos)
                    if start != -1:
                        segments.append({
                            "content": sub,
                            "start": start,
                            "end": start + len(sub),
                            "type": "sub_paragraph"
                        })
                        current_pos = start + len(sub)
            else:
                # 直接添加段落
                start = document.find(para, current_pos)
                if start != -1:
                    segments.append({
                        "content": para,
                        "start": start,
                        "end": start + len(para),
                        "type": "paragraph"
                    })
                    current_pos = start + len(para)
        
        return segments
    
    def _split_sentences(self, text: str) -> List[str]:
        """智能句子分割"""
        # 使用正则表达式分割句子，但保留标点符号
        sentence_endings = r'[.!?。！？]'
        sentences = re.split(f'({sentence_endings})', text)
        
        # 重新组合句子和标点
        result = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                result.append(sentences[i] + sentences[i+1])
            else:
                result.append(sentences[i])
        
        return [s.strip() for s in result if s.strip()]
    
    async def _detect_semantic_boundaries(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """检测语义边界"""
        boundaries = []
        
        # 批量生成嵌入
        texts = [seg["content"] for seg in segments]
        if self.embeddings is None:
            # 模拟模式：生成随机相似度
            embeddings = [[0.1] * 384 for _ in texts]
        else:
            embeddings = await self._batch_embed(texts)
        
        # 计算相邻段落的语义相似度
        for i in range(len(segments) - 1):
            similarity = self._cosine_similarity(embeddings[i], embeddings[i+1])
            
            # 如果相似度低于阈值，标记为边界
            if similarity < self.semantic_threshold:
                boundaries.append({
                    "position": segments[i]["end"],
                    "confidence": 1 - similarity,
                    "type": "semantic",
                    "segments": (i, i+1)
                })
        
        # 检测主题转换
        topic_boundaries = await self._detect_topic_shifts(segments)
        boundaries.extend(topic_boundaries)
        
        # 按位置排序并去重
        boundaries = sorted(boundaries, key=lambda x: x["position"])
        return self._merge_nearby_boundaries(boundaries)
    
    async def _detect_topic_shifts(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """检测主题转换"""
        boundaries = []
        
        # 批量分析主题
        batch_size = 10
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i+batch_size]
            
            # 构建主题分析提示
            texts = [seg["content"][:200] for seg in batch]  # 使用前200字符
            prompt = f"""
分析以下文本片段，识别主题转换点。
返回JSON格式：{{"shifts": [int]}}，其中shifts是发生主题转换的片段索引。

文本片段：
"""
            for j, text in enumerate(texts):
                prompt += f"\n{j}: {text}"
            
            try:
                if self.llm is None:
                    # 模拟模式：随机生成一些主题转换点
                    import random
                    result = {"shifts": [random.randint(0, len(batch)-2)] if random.random() > 0.7 else []}
                else:
                    response = await self.llm.ainvoke([HumanMessage(content=prompt)])
                    # 解析响应
                    import json
                    result = json.loads(response.content)
                
                for shift_idx in result.get("shifts", []):
                    if shift_idx < len(batch) - 1:
                        actual_idx = i + shift_idx
                        boundaries.append({
                            "position": segments[actual_idx]["end"],
                            "confidence": 0.8,
                            "type": "topic_shift",
                            "segments": (actual_idx, actual_idx + 1)
                        })
            except Exception as e:
                logger.warning(f"主题检测失败: {e}")
        
        return boundaries
    
    def _merge_nearby_boundaries(
        self,
        boundaries: List[Dict[str, Any]],
        merge_distance: int = 50
    ) -> List[Dict[str, Any]]:
        """合并相近的边界"""
        if not boundaries:
            return []
        
        merged = [boundaries[0]]
        
        for boundary in boundaries[1:]:
            last = merged[-1]
            if boundary["position"] - last["position"] < merge_distance:
                # 合并边界，取更高的置信度
                last["confidence"] = max(last["confidence"], boundary["confidence"])
                if boundary["type"] != last["type"]:
                    last["type"] = "mixed"
            else:
                merged.append(boundary)
        
        return merged
    
    async def _create_dynamic_chunks(
        self,
        document: str,
        segments: List[Dict[str, Any]],
        boundaries: List[Dict[str, Any]]
    ) -> List[S2Chunk]:
        """创建动态大小的分块"""
        chunks = []
        
        # 将边界位置转换为集合以便快速查找
        boundary_positions = {b["position"] for b in boundaries}
        
        current_chunk_start = 0
        current_chunk_content = ""
        current_segments = []
        
        for i, segment in enumerate(segments):
            # 检查是否应该在此段落后创建新分块
            should_split = False
            
            # 条件1：达到边界
            if segment["end"] in boundary_positions:
                should_split = True
            
            # 条件2：超过最大大小
            if len(current_chunk_content) + len(segment["content"]) > self.max_chunk_size:
                should_split = True
            
            # 条件3：当前块已经达到目标大小且遇到段落边界
            if (len(current_chunk_content) > self.target_chunk_size and 
                segment["type"] == "paragraph"):
                should_split = True
            
            if should_split and current_chunk_content:
                # 创建分块
                chunk_id = self._generate_chunk_id(current_chunk_content, len(chunks))
                chunk = S2Chunk(
                    id=chunk_id,
                    content=current_chunk_content.strip(),
                    start_char=current_chunk_start,
                    end_char=segment["start"],
                    start_token=0,  # TODO: 计算实际token
                    end_token=0,
                    metadata={
                        "segment_indices": [s["index"] for s in current_segments if "index" in s],
                        "boundary_type": self._get_boundary_type(segment["end"], boundaries)
                    }
                )
                chunks.append(chunk)
                
                # 重置
                current_chunk_start = segment["start"]
                current_chunk_content = segment["content"]
                current_segments = [segment]
            else:
                # 添加到当前块
                if current_chunk_content:
                    current_chunk_content += "\n\n" + segment["content"]
                else:
                    current_chunk_content = segment["content"]
                    current_chunk_start = segment["start"]
                current_segments.append(segment)
        
        # 处理最后一个块
        if current_chunk_content:
            chunk_id = self._generate_chunk_id(current_chunk_content, len(chunks))
            chunk = S2Chunk(
                id=chunk_id,
                content=current_chunk_content.strip(),
                start_char=current_chunk_start,
                end_char=len(document),
                start_token=0,
                end_token=0,
                metadata={}
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _optimize_chunks(self, chunks: List[S2Chunk]) -> List[S2Chunk]:
        """优化分块 - 合并过小的块，分割过大的块"""
        optimized = []
        i = 0
        
        while i < len(chunks):
            chunk = chunks[i]
            
            # 处理过小的块
            if len(chunk.content) < self.min_chunk_size and i < len(chunks) - 1:
                # 尝试与下一个块合并
                next_chunk = chunks[i + 1]
                if len(chunk.content) + len(next_chunk.content) <= self.max_chunk_size:
                    # 合并
                    merged_content = chunk.content + "\n\n" + next_chunk.content
                    merged_chunk = S2Chunk(
                        id=self._generate_chunk_id(merged_content, len(optimized)),
                        content=merged_content,
                        start_char=chunk.start_char,
                        end_char=next_chunk.end_char,
                        start_token=chunk.start_token,
                        end_token=next_chunk.end_token,
                        metadata={
                            **chunk.metadata,
                            "merged": True,
                            "original_chunks": [chunk.id, next_chunk.id]
                        }
                    )
                    optimized.append(merged_chunk)
                    i += 2  # 跳过下一个块
                    continue
            
            # 处理过大的块
            elif len(chunk.content) > self.max_chunk_size * 1.5:
                # 分割
                sub_chunks = await self._split_large_chunk(chunk)
                optimized.extend(sub_chunks)
                i += 1
                continue
            
            # 正常大小的块
            optimized.append(chunk)
            i += 1
        
        return optimized
    
    async def _split_large_chunk(self, chunk: S2Chunk) -> List[S2Chunk]:
        """分割过大的块"""
        # 使用句子边界分割
        sentences = self._split_sentences(chunk.content)
        
        sub_chunks = []
        current_content = ""
        current_start = chunk.start_char
        
        for sent in sentences:
            if len(current_content) + len(sent) > self.target_chunk_size and current_content:
                # 创建子块
                sub_chunk = S2Chunk(
                    id=f"{chunk.id}_sub{len(sub_chunks)}",
                    content=current_content.strip(),
                    start_char=current_start,
                    end_char=current_start + len(current_content),
                    start_token=0,
                    end_token=0,
                    metadata={
                        **chunk.metadata,
                        "split": True,
                        "parent_chunk": chunk.id
                    }
                )
                sub_chunks.append(sub_chunk)
                
                current_content = sent
                current_start += len(current_content)
            else:
                current_content += " " + sent if current_content else sent
        
        # 添加最后一个子块
        if current_content:
            sub_chunk = S2Chunk(
                id=f"{chunk.id}_sub{len(sub_chunks)}",
                content=current_content.strip(),
                start_char=current_start,
                end_char=chunk.end_char,
                start_token=0,
                end_token=0,
                metadata={
                    **chunk.metadata,
                    "split": True,
                    "parent_chunk": chunk.id
                }
            )
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _add_overlap_windows(
        self,
        chunks: List[S2Chunk],
        document: str
    ) -> List[S2Chunk]:
        """添加重叠窗口以保持上下文连续性"""
        if not chunks or self.overlap_size <= 0:
            return chunks
        
        enhanced_chunks = []
        
        for i, chunk in enumerate(chunks):
            # 添加前文重叠
            if i > 0:
                prev_chunk = chunks[i-1]
                overlap_start = max(0, len(prev_chunk.content) - self.overlap_size)
                prefix = prev_chunk.content[overlap_start:]
                
                # 更新内容和元数据
                chunk.content = prefix + "\n[...]\n" + chunk.content
                chunk.metadata["has_prefix_overlap"] = True
                chunk.metadata["prefix_length"] = len(prefix)
            
            # 添加后文重叠
            if i < len(chunks) - 1:
                next_chunk = chunks[i+1]
                suffix = next_chunk.content[:self.overlap_size]
                
                chunk.content = chunk.content + "\n[...]\n" + suffix
                chunk.metadata["has_suffix_overlap"] = True
                chunk.metadata["suffix_length"] = len(suffix)
            
            enhanced_chunks.append(chunk)
        
        return enhanced_chunks
    
    async def _calculate_semantic_density(self, text: str) -> float:
        """计算语义密度 - 信息含量的度量"""
        # 简化实现：基于实体和关键词密度
        words = text.split()
        if not words:
            return 0.0
        
        # 计算独特词汇比例
        unique_words = set(words)
        uniqueness_ratio = len(unique_words) / len(words)
        
        # 计算平均词长（假设长词包含更多信息）
        avg_word_length = sum(len(w) for w in words) / len(words)
        
        # 综合评分
        density = (uniqueness_ratio * 0.6 + min(avg_word_length / 10, 1.0) * 0.4)
        
        return round(density, 3)
    
    async def _calculate_coherence(self, text: str) -> float:
        """计算文本连贯性"""
        # 简化实现：基于句子之间的语义相似度
        sentences = self._split_sentences(text)
        if len(sentences) < 2:
            return 1.0
        
        # 计算相邻句子的平均相似度
        embeddings = await self._batch_embed(sentences[:5])  # 限制数量
        
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i+1])
            similarities.append(sim)
        
        return round(np.mean(similarities) if similarities else 0.5, 3)
    
    async def _batch_embed(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        # 检查缓存
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self._embedding_cache:
                embeddings.append(self._embedding_cache[text_hash])
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 批量生成未缓存的嵌入
        if uncached_texts:
            if self.embeddings is None:
                # 模拟模式：生成随机嵌入
                new_embeddings = [[0.1] * 384 for _ in uncached_texts]
            else:
                new_embeddings = await self.embeddings.aembed_documents(uncached_texts)
            
            # 更新缓存和结果
            for i, (idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                text_hash = hashlib.md5(text.encode()).hexdigest()
                self._embedding_cache[text_hash] = new_embeddings[i]
                embeddings[idx] = new_embeddings[i]
        
        return embeddings
    
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
    
    def _generate_chunk_id(self, content: str, index: int) -> str:
        """生成分块ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"s2_chunk_{index}_{content_hash}"
    
    def _get_boundary_type(
        self,
        position: int,
        boundaries: List[Dict[str, Any]]
    ) -> Optional[str]:
        """获取边界类型"""
        for boundary in boundaries:
            if abs(boundary["position"] - position) < 10:
                return boundary["type"]
        return None


# 工厂函数
def create_s2_chunker(config: Optional[Dict[str, Any]] = None) -> S2SemanticChunker:
    """创建S2语义分块器实例"""
    return S2SemanticChunker(config)