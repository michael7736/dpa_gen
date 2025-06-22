"""
基于LangGraph的文档处理智能体
实现文档解析、分块、向量化和知识图谱构建的完整工作流
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, TypedDict
from uuid import UUID, uuid4
from datetime import datetime

from langgraph import StateGraph, END
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

from ..config.settings import get_settings
from ..core.knowledge_index import KnowledgeIndexer
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DocumentProcessingState(TypedDict):
    """文档处理状态"""
    # 输入信息
    project_id: str
    document_id: str
    document_path: str
    document_type: str
    processing_config: Dict[str, Any]
    
    # 处理过程数据
    raw_content: Optional[str]
    parsed_content: Optional[Dict[str, Any]]
    document_structure: Optional[Dict[str, Any]]
    chunks: Optional[List[Dict[str, Any]]]
    embeddings: Optional[List[List[float]]]
    entities: Optional[List[Dict[str, Any]]]
    knowledge_graph: Optional[Dict[str, Any]]
    
    # 状态和结果
    processing_status: str
    current_step: str
    error_message: Optional[str]
    warnings: List[str]
    processing_time: float
    result: Optional[Dict[str, Any]]


class DocumentProcessingAgent:
    """基于LangGraph的文档处理智能体"""
    
    def __init__(self):
        self.knowledge_indexer = KnowledgeIndexer()
        self.embeddings = OpenAIEmbeddings(
            model=settings.ai_model.default_embedding_model,
            dimensions=settings.ai_model.embedding_dimension
        )
        self.graph = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """构建文档处理工作流"""
        workflow = StateGraph(DocumentProcessingState)
        
        # 添加处理节点
        workflow.add_node("parse_document", self.parse_document)
        workflow.add_node("extract_structure", self.extract_structure)
        workflow.add_node("semantic_chunking", self.semantic_chunking)
        workflow.add_node("generate_embeddings", self.generate_embeddings)
        workflow.add_node("extract_entities", self.extract_entities)
        workflow.add_node("build_knowledge_graph", self.build_knowledge_graph)
        workflow.add_node("index_to_vector_db", self.index_to_vector_db)
        workflow.add_node("finalize_processing", self.finalize_processing)
        workflow.add_node("handle_error", self.handle_error)
        
        # 定义工作流路径
        workflow.set_entry_point("parse_document")
        
        # 条件路由
        workflow.add_conditional_edges(
            "parse_document",
            self._should_continue_after_parsing,
            {
                "continue": "extract_structure",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "extract_structure",
            self._should_continue_after_structure,
            {
                "continue": "semantic_chunking",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "semantic_chunking",
            self._should_continue_after_chunking,
            {
                "continue": "generate_embeddings",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("generate_embeddings", "extract_entities")
        workflow.add_edge("extract_entities", "build_knowledge_graph")
        workflow.add_edge("build_knowledge_graph", "index_to_vector_db")
        workflow.add_edge("index_to_vector_db", "finalize_processing")
        workflow.add_edge("finalize_processing", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _should_continue_after_parsing(self, state: DocumentProcessingState) -> str:
        """解析后的条件判断"""
        if state["processing_status"] == "error":
            return "error"
        if not state.get("raw_content"):
            return "error"
        return "continue"
    
    def _should_continue_after_structure(self, state: DocumentProcessingState) -> str:
        """结构提取后的条件判断"""
        if state["processing_status"] == "error":
            return "error"
        return "continue"
    
    def _should_continue_after_chunking(self, state: DocumentProcessingState) -> str:
        """分块后的条件判断"""
        if state["processing_status"] == "error":
            return "error"
        if not state.get("chunks") or len(state["chunks"]) == 0:
            return "error"
        return "continue"
    
    async def parse_document(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """解析文档"""
        start_time = datetime.utcnow()
        state["current_step"] = "parse_document"
        
        try:
            logger.info(f"开始解析文档: {state['document_path']}")
            
            # 根据文件类型选择合适的加载器
            if state["document_path"].endswith('.pdf'):
                loader = PyPDFLoader(state["document_path"])
            elif state["document_path"].endswith(('.docx', '.doc')):
                loader = UnstructuredWordDocumentLoader(state["document_path"])
            elif state["document_path"].endswith(('.txt', '.md')):
                with open(state["document_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                state["raw_content"] = content
                state["processing_status"] = "parsed"
                logger.info(f"成功解析文本文档: {len(content)} 个字符")
                return state
            else:
                raise ValueError(f"不支持的文档类型: {state['document_path']}")
            
            # 加载文档
            documents = await loader.aload()
            raw_content = "\n".join([doc.page_content for doc in documents])
            
            # 提取基本元数据
            parsed_content = {
                "total_pages": len(documents),
                "total_chars": len(raw_content),
                "documents": [
                    {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in documents
                ]
            }
            
            state["raw_content"] = raw_content
            state["parsed_content"] = parsed_content
            state["processing_status"] = "parsed"
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"文档解析完成: {len(raw_content)} 个字符, 耗时 {processing_time:.2f}s")
            
        except Exception as e:
            state["error_message"] = f"文档解析失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"文档解析失败: {e}")
            
        return state
    
    async def extract_structure(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """提取文档结构"""
        state["current_step"] = "extract_structure"
        
        try:
            logger.info("开始提取文档结构")
            
            content = state["raw_content"]
            parsed_content = state.get("parsed_content", {})
            
            # 简化的结构提取（可以根据需要扩展）
            structure = {
                "title": self._extract_title(content),
                "sections": self._extract_sections(content),
                "document_type": state["document_type"],
                "total_pages": parsed_content.get("total_pages", 0),
                "total_chars": len(content),
                "language": "zh"  # 可以通过语言检测改进
            }
            
            state["document_structure"] = structure
            state["processing_status"] = "structured"
            
            logger.info(f"结构提取完成: {len(structure['sections'])} 个章节")
            
        except Exception as e:
            state["error_message"] = f"结构提取失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"结构提取失败: {e}")
            
        return state
    
    async def semantic_chunking(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """语义分块"""
        state["current_step"] = "semantic_chunking"
        
        try:
            logger.info("开始语义分块")
            
            content = state["raw_content"]
            config = state.get("processing_config", {})
            
            # 获取分块配置
            chunk_size = config.get("chunk_size", 1000)
            chunk_overlap = config.get("chunk_overlap", 200)
            use_semantic_chunking = config.get("use_semantic_chunking", True)
            
            if use_semantic_chunking and len(content) > 500:
                # 使用语义分块器
                text_splitter = SemanticChunker(
                    embeddings=self.embeddings,
                    breakpoint_threshold_type="percentile",
                    breakpoint_threshold_amount=80
                )
            else:
                # 使用递归字符分块器
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n\n", "\n", "。", "!", "?", ";", "；", "？", "！"]
                )
            
            # 执行分块
            chunks_docs = text_splitter.create_documents([content])
            
            # 构建块数据
            chunks = []
            for i, chunk_doc in enumerate(chunks_docs):
                chunk_data = {
                    "id": str(uuid4()),
                    "content": chunk_doc.page_content,
                    "chunk_index": i,
                    "chunk_type": "paragraph",  # 可以根据内容类型改进
                    "word_count": len(chunk_doc.page_content),
                    "char_start": None,  # 可以通过内容匹配计算
                    "char_end": None,
                    "page_number": None,  # 可以通过解析结果计算
                    "section_id": None,  # 后续关联章节
                    "keywords": [],  # 后续提取
                    "entities": [],  # 后续提取
                    "metadata": chunk_doc.metadata
                }
                chunks.append(chunk_data)
            
            state["chunks"] = chunks
            state["processing_status"] = "chunked"
            
            logger.info(f"语义分块完成: {len(chunks)} 个块")
            
        except Exception as e:
            state["error_message"] = f"语义分块失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"语义分块失败: {e}")
            
        return state
    
    async def generate_embeddings(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """生成嵌入向量"""
        state["current_step"] = "generate_embeddings"
        
        try:
            logger.info("开始生成嵌入向量")
            
            chunks = state["chunks"]
            texts = [chunk["content"] for chunk in chunks]
            
            # 批量生成嵌入向量
            embeddings = await self.embeddings.aembed_documents(texts)
            
            # 将嵌入向量添加到块数据中
            for i, chunk in enumerate(chunks):
                chunk["embedding_vector"] = embeddings[i]
                chunk["embedding_model"] = settings.ai_model.default_embedding_model
            
            state["embeddings"] = embeddings
            state["processing_status"] = "embedded"
            
            logger.info(f"嵌入向量生成完成: {len(embeddings)} 个向量")
            
        except Exception as e:
            state["error_message"] = f"嵌入向量生成失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"嵌入向量生成失败: {e}")
            
        return state
    
    async def extract_entities(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """提取实体"""
        state["current_step"] = "extract_entities"
        
        try:
            logger.info("开始提取实体")
            
            chunks = state["chunks"]
            
            # 简化的实体提取（可以集成NER模型）
            all_entities = []
            
            for chunk in chunks:
                entities = self._extract_simple_entities(chunk["content"])
                chunk["entities"] = entities
                all_entities.extend(entities)
            
            state["entities"] = all_entities
            state["processing_status"] = "entities_extracted"
            
            logger.info(f"实体提取完成: {len(all_entities)} 个实体")
            
        except Exception as e:
            state["error_message"] = f"实体提取失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"实体提取失败: {e}")
            
        return state
    
    async def build_knowledge_graph(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """构建知识图谱"""
        state["current_step"] = "build_knowledge_graph"
        
        try:
            logger.info("开始构建知识图谱")
            
            project_id = UUID(state["project_id"])
            document_id = UUID(state["document_id"])
            chunks = state["chunks"]
            document_structure = state["document_structure"]
            
            # 使用知识索引器构建图谱
            graph_result = await self.knowledge_indexer.build_knowledge_graph(
                project_id=project_id,
                document_id=document_id,
                chunks=chunks,
                document_structure=document_structure
            )
            
            state["knowledge_graph"] = graph_result
            state["processing_status"] = "graph_built"
            
            logger.info(f"知识图谱构建完成: {graph_result}")
            
        except Exception as e:
            state["error_message"] = f"知识图谱构建失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"知识图谱构建失败: {e}")
            
        return state
    
    async def index_to_vector_db(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """索引到向量数据库"""
        state["current_step"] = "index_to_vector_db"
        
        try:
            logger.info("开始索引到向量数据库")
            
            project_id = UUID(state["project_id"])
            document_id = UUID(state["document_id"])
            chunks = state["chunks"]
            
            # 使用知识索引器进行向量索引
            index_result = await self.knowledge_indexer.index_document_chunks(
                project_id=project_id,
                document_id=document_id,
                chunks=chunks
            )
            
            state["processing_status"] = "indexed"
            
            logger.info(f"向量索引完成: {index_result}")
            
        except Exception as e:
            state["error_message"] = f"向量索引失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"向量索引失败: {e}")
            
        return state
    
    async def finalize_processing(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """完成处理"""
        state["current_step"] = "finalize_processing"
        
        try:
            # 构建最终结果
            result = {
                "document_id": state["document_id"],
                "project_id": state["project_id"],
                "processing_status": "completed",
                "total_chunks": len(state.get("chunks", [])),
                "total_entities": len(state.get("entities", [])),
                "knowledge_graph": state.get("knowledge_graph", {}),
                "document_structure": state.get("document_structure", {}),
                "processing_time": state.get("processing_time", 0),
                "warnings": state.get("warnings", [])
            }
            
            state["result"] = result
            state["processing_status"] = "completed"
            
            logger.info(f"文档处理完成: {state['document_id']}")
            
        except Exception as e:
            state["error_message"] = f"处理完成阶段失败: {str(e)}"
            state["processing_status"] = "error"
            logger.error(f"处理完成阶段失败: {e}")
            
        return state
    
    async def handle_error(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """处理错误"""
        state["current_step"] = "handle_error"
        
        error_result = {
            "document_id": state["document_id"],
            "project_id": state["project_id"],
            "processing_status": "failed",
            "error_message": state.get("error_message", "未知错误"),
            "failed_step": state.get("current_step", "unknown"),
            "warnings": state.get("warnings", [])
        }
        
        state["result"] = error_result
        state["processing_status"] = "failed"
        
        logger.error(f"文档处理失败: {state['document_id']}, 错误: {state.get('error_message')}")
        
        return state
    
    def _extract_title(self, content: str) -> str:
        """提取文档标题"""
        lines = content.split('\n')
        for line in lines[:10]:  # 在前10行中查找标题
            line = line.strip()
            if line and len(line) < 100:
                return line
        return "未知标题"
    
    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """提取章节信息"""
        sections = []
        lines = content.split('\n')
        
        current_section = None
        section_id = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 简化的章节检测逻辑
            if self._is_section_header(line):
                if current_section:
                    sections.append(current_section)
                
                section_id += 1
                current_section = {
                    "id": str(uuid4()),
                    "title": line,
                    "section_type": "section",
                    "level": self._get_section_level(line),
                    "order_index": section_id,
                    "line_start": i,
                    "content": ""
                }
            elif current_section:
                current_section["content"] += line + "\n"
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """判断是否为章节标题"""
        if not line:
            return False
        
        # 检查是否包含章节标识符
        section_indicators = [
            "第", "章", "节", "部分", "Chapter", "Section", "Part",
            "一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、", "十、",
            "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10."
        ]
        
        return any(indicator in line for indicator in section_indicators) and len(line) < 100
    
    def _get_section_level(self, line: str) -> int:
        """获取章节级别"""
        if "第" in line and "章" in line:
            return 1
        elif "第" in line and "节" in line:
            return 2
        elif any(char in line for char in ["一、", "二、", "三、", "四、", "五、"]):
            return 2
        elif any(char in line for char in ["1.", "2.", "3.", "4.", "5."]):
            return 3
        else:
            return 1
    
    def _extract_simple_entities(self, text: str) -> List[Dict[str, Any]]:
        """简化的实体提取"""
        entities = []
        
        # 简单的关键词提取（可以替换为更复杂的NER）
        import re
        
        # 提取可能的人名
        person_pattern = r'[A-Z][a-z]+\s+[A-Z][a-z]+'
        persons = re.findall(person_pattern, text)
        
        for person in persons:
            entities.append({
                "text": person,
                "type": "PERSON",
                "confidence": 0.8
            })
        
        # 提取可能的组织名
        org_pattern = r'[A-Z][A-Za-z\s]+(?:公司|Corporation|Corp|Inc|Ltd|Limited)'
        orgs = re.findall(org_pattern, text)
        
        for org in orgs:
            entities.append({
                "text": org,
                "type": "ORGANIZATION",
                "confidence": 0.7
            })
        
        return entities
    
    async def process_document(
        self,
        project_id: str,
        document_id: str,
        document_path: str,
        document_type: str,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理文档的主入口"""
        start_time = datetime.utcnow()
        
        # 初始化状态
        initial_state = DocumentProcessingState(
            project_id=project_id,
            document_id=document_id,
            document_path=document_path,
            document_type=document_type,
            processing_config=processing_config or {},
            raw_content=None,
            parsed_content=None,
            document_structure=None,
            chunks=None,
            embeddings=None,
            entities=None,
            knowledge_graph=None,
            processing_status="pending",
            current_step="init",
            error_message=None,
            warnings=[],
            processing_time=0.0,
            result=None
        )
        
        try:
            # 执行工作流
            final_state = await self.graph.ainvoke(initial_state)
            
            # 计算总处理时间
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            final_state["processing_time"] = processing_time
            
            return final_state.get("result", {})
            
        except Exception as e:
            logger.error(f"文档处理工作流执行失败: {e}")
            
            error_result = {
                "document_id": document_id,
                "project_id": project_id,
                "processing_status": "failed",
                "error_message": str(e),
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
            
            return error_result


# 全局文档处理智能体实例
_document_processing_agent = None

def get_document_processing_agent() -> DocumentProcessingAgent:
    """获取文档处理智能体实例（单例模式）"""
    global _document_processing_agent
    if _document_processing_agent is None:
        _document_processing_agent = DocumentProcessingAgent()
    return _document_processing_agent 