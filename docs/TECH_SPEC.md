# DPA 智能知识引擎 - 技术规格文档 (TECH_SPEC)

> **版本**: v3.0  
> **更新日期**: 2024年12月18日  
> **状态**: 基于LangGraph/LangChain深度集成的知识引擎架构

## 1. 系统架构概览

### 1.1 智能知识引擎系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                   用户界面层 (UI Layer)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐   │
│  │研究工作台   │ │知识图谱     │ │项目管理     │ │报告生成   │   │
│  │(Next.js)    │ │可视化       │ │仪表板       │ │导出       │   │
│  │             │ │(D3.js)      │ │(React)      │ │(PDF/MD)   │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                   API网关层 (API Gateway Layer)                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐   │
│  │身份认证     │ │项目隔离     │ │API路由      │ │实时通信   │   │
│  │(JWT)        │ │(RBAC)       │ │(FastAPI)    │ │(WebSocket)│   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                   LangGraph智能体层 (Agent Layer)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐   │
│  │文档处理     │ │研究规划     │ │知识问答     │ │记忆管理   │   │
│  │智能体       │ │智能体       │ │智能体       │ │智能体     │   │
│  │(LangGraph)  │ │(LangGraph)  │ │(LangGraph)  │ │(LangGraph)│   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                   LangChain工具层 (Tools Layer)                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐   │
│  │文档解析工具 │ │向量检索工具 │ │图查询工具   │ │外部API   │   │
│  │(LangChain)  │ │(LangChain)  │ │(LangChain)  │ │工具       │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                   数据存储层 (Storage Layer)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐   │
│  │项目数据库   │ │向量数据库   │ │知识图谱     │ │文件存储   │   │
│  │(PostgreSQL) │ │(Qdrant)     │ │(Neo4j)      │ │(MinIO)    │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

- **LangGraph优先**: 所有复杂工作流均基于LangGraph状态机实现
- **LangChain深度集成**: 充分利用LangChain的工具生态和RAG能力
- **层次化知识索引**: 多维度、多层次的知识组织和检索
- **渐进式学习**: 项目记忆库支持持续学习和知识演化
- **精准溯源**: 每个回答都能准确追溯到原始文档位置
- **模块化设计**: 高内聚、低耦合的组件化架构

### 1.3 技术栈选型

#### 1.3.1 核心框架
- **LangGraph**: 智能体工作流编排引擎
- **LangChain**: RAG工具链和模型集成
- **FastAPI**: 高性能异步Web框架
- **Pydantic**: 数据验证和序列化

#### 1.3.2 AI/ML组件
- **Embedding模型**: OpenAI text-embedding-3-large / BGE-M3
- **语言模型**: OpenAI GPT-4o, Anthropic Claude-3.5, DeepSeek-V3
- **向量数据库**: Qdrant (支持混合检索)
- **图数据库**: Neo4j (知识图谱存储)

#### 1.3.3 数据存储
- **关系数据库**: PostgreSQL (项目元数据)
- **文档存储**: MinIO (S3兼容对象存储)
- **缓存**: Redis (会话和缓存管理)
- **搜索引擎**: Elasticsearch (全文检索)

#### 1.3.4 前端技术
- **框架**: Next.js 14 + TypeScript
- **UI组件**: shadcn/ui + Tailwind CSS
- **可视化**: D3.js + React Flow (知识图谱)
- **状态管理**: Zustand + React Query

## 2. 基于LangGraph的智能体架构

### 2.1 文档处理智能体 (Document Processing Agent)

#### 2.1.1 LangGraph工作流定义
```python
from langgraph import StateGraph, END
from langchain_core.tools import BaseTool
from typing import TypedDict, List

class DocumentProcessingState(TypedDict):
    """文档处理状态"""
    project_id: str
    document_path: str
    document_type: str
    raw_content: str
    parsed_content: dict
    chunks: List[dict]
    embeddings: List[List[float]]
    entities: List[dict]
    knowledge_graph: dict
    processing_status: str
    error_message: str

class DocumentProcessingAgent:
    """基于LangGraph的文档处理智能体"""
    
    def __init__(self):
        self.graph = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """构建文档处理工作流"""
        workflow = StateGraph(DocumentProcessingState)
        
        # 添加节点
        workflow.add_node("parse_document", self.parse_document)
        workflow.add_node("extract_structure", self.extract_structure)
        workflow.add_node("semantic_chunking", self.semantic_chunking)
        workflow.add_node("generate_embeddings", self.generate_embeddings)
        workflow.add_node("extract_entities", self.extract_entities)
        workflow.add_node("build_knowledge_graph", self.build_knowledge_graph)
        workflow.add_node("store_results", self.store_results)
        
        # 定义工作流
        workflow.set_entry_point("parse_document")
        workflow.add_edge("parse_document", "extract_structure")
        workflow.add_edge("extract_structure", "semantic_chunking")
        workflow.add_edge("semantic_chunking", "generate_embeddings")
        workflow.add_edge("generate_embeddings", "extract_entities")
        workflow.add_edge("extract_entities", "build_knowledge_graph")
        workflow.add_edge("build_knowledge_graph", "store_results")
        workflow.add_edge("store_results", END)
        
        return workflow.compile()
    
    async def parse_document(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """解析文档"""
        from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
        
        try:
            if state["document_path"].endswith('.pdf'):
                loader = PyPDFLoader(state["document_path"])
            elif state["document_path"].endswith('.docx'):
                loader = UnstructuredWordDocumentLoader(state["document_path"])
            else:
                raise ValueError(f"Unsupported document type: {state['document_path']}")
            
            documents = await loader.aload()
            raw_content = "\n".join([doc.page_content for doc in documents])
            
            state["raw_content"] = raw_content
            state["processing_status"] = "parsed"
            
        except Exception as e:
            state["error_message"] = str(e)
            state["processing_status"] = "error"
            
        return state
    
    async def semantic_chunking(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """语义分块"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_experimental.text_splitter import SemanticChunker
        from langchain_openai import OpenAIEmbeddings
        
        try:
            # 使用语义分块器
            embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            text_splitter = SemanticChunker(
                embeddings=embeddings,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=80
            )
            
            chunks = text_splitter.create_documents([state["raw_content"]])
            
            state["chunks"] = [
                {
                    "content": chunk.page_content,
                    "metadata": chunk.metadata,
                    "index": i
                }
                for i, chunk in enumerate(chunks)
            ]
            state["processing_status"] = "chunked"
            
        except Exception as e:
            state["error_message"] = str(e)
            state["processing_status"] = "error"
            
        return state
```

#### 2.1.2 LangChain工具集成
```python
from langchain_core.tools import tool
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings

@tool
def store_embeddings_tool(chunks: List[dict], project_id: str) -> dict:
    """存储向量嵌入到Qdrant"""
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # 创建文档对象
        documents = [
            Document(
                page_content=chunk["content"],
                metadata={
                    **chunk["metadata"],
                    "project_id": project_id,
                    "chunk_index": chunk["index"]
                }
            )
            for chunk in chunks
        ]
        
        # 存储到Qdrant
        vectorstore = Qdrant.from_documents(
            documents,
            embeddings,
            url="http://localhost:6333",
            collection_name=f"project_{project_id}"
        )
        
        return {"status": "success", "count": len(chunks)}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def extract_entities_tool(text: str) -> List[dict]:
    """提取命名实体"""
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_template("""
    从以下文本中提取关键实体，包括：
    - 人名 (PERSON)
    - 组织机构 (ORGANIZATION) 
    - 地点 (LOCATION)
    - 日期 (DATE)
    - 专业术语 (TERM)
    
    文本: {text}
    
    返回JSON格式:
    {{"entities": [{{"text": "实体", "type": "类型", "start": 0, "end": 2}}]}}
    """)
    
    chain = prompt | llm
    result = chain.invoke({"text": text[:2000]})  # 限制长度
    
    try:
        import json
                 return json.loads(result.content)["entities"]
     except:
         return []
```

### 2.2 研究规划智能体 (Research Planning Agent)

#### 2.2.1 基于DeepResearch的规划工作流
```python
from langgraph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class ResearchPlanningState(TypedDict):
    """研究规划状态"""
    research_query: str
    project_id: str
    existing_documents: List[str]
    research_plan: dict
    search_queries: List[str]
    current_step: int
    total_steps: int
    findings: List[dict]
    synthesis_report: str
    status: str

class ResearchPlanningAgent:
    """基于DeepResearch工作流的研究规划智能体"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建研究规划工作流"""
        workflow = StateGraph(ResearchPlanningState)
        
        # 添加节点 - 参考DeepResearch工作流
        workflow.add_node("analyze_query", self.analyze_research_query)
        workflow.add_node("create_plan", self.create_research_plan)
        workflow.add_node("generate_searches", self.generate_search_queries)
        workflow.add_node("execute_search", self.execute_search_step)
        workflow.add_node("synthesize_findings", self.synthesize_findings)
        workflow.add_node("generate_report", self.generate_final_report)
        
        # 定义工作流路径
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "create_plan")
        workflow.add_edge("create_plan", "generate_searches")
        workflow.add_edge("generate_searches", "execute_search")
        
        # 条件路径：继续搜索或进入综合阶段
        workflow.add_conditional_edges(
            "execute_search",
            self._should_continue_search,
            {
                "continue": "execute_search",
                "synthesize": "synthesize_findings"
            }
        )
        
        workflow.add_edge("synthesize_findings", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    async def analyze_research_query(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """分析研究查询"""
        prompt = ChatPromptTemplate.from_template("""
        分析以下研究查询，确定研究的范围、深度和关键方向：
        
        查询: {query}
        现有文档: {documents}
        
        请提供：
        1. 研究主题的核心概念
        2. 需要深入探索的子领域
        3. 可能的研究角度和方法
        4. 预期的研究深度和广度
        
        返回JSON格式的分析结果。
        """)
        
        chain = prompt | self.llm
        result = await chain.ainvoke({
            "query": state["research_query"],
            "documents": ", ".join(state["existing_documents"])
        })
        
        try:
            import json
            analysis = json.loads(result.content)
            state["status"] = "analyzed"
            state["research_analysis"] = analysis
        except Exception as e:
            state["status"] = "error"
            state["error"] = str(e)
            
        return state
    
    async def create_research_plan(self, state: ResearchPlanningState) -> ResearchPlanningState:
        """创建详细的研究计划"""
        prompt = ChatPromptTemplate.from_template("""
        基于研究分析，创建一个详细的分阶段研究计划：
        
        研究查询: {query}
        分析结果: {analysis}
        
        请创建包含以下要素的研究计划：
        1. 研究阶段划分（3-5个阶段）
        2. 每个阶段的具体目标
        3. 需要搜索的关键词和概念
        4. 预期的输出和里程碑
        5. 阶段间的依赖关系
        
        返回JSON格式的研究计划。
        """)
        
        chain = prompt | self.llm
        result = await chain.ainvoke({
            "query": state["research_query"],
            "analysis": state.get("research_analysis", {})
        })
        
        try:
            import json
            plan = json.loads(result.content)
            state["research_plan"] = plan
            state["total_steps"] = len(plan.get("stages", []))
            state["current_step"] = 0
            state["status"] = "planned"
        except Exception as e:
            state["status"] = "error"
            state["error"] = str(e)
            
        return state

### 2.3 知识问答智能体 (Knowledge QA Agent)

#### 2.3.1 RAG增强的问答系统
```python
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Qdrant
from langchain_core.output_parsers import JsonOutputParser

class KnowledgeQAState(TypedDict):
    """知识问答状态"""
    question: str
    project_id: str
    context_documents: List[str]
    retrieved_chunks: List[dict]
    answer: str
    sources: List[dict]
    confidence_score: float
    follow_up_questions: List[str]
    status: str

class KnowledgeQAAgent:
    """基于RAG的知识问答智能体"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建问答工作流"""
        workflow = StateGraph(KnowledgeQAState)
        
        workflow.add_node("analyze_question", self.analyze_question)
        workflow.add_node("retrieve_context", self.retrieve_relevant_context)
        workflow.add_node("rerank_results", self.rerank_retrieved_results)
        workflow.add_node("generate_answer", self.generate_contextual_answer)
        workflow.add_node("validate_answer", self.validate_answer_quality)
        workflow.add_node("generate_follow_ups", self.generate_follow_up_questions)
        
        workflow.set_entry_point("analyze_question")
        workflow.add_edge("analyze_question", "retrieve_context")
        workflow.add_edge("retrieve_context", "rerank_results")
        workflow.add_edge("rerank_results", "generate_answer")
        workflow.add_edge("generate_answer", "validate_answer")
        workflow.add_edge("validate_answer", "generate_follow_ups")
        workflow.add_edge("generate_follow_ups", END)
        
        return workflow.compile()
    
    async def retrieve_relevant_context(self, state: KnowledgeQAState) -> KnowledgeQAState:
        """检索相关上下文"""
        try:
            # 连接到项目特定的向量库
            vectorstore = Qdrant(
                client=QdrantClient(url="http://localhost:6333"),
                collection_name=f"project_{state['project_id']}",
                embeddings=self.embeddings
            )
            
            # 混合检索：向量相似度 + 关键词匹配
            retriever = vectorstore.as_retriever(
                search_type="mmr",  # 最大边际相关性
                search_kwargs={
                    "k": 10,
                    "fetch_k": 20,
                    "lambda_mult": 0.7
                }
            )
            
            # 检索相关文档块
            retrieved_docs = await retriever.aget_relevant_documents(state["question"])
            
            state["retrieved_chunks"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, 'score', 0.0)
                }
                for doc in retrieved_docs
            ]
            
            state["status"] = "retrieved"
            
        except Exception as e:
            state["status"] = "error"
            state["error"] = str(e)
            
        return state
    
    async def generate_contextual_answer(self, state: KnowledgeQAState) -> KnowledgeQAState:
        """生成基于上下文的答案"""
        # 构建上下文
        context = "\n\n".join([
            f"文档片段 {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(state["retrieved_chunks"][:5])
        ])
        
        prompt = ChatPromptTemplate.from_template("""
        基于以下上下文信息回答用户问题。请确保：
        1. 答案完全基于提供的上下文
        2. 明确引用相关的文档片段
        3. 如果上下文不足以回答问题，请诚实说明
        4. 提供准确的源文档引用
        
        上下文:
        {context}
        
        问题: {question}
        
        请以JSON格式返回答案：
        {{
            "answer": "详细答案",
            "sources": [
                {{"chunk_index": 1, "relevance": "high", "quote": "相关引用"}}
            ],
            "confidence": 0.85,
            "limitations": "回答的局限性说明"
        }}
        """)
        
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            result = await chain.ainvoke({
                "context": context,
                "question": state["question"]
            })
            
            state["answer"] = result["answer"]
            state["sources"] = result["sources"]
            state["confidence_score"] = result["confidence"]
            state["status"] = "answered"
            
        except Exception as e:
            state["status"] = "error"
            state["error"] = str(e)
            
        return state

### 2.4 记忆管理智能体 (Memory Management Agent)

#### 2.4.1 渐进式学习记忆系统
```python
class MemoryManagementState(TypedDict):
    """记忆管理状态"""
    project_id: str
    interaction_type: str  # "qa", "feedback", "annotation"
    content: dict
    user_feedback: dict
    memory_updates: List[dict]
    knowledge_evolution: dict
    status: str

class MemoryManagementAgent:
    """项目记忆管理智能体"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建记忆管理工作流"""
        workflow = StateGraph(MemoryManagementState)
        
        workflow.add_node("analyze_interaction", self.analyze_user_interaction)
        workflow.add_node("extract_insights", self.extract_learning_insights)
        workflow.add_node("update_memories", self.update_project_memories)
        workflow.add_node("evolve_knowledge", self.evolve_knowledge_base)
        workflow.add_node("optimize_retrieval", self.optimize_retrieval_strategy)
        
        workflow.set_entry_point("analyze_interaction")
        workflow.add_edge("analyze_interaction", "extract_insights")
        workflow.add_edge("extract_insights", "update_memories")
        workflow.add_edge("update_memories", "evolve_knowledge")
        workflow.add_edge("evolve_knowledge", "optimize_retrieval")
        workflow.add_edge("optimize_retrieval", END)
        
        return workflow.compile()
    
    async def extract_learning_insights(self, state: MemoryManagementState) -> MemoryManagementState:
        """提取学习洞察"""
        prompt = ChatPromptTemplate.from_template("""
        分析用户交互，提取可学习的洞察：
        
        交互类型: {interaction_type}
        内容: {content}
        用户反馈: {feedback}
        
        请识别：
        1. 用户的知识偏好和兴趣点
        2. 常见的问题模式和主题
        3. 需要改进的回答质量方面
        4. 新的概念关联和知识连接
        5. 用户的研究方法和思维模式
        
        返回JSON格式的洞察分析。
        """)
        
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            insights = await chain.ainvoke({
                "interaction_type": state["interaction_type"],
                "content": state["content"],
                "feedback": state.get("user_feedback", {})
            })
            
            state["learning_insights"] = insights
            state["status"] = "insights_extracted"
            
        except Exception as e:
            state["status"] = "error"
            state["error"] = str(e)
            
                 return state
```

## 3. 数据模型设计

### 3.1 Pydantic数据模型
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProjectType(str, Enum):
    """项目类型"""
    RESEARCH = "research"
    LITERATURE_REVIEW = "literature_review"
    TECHNICAL_ANALYSIS = "technical_analysis"
    LEGAL_REVIEW = "legal_review"

class DocumentType(str, Enum):
    """文档类型"""
    ACADEMIC_PAPER = "academic_paper"
    TECHNICAL_REPORT = "technical_report"
    LEGAL_DOCUMENT = "legal_document"
    MANUAL = "manual"
    BOOK_CHAPTER = "book_chapter"

class ProcessingStatus(str, Enum):
    """处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 核心数据模型
class User(BaseModel):
    """用户模型"""
    id: Optional[int] = None
    email: str = Field(..., description="用户邮箱")
    username: str = Field(..., description="用户名")
    hashed_password: str = Field(..., description="加密密码")
    is_active: bool = Field(default=True, description="是否激活")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Project(BaseModel):
    """项目模型"""
    id: Optional[int] = None
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    project_type: ProjectType = Field(..., description="项目类型")
    status: str = Field(default="active", description="项目状态")
    owner_id: int = Field(..., description="所属用户ID")
    settings: Dict[str, Any] = Field(default_factory=dict, description="项目设置")
    research_query: Optional[str] = Field(None, description="研究查询")
    research_plan: Optional[Dict[str, Any]] = Field(None, description="研究计划")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Document(BaseModel):
    """文档模型"""
    id: Optional[int] = None
    title: str = Field(..., description="文档标题")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_hash: str = Field(..., description="文件哈希")
    file_size: int = Field(..., description="文件大小")
    document_type: DocumentType = Field(..., description="文档类型")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    content: Optional[str] = Field(None, description="提取的文本内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    project_id: int = Field(..., description="所属项目ID")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Chunk(BaseModel):
    """文档块模型"""
    id: Optional[int] = None
    document_id: int = Field(..., description="所属文档ID")
    chunk_index: int = Field(..., description="块序号")
    content: str = Field(..., description="块内容")
    vector_id: Optional[str] = Field(None, description="向量ID")
    start_page: Optional[int] = Field(None, description="起始页码")
    end_page: Optional[int] = Field(None, description="结束页码")
    start_char: Optional[int] = Field(None, description="起始字符位置")
    end_char: Optional[int] = Field(None, description="结束字符位置")
    chunk_type: str = Field(default="text", description="块类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="块元数据")
    created_at: Optional[datetime] = None

class Conversation(BaseModel):
    """对话模型"""
    id: Optional[int] = None
    project_id: int = Field(..., description="所属项目ID")
    user_id: int = Field(..., description="用户ID")
    title: Optional[str] = Field(None, description="对话标题")
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="消息列表")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Entity(BaseModel):
    """实体模型"""
    id: Optional[int] = None
    text: str = Field(..., description="实体文本")
    entity_type: str = Field(..., description="实体类型")
    document_id: int = Field(..., description="所属文档ID")
    start_char: int = Field(..., description="起始位置")
    end_char: int = Field(..., description="结束位置")
    confidence: float = Field(default=1.0, description="置信度")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="实体元数据")

### 3.2 LangGraph状态模型
```python
class GlobalAgentState(TypedDict):
    """全局智能体状态"""
    project_id: str
    user_id: str
    session_id: str
    current_task: str
    task_history: List[dict]
    context_memory: dict
    error_state: Optional[dict]
    
class DocumentProcessingResult(BaseModel):
    """文档处理结果"""
    document_id: int
    chunks_created: int
    entities_extracted: int
    embeddings_stored: bool
    knowledge_graph_updated: bool
    processing_time: float
    status: ProcessingStatus
    error_message: Optional[str] = None

class ResearchPlanResult(BaseModel):
    """研究规划结果"""
    plan_id: str
    stages: List[dict]
    total_estimated_time: int
    key_concepts: List[str]
    search_strategies: List[str]
    success_criteria: List[str]

class QAResult(BaseModel):
    """问答结果"""
    question: str
    answer: str
    sources: List[dict]
    confidence_score: float
    response_time: float
    follow_up_questions: List[str]
    limitations: Optional[str] = None

## 4. API设计

### 4.1 RESTful API端点
```python
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer
from typing import List, Optional

app = FastAPI(title="DPA智能知识引擎", version="3.0.0")
security = HTTPBearer()

# 项目管理API
@app.post("/api/v1/projects", response_model=Project)
async def create_project(
    project: Project,
    current_user: User = Depends(get_current_user)
):
    """创建新项目"""
    pass

@app.get("/api/v1/projects", response_model=List[Project])
async def list_projects(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """获取项目列表"""
    pass

@app.get("/api/v1/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取项目详情"""
    pass

# 文档管理API
@app.post("/api/v1/projects/{project_id}/documents")
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    document_type: DocumentType = DocumentType.ACADEMIC_PAPER,
    current_user: User = Depends(get_current_user)
):
    """上传文档"""
    # 启动文档处理智能体
    agent = DocumentProcessingAgent()
    result = await agent.graph.ainvoke({
        "project_id": str(project_id),
        "document_path": file.filename,
        "document_type": document_type.value,
        "processing_status": "pending"
    })
    return result

@app.get("/api/v1/projects/{project_id}/documents", response_model=List[Document])
async def list_documents(
    project_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取文档列表"""
    pass

# 知识问答API
@app.post("/api/v1/projects/{project_id}/qa")
async def ask_question(
    project_id: int,
    question: str,
    context_documents: Optional[List[int]] = None,
    current_user: User = Depends(get_current_user)
):
    """知识问答"""
    agent = KnowledgeQAAgent()
    result = await agent.graph.ainvoke({
        "question": question,
        "project_id": str(project_id),
        "context_documents": context_documents or [],
        "status": "pending"
    })
    return result

# 研究规划API
@app.post("/api/v1/projects/{project_id}/research-plan")
async def create_research_plan(
    project_id: int,
    research_query: str,
    current_user: User = Depends(get_current_user)
):
    """创建研究规划"""
    agent = ResearchPlanningAgent()
    result = await agent.graph.ainvoke({
        "research_query": research_query,
        "project_id": str(project_id),
        "existing_documents": [],
        "status": "pending"
    })
    return result

@app.get("/api/v1/projects/{project_id}/research-plan")
async def get_research_plan(
    project_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取研究规划"""
    pass

# 记忆管理API
@app.post("/api/v1/projects/{project_id}/memory/feedback")
async def submit_feedback(
    project_id: int,
    interaction_id: str,
    feedback: dict,
    current_user: User = Depends(get_current_user)
):
    """提交用户反馈"""
    agent = MemoryManagementAgent()
    result = await agent.graph.ainvoke({
        "project_id": str(project_id),
        "interaction_type": "feedback",
        "content": {"interaction_id": interaction_id},
        "user_feedback": feedback,
        "status": "pending"
    })
    return result

### 4.2 WebSocket实时通信
```python
from fastapi import WebSocket, WebSocketDisconnect
import json

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/{project_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int, user_id: int):
    """WebSocket端点用于实时通信"""
    client_id = f"{project_id}_{user_id}"
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            if message["type"] == "document_processing_status":
                # 发送文档处理状态更新
                await manager.send_personal_message({
                    "type": "processing_update",
                    "status": "processing",
                    "progress": 50
                }, client_id)
            
            elif message["type"] == "qa_request":
                # 处理实时问答请求
                agent = KnowledgeQAAgent()
                result = await agent.graph.ainvoke({
                    "question": message["question"],
                    "project_id": str(project_id),
                    "status": "pending"
                })
                
                await manager.send_personal_message({
                    "type": "qa_response",
                    "result": result
                }, client_id)
                
         except WebSocketDisconnect:
         manager.disconnect(client_id)
```

## 5. 部署架构

### 5.1 Docker Compose开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  # 后端API服务
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/dpa_dev
      - QDRANT_URL=http://qdrant:6333
      - NEO4J_URL=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - qdrant
      - neo4j
      - redis
    volumes:
      - ./backend:/app
      - ./data:/app/data
    
  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    
  # PostgreSQL数据库
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dpa_dev
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    
  # Qdrant向量数据库
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    
  # Neo4j图数据库
  neo4j:
    image: neo4j:5.15
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    
  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    
  # MinIO对象存储
  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  postgres_data:
  qdrant_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
  minio_data:
```

### 5.2 LangGraph工作流编排
```python
# src/graphs/master_workflow.py
from langgraph import StateGraph, END
from typing import TypedDict, List, Dict, Any

class MasterWorkflowState(TypedDict):
    """主工作流状态"""
    project_id: str
    user_id: str
    task_type: str  # "document_upload", "research_plan", "qa", "memory_update"
    input_data: Dict[str, Any]
    current_agent: str
    agent_results: Dict[str, Any]
    final_result: Dict[str, Any]
    error_state: Dict[str, Any]
    status: str

class MasterWorkflow:
    """主工作流编排器"""
    
    def __init__(self):
        self.document_agent = DocumentProcessingAgent()
        self.research_agent = ResearchPlanningAgent()
        self.qa_agent = KnowledgeQAAgent()
        self.memory_agent = MemoryManagementAgent()
        self.graph = self._build_master_workflow()
    
    def _build_master_workflow(self) -> StateGraph:
        """构建主工作流"""
        workflow = StateGraph(MasterWorkflowState)
        
        # 添加路由节点
        workflow.add_node("route_task", self.route_to_agent)
        workflow.add_node("document_processing", self.handle_document_processing)
        workflow.add_node("research_planning", self.handle_research_planning)
        workflow.add_node("knowledge_qa", self.handle_knowledge_qa)
        workflow.add_node("memory_management", self.handle_memory_management)
        workflow.add_node("aggregate_results", self.aggregate_results)
        workflow.add_node("error_handling", self.handle_errors)
        
        # 设置工作流路径
        workflow.set_entry_point("route_task")
        
        # 条件路由
        workflow.add_conditional_edges(
            "route_task",
            self._determine_agent,
            {
                "document": "document_processing",
                "research": "research_planning", 
                "qa": "knowledge_qa",
                "memory": "memory_management",
                "error": "error_handling"
            }
        )
        
        # 所有智能体完成后聚合结果
        workflow.add_edge("document_processing", "aggregate_results")
        workflow.add_edge("research_planning", "aggregate_results")
        workflow.add_edge("knowledge_qa", "aggregate_results")
        workflow.add_edge("memory_management", "aggregate_results")
        workflow.add_edge("error_handling", "aggregate_results")
        workflow.add_edge("aggregate_results", END)
        
        return workflow.compile()
    
    def _determine_agent(self, state: MasterWorkflowState) -> str:
        """确定使用哪个智能体"""
        task_type = state["task_type"]
        
        if task_type == "document_upload":
            return "document"
        elif task_type == "research_plan":
            return "research"
        elif task_type == "qa":
            return "qa"
        elif task_type == "memory_update":
            return "memory"
        else:
            return "error"
    
    async def handle_document_processing(self, state: MasterWorkflowState) -> MasterWorkflowState:
        """处理文档处理任务"""
        try:
            result = await self.document_agent.graph.ainvoke({
                "project_id": state["project_id"],
                "document_path": state["input_data"]["file_path"],
                "document_type": state["input_data"]["document_type"],
                "processing_status": "pending"
            })
            
            state["agent_results"]["document"] = result
            state["current_agent"] = "document"
            state["status"] = "completed"
            
        except Exception as e:
            state["error_state"] = {"agent": "document", "error": str(e)}
            state["status"] = "error"
            
        return state

### 5.3 监控和日志系统
```python
# src/utils/monitoring.py
import logging
import time
from functools import wraps
from typing import Dict, Any
from langsmith import traceable
from prometheus_client import Counter, Histogram, Gauge
import structlog

# Prometheus指标
REQUEST_COUNT = Counter('dpa_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('dpa_request_duration_seconds', 'Request duration')
ACTIVE_AGENTS = Gauge('dpa_active_agents', 'Number of active agents')
DOCUMENT_PROCESSING_TIME = Histogram('dpa_document_processing_seconds', 'Document processing time')

# 结构化日志配置
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def monitor_agent_performance(agent_name: str):
    """智能体性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        @traceable(name=f"{agent_name}_execution")
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            ACTIVE_AGENTS.inc()
            
            try:
                logger.info(
                    "agent_execution_started",
                    agent=agent_name,
                    function=func.__name__
                )
                
                result = await func(*args, **kwargs)
                
                duration = time.time() - start_time
                REQUEST_DURATION.observe(duration)
                
                logger.info(
                    "agent_execution_completed",
                    agent=agent_name,
                    function=func.__name__,
                    duration=duration,
                    status="success"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "agent_execution_failed",
                    agent=agent_name,
                    function=func.__name__,
                    duration=duration,
                    error=str(e),
                    status="error"
                )
                
                raise
                
            finally:
                ACTIVE_AGENTS.dec()
                
        return wrapper
    return decorator

class LangGraphTracer:
    """LangGraph执行追踪器"""
    
    def __init__(self):
        self.execution_logs = []
    
    def trace_node_execution(self, node_name: str, state: Dict[str, Any], result: Dict[str, Any]):
        """追踪节点执行"""
        log_entry = {
            "timestamp": time.time(),
            "node": node_name,
            "input_state": state,
            "output_state": result,
            "execution_time": time.time()
        }
        
        self.execution_logs.append(log_entry)
        
        logger.info(
            "langgraph_node_executed",
            node=node_name,
            state_keys=list(state.keys()),
            result_keys=list(result.keys())
        )

## 6. 实施计划

### 6.1 开发里程碑（9个月计划）

#### 阶段1：基础架构搭建（月1-2）
**目标**: 建立基于LangGraph/LangChain的核心架构

**关键任务**:
- [ ] 搭建Docker开发环境
- [ ] 实现基础数据模型和数据库连接
- [ ] 创建文档处理智能体基础框架
- [ ] 集成OpenAI/Anthropic API
- [ ] 建立Qdrant向量数据库连接
- [ ] 实现基础的文档上传和解析功能

**验收标准**:
- 能够成功上传PDF文档并提取文本
- 文档内容能够存储到向量数据库
- 基础的LangGraph工作流能够正常运行

#### 阶段2：核心智能体开发（月3-4）
**目标**: 完成四大核心智能体的基础功能

**关键任务**:
- [ ] 完善文档处理智能体（语义分块、实体提取）
- [ ] 实现知识问答智能体（RAG检索、答案生成）
- [ ] 开发研究规划智能体（基于DeepResearch工作流）
- [ ] 创建记忆管理智能体（用户反馈学习）
- [ ] 建立智能体间的协调机制

**验收标准**:
- 能够对单篇文档进行精准问答（溯源率>95%）
- 能够生成基础的研究规划
- 用户反馈能够被正确记录和学习

#### 阶段3：多文档知识整合（月5-6）
**目标**: 实现跨文档的知识整合和关联分析

**关键任务**:
- [ ] 实现跨文档概念关联
- [ ] 建立Neo4j知识图谱存储
- [ ] 开发概念演化追踪
- [ ] 实现多文档对比分析
- [ ] 优化检索策略（混合检索、重排序）

**验收标准**:
- 能够回答需要整合多个文档信息的复杂问题
- 知识图谱能够可视化概念关系
- 检索准确率达到85%以上

#### 阶段4：前端界面和用户体验（月7-8）
**目标**: 完成用户友好的Web界面

**关键任务**:
- [ ] 开发Next.js前端应用
- [ ] 实现项目管理界面
- [ ] 创建文档上传和管理界面
- [ ] 开发知识问答对话界面
- [ ] 实现知识图谱可视化
- [ ] 建立WebSocket实时通信

**验收标准**:
- 界面响应速度<2秒
- 支持实时文档处理状态更新
- 知识图谱可视化清晰易懂

#### 阶段5：系统优化和测试（月9）
**目标**: 系统性能优化和全面测试

**关键任务**:
- [ ] 性能优化（缓存、异步处理）
- [ ] 全面的单元测试和集成测试
- [ ] 用户验收测试
- [ ] 安全性测试和加固
- [ ] 部署脚本和文档完善

**验收标准**:
- 测试覆盖率>85%
- 系统响应时间满足PRD要求
- 通过安全性评估

### 6.2 风险缓解策略

**技术风险**:
- **API稳定性**: 集成多个LLM提供商，实现自动故障转移
- **向量检索性能**: 使用Qdrant的高性能特性，实现分片和缓存
- **知识图谱复杂度**: 渐进式构建，从简单关系开始

**资源风险**:
- **API成本控制**: 实现智能缓存和批处理，监控使用量
- **开发进度**: 采用敏捷开发，每两周一个迭代

**质量风险**:
- **答案准确性**: 建立评估数据集，持续监控准确率
- **用户体验**: 早期用户测试，快速迭代改进

### 6.3 成功指标

**技术指标**:
- 文档处理成功率 > 98%
- 问答响应时间 < 3秒
- 溯源准确率 > 95%
- 系统可用性 > 99.5%

**用户指标**:
- 用户满意度 > 4.0/5.0
- 月活跃用户留存率 > 60%
- 平均会话时长 > 15分钟

**业务指标**:
 - 研究效率提升 > 70%
 - 用户采纳率 > 80%
 - 错误报告 < 5%

---

## 总结

本技术规格文档基于最新的PRD需求，充分利用LangGraph和LangChain框架，设计了一个现代化的智能知识引擎系统。核心特点包括：

1. **LangGraph优先**: 所有复杂工作流均基于LangGraph状态机实现，确保可维护性和可扩展性
2. **LangChain深度集成**: 充分利用LangChain的RAG能力和工具生态，减少重复开发
3. **智能体架构**: 四大核心智能体分工协作，实现文档处理、研究规划、知识问答和记忆管理
4. **现代化技术栈**: 基于FastAPI、Next.js、Qdrant、Neo4j等现代技术构建
5. **完整的监控体系**: 集成LangSmith、Prometheus等监控工具，确保系统可观测性

该架构设计既满足了PRD中的所有功能需求，又通过充分复用成熟框架大大降低了开发复杂度和维护成本。
