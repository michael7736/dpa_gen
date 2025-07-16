"""
高级重排序服务
支持多种重排序策略，提高RAG系统的准确性
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import re
from collections import Counter

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..utils.logger import get_logger
from ..config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class RerankerService:
    """重排序服务"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        # 使用更快的模型进行重排序
        import os
        if settings.ai_model.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.ai_model.openai_api_key
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    async def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        strategy: str = "hybrid",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        重排序文档块
        
        Args:
            query: 用户查询
            chunks: 检索到的文档块列表
            strategy: 重排序策略 (similarity/relevance/hybrid)
            top_k: 返回的文档块数量
            
        Returns:
            重排序后的文档块列表
        """
        if not chunks:
            return []
        
        # 根据策略选择重排序方法
        if strategy == "similarity":
            return await self._similarity_rerank(chunks, top_k)
        elif strategy == "relevance":
            return await self._relevance_rerank(query, chunks, top_k)
        elif strategy == "hybrid":
            return await self._hybrid_rerank(query, chunks, top_k)
        else:
            # 默认使用相似度排序
            return await self._similarity_rerank(chunks, top_k)
    
    async def _similarity_rerank(
        self,
        chunks: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """基于向量相似度的重排序"""
        # 直接使用检索分数排序
        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
        
        # 去重
        unique_chunks = self._deduplicate_chunks(sorted_chunks)
        
        return unique_chunks[:top_k]
    
    async def _relevance_rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """基于语义相关性的重排序（使用LLM）"""
        try:
            # 批量评分以提高效率
            batch_size = 5
            all_scores = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                scores = await self._score_relevance_batch(query, batch)
                all_scores.extend(scores)
            
            # 将分数添加到chunks
            for chunk, score in zip(chunks, all_scores):
                chunk["relevance_score"] = score
            
            # 按相关性分数排序
            sorted_chunks = sorted(
                chunks,
                key=lambda x: x.get("relevance_score", 0),
                reverse=True
            )
            
            # 去重
            unique_chunks = self._deduplicate_chunks(sorted_chunks)
            
            return unique_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"Relevance reranking error: {e}")
            # 退回到相似度排序
            return await self._similarity_rerank(chunks, top_k)
    
    async def _hybrid_rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """混合重排序策略"""
        # 1. 计算多个维度的分数
        for chunk in chunks:
            # 向量相似度分数（已有）
            similarity_score = chunk.get("score", 0)
            
            # 关键词匹配分数
            keyword_score = self._calculate_keyword_score(query, chunk["content"])
            
            # 新鲜度分数（如果有时间戳）
            freshness_score = self._calculate_freshness_score(chunk.get("metadata", {}))
            
            # 长度合理性分数
            length_score = self._calculate_length_score(chunk["content"])
            
            # 综合分数（加权平均）
            chunk["hybrid_score"] = (
                0.4 * similarity_score +
                0.3 * keyword_score +
                0.2 * freshness_score +
                0.1 * length_score
            )
        
        # 按综合分数排序
        sorted_chunks = sorted(
            chunks,
            key=lambda x: x.get("hybrid_score", 0),
            reverse=True
        )
        
        # 去重
        unique_chunks = self._deduplicate_chunks(sorted_chunks)
        
        # 如果结果太少，使用LLM进一步筛选
        if len(unique_chunks) > top_k * 2:
            unique_chunks = await self._llm_filter(query, unique_chunks[:top_k * 2])
        
        return unique_chunks[:top_k]
    
    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """计算关键词匹配分数"""
        # 分词（支持中文）
        import jieba
        query_words = set(jieba.lcut(query.lower()))
        content_words = jieba.lcut(content.lower())
        
        # 去除停用词
        stop_words = {'的', '了', '在', '是', '和', '与', '及', '等', '中', '有', '个', '为', '上'}
        query_words = {w for w in query_words if w not in stop_words and len(w) > 1}
        content_words = [w for w in content_words if w not in stop_words and len(w) > 1]
        
        if not query_words or not content_words:
            return 0.0
        
        # 计算匹配度
        content_set = set(content_words)
        matches = len(query_words.intersection(content_set))
        score = matches / len(query_words)
        
        # 考虑词频
        content_counter = Counter(content_words)
        freq_bonus = sum(
            min(content_counter.get(word, 0) / len(content_words), 0.05)
            for word in query_words
        )
        
        return min(score + freq_bonus, 1.0)
    
    def _calculate_freshness_score(self, metadata: Dict[str, Any]) -> float:
        """计算新鲜度分数"""
        # 如果没有时间信息，返回中等分数
        if "created_at" not in metadata and "updated_at" not in metadata:
            return 0.5
        
        # 获取最新时间
        time_str = metadata.get("updated_at") or metadata.get("created_at")
        try:
            # 解析时间
            if isinstance(time_str, str):
                doc_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            else:
                doc_time = time_str
            
            # 计算时间差（天）
            age_days = (datetime.now() - doc_time).days
            
            # 转换为分数（越新分数越高）
            if age_days <= 7:
                return 1.0
            elif age_days <= 30:
                return 0.8
            elif age_days <= 90:
                return 0.6
            elif age_days <= 365:
                return 0.4
            else:
                return 0.2
                
        except Exception:
            return 0.5
    
    def _calculate_length_score(self, content: str) -> float:
        """计算长度合理性分数"""
        length = len(content)
        
        # 理想长度范围：200-800字符
        if 200 <= length <= 800:
            return 1.0
        elif 100 <= length < 200:
            return 0.8
        elif 800 < length <= 1500:
            return 0.8
        elif 50 <= length < 100:
            return 0.5
        elif length > 1500:
            return 0.5
        else:
            return 0.2
    
    def _deduplicate_chunks(
        self,
        chunks: List[Dict[str, Any]],
        similarity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """去除重复的文档块"""
        if not chunks:
            return []
        
        unique_chunks = [chunks[0]]
        
        for chunk in chunks[1:]:
            is_duplicate = False
            
            for unique_chunk in unique_chunks:
                # 简单的文本相似度检查
                similarity = self._text_similarity(
                    chunk["content"],
                    unique_chunk["content"]
                )
                
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简单版）"""
        # 使用Jaccard相似度
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _score_relevance_batch(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> List[float]:
        """批量评分文档块的相关性"""
        prompt = f"""请评估以下文档片段与查询的相关性，为每个片段打分（0-10分）。
只返回分数列表，用逗号分隔。

查询：{query}

文档片段：
"""
        for i, chunk in enumerate(chunks):
            prompt += f"\n{i+1}. {chunk['content'][:200]}..."
        
        prompt += "\n\n请返回分数列表（如：8,6,9,7,5）："
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            scores_str = response.content.strip()
            scores = [float(s.strip()) / 10 for s in scores_str.split(",")]
            
            # 确保返回正确数量的分数
            while len(scores) < len(chunks):
                scores.append(0.5)
            
            return scores[:len(chunks)]
            
        except Exception as e:
            self.logger.error(f"Batch scoring error: {e}")
            # 返回默认分数
            return [0.5] * len(chunks)
    
    async def _llm_filter(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """使用LLM进一步筛选最相关的块"""
        prompt = f"""从以下文档片段中，选择最能回答查询的片段。
返回最相关的片段编号列表（如：1,3,5）。

查询：{query}

文档片段：
"""
        for i, chunk in enumerate(chunks):
            prompt += f"\n{i+1}. {chunk['content'][:150]}..."
        
        prompt += "\n\n最相关的片段编号："
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            indices_str = response.content.strip()
            indices = [int(idx.strip()) - 1 for idx in indices_str.split(",")]
            
            # 返回选中的块
            selected_chunks = [
                chunks[idx] for idx in indices 
                if 0 <= idx < len(chunks)
            ]
            
            # 如果选择太少，添加一些高分块
            if len(selected_chunks) < 3:
                for chunk in chunks:
                    if chunk not in selected_chunks:
                        selected_chunks.append(chunk)
                    if len(selected_chunks) >= 5:
                        break
            
            return selected_chunks
            
        except Exception as e:
            self.logger.error(f"LLM filter error: {e}")
            # 返回原始列表
            return chunks


class CrossEncoderReranker(RerankerService):
    """交叉编码器重排序器（未来扩展）"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        super().__init__()
        self.model_name = model_name
        # 未来可以集成sentence-transformers的CrossEncoder
        
    async def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """使用交叉编码器重排序"""
        # 暂时使用父类的混合策略
        return await super().rerank(query, chunks, strategy="hybrid", top_k=top_k)