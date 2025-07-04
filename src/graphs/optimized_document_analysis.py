"""
优化的文档分析工作流
增强了性能、错误处理和可观测性
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from functools import lru_cache, wraps
import hashlib
import json
from enum import Enum

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from tenacity import retry, stop_after_attempt, wait_exponential

from ..services.cache_service import CacheService
from ..utils.logger import get_logger
from ..config.feature_flags import FeatureFlags
from .document_analysis_workflow import (
    DocumentAnalysisWorkflow,
    AnalysisState,
    AnalysisStage
)

logger = get_logger(__name__)


class OptimizedDocumentAnalysisWorkflow(DocumentAnalysisWorkflow):
    """优化的文档分析工作流"""
    
    def __init__(self, db_session, config: Optional[Dict[str, Any]] = None):
        super().__init__(db_session)
        self.config = config or {}
        self.cache_service = CacheService()
        self.feature_flags = FeatureFlags()
        
        # 性能配置
        self.batch_size = self.config.get('batch_size', 5)
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 3)
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1小时
        
        # 错误处理配置
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
        
        # 监控
        self.metrics = {
            'stage_durations': {},
            'llm_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': []
        }
    
    def _get_cache_key(self, prefix: str, content: str) -> str:
        """生成缓存键"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"doc_analysis:{prefix}:{content_hash}"
    
    async def _cached_llm_call(self, cache_key: str, prompt: str, content: str, use_fast: bool = False):
        """带缓存的LLM调用"""
        # 检查缓存
        cached = await self.cache_service.get(cache_key)
        if cached:
            self.metrics['cache_hits'] += 1
            logger.debug(f"Cache hit for {cache_key}")
            return cached
        
        self.metrics['cache_misses'] += 1
        
        # 执行LLM调用
        llm = self.fast_llm if use_fast else self.llm
        response = await self._retry_llm_call(llm, prompt, content)
        
        # 存入缓存
        await self.cache_service.set(cache_key, response, expire=self.cache_ttl)
        
        return response
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _retry_llm_call(self, llm, prompt: str, content: str):
        """带重试的LLM调用"""
        try:
            self.metrics['llm_calls'] += 1
            response = await llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content=content)
            ])
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            self.metrics['errors'].append({
                'type': 'llm_error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            raise
    
    async def _intelligent_chunking(self, content: str) -> List[Dict[str, Any]]:
        """优化的智能分块"""
        cache_key = self._get_cache_key("chunks", content[:1000])
        
        # 如果内容很短，直接返回
        if len(content) < 1000:
            return [{"chunk_id": 1, "content": content, "topic": "全文"}]
        
        # 使用缓存的分块结果
        cached_chunks = await self.cache_service.get(cache_key)
        if cached_chunks:
            return cached_chunks
        
        # 批量处理长文档
        chunks = []
        chunk_size = 1000
        
        for i in range(0, len(content), chunk_size):
            chunk_content = content[i:i + chunk_size]
            
            # 确保在句子边界切分
            if i + chunk_size < len(content):
                last_period = chunk_content.rfind('。')
                if last_period == -1:
                    last_period = chunk_content.rfind('.')
                if last_period > 0:
                    chunk_content = chunk_content[:last_period + 1]
            
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "content": chunk_content,
                "topic": f"第{len(chunks) + 1}部分",
                "position": f"字符 {i}-{i + len(chunk_content)}",
                "key_concepts": [],
                "metadata_tags": []
            })
        
        # 批量提取每个块的元数据
        if self.feature_flags.is_enabled("batch_metadata_extraction"):
            chunks = await self._batch_extract_chunk_metadata(chunks)
        
        # 缓存结果
        await self.cache_service.set(cache_key, chunks, expire=self.cache_ttl)
        
        return chunks
    
    async def _batch_extract_chunk_metadata(self, chunks: List[Dict]) -> List[Dict]:
        """批量提取分块元数据"""
        # 将块分组进行批处理
        batches = [chunks[i:i + self.batch_size] for i in range(0, len(chunks), self.batch_size)]
        
        tasks = []
        for batch in batches:
            task = self._extract_batch_metadata(batch)
            tasks.append(task)
        
        # 并发执行批处理
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        enhanced_chunks = []
        for batch_result in results:
            if isinstance(batch_result, Exception):
                logger.error(f"Batch metadata extraction failed: {batch_result}")
                # 返回原始块
                enhanced_chunks.extend(batch)
            else:
                enhanced_chunks.extend(batch_result)
        
        return enhanced_chunks
    
    async def _extract_batch_metadata(self, batch: List[Dict]) -> List[Dict]:
        """提取一批块的元数据"""
        batch_content = "\n\n---\n\n".join([
            f"块{chunk['chunk_id']}:\n{chunk['content'][:500]}"
            for chunk in batch
        ])
        
        prompt = f"""为以下{len(batch)}个文档块提取元数据。
对每个块，识别：
1. 主要主题
2. 关键概念（最多3个）
3. 元数据标签

输出JSON格式：
[
    {{"chunk_id": 1, "topic": "主题", "key_concepts": ["概念1"], "tags": ["标签1"]}}
]"""
        
        cache_key = self._get_cache_key("batch_metadata", batch_content[:500])
        response = await self._cached_llm_call(cache_key, prompt, batch_content, use_fast=True)
        
        try:
            metadata_list = json.loads(response)
            
            # 更新原始块
            for chunk in batch:
                for metadata in metadata_list:
                    if metadata.get('chunk_id') == chunk['chunk_id']:
                        chunk['topic'] = metadata.get('topic', chunk['topic'])
                        chunk['key_concepts'] = metadata.get('key_concepts', [])
                        chunk['metadata_tags'] = metadata.get('tags', [])
                        break
            
            return batch
        except:
            logger.warning("Failed to parse batch metadata")
            return batch
    
    async def prepare_document(self, state: AnalysisState) -> AnalysisState:
        """优化的文档准备阶段"""
        start_time = datetime.now()
        state["current_stage"] = AnalysisStage.PREPARATION
        logger.info(f"Starting optimized document preparation for {state['document_id']}")
        
        try:
            # 并发执行分块和元数据提取
            tasks = [
                self._intelligent_chunking(state["document_content"]),
                self._extract_metadata(state["document_content"])
            ]
            
            chunks, metadata = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理错误
            if isinstance(chunks, Exception):
                state["errors"].append(f"Chunking error: {str(chunks)}")
                chunks = [{"content": state["document_content"], "chunk_id": 1}]
            
            if isinstance(metadata, Exception):
                state["errors"].append(f"Metadata extraction error: {str(metadata)}")
                metadata = {"document_type": "unknown"}
            
            state["stage_results"]["preparation"] = {
                "chunks": chunks,
                "metadata": metadata,
                "chunk_count": len(chunks),
                "estimated_reading_time": len(state["document_content"]) / 1000,
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
        except Exception as e:
            state["errors"].append(f"Preparation error: {str(e)}")
            logger.error(f"Document preparation failed: {e}")
        
        finally:
            self.metrics['stage_durations']['preparation'] = (datetime.now() - start_time).total_seconds()
        
        return state
    
    async def deep_exploration(self, state: AnalysisState) -> AnalysisState:
        """优化的深度探索阶段"""
        start_time = datetime.now()
        state["current_stage"] = AnalysisStage.DEEP_EXPLORATION
        
        try:
            # 并发执行多个分析任务
            tasks = []
            
            # 只有在有足够信息时才执行某些任务
            if state.get("structured_summary"):
                tasks.append(self._generate_layered_questions(
                    state["document_content"],
                    state["structured_summary"]
                ))
            
            if state.get("knowledge_graph") and state["knowledge_graph"].get("entities"):
                tasks.append(self._analyze_cross_references(
                    state["document_content"],
                    state["knowledge_graph"]
                ))
            
            if state.get("structured_summary", {}).get("main_arguments"):
                tasks.append(self._trace_evidence_chains(
                    state["document_content"],
                    state["structured_summary"]["main_arguments"]
                ))
            
            # 并发执行
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                deep_insights = {}
                if len(results) > 0 and not isinstance(results[0], Exception):
                    deep_insights["layered_qa"] = results[0]
                
                if len(results) > 1 and not isinstance(results[1], Exception):
                    deep_insights["cross_references"] = results[1]
                
                if len(results) > 2 and not isinstance(results[2], Exception):
                    deep_insights["evidence_chains"] = results[2]
                
                state["deep_insights"] = deep_insights
            else:
                state["deep_insights"] = {"note": "需要更多信息才能进行深度探索"}
            
            state["stage_results"]["deep_exploration"] = state["deep_insights"]
            
        except Exception as e:
            state["errors"].append(f"Deep exploration error: {str(e)}")
            logger.error(f"Deep exploration failed: {e}")
            state["deep_insights"] = {}
        
        finally:
            self.metrics['stage_durations']['deep_exploration'] = (datetime.now() - start_time).total_seconds()
        
        return state
    
    async def save_to_memory(self, state: AnalysisState) -> AnalysisState:
        """优化的保存到记忆系统"""
        start_time = datetime.now()
        
        try:
            # 批量保存操作
            save_tasks = []
            
            # 保存项目记忆
            if state.get("integrated_knowledge"):
                save_tasks.append(self._save_project_memory(state))
            
            # 保存分析记录
            save_tasks.append(self._save_analysis_record(state))
            
            # 并发执行保存
            await asyncio.gather(*save_tasks, return_exceptions=True)
            
            state["end_time"] = datetime.now()
            
            # 记录性能指标
            logger.info(f"Analysis completed for {state['document_id']}. Metrics: {self.metrics}")
            
        except Exception as e:
            state["errors"].append(f"Memory save error: {str(e)}")
            logger.error(f"Failed to save to memory: {e}")
        
        finally:
            self.metrics['stage_durations']['save_to_memory'] = (datetime.now() - start_time).total_seconds()
        
        return state
    
    async def _save_project_memory(self, state: AnalysisState):
        """保存项目记忆"""
        learned_facts = state["integrated_knowledge"].get("novel_insights", [])
        key_concepts = list(state["knowledge_graph"].get("entities", {}).keys())[:20]
        
        await self.project_memory.update_project_memory(
            state["project_id"],
            {
                "learned_facts": learned_facts,
                "key_concepts": key_concepts,
                "last_analysis": {
                    "document_id": state["document_id"],
                    "timestamp": datetime.now().isoformat(),
                    "summary": state.get("final_output", {}).get("executive_summary", "")
                }
            }
        )
    
    async def _save_analysis_record(self, state: AnalysisState):
        """保存分析记录"""
        from ..models.memory import MemoryCreate, MemoryType, MemoryScope
        
        await self.memory_service.create_memory(MemoryCreate(
            memory_type=MemoryType.LEARNED_KNOWLEDGE,
            scope=MemoryScope.PROJECT,
            project_id=state["project_id"],
            user_id=state["user_id"],
            key=f"analysis_{state['document_id']}_{datetime.now().isoformat()}",
            content={
                "document_id": state["document_id"],
                "analysis_goal": state["analysis_goal"],
                "summary": state.get("final_output", {}).get("executive_summary"),
                "key_findings": state.get("integrated_knowledge", {}).get("novel_insights", [])[:5],
                "metrics": self.metrics,
                "errors": state["errors"]
            },
            summary=f"Deep analysis of document {state['document_id']}",
            importance=0.8
        ))
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total_duration = sum(self.metrics['stage_durations'].values())
        
        return {
            "total_duration_seconds": total_duration,
            "stage_durations": self.metrics['stage_durations'],
            "llm_calls": self.metrics['llm_calls'],
            "cache_performance": {
                "hits": self.metrics['cache_hits'],
                "misses": self.metrics['cache_misses'],
                "hit_rate": self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])
            },
            "errors": self.metrics['errors'],
            "average_stage_duration": total_duration / max(1, len(self.metrics['stage_durations']))
        }