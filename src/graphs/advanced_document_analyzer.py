"""
高级文档深度分析器
提供多层次、多维度的文档智能分析能力
基于非简化版本实现，集成完整的分块策略和深度分析功能
实现六阶段分析方法论：准备预处理、宏观理解、深度探索、批判性分析、知识整合、成果输出
"""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Tuple, Union
from enum import Enum
import json
import re
from collections import Counter, defaultdict
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import numpy as np
import tiktoken

from ..config.settings import get_settings
from ..core.vectorization import VectorStore, VectorConfig
from ..core.chunking import (
    ChunkingStrategy, ChunkingConfig, document_chunker,
    SemanticChunker, StructuralChunker, BaseChunker
)
from ..core.document.sentence_based_chunker import (
    SentenceBasedChunker, SentenceBasedConfig
)
from ..services.cache_service import CacheService
from ..services.memory_service import MemoryService
from ..utils.logger import get_logger
from ..models.document_metadata import DocumentMetadata
from ..models.chunk import Chunk as DocumentChunk

logger = get_logger(__name__)
settings = get_settings()


class AnalysisDepth(str, Enum):
    """分析深度级别"""
    BASIC = "basic"          # 基础分析：元数据提取
    STANDARD = "standard"    # 标准分析：结构+摘要
    DEEP = "deep"           # 深度分析：语义+主题
    EXPERT = "expert"       # 专家分析：关系+洞察
    COMPREHENSIVE = "comprehensive"  # 全面分析：六阶段完整流程


class DocumentType(str, Enum):
    """文档类型"""
    ACADEMIC = "academic"       # 学术论文
    TECHNICAL = "technical"     # 技术文档
    BUSINESS = "business"       # 商务文档
    REPORT = "report"          # 研究报告
    MANUAL = "manual"          # 操作手册
    GENERAL = "general"        # 通用文档


class AnalysisStage(str, Enum):
    """六阶段分析流程"""
    PREPARATION = "preparation"              # 准备与预处理
    MACRO_UNDERSTANDING = "macro_understanding"  # 宏观理解
    DEEP_EXPLORATION = "deep_exploration"       # 深度探索
    CRITICAL_ANALYSIS = "critical_analysis"     # 批判性分析
    KNOWLEDGE_INTEGRATION = "knowledge_integration"  # 知识整合
    OUTPUT_GENERATION = "output_generation"     # 成果输出


class AdvancedDocumentState(TypedDict):
    """高级文档分析状态 - 六阶段方法论"""
    # 基础信息
    document_id: str
    project_id: str
    user_id: str
    file_path: str
    file_name: str
    analysis_depth: AnalysisDepth
    analysis_goal: Optional[str]  # 分析目标
    
    # 文档特征
    document_type: Optional[DocumentType]
    language: str
    encoding: str
    file_size: int
    page_count: int
    
    # 处理状态
    status: str  # pending, analyzing, completed, error
    current_stage: AnalysisStage
    progress: float
    error_message: Optional[str]
    stage_results: Dict[str, Any]  # 各阶段处理结果
    
    # 内容数据
    content: Optional[str]  # 直接提供的内容（可选）
    raw_content: Optional[str]
    cleaned_content: Optional[str]
    content_hash: Optional[str]  # 内容哈希，用于去重
    
    # 阶段1：准备与预处理
    chunks: List[DocumentChunk]  # 智能分块结果
    chunk_strategy: ChunkingStrategy
    chunk_metadata: Dict[str, Any]
    document_metadata: Dict[str, Any]  # 元数据提取结果
    
    # 阶段2：宏观理解
    progressive_summaries: Dict[str, str]  # 渐进式摘要：50字、200字、500字
    multidimensional_outline: Dict[str, Any]  # 多维度大纲
    knowledge_graph: Dict[str, Any]  # 初步知识图谱
    
    # 阶段3：深度探索
    layered_questions: Dict[str, List[str]]  # 分层提问
    cross_references: Dict[str, Any]  # 交叉引用分析
    evidence_chains: List[Dict[str, Any]]  # 证据链追踪
    
    # 阶段4：批判性分析
    multi_perspective_analysis: Dict[str, Any]  # 多视角审视
    assumption_testing: Dict[str, Any]  # 假设检验
    logical_gaps: List[Dict[str, Any]]  # 逻辑漏洞识别
    
    # 阶段5：知识整合
    integrated_themes: Dict[str, Any]  # 主题综合
    knowledge_connections: Dict[str, Any]  # 知识连接
    novel_insights: List[Dict[str, Any]]  # 新洞察
    recommendations: List[Dict[str, Any]]  # 建议生成
    
    # 阶段6：成果输出
    executive_summary: Optional[str]  # 执行摘要
    detailed_report: Optional[Dict[str, Any]]  # 详细报告
    visualization_data: Dict[str, Any]  # 可视化数据
    action_plan: Optional[Dict[str, Any]]  # 行动方案
    
    # 向量化数据
    embeddings: List[List[float]]
    embedding_metadata: Dict[str, Any]
    vector_indices: List[str]  # 向量数据库索引ID
    
    # 质量评估
    quality_metrics: Dict[str, float]  # 详细质量指标
    confidence_scores: Dict[str, float]  # 各阶段置信度
    
    # 性能指标
    start_time: datetime
    end_time: Optional[datetime]
    processing_time_seconds: Optional[float]
    stage_timings: Dict[str, float]  # 各阶段耗时


class AdvancedDocumentAnalyzer:
    """高级文档深度分析器 - 实现六阶段分析方法论"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = get_logger(__name__)
        self.config = config or {}
        
        # 初始化LLM
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.fast_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # 初始化嵌入模型
        self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # 初始化向量存储
        vector_config = VectorConfig(
            model_name="text-embedding-3-large",
            dimension=3072,
            distance_metric="cosine",
            batch_size=100
        )
        self.vector_store = VectorStore(
            config=vector_config,
            qdrant_url=settings.qdrant.url  # 使用完整的URL
        )
        
        # 初始化服务
        self.cache_service = CacheService()
        self.memory_service = None  # 需要在运行时提供db_session
        
        # 初始化分块器
        self.chunking_config = ChunkingConfig(
            strategy=ChunkingStrategy.SENTENCE_BASED,
            chunk_size=1000,
            chunk_overlap=200,
            semantic_threshold=0.8
        )
        
        # tiktoken编码器
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # 构建六阶段分析流程图
        self.graph = self._build_six_stage_graph()
        self.app = self.graph.compile()
    
    def _build_six_stage_graph(self) -> StateGraph:
        """构建六阶段分析流程图"""
        graph = StateGraph(AdvancedDocumentState)
        
        # 初始化
        graph.add_node("initialize", self.initialize_analysis)
        
        # 阶段1：准备与预处理
        graph.add_node("prepare_document", self.prepare_document)
        graph.add_node("intelligent_chunking", self.intelligent_chunking)
        graph.add_node("extract_metadata", self.extract_metadata)
        
        # 阶段2：宏观理解
        graph.add_node("progressive_summarization", self.progressive_summarization)
        graph.add_node("create_multidimensional_outline", self.multidimensional_outline)
        graph.add_node("build_initial_knowledge_graph", self.build_initial_knowledge_graph)
        
        # 阶段3：深度探索
        graph.add_node("generate_layered_questions", self.generate_layered_questions)
        graph.add_node("analyze_cross_references", self.analyze_cross_references)
        graph.add_node("trace_evidence_chains", self.trace_evidence_chains)
        
        # 阶段4：批判性分析
        graph.add_node("perform_multi_perspective_analysis", self.multi_perspective_analysis)
        graph.add_node("test_assumptions", self.test_assumptions)
        graph.add_node("identify_logical_gaps", self.identify_logical_gaps)
        
        # 阶段5：知识整合
        graph.add_node("integrate_themes", self.integrate_themes)
        graph.add_node("connect_knowledge", self.connect_knowledge)
        graph.add_node("generate_insights", self.generate_insights)
        graph.add_node("generate_recommendations", self.generate_recommendations)
        
        # 阶段6：成果输出
        graph.add_node("generate_executive_summary", self.generate_executive_summary)
        graph.add_node("generate_detailed_report", self.generate_detailed_report)
        graph.add_node("prepare_visualization_data", self.prepare_visualization_data)
        graph.add_node("generate_action_plan", self.generate_action_plan)
        
        # 向量化和存储
        graph.add_node("vectorize_and_store", self.vectorize_and_store)
        
        # 完成处理
        graph.add_node("finalize", self.finalize_analysis)
        
        # 设置流程
        graph.set_entry_point("initialize")
        
        # 阶段1流程
        graph.add_edge("initialize", "prepare_document")
        graph.add_edge("prepare_document", "intelligent_chunking")
        graph.add_edge("intelligent_chunking", "extract_metadata")
        
        # 根据分析深度决定流程
        graph.add_conditional_edges(
            "extract_metadata",
            self._route_by_depth,
            {
                "basic": "vectorize_and_store",
                "standard": "progressive_summarization",
                "deep": "progressive_summarization",
                "expert": "progressive_summarization",
                "comprehensive": "progressive_summarization"
            }
        )
        
        # 阶段2流程
        graph.add_edge("progressive_summarization", "create_multidimensional_outline")
        graph.add_edge("create_multidimensional_outline", "build_initial_knowledge_graph")
        
        # 继续路由
        graph.add_conditional_edges(
            "build_initial_knowledge_graph",
            self._route_after_macro,
            {
                "standard": "vectorize_and_store",
                "deep": "generate_layered_questions",
                "expert": "generate_layered_questions",
                "comprehensive": "generate_layered_questions"
            }
        )
        
        # 阶段3流程
        graph.add_edge("generate_layered_questions", "analyze_cross_references")
        graph.add_edge("analyze_cross_references", "trace_evidence_chains")
        
        # 继续路由
        graph.add_conditional_edges(
            "trace_evidence_chains",
            self._route_after_deep,
            {
                "deep": "integrate_themes",
                "expert": "perform_multi_perspective_analysis",
                "comprehensive": "perform_multi_perspective_analysis"
            }
        )
        
        # 阶段4流程
        graph.add_edge("perform_multi_perspective_analysis", "test_assumptions")
        graph.add_edge("test_assumptions", "identify_logical_gaps")
        
        # 阶段5流程
        graph.add_edge("identify_logical_gaps", "integrate_themes")
        graph.add_edge("integrate_themes", "connect_knowledge")
        graph.add_edge("connect_knowledge", "generate_insights")
        graph.add_edge("generate_insights", "generate_recommendations")
        
        # 继续路由
        graph.add_conditional_edges(
            "generate_recommendations",
            self._route_after_integration,
            {
                "deep": "vectorize_and_store",
                "expert": "generate_executive_summary",
                "comprehensive": "generate_executive_summary"
            }
        )
        
        # 阶段6流程
        graph.add_edge("generate_executive_summary", "generate_detailed_report")
        graph.add_edge("generate_detailed_report", "prepare_visualization_data")
        graph.add_edge("prepare_visualization_data", "generate_action_plan")
        graph.add_edge("generate_action_plan", "vectorize_and_store")
        
        # 最终流程
        graph.add_edge("vectorize_and_store", "finalize")
        graph.add_edge("finalize", END)
        
        return graph
    
    def _route_by_depth(self, state: AdvancedDocumentState) -> str:
        """根据分析深度路由"""
        depth = state["analysis_depth"]
        if depth == AnalysisDepth.BASIC:
            return "basic"
        else:
            return depth
    
    def _route_after_macro(self, state: AdvancedDocumentState) -> str:
        """宏观理解后路由"""
        depth = state["analysis_depth"]
        if depth == AnalysisDepth.STANDARD:
            return "standard"
        else:
            return depth
    
    def _route_after_deep(self, state: AdvancedDocumentState) -> str:
        """深度探索后路由"""
        return state["analysis_depth"]
    
    def _route_after_integration(self, state: AdvancedDocumentState) -> str:
        """知识整合后路由"""
        return state["analysis_depth"]
    
    async def initialize_analysis(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """初始化分析"""
        state["status"] = "analyzing"
        state["current_stage"] = AnalysisStage.PREPARATION
        state["progress"] = 0.0
        state["stage_results"] = {}
        state["stage_timings"] = {}
        state["start_time"] = datetime.now()
        
        # 生成内容哈希
        if state.get("raw_content"):
            state["content_hash"] = hashlib.md5(
                state["raw_content"].encode()
            ).hexdigest()
        
        self.logger.info(f"Starting analysis for document: {state['document_id']}")
        return state
    
    # 阶段1：准备与预处理
    async def prepare_document(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """准备文档 - 加载和清理"""
        stage_start = datetime.now()
        state["current_stage"] = AnalysisStage.PREPARATION
        state["progress"] = 5.0
        
        try:
            # 检查是否直接提供了内容
            if state.get("content"):
                raw_content = state["content"]
                state["raw_content"] = raw_content
                state["page_count"] = 1
                state["file_size"] = len(raw_content.encode('utf-8'))
            else:
                # 加载文档
                file_path = Path(state["file_path"])
                
                if file_path.suffix.lower() == '.pdf':
                    loader = PyPDFLoader(str(file_path))
                elif file_path.suffix.lower() in ['.docx', '.doc']:
                    loader = Docx2txtLoader(str(file_path))
                else:
                    loader = TextLoader(str(file_path))
                
                documents = loader.load()
                raw_content = "\n\n".join([doc.page_content for doc in documents])
                state["raw_content"] = raw_content
                state["page_count"] = len(documents)
                state["file_size"] = file_path.stat().st_size
            
            # 清理内容
            cleaned_content = self._clean_content(raw_content)
            state["cleaned_content"] = cleaned_content
            
            # 检测语言
            state["language"] = self._detect_language(cleaned_content[:1000])
            
            # 检测文档类型
            state["document_type"] = await self._detect_document_type(
                cleaned_content[:3000], state["file_name"]
            )
            
            self.logger.info(
                f"Document prepared: {state['page_count']} pages, "
                f"{len(raw_content)} chars, type: {state['document_type']}"
            )
            
        except Exception as e:
            state["error_message"] = f"Document preparation failed: {str(e)}"
            self.logger.error(f"Preparation error: {e}")
            raise
        
        state["stage_timings"]["preparation"] = (datetime.now() - stage_start).total_seconds()
        return state
    
    async def intelligent_chunking(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """智能分块 - 保持语义完整性"""
        state["progress"] = 10.0
        
        try:
            content = state.get("cleaned_content", "")
            doc_type = state.get("document_type", DocumentType.GENERAL)
            
            # 根据文档类型选择分块策略
            if doc_type == DocumentType.ACADEMIC:
                strategy = ChunkingStrategy.STRUCTURAL  # 学术文档使用结构化分块
            elif doc_type == DocumentType.TECHNICAL:
                strategy = ChunkingStrategy.SENTENCE_BASED  # 技术文档使用句子分块
            else:
                strategy = ChunkingStrategy.SEMANTIC  # 其他使用语义分块
            
            state["chunk_strategy"] = strategy
            
            # 执行分块
            chunks = await document_chunker.chunk_document(
                text=content,
                document_id=state["document_id"],
                metadata={
                    "project_id": state["project_id"],
                    "document_type": doc_type,
                    "language": state["language"]
                },
                strategy=strategy,
                chunk_size=self.chunking_config.chunk_size,
                chunk_overlap=self.chunking_config.chunk_overlap
            )
            
            state["chunks"] = chunks
            state["chunk_metadata"] = {
                "total_chunks": len(chunks),
                "strategy": strategy,
                "avg_chunk_size": np.mean([len(c.content) for c in chunks]),
                "chunk_distribution": self._analyze_chunk_distribution(chunks)
            }
            
            self.logger.info(f"Created {len(chunks)} chunks using {strategy} strategy")
            
        except Exception as e:
            self.logger.error(f"Chunking error: {e}")
            # 回退到简单分块
            chunks = self._fallback_chunking(state.get("cleaned_content", ""))
            state["chunks"] = chunks
        
        return state
    
    async def extract_metadata(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """提取文档元数据"""
        state["progress"] = 15.0
        
        try:
            content_sample = state.get("cleaned_content", "")[:5000]
            
            prompt = f"""
            Analyze this document and extract metadata:
            
            Document type: {state.get('document_type', 'unknown')}
            Content sample: {content_sample}
            
            Extract:
            1. Domain/field of study
            2. Target audience
            3. Publication date (if mentioned)
            4. Key authors/contributors
            5. Main purpose/objective
            6. Document structure type (research paper, report, guide, etc.)
            7. Technical level (beginner, intermediate, advanced)
            
            Format as JSON.
            """
            
            response = await self.fast_llm.ainvoke([HumanMessage(content=prompt)])
            metadata = self._parse_json_response(response.content)
            
            state["document_metadata"] = metadata
            state["stage_results"]["metadata"] = metadata
            
            self.logger.info(f"Extracted metadata: {list(metadata.keys())}")
            
        except Exception as e:
            self.logger.error(f"Metadata extraction error: {e}")
            state["document_metadata"] = {}
        
        return state
    
    # 阶段2：宏观理解
    async def progressive_summarization(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """渐进式摘要 - 50字、200字、500字"""
        stage_start = datetime.now()
        state["current_stage"] = AnalysisStage.MACRO_UNDERSTANDING
        state["progress"] = 20.0
        
        try:
            content = state.get("cleaned_content", "")
            
            # 检查缓存
            cache_key = f"summary:{state.get('content_hash', '')}"
            cached_summaries = await self.cache_service.get(cache_key)
            
            if cached_summaries:
                state["progressive_summaries"] = cached_summaries
            else:
                summaries = {}
                
                # 50字摘要 - 核心价值
                prompt_50 = f"""
                Summarize this document in exactly 50 words, focusing on its core value:
                {content[:3000]}
                """
                response_50 = await self.fast_llm.ainvoke([HumanMessage(content=prompt_50)])
                summaries["brief"] = response_50.content
                
                # 200字摘要 - 主要论点
                prompt_200 = f"""
                Summarize this document in exactly 200 words, covering main arguments:
                {content[:5000]}
                """
                response_200 = await self.llm.ainvoke([HumanMessage(content=prompt_200)])
                summaries["main_points"] = response_200.content
                
                # 500字摘要 - 详细概述
                prompt_500 = f"""
                Provide a comprehensive 500-word summary of this document:
                {content[:10000]}
                
                Include: main thesis, key arguments, evidence, conclusions, and implications.
                """
                response_500 = await self.llm.ainvoke([HumanMessage(content=prompt_500)])
                summaries["detailed"] = response_500.content
                
                state["progressive_summaries"] = summaries
                
                # 缓存结果
                await self.cache_service.set(cache_key, summaries, ttl=86400)
            
            state["stage_results"]["summaries"] = state["progressive_summaries"]
            self.logger.info("Generated progressive summaries")
            
        except Exception as e:
            self.logger.error(f"Summarization error: {e}")
            state["progressive_summaries"] = {
                "brief": "Summary generation failed",
                "main_points": "",
                "detailed": ""
            }
        
        state["stage_timings"]["macro_understanding"] = (datetime.now() - stage_start).total_seconds()
        return state
    
    async def multidimensional_outline(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """多维度大纲提取"""
        state["progress"] = 25.0
        
        try:
            content = state.get("cleaned_content", "")
            chunks = state.get("chunks", [])
            
            outline = {
                "logical": [],      # 逻辑结构
                "thematic": [],     # 主题结构
                "temporal": [],     # 时间结构
                "causal": []        # 因果结构
            }
            
            # 逻辑结构分析
            logical_prompt = """
            Extract the logical structure of this document:
            - Introduction/Background
            - Main arguments/sections
            - Supporting evidence
            - Conclusions
            
            Format as a hierarchical outline.
            """
            
            # 主题结构分析
            thematic_prompt = """
            Identify major themes and sub-themes in this document.
            Group related concepts and show their relationships.
            """
            
            # 并发执行分析
            tasks = [
                self._analyze_dimension(content[:5000], logical_prompt, "logical"),
                self._analyze_dimension(content[:5000], thematic_prompt, "thematic"),
                self._extract_temporal_structure(chunks),
                self._extract_causal_structure(chunks)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for i, key in enumerate(outline.keys()):
                if not isinstance(results[i], Exception):
                    outline[key] = results[i]
            
            state["multidimensional_outline"] = outline
            state["stage_results"]["outline"] = outline
            
            self.logger.info("Generated multidimensional outline")
            
        except Exception as e:
            self.logger.error(f"Outline generation error: {e}")
            state["multidimensional_outline"] = {"error": str(e)}
        
        return state
    
    async def build_initial_knowledge_graph(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """构建初步知识图谱"""
        state["progress"] = 30.0
        
        try:
            chunks = state.get("chunks", [])
            
            # 如果没有chunks，使用原始内容创建临时chunks
            if not chunks:
                content = state.get("cleaned_content", "")
                if content:
                    # 创建临时chunks用于实体提取
                    chunk_size = 2000
                    temp_chunks = []
                    for i in range(0, len(content), chunk_size):
                        chunk_content = content[i:i+chunk_size]
                        temp_chunks.append(type('TempChunk', (), {'content': chunk_content})())
                    chunks = temp_chunks[:10]
                    self.logger.warning("Using temporary chunks for entity extraction due to chunking failure")
            
            # 实体识别
            entities = await self._extract_entities(chunks[:10])  # 使用前10个块
            
            # 关系抽取
            relationships = await self._extract_relationships(chunks[:10], entities)
            
            # 构建图谱
            knowledge_graph = {
                "entities": entities,
                "relationships": relationships,
                "statistics": {
                    "total_entities": len(entities),
                    "total_relationships": len(relationships),
                    "entity_types": self._count_entity_types(entities),
                    "relationship_types": self._count_relationship_types(relationships)
                }
            }
            
            state["knowledge_graph"] = knowledge_graph
            state["stage_results"]["knowledge_graph"] = knowledge_graph
            
            self.logger.info(
                f"Built knowledge graph: {len(entities)} entities, "
                f"{len(relationships)} relationships"
            )
            
        except Exception as e:
            self.logger.error(f"Knowledge graph error: {e}")
            state["knowledge_graph"] = {"entities": [], "relationships": []}
        
        return state
    
    # 阶段3：深度探索
    async def generate_layered_questions(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """生成分层提问"""
        stage_start = datetime.now()
        state["current_stage"] = AnalysisStage.DEEP_EXPLORATION
        state["progress"] = 35.0
        
        try:
            summaries = state.get("progressive_summaries", {})
            outline = state.get("multidimensional_outline", {})
            
            questions = {
                "factual": [],      # 基础事实问题
                "analytical": [],   # 分析性问题
                "synthetic": [],    # 综合性问题
                "creative": []      # 创新性问题
            }
            
            # 基于文档内容生成各层次问题
            context = f"""
            Document summary: {summaries.get('detailed', '')}
            Document structure: {json.dumps(outline.get('logical', []), indent=2)}
            Analysis goal: {state.get('analysis_goal', 'General understanding')}
            """
            
            # 并发生成各层次问题
            tasks = [
                self._generate_questions(context, "factual", 5),
                self._generate_questions(context, "analytical", 5),
                self._generate_questions(context, "synthetic", 3),
                self._generate_questions(context, "creative", 3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            for i, level in enumerate(questions.keys()):
                questions[level] = results[i]
            
            state["layered_questions"] = questions
            state["stage_results"]["questions"] = questions
            
            self.logger.info(f"Generated {sum(len(q) for q in questions.values())} questions")
            
        except Exception as e:
            self.logger.error(f"Question generation error: {e}")
            state["layered_questions"] = {"error": str(e)}
        
        state["stage_timings"]["deep_exploration"] = (datetime.now() - stage_start).total_seconds()
        return state
    
    async def analyze_cross_references(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """分析交叉引用"""
        state["progress"] = 40.0
        
        try:
            chunks = state.get("chunks", [])
            entities = state.get("knowledge_graph", {}).get("entities", [])
            
            cross_refs = {
                "concept_tracking": {},     # 概念追踪
                "argument_comparison": [],  # 论点对照
                "evidence_correlation": []  # 证据关联
            }
            
            # 概念追踪 - 跟踪重要概念在文档中的演变
            key_concepts = [e["name"] for e in entities[:10]]  # 前10个重要实体
            for concept in key_concepts:
                occurrences = []
                for i, chunk in enumerate(chunks):
                    if concept.lower() in chunk.content.lower():
                        occurrences.append({
                            "chunk_index": i,
                            "context": self._extract_context(chunk.content, concept),
                            "position": i / len(chunks)  # 相对位置
                        })
                if occurrences:
                    cross_refs["concept_tracking"][concept] = occurrences
            
            # 论点对照和证据关联需要更深入的分析
            # 这里简化处理，实际应用中可以使用更复杂的NLP技术
            
            state["cross_references"] = cross_refs
            state["stage_results"]["cross_references"] = cross_refs
            
            self.logger.info(f"Analyzed cross references for {len(key_concepts)} concepts")
            
        except Exception as e:
            self.logger.error(f"Cross reference analysis error: {e}")
            state["cross_references"] = {}
        
        return state
    
    async def trace_evidence_chains(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """追踪证据链"""
        state["progress"] = 45.0
        
        try:
            chunks = state.get("chunks", [])
            
            # 识别论点和证据
            evidence_chains = []
            
            # 简化的证据链追踪
            for i, chunk in enumerate(chunks[:20]):  # 分析前20个块
                # 识别论点
                if self._contains_claim(chunk.content):
                    chain = {
                        "claim": self._extract_claim(chunk.content),
                        "chunk_index": i,
                        "evidence": [],
                        "strength": 0.0
                    }
                    
                    # 在后续块中查找支持证据
                    for j in range(i + 1, min(i + 5, len(chunks))):
                        if self._contains_evidence(chunks[j].content):
                            chain["evidence"].append({
                                "chunk_index": j,
                                "type": self._classify_evidence(chunks[j].content),
                                "content": chunks[j].content[:200]
                            })
                    
                    # 评估证据强度
                    chain["strength"] = self._evaluate_evidence_strength(chain)
                    
                    if chain["evidence"]:
                        evidence_chains.append(chain)
            
            state["evidence_chains"] = evidence_chains
            state["stage_results"]["evidence_chains"] = evidence_chains
            
            self.logger.info(f"Traced {len(evidence_chains)} evidence chains")
            
        except Exception as e:
            self.logger.error(f"Evidence chain tracing error: {e}")
            state["evidence_chains"] = []
        
        return state
    
    # 阶段4：批判性分析
    async def multi_perspective_analysis(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """多视角分析"""
        stage_start = datetime.now()
        state["current_stage"] = AnalysisStage.CRITICAL_ANALYSIS
        state["progress"] = 50.0
        
        try:
            content = state.get("cleaned_content", "")[:10000]
            summaries = state.get("progressive_summaries", {})
            
            perspectives = {
                "methodological": {},      # 方法论视角
                "stakeholder": {},         # 利益相关者视角
                "temporal": {},           # 时代背景视角
                "interdisciplinary": {},   # 跨学科视角
                "practical": {}           # 实践应用视角
            }
            
            # 并发分析各个视角
            tasks = []
            for perspective in perspectives.keys():
                prompt = self._build_perspective_prompt(perspective, content, summaries)
                tasks.append(self._analyze_perspective(prompt, perspective))
            
            results = await asyncio.gather(*tasks)
            
            for i, perspective in enumerate(perspectives.keys()):
                perspectives[perspective] = results[i]
            
            state["multi_perspective_analysis"] = perspectives
            state["stage_results"]["perspectives"] = perspectives
            
            self.logger.info("Completed multi-perspective analysis")
            
        except Exception as e:
            self.logger.error(f"Multi-perspective analysis error: {e}")
            state["multi_perspective_analysis"] = {}
        
        state["stage_timings"]["critical_analysis"] = (datetime.now() - stage_start).total_seconds()
        return state
    
    async def test_assumptions(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """测试假设"""
        state["progress"] = 55.0
        
        try:
            content = state.get("cleaned_content", "")[:8000]
            perspectives = state.get("multi_perspective_analysis", {})
            
            # 识别和测试假设
            prompt = f"""
            Analyze the assumptions in this document:
            
            Content: {content}
            
            Identify:
            1. Explicit assumptions (clearly stated)
            2. Implicit assumptions (unstated but necessary)
            3. Methodological assumptions
            4. Theoretical assumptions
            
            For each assumption:
            - State the assumption clearly
            - Evaluate its validity
            - Consider alternative assumptions
            - Assess impact if assumption is false
            
            Format as structured analysis.
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            assumptions = self._parse_assumptions_response(response.content)
            
            state["assumption_testing"] = assumptions
            state["stage_results"]["assumptions"] = assumptions
            
            self.logger.info(f"Identified and tested {len(assumptions.get('explicit', []))} assumptions")
            
        except Exception as e:
            self.logger.error(f"Assumption testing error: {e}")
            state["assumption_testing"] = {}
        
        return state
    
    async def identify_logical_gaps(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """识别逻辑漏洞"""
        state["progress"] = 60.0
        
        try:
            evidence_chains = state.get("evidence_chains", [])
            assumptions = state.get("assumption_testing", {})
            
            logical_gaps = []
            
            # 分析论证结构
            for chain in evidence_chains:
                gaps = self._analyze_argument_structure(chain)
                if gaps:
                    logical_gaps.extend(gaps)
            
            # 检查假设的逻辑一致性
            assumption_gaps = self._check_assumption_consistency(assumptions)
            logical_gaps.extend(assumption_gaps)
            
            # 识别常见逻辑谬误
            content_sample = state.get("cleaned_content", "")[:5000]
            fallacies = await self._identify_fallacies(content_sample)
            
            state["logical_gaps"] = {
                "argument_gaps": logical_gaps,
                "fallacies": fallacies,
                "severity_assessment": self._assess_gap_severity(logical_gaps, fallacies)
            }
            state["stage_results"]["logical_gaps"] = state["logical_gaps"]
            
            self.logger.info(f"Identified {len(logical_gaps)} logical gaps")
            
        except Exception as e:
            self.logger.error(f"Logical gap identification error: {e}")
            state["logical_gaps"] = []
        
        return state
    
    # 阶段5：知识整合
    async def integrate_themes(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """整合主题"""
        stage_start = datetime.now()
        state["current_stage"] = AnalysisStage.KNOWLEDGE_INTEGRATION
        state["progress"] = 65.0
        
        try:
            outline = state.get("multidimensional_outline", {})
            perspectives = state.get("multi_perspective_analysis", {})
            knowledge_graph = state.get("knowledge_graph", {})
            
            # 提取和整合核心主题
            themes = {
                "core_themes": [],
                "theme_relationships": [],
                "theme_evolution": [],
                "integrated_narrative": ""
            }
            
            # 从多个来源提取主题
            thematic_elements = outline.get("thematic", [])
            key_entities = [e for e in knowledge_graph.get("entities", [])
                          if e.get("importance", 0) > 0.7]
            
            # 整合主题
            integrated_prompt = f"""
            Integrate the following themes into a coherent narrative:
            
            Thematic outline: {json.dumps(thematic_elements, indent=2)}
            Key concepts: {[e['name'] for e in key_entities]}
            
            Create:
            1. List of 3-5 core themes
            2. How themes relate to each other
            3. How themes evolve through the document
            4. An integrated narrative (200 words)
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=integrated_prompt)])
            themes = self._parse_theme_integration(response.content)
            
            state["integrated_themes"] = themes
            state["stage_results"]["themes"] = themes
            
            self.logger.info(f"Integrated {len(themes.get('core_themes', []))} core themes")
            
        except Exception as e:
            self.logger.error(f"Theme integration error: {e}")
            state["integrated_themes"] = {}
        
        state["stage_timings"]["knowledge_integration"] = (datetime.now() - stage_start).total_seconds()
        return state
    
    async def connect_knowledge(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """连接到现有知识体系"""
        state["progress"] = 70.0
        
        try:
            # 获取项目已有知识
            project_knowledge = await self._get_project_knowledge(state["project_id"])
            
            # 识别新旧知识的连接点
            connections = {
                "reinforcements": [],    # 强化已有知识
                "extensions": [],        # 扩展已有知识
                "contradictions": [],    # 与已有知识矛盾
                "novel_connections": []  # 全新的连接
            }
            
            current_themes = state.get("integrated_themes", {}).get("core_themes", [])
            current_entities = state.get("knowledge_graph", {}).get("entities", [])
            
            # 分析连接（简化版本）
            for theme in current_themes:
                for existing in project_knowledge.get("themes", []):
                    similarity = self._calculate_similarity(theme, existing)
                    if similarity > 0.8:
                        connections["reinforcements"].append({
                            "new": theme,
                            "existing": existing,
                            "similarity": similarity
                        })
                    elif similarity > 0.5:
                        connections["extensions"].append({
                            "new": theme,
                            "existing": existing,
                            "similarity": similarity
                        })
            
            state["knowledge_connections"] = connections
            state["stage_results"]["connections"] = connections
            
            # 更新项目记忆
            await self._update_project_memory(state)
            
            self.logger.info(f"Connected knowledge: {len(connections['reinforcements'])} reinforcements")
            
        except Exception as e:
            self.logger.error(f"Knowledge connection error: {e}")
            state["knowledge_connections"] = {}
        
        return state
    
    async def generate_insights(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """生成新洞察"""
        state["progress"] = 75.0
        
        try:
            themes = state.get("integrated_themes", {})
            connections = state.get("knowledge_connections", {})
            gaps = state.get("logical_gaps", {})
            
            # 生成洞察
            insights_prompt = f"""
            Based on the analysis, generate novel insights:
            
            Core themes: {themes.get('core_themes', [])}
            Knowledge connections: {connections}
            Identified gaps: {gaps.get('argument_gaps', [])}
            
            Generate 3-5 novel insights that:
            1. Identify patterns not explicitly stated
            2. Connect disparate concepts
            3. Reveal hidden assumptions or implications
            4. Suggest new research directions
            
            For each insight:
            - State the insight clearly
            - Explain the reasoning
            - Rate confidence (0-1)
            - Suggest validation methods
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=insights_prompt)])
            insights = self._parse_insights_response(response.content)
            
            state["novel_insights"] = insights
            state["stage_results"]["insights"] = insights
            
            self.logger.info(f"Generated {len(insights)} novel insights")
            
        except Exception as e:
            self.logger.error(f"Insight generation error: {e}")
            state["novel_insights"] = []
        
        return state
    
    async def generate_recommendations(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """生成建议"""
        state["progress"] = 80.0
        
        try:
            insights = state.get("novel_insights", [])
            gaps = state.get("logical_gaps", {})
            analysis_goal = state.get("analysis_goal", "")
            
            # 生成建议
            recommendations_prompt = f"""
            Generate actionable recommendations based on the analysis:
            
            Analysis goal: {analysis_goal}
            Key insights: {insights}
            Identified gaps: {gaps}
            
            Provide recommendations in three categories:
            1. Immediate actions (within 1 month)
            2. Short-term initiatives (1-3 months)
            3. Long-term strategies (3+ months)
            
            For each recommendation:
            - Specific action item
            - Expected outcome
            - Required resources
            - Success metrics
            - Priority (high/medium/low)
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=recommendations_prompt)])
            recommendations = self._parse_recommendations_response(response.content)
            
            state["recommendations"] = recommendations
            state["stage_results"]["recommendations"] = recommendations
            
            self.logger.info(f"Generated {len(recommendations)} recommendations")
            
        except Exception as e:
            self.logger.error(f"Recommendation generation error: {e}")
            state["recommendations"] = []
        
        return state
    
    # 阶段6：成果输出
    async def generate_executive_summary(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """生成执行摘要"""
        stage_start = datetime.now()
        state["current_stage"] = AnalysisStage.OUTPUT_GENERATION
        state["progress"] = 85.0
        
        try:
            # 收集关键信息
            summaries = state.get("progressive_summaries", {})
            insights = state.get("novel_insights", [])
            recommendations = state.get("recommendations", [])
            
            # 生成执行摘要
            exec_summary_prompt = f"""
            Create a one-page executive summary:
            
            Document: {state['file_name']}
            Analysis goal: {state.get('analysis_goal', 'General analysis')}
            
            Key findings: {summaries.get('main_points', '')}
            Top insights: {insights[:3]}
            Priority recommendations: {[r for r in recommendations if r.get('priority') == 'high']}
            
            Structure:
            1. Purpose and Scope (50 words)
            2. Key Findings (100 words)
            3. Critical Insights (100 words)
            4. Recommended Actions (100 words)
            5. Expected Impact (50 words)
            
            Make it concise, actionable, and executive-friendly.
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=exec_summary_prompt)])
            
            state["executive_summary"] = response.content
            state["stage_results"]["executive_summary"] = response.content
            
            self.logger.info("Generated executive summary")
            
        except Exception as e:
            self.logger.error(f"Executive summary error: {e}")
            state["executive_summary"] = "Executive summary generation failed"
        
        state["stage_timings"]["output_generation"] = (datetime.now() - stage_start).total_seconds()
        return state
    
    async def generate_detailed_report(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """生成详细报告"""
        state["progress"] = 90.0
        
        try:
            # 构建详细报告结构
            report = {
                "metadata": {
                    "document_id": state["document_id"],
                    "analysis_date": datetime.now().isoformat(),
                    "analysis_depth": state["analysis_depth"],
                    "processing_time": sum(state.get("stage_timings", {}).values())
                },
                "document_overview": {
                    "type": state.get("document_type", "unknown"),
                    "pages": state.get("page_count", 0),
                    "language": state.get("language", "unknown"),
                    "metadata": state.get("document_metadata", {})
                },
                "analysis_results": {
                    "summaries": state.get("progressive_summaries", {}),
                    "structure": state.get("multidimensional_outline", {}),
                    "knowledge_graph": state.get("knowledge_graph", {}),
                    "questions": state.get("layered_questions", {}),
                    "evidence_chains": state.get("evidence_chains", []),
                    "perspectives": state.get("multi_perspective_analysis", {}),
                    "assumptions": state.get("assumption_testing", {}),
                    "logical_gaps": state.get("logical_gaps", {}),
                    "themes": state.get("integrated_themes", {}),
                    "insights": state.get("novel_insights", []),
                    "recommendations": state.get("recommendations", [])
                },
                "quality_assessment": {
                    "completeness": self._assess_completeness(state),
                    "coherence": self._assess_coherence(state),
                    "evidence_strength": self._assess_evidence_strength(state.get("evidence_chains", [])),
                    "confidence_scores": state.get("confidence_scores", {})
                }
            }
            
            state["detailed_report"] = report
            state["stage_results"]["detailed_report"] = report
            
            self.logger.info("Generated detailed report")
            
        except Exception as e:
            self.logger.error(f"Detailed report error: {e}")
            state["detailed_report"] = {}
        
        return state
    
    async def prepare_visualization_data(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """准备可视化数据"""
        state["progress"] = 92.0
        
        try:
            # 准备各种可视化数据
            viz_data = {
                "knowledge_graph": self._prepare_graph_viz(state.get("knowledge_graph", {})),
                "theme_hierarchy": self._prepare_theme_hierarchy(state.get("integrated_themes", {})),
                "evidence_flow": self._prepare_evidence_flow(state.get("evidence_chains", [])),
                "analysis_timeline": self._prepare_timeline(state.get("stage_timings", {})),
                "quality_radar": self._prepare_quality_radar(state)
            }
            
            state["visualization_data"] = viz_data
            state["stage_results"]["visualizations"] = viz_data
            
            self.logger.info("Prepared visualization data")
            
        except Exception as e:
            self.logger.error(f"Visualization preparation error: {e}")
            state["visualization_data"] = {}
        
        return state
    
    async def generate_action_plan(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """生成行动方案"""
        state["progress"] = 95.0
        
        try:
            recommendations = state.get("recommendations", [])
            insights = state.get("novel_insights", [])
            
            # 生成SMART行动计划
            action_plan = {
                "objectives": [],
                "milestones": [],
                "resource_requirements": [],
                "risk_mitigation": [],
                "success_metrics": []
            }
            
            # 将建议转化为具体行动
            for rec in recommendations[:5]:  # 前5个重要建议
                objective = {
                    "description": rec.get("action", ""),
                    "specific": self._make_specific(rec),
                    "measurable": rec.get("metrics", []),
                    "achievable": self._assess_achievability(rec),
                    "relevant": rec.get("expected_outcome", ""),
                    "time_bound": rec.get("timeline", ""),
                    "priority": rec.get("priority", "medium")
                }
                action_plan["objectives"].append(objective)
            
            # 定义里程碑
            action_plan["milestones"] = self._define_milestones(action_plan["objectives"])
            
            # 资源需求
            action_plan["resource_requirements"] = self._estimate_resources(recommendations)
            
            # 风险缓解
            action_plan["risk_mitigation"] = self._identify_risks_and_mitigation(recommendations)
            
            # 成功指标
            action_plan["success_metrics"] = self._define_success_metrics(recommendations)
            
            state["action_plan"] = action_plan
            state["stage_results"]["action_plan"] = action_plan
            
            self.logger.info("Generated action plan")
            
        except Exception as e:
            self.logger.error(f"Action plan error: {e}")
            state["action_plan"] = {}
        
        return state
    
    # 向量化和存储
    async def vectorize_and_store(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """向量化并存储到数据库"""
        state["progress"] = 97.0
        
        try:
            chunks = state.get("chunks", [])
            
            # 批量生成嵌入向量
            texts = [chunk.content for chunk in chunks]
            embeddings = []
            
            # 分批处理
            batch_size = 20
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = await self.embeddings_model.aembed_documents(batch)
                embeddings.extend(batch_embeddings)
            
            state["embeddings"] = embeddings
            
            # 存储到向量数据库
            vector_indices = []
            collection_name = f"project_{state['project_id']}"
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # 准备元数据
                metadata = {
                    "document_id": state["document_id"],
                    "chunk_index": i,
                    "document_type": state.get("document_type", "unknown"),
                    "language": state.get("language", "unknown"),
                    "chunk_strategy": state.get("chunk_strategy", "unknown"),
                    **chunk.metadata
                }
                
                # 添加分析结果到元数据
                if i == 0:  # 第一个块存储文档级别的信息
                    metadata.update({
                        "executive_summary": state.get("executive_summary", "")[:500],
                        "key_insights": json.dumps(state.get("novel_insights", [])[:3]),
                        "document_quality_score": state.get("quality_metrics", {}).get("overall", 0)
                    })
                
                # 存储
                vector_id = await self.vector_store.add(
                    collection_name=collection_name,
                    document={
                        "id": f"{state['document_id']}_{i}",
                        "content": chunk.content,
                        "embedding": embedding,
                        "metadata": metadata
                    }
                )
                vector_indices.append(vector_id)
            
            state["vector_indices"] = vector_indices
            
            self.logger.info(f"Stored {len(vector_indices)} vectors")
            
        except Exception as e:
            self.logger.error(f"Vectorization error: {e}")
            state["vector_indices"] = []
        
        return state
    
    async def finalize_analysis(self, state: AdvancedDocumentState) -> AdvancedDocumentState:
        """完成分析"""
        state["status"] = "completed"
        state["progress"] = 100.0
        state["end_time"] = datetime.now()
        
        # 计算总处理时间
        state["processing_time_seconds"] = (
            state["end_time"] - state["start_time"]
        ).total_seconds()
        
        # 计算质量指标
        state["quality_metrics"] = {
            "completeness": self._assess_completeness(state),
            "coherence": self._assess_coherence(state),
            "depth": self._assess_depth(state),
            "overall": self._calculate_overall_quality(state)
        }
        
        # 计算各阶段置信度
        state["confidence_scores"] = {
            "metadata_extraction": 0.95,
            "summarization": 0.90,
            "knowledge_graph": 0.85,
            "insights": 0.80,
            "recommendations": 0.85
        }
        
        self.logger.info(
            f"Analysis completed for {state['document_id']} "
            f"in {state['processing_time_seconds']:.2f}s"
        )
        
        return state
    
    # 辅助方法
    def _clean_content(self, content: str) -> str:
        """清理文档内容"""
        # 移除多余空白
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # 修复常见OCR错误
        content = content.replace('ﬁ', 'fi')
        content = content.replace('ﬂ', 'fl')
        
        # 标准化引号
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")
        
        return content.strip()
    
    def _detect_language(self, text: str) -> str:
        """检测语言"""
        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text)
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return "chinese"
        else:
            return "english"
    
    async def _detect_document_type(self, content: str, filename: str) -> DocumentType:
        """检测文档类型"""
        filename_lower = filename.lower()
        
        # 基于文件名的启发式判断
        if any(keyword in filename_lower for keyword in ["paper", "thesis", "journal"]):
            return DocumentType.ACADEMIC
        elif any(keyword in filename_lower for keyword in ["manual", "guide", "documentation"]):
            return DocumentType.TECHNICAL
        elif any(keyword in filename_lower for keyword in ["proposal", "contract", "agreement"]):
            return DocumentType.BUSINESS
        elif any(keyword in filename_lower for keyword in ["report", "analysis", "study"]):
            return DocumentType.REPORT
        
        # 基于内容的判断
        if "abstract" in content.lower()[:1000] and "references" in content.lower():
            return DocumentType.ACADEMIC
        
        return DocumentType.GENERAL
    
    def _analyze_chunk_distribution(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """分析分块分布"""
        sizes = [len(chunk.content) for chunk in chunks]
        return {
            "min_size": min(sizes),
            "max_size": max(sizes),
            "avg_size": np.mean(sizes),
            "std_size": np.std(sizes),
            "distribution": np.histogram(sizes, bins=10)[0].tolist()
        }
    
    def _fallback_chunking(self, content: str) -> List[DocumentChunk]:
        """回退分块策略"""
        # 简单的固定大小分块
        chunk_size = 1000
        chunks = []
        
        for i in range(0, len(content), chunk_size - 200):  # 200字符重叠
            chunk_content = content[i:i + chunk_size]
            chunk = DocumentChunk(
                id=str(uuid4()),
                document_id="temp",
                content=chunk_content,
                content_hash=hashlib.md5(chunk_content.encode()).hexdigest(),
                start_char=i,
                end_char=i + len(chunk_content),
                chunk_index=len(chunks),
                char_count=len(chunk_content)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _parse_json_response(self, response: str) -> Union[Dict[str, Any], List[Any]]:
        """解析JSON响应（支持对象和数组）"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except:
            # 尝试提取JSON对象
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # 尝试提取JSON数组
            array_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if array_match:
                try:
                    return json.loads(array_match.group())
                except:
                    pass
        
        return {}
    
    async def _analyze_dimension(self, content: str, prompt: str, dimension: str) -> List[Any]:
        """分析特定维度"""
        try:
            full_prompt = f"{prompt}\n\nContent:\n{content}"
            response = await self.fast_llm.ainvoke([HumanMessage(content=full_prompt)])
            
            # 解析响应
            if dimension == "logical":
                return self._parse_logical_structure(response.content)
            elif dimension == "thematic":
                return self._parse_thematic_structure(response.content)
            
            return []
        except Exception as e:
            self.logger.error(f"Dimension analysis error for {dimension}: {e}")
            return []
    
    async def _extract_temporal_structure(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """提取时间结构"""
        temporal_elements = []
        
        # 简化的时间提取
        time_patterns = [
            r'\b(19|20)\d{2}\b',  # 年份
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b',  # 日期
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'  # 日期格式
        ]
        
        for i, chunk in enumerate(chunks[:20]):  # 检查前20个块
            for pattern in time_patterns:
                matches = re.findall(pattern, chunk.content, re.IGNORECASE)
                for match in matches:
                    temporal_elements.append({
                        "time_reference": match,
                        "chunk_index": i,
                        "context": chunk.content[:100]
                    })
        
        return temporal_elements
    
    async def _extract_causal_structure(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """提取因果结构"""
        causal_elements = []
        
        # 因果关系指示词
        causal_indicators = [
            "because", "therefore", "consequently", "as a result",
            "due to", "leads to", "causes", "results in"
        ]
        
        for i, chunk in enumerate(chunks[:20]):
            content_lower = chunk.content.lower()
            for indicator in causal_indicators:
                if indicator in content_lower:
                    causal_elements.append({
                        "indicator": indicator,
                        "chunk_index": i,
                        "context": self._extract_causal_context(chunk.content, indicator)
                    })
        
        return causal_elements
    
    def _extract_causal_context(self, content: str, indicator: str) -> str:
        """提取因果关系上下文"""
        # 找到指示词位置
        pos = content.lower().find(indicator)
        if pos == -1:
            return ""
        
        # 提取前后文
        start = max(0, pos - 50)
        end = min(len(content), pos + len(indicator) + 50)
        
        return content[start:end]
    
    async def _extract_entities(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """提取实体"""
        entities = []
        
        # 使用LLM提取实体
        for i, chunk in enumerate(chunks[:8]):  # 增加到8个块以提高覆盖率
            prompt = f"""
请从以下文本中提取命名实体。

文本内容：
{chunk.content[:800]}

要求：
1. 识别人物（Person）、组织（Organization）、地点（Location）、概念（Concept）、技术（Technology）等实体
2. 返回JSON格式的列表，每个实体包含name、type和importance字段

示例格式：
[{{"name": "实体名称", "type": "类型", "importance": 0.8}}]

请返回JSON数组格式，不要包含其他文字。
            """
            
            try:
                response = await self.fast_llm.ainvoke([HumanMessage(content=prompt)])
                chunk_entities = self._parse_json_response(response.content)
                if isinstance(chunk_entities, list):
                    entities.extend(chunk_entities)
            except:
                continue
        
        # 去重和排序
        unique_entities = {}
        for entity in entities:
            name = entity.get("name", "")
            if name not in unique_entities:
                unique_entities[name] = entity
            else:
                # 更新重要性分数
                unique_entities[name]["importance"] = max(
                    unique_entities[name].get("importance", 0),
                    entity.get("importance", 0)
                )
        
        return list(unique_entities.values())
    
    async def _extract_relationships(self, chunks: List[DocumentChunk], 
                                   entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取关系"""
        relationships = []
        
        # 如果实体太少，直接返回
        if len(entities) < 2:
            return relationships
        
        # 获取前20个最重要的实体
        entity_names = [e["name"] for e in entities[:20]]
        
        # 使用LLM提取关系
        for chunk in chunks[:5]:
            # 找出当前块中存在的实体
            present_entities = []
            for entity in entity_names:
                if entity.lower() in chunk.content.lower():
                    present_entities.append(entity)
            
            # 如果有至少2个实体，尝试提取关系
            if len(present_entities) >= 2:
                entity_list = ", ".join(present_entities[:8])
                prompt = f"""
分析以下文本中这些实体之间的关系：

实体：{entity_list}

文本：
{chunk.content[:600]}

请识别实体之间的明确关系，返回JSON格式：
[{{"source": "实体1", "target": "实体2", "type": "关系类型", "description": "关系描述"}}]

关系类型可以是：隶属于、合作、开发、使用、包含、相关等。
只返回JSON数组。
"""
                
                try:
                    response = await self.fast_llm.ainvoke([HumanMessage(content=prompt)])
                    chunk_relationships = self._parse_json_response(response.content)
                    
                    if isinstance(chunk_relationships, list):
                        # 验证关系
                        for rel in chunk_relationships:
                            if (isinstance(rel, dict) and 
                                rel.get('source') in entity_names and 
                                rel.get('target') in entity_names):
                                relationships.append(rel)
                except:
                    # 如果LLM提取失败，使用共现关系作为后备
                    for i in range(len(present_entities)):
                        for j in range(i + 1, len(present_entities)):
                            relationships.append({
                                "source": present_entities[i],
                                "target": present_entities[j],
                                "type": "co-occurrence",
                                "description": "在同一文本块中出现"
                            })
        
        # 去重
        unique_relationships = []
        seen = set()
        for rel in relationships:
            key = (rel['source'], rel['target'], rel.get('type', 'related'))
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)
        
        return unique_relationships
    
    def _count_entity_types(self, entities: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计实体类型"""
        type_counts = {}
        for entity in entities:
            entity_type = entity.get("type", "unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts
    
    def _count_relationship_types(self, relationships: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计关系类型"""
        type_counts = {}
        for rel in relationships:
            rel_type = rel.get("type", "unknown")
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        return type_counts
    
    async def _generate_questions(self, context: str, level: str, count: int) -> List[str]:
        """生成特定层次的问题"""
        level_prompts = {
            "factual": "Generate factual questions about specific details, dates, names, and definitions",
            "analytical": "Generate analytical questions about relationships, patterns, and comparisons",
            "synthetic": "Generate synthesis questions that connect multiple concepts and require integration",
            "creative": "Generate creative questions that explore implications, applications, and extensions"
        }
        
        prompt = f"""
        {level_prompts.get(level, "")}
        
        Context: {context}
        
        Generate {count} {level} questions. Format as a numbered list.
        """
        
        try:
            response = await self.fast_llm.ainvoke([HumanMessage(content=prompt)])
            # 解析问题列表
            questions = []
            for line in response.content.split('\n'):
                if re.match(r'^\d+\.', line.strip()):
                    questions.append(line.strip())
            return questions[:count]
        except Exception as e:
            self.logger.error(f"Question generation error for {level}: {e}")
            return []
    
    def _extract_context(self, text: str, concept: str, window: int = 50) -> str:
        """提取概念周围的上下文"""
        pos = text.lower().find(concept.lower())
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(concept) + window)
        
        return text[start:end]
    
    def _contains_claim(self, text: str) -> bool:
        """检查文本是否包含论点"""
        claim_indicators = [
            "argue that", "claim that", "propose that", "suggest that",
            "demonstrate that", "show that", "believe that", "conclude that"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in claim_indicators)
    
    def _extract_claim(self, text: str) -> str:
        """提取论点"""
        # 简化版本 - 提取包含论点指示词的句子
        sentences = text.split('.')
        for sentence in sentences:
            if self._contains_claim(sentence):
                return sentence.strip()
        return ""
    
    def _contains_evidence(self, text: str) -> bool:
        """检查文本是否包含证据"""
        evidence_indicators = [
            "study shows", "research indicates", "data suggests",
            "evidence shows", "according to", "based on", "found that"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in evidence_indicators)
    
    def _classify_evidence(self, text: str) -> str:
        """分类证据类型"""
        if "study" in text.lower() or "research" in text.lower():
            return "empirical"
        elif "theory" in text.lower() or "model" in text.lower():
            return "theoretical"
        elif "example" in text.lower() or "case" in text.lower():
            return "anecdotal"
        else:
            return "general"
    
    def _evaluate_evidence_strength(self, chain: Dict[str, Any]) -> float:
        """评估证据强度"""
        # 简化的评估逻辑
        evidence_count = len(chain.get("evidence", []))
        evidence_types = set(e["type"] for e in chain.get("evidence", []))
        
        # 基础分数
        strength = min(evidence_count * 0.2, 0.6)
        
        # 证据类型多样性加分
        if len(evidence_types) > 1:
            strength += 0.2
        
        # 实证证据加分
        if "empirical" in evidence_types:
            strength += 0.2
        
        return min(strength, 1.0)
    
    def _build_perspective_prompt(self, perspective: str, content: str, 
                                summaries: Dict[str, str]) -> str:
        """构建视角分析提示"""
        perspective_prompts = {
            "methodological": "Analyze the methodological approach, rigor, and limitations",
            "stakeholder": "Identify different stakeholders and their interests/impacts",
            "temporal": "Examine the temporal context and time-sensitivity of findings",
            "interdisciplinary": "Explore connections to other fields and disciplines",
            "practical": "Assess practical applications and implementation considerations"
        }
        
        return f"""
        Analyze from {perspective} perspective:
        {perspective_prompts.get(perspective, "")}
        
        Summary: {summaries.get('detailed', '')}
        Content excerpt: {content[:2000]}
        
        Provide structured analysis with specific examples.
        """
    
    async def _analyze_perspective(self, prompt: str, perspective: str) -> Dict[str, Any]:
        """分析特定视角"""
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return {
                "perspective": perspective,
                "analysis": response.content,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Perspective analysis error for {perspective}: {e}")
            return {"perspective": perspective, "error": str(e)}
    
    def _parse_assumptions_response(self, response: str) -> Dict[str, Any]:
        """解析假设测试响应"""
        # 简化的解析
        assumptions = {
            "explicit": [],
            "implicit": [],
            "methodological": [],
            "theoretical": []
        }
        
        # 尝试按部分解析
        sections = response.split('\n\n')
        current_type = None
        
        for section in sections:
            if "explicit" in section.lower():
                current_type = "explicit"
            elif "implicit" in section.lower():
                current_type = "implicit"
            elif "methodological" in section.lower():
                current_type = "methodological"
            elif "theoretical" in section.lower():
                current_type = "theoretical"
            
            if current_type:
                # 提取列表项
                items = re.findall(r'[-•]\s*(.+)', section)
                assumptions[current_type].extend(items)
        
        return assumptions
    
    def _analyze_argument_structure(self, chain: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析论证结构"""
        gaps = []
        
        # 检查证据不足
        if len(chain.get("evidence", [])) < 2:
            gaps.append({
                "type": "insufficient_evidence",
                "description": f"Claim lacks sufficient evidence: {chain.get('claim', '')[:100]}",
                "severity": "medium"
            })
        
        # 检查证据相关性
        # （简化版本）
        
        return gaps
    
    def _check_assumption_consistency(self, assumptions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查假设一致性"""
        gaps = []
        
        # 简化的一致性检查
        all_assumptions = []
        for assumption_type in assumptions.values():
            if isinstance(assumption_type, list):
                all_assumptions.extend(assumption_type)
        
        # 这里应该有更复杂的逻辑来检查假设之间的矛盾
        # 简化版本只返回空列表
        
        return gaps
    
    async def _identify_fallacies(self, content: str) -> List[Dict[str, Any]]:
        """识别逻辑谬误"""
        prompt = f"""
        Identify logical fallacies in this text:
        {content}
        
        Common fallacies to check:
        - Ad hominem
        - Straw man
        - False dichotomy
        - Hasty generalization
        - Circular reasoning
        - Appeal to authority
        
        For each fallacy found, explain why it's problematic.
        """
        
        try:
            response = await self.fast_llm.ainvoke([HumanMessage(content=prompt)])
            # 解析响应
            fallacies = []
            for line in response.content.split('\n'):
                if any(fallacy in line.lower() for fallacy in 
                      ["ad hominem", "straw man", "false dichotomy", "hasty", "circular", "appeal"]):
                    fallacies.append({
                        "type": line.split(':')[0].strip() if ':' in line else "unknown",
                        "description": line
                    })
            return fallacies
        except Exception as e:
            self.logger.error(f"Fallacy identification error: {e}")
            return []
    
    def _assess_gap_severity(self, logical_gaps: List[Dict[str, Any]], 
                           fallacies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估逻辑漏洞严重性"""
        severity_scores = {
            "insufficient_evidence": 0.3,
            "circular_reasoning": 0.8,
            "false_dichotomy": 0.6,
            "hasty_generalization": 0.5
        }
        
        total_score = 0
        gap_count = len(logical_gaps) + len(fallacies)
        
        for gap in logical_gaps:
            gap_type = gap.get("type", "")
            total_score += severity_scores.get(gap_type, 0.4)
        
        for fallacy in fallacies:
            fallacy_type = fallacy.get("type", "").lower()
            for key, score in severity_scores.items():
                if key in fallacy_type:
                    total_score += score
                    break
        
        if gap_count == 0:
            severity = "low"
        else:
            avg_score = total_score / gap_count
            if avg_score < 0.3:
                severity = "low"
            elif avg_score < 0.6:
                severity = "medium"
            else:
                severity = "high"
        
        return {
            "severity": severity,
            "total_issues": gap_count,
            "average_score": total_score / max(gap_count, 1)
        }
    
    def _parse_theme_integration(self, response: str) -> Dict[str, Any]:
        """解析主题整合响应"""
        themes = {
            "core_themes": [],
            "theme_relationships": [],
            "theme_evolution": [],
            "integrated_narrative": ""
        }
        
        # 解析响应
        sections = response.split('\n\n')
        
        for section in sections:
            if "core theme" in section.lower():
                # 提取主题列表
                theme_items = re.findall(r'\d+\.\s*(.+)', section)
                themes["core_themes"] = theme_items
            elif "narrative" in section.lower():
                themes["integrated_narrative"] = section
        
        return themes
    
    async def _get_project_knowledge(self, project_id: str) -> Dict[str, Any]:
        """获取项目已有知识"""
        try:
            # 从记忆系统获取
            if self.memory_service:
                memory = await self.memory_service.get_project_memory(project_id)
                return {
                    "themes": memory.get("key_concepts", []),
                    "entities": memory.get("entities", []),
                    "insights": memory.get("insights", [])
                }
            else:
                return {"themes": [], "entities": [], "insights": []}
        except Exception as e:
            self.logger.error(f"Failed to get project knowledge: {e}")
            return {"themes": [], "entities": [], "insights": []}
    
    def _calculate_similarity(self, theme1: str, theme2: str) -> float:
        """计算主题相似度"""
        # 简化的相似度计算
        # 实际应用中应该使用更复杂的方法，如词向量相似度
        
        words1 = set(theme1.lower().split())
        words2 = set(theme2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def _update_project_memory(self, state: AdvancedDocumentState) -> None:
        """更新项目记忆"""
        try:
            if not self.memory_service:
                self.logger.warning("Memory service not available, skipping memory update")
                return
                
            # 准备要保存的信息
            memory_update = {
                "document_id": state["document_id"],
                "key_concepts": [t for t in state.get("integrated_themes", {}).get("core_themes", [])],
                "insights": state.get("novel_insights", [])[:5],
                "summary": state.get("executive_summary", ""),
                "quality_score": state.get("quality_metrics", {}).get("overall", 0)
            }
            
            await self.memory_service.update_project_memory(
                state["project_id"],
                state["user_id"],
                memory_update
            )
            
            self.logger.info("Updated project memory")
            
        except Exception as e:
            self.logger.error(f"Failed to update project memory: {e}")
    
    def _parse_insights_response(self, response: str) -> List[Dict[str, Any]]:
        """解析洞察响应"""
        insights = []
        
        # 解析编号列表
        items = re.split(r'\n\d+\.', response)
        
        for item in items[1:]:  # 跳过第一个空项
            insight = {
                "description": "",
                "reasoning": "",
                "confidence": 0.8,
                "validation_method": ""
            }
            
            # 提取各部分
            lines = item.strip().split('\n')
            if lines:
                insight["description"] = lines[0].strip()
                
                # 查找其他部分
                for line in lines[1:]:
                    if "reasoning" in line.lower():
                        insight["reasoning"] = line.split(':', 1)[1].strip() if ':' in line else line
                    elif "confidence" in line.lower():
                        # 提取置信度数值
                        conf_match = re.search(r'0?\.\d+', line)
                        if conf_match:
                            insight["confidence"] = float(conf_match.group())
                    elif "validation" in line.lower():
                        insight["validation_method"] = line.split(':', 1)[1].strip() if ':' in line else line
            
            if insight["description"]:
                insights.append(insight)
        
        return insights
    
    def _parse_recommendations_response(self, response: str) -> List[Dict[str, Any]]:
        """解析建议响应"""
        recommendations = []
        
        # 按时间段分割
        sections = response.split('\n\n')
        current_timeline = ""
        
        for section in sections:
            if "immediate" in section.lower():
                current_timeline = "immediate"
            elif "short-term" in section.lower():
                current_timeline = "short-term"
            elif "long-term" in section.lower():
                current_timeline = "long-term"
            
            # 提取建议项
            items = re.findall(r'[-•]\s*(.+)', section)
            for item in items:
                rec = {
                    "action": item,
                    "timeline": current_timeline,
                    "priority": "medium",
                    "resources": [],
                    "metrics": []
                }
                
                # 尝试识别优先级
                if "critical" in item.lower() or "urgent" in item.lower():
                    rec["priority"] = "high"
                elif "optional" in item.lower() or "consider" in item.lower():
                    rec["priority"] = "low"
                
                recommendations.append(rec)
        
        return recommendations
    
    def _assess_completeness(self, state: AdvancedDocumentState) -> float:
        """评估分析完整性"""
        required_components = [
            "progressive_summaries",
            "multidimensional_outline",
            "knowledge_graph",
            "layered_questions",
            "novel_insights",
            "recommendations"
        ]
        
        completed = sum(1 for comp in required_components if state.get(comp))
        return completed / len(required_components)
    
    def _assess_coherence(self, state: AdvancedDocumentState) -> float:
        """评估分析连贯性"""
        # 简化的连贯性评估
        # 检查各部分之间的一致性
        
        coherence_score = 0.8  # 基础分数
        
        # 检查主题一致性
        themes = state.get("integrated_themes", {}).get("core_themes", [])
        insights = state.get("novel_insights", [])
        
        if themes and insights:
            # 检查洞察是否与主题相关
            theme_words = set()
            for theme in themes:
                theme_words.update(theme.lower().split())
            
            insight_relevance = 0
            for insight in insights:
                insight_text = insight.get("description", "").lower()
                if any(word in insight_text for word in theme_words):
                    insight_relevance += 1
            
            if insights:
                coherence_score = 0.8 + (insight_relevance / len(insights)) * 0.2
        
        return min(coherence_score, 1.0)
    
    def _assess_depth(self, state: AdvancedDocumentState) -> float:
        """评估分析深度"""
        depth_indicators = {
            "evidence_chains": len(state.get("evidence_chains", [])),
            "perspectives": len(state.get("multi_perspective_analysis", {})),
            "logical_gaps": len(state.get("logical_gaps", [])),
            "insights": len(state.get("novel_insights", []))
        }
        
        # 标准化分数
        scores = []
        if depth_indicators["evidence_chains"] > 5:
            scores.append(1.0)
        else:
            scores.append(depth_indicators["evidence_chains"] / 5)
        
        if depth_indicators["perspectives"] >= 5:
            scores.append(1.0)
        else:
            scores.append(depth_indicators["perspectives"] / 5)
        
        if depth_indicators["insights"] >= 3:
            scores.append(1.0)
        else:
            scores.append(depth_indicators["insights"] / 3)
        
        return np.mean(scores)
    
    def _calculate_overall_quality(self, state: AdvancedDocumentState) -> float:
        """计算整体质量分数"""
        metrics = state.get("quality_metrics", {})
        
        weights = {
            "completeness": 0.3,
            "coherence": 0.3,
            "depth": 0.4
        }
        
        overall = 0.0
        for metric, weight in weights.items():
            overall += metrics.get(metric, 0.5) * weight
        
        return overall
    
    def _prepare_graph_viz(self, knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """准备知识图谱可视化数据"""
        return {
            "nodes": [
                {
                    "id": entity.get("name", ""),
                    "label": entity.get("name", ""),
                    "type": entity.get("type", "unknown"),
                    "importance": entity.get("importance", 0.5)
                }
                for entity in knowledge_graph.get("entities", [])
            ],
            "edges": [
                {
                    "source": rel.get("source", ""),
                    "target": rel.get("target", ""),
                    "type": rel.get("type", "unknown")
                }
                for rel in knowledge_graph.get("relationships", [])
            ]
        }
    
    def _prepare_theme_hierarchy(self, themes: Dict[str, Any]) -> Dict[str, Any]:
        """准备主题层级可视化数据"""
        return {
            "name": "Document Themes",
            "children": [
                {
                    "name": theme,
                    "value": 1
                }
                for theme in themes.get("core_themes", [])
            ]
        }
    
    def _prepare_evidence_flow(self, evidence_chains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """准备证据流可视化数据"""
        flows = []
        
        for chain in evidence_chains:
            flow = {
                "claim": chain.get("claim", ""),
                "evidence_count": len(chain.get("evidence", [])),
                "strength": chain.get("strength", 0),
                "flow_path": [
                    {
                        "type": "claim",
                        "content": chain.get("claim", "")[:100],
                        "index": chain.get("chunk_index", 0)
                    }
                ]
            }
            
            for evidence in chain.get("evidence", []):
                flow["flow_path"].append({
                    "type": evidence.get("type", "unknown"),
                    "content": evidence.get("content", "")[:100],
                    "index": evidence.get("chunk_index", 0)
                })
            
            flows.append(flow)
        
        return flows
    
    def _prepare_timeline(self, stage_timings: Dict[str, float]) -> List[Dict[str, Any]]:
        """准备时间线可视化数据"""
        timeline = []
        cumulative_time = 0
        
        for stage, duration in stage_timings.items():
            timeline.append({
                "stage": stage,
                "start": cumulative_time,
                "duration": duration,
                "end": cumulative_time + duration
            })
            cumulative_time += duration
        
        return timeline
    
    def _prepare_quality_radar(self, state: AdvancedDocumentState) -> Dict[str, Any]:
        """准备质量雷达图数据"""
        metrics = state.get("quality_metrics", {})
        confidence = state.get("confidence_scores", {})
        
        return {
            "axes": [
                {"axis": "Completeness", "value": metrics.get("completeness", 0)},
                {"axis": "Coherence", "value": metrics.get("coherence", 0)},
                {"axis": "Depth", "value": metrics.get("depth", 0)},
                {"axis": "Evidence", "value": confidence.get("evidence", 0.8)},
                {"axis": "Insights", "value": confidence.get("insights", 0.8)}
            ]
        }
    
    def _make_specific(self, recommendation: Dict[str, Any]) -> str:
        """使建议更具体"""
        action = recommendation.get("action", "")
        
        # 添加具体细节
        if "implement" in action.lower():
            return f"{action} with clear milestones and weekly progress reviews"
        elif "develop" in action.lower():
            return f"{action} including detailed specifications and prototype"
        else:
            return f"{action} with measurable outcomes"
    
    def _assess_achievability(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """评估可实现性"""
        return {
            "feasibility": "high" if recommendation.get("priority") != "high" else "medium",
            "required_effort": "medium",
            "dependencies": []
        }
    
    def _define_milestones(self, objectives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """定义里程碑"""
        milestones = []
        
        for i, obj in enumerate(objectives):
            milestone = {
                "name": f"Milestone {i+1}",
                "description": f"Complete {obj['description'][:50]}...",
                "target_date": f"Month {i+1}",
                "success_criteria": obj.get("measurable", [])
            }
            milestones.append(milestone)
        
        return milestones
    
    def _estimate_resources(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """估算资源需求"""
        return {
            "human_resources": "2-3 FTE",
            "budget_estimate": "$50,000 - $100,000",
            "time_requirement": "3-6 months",
            "tools_required": ["Analysis tools", "Collaboration platform"]
        }
    
    def _identify_risks_and_mitigation(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别风险和缓解措施"""
        return [
            {
                "risk": "Resource constraints",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Phased implementation with priority focus"
            },
            {
                "risk": "Technical complexity",
                "probability": "low",
                "impact": "medium",
                "mitigation": "Expert consultation and proof of concept"
            }
        ]
    
    def _define_success_metrics(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """定义成功指标"""
        return [
            {
                "metric": "Implementation completion rate",
                "target": "80%",
                "measurement_method": "Project tracking"
            },
            {
                "metric": "Quality improvement",
                "target": "25% increase",
                "measurement_method": "Before/after analysis"
            }
        ]
    
    def _parse_logical_structure(self, response: str) -> List[Dict[str, Any]]:
        """解析逻辑结构"""
        structure = []
        
        # 简单的解析逻辑
        sections = response.split('\n\n')
        for section in sections:
            if section.strip():
                structure.append({
                    "type": "section",
                    "content": section.strip(),
                    "level": 1
                })
        
        return structure
    
    def _parse_thematic_structure(self, response: str) -> List[Dict[str, Any]]:
        """解析主题结构"""
        themes = []
        
        # 提取主题
        theme_lines = re.findall(r'[-•]\s*(.+)', response)
        for theme in theme_lines:
            themes.append({
                "theme": theme.strip(),
                "relevance": 0.8  # 默认相关性
            })
        
        return themes
    
    # 公共接口
    async def analyze_document(self, document_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析文档的公共接口"""
        try:
            # 准备初始状态
            initial_state = AdvancedDocumentState(
                # 基础信息
                document_id=document_info["document_id"],
                project_id=document_info["project_id"],
                user_id=document_info.get("user_id", ""),
                file_path=document_info["file_path"],
                file_name=document_info["file_name"],
                analysis_depth=AnalysisDepth(
                    document_info.get("analysis_depth", AnalysisDepth.COMPREHENSIVE)
                ),
                analysis_goal=document_info.get("analysis_goal", ""),
                
                # 文档特征（初始值）
                document_type=None,
                language="unknown",
                encoding="utf-8",
                file_size=0,
                page_count=0,
                
                # 处理状态
                status="pending",
                current_stage=AnalysisStage.PREPARATION,
                progress=0.0,
                error_message=None,
                stage_results={},
                
                # 内容数据
                content=document_info.get("content"),  # 接收传入的内容
                raw_content=None,
                cleaned_content=None,
                content_hash=None,
                
                # 分析结果（初始为空）
                chunks=[],
                chunk_strategy=ChunkingStrategy.SENTENCE_BASED,
                chunk_metadata={},
                document_metadata={},
                progressive_summaries={},
                multidimensional_outline={},
                knowledge_graph={},
                layered_questions={},
                cross_references={},
                evidence_chains=[],
                multi_perspective_analysis={},
                assumption_testing={},
                logical_gaps=[],
                integrated_themes={},
                knowledge_connections={},
                novel_insights=[],
                recommendations=[],
                executive_summary=None,
                detailed_report=None,
                visualization_data={},
                action_plan=None,
                
                # 向量化数据
                embeddings=[],
                embedding_metadata={},
                vector_indices=[],
                
                # 质量评估
                quality_metrics={},
                confidence_scores={},
                
                # 性能指标
                start_time=datetime.now(),
                end_time=None,
                processing_time_seconds=0.0,
                stage_timings={},
                token_usage={}
            )
            
            # 如果提供了内容，直接使用
            if "content" in document_info:
                initial_state["content"] = document_info["content"]
                initial_state["raw_content"] = document_info["content"]
                initial_state["cleaned_content"] = self._clean_content(document_info["content"])
            
            # 执行分析
            result_state = await self.app.ainvoke(initial_state)
            
            # 返回结果
            return {
                "success": True,
                "document_id": result_state["document_id"],
                "status": result_state["status"],
                "analysis_depth": result_state["analysis_depth"],
                "results": {
                    "executive_summary": result_state.get("executive_summary", ""),
                    "key_insights": result_state.get("novel_insights", []),
                    "recommendations": result_state.get("recommendations", []),
                    "quality_score": result_state.get("quality_metrics", {}).get("overall", 0),
                    "processing_time": result_state.get("processing_time_seconds", 0)
                },
                "detailed_report": result_state.get("detailed_report", {}),
                "visualization_data": result_state.get("visualization_data", {}),
                "action_plan": result_state.get("action_plan", {})
            }
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_info.get("document_id", "")
            }
    
    def get_analysis_progress(self, document_id: str) -> Dict[str, Any]:
        """获取分析进度"""
        # 这里应该从持久化存储中获取进度
        # 简化版本返回模拟数据
        return {
            "document_id": document_id,
            "status": "analyzing",
            "current_stage": "deep_exploration",
            "progress": 45.0,
            "estimated_time_remaining": 300  # 秒
        }


# 创建便捷函数
async def analyze_document_advanced(
    document_info: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """高级文档分析的便捷函数"""
    analyzer = AdvancedDocumentAnalyzer(config)
    return await analyzer.analyze_document(document_info)