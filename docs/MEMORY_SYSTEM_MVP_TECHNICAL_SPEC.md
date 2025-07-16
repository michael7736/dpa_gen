# DPA记忆系统MVP技术规格

## 1. MVP架构简化

### 1.1 简化的状态定义

```python
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import MessagesState, add_messages

class MVPCognitiveState(TypedDict):
    """MVP版认知状态 - 最小可行集"""
    
    # 基础交互
    messages: Annotated[List[BaseMessage], add_messages]
    thread_id: str
    project_id: str
    
    # 简化的记忆层
    working_memory: Dict[str, Any]      # 最多20项
    recent_documents: List[Dict]        # 最近10个文档
    
    # 处理状态
    current_chunk: Dict                 # 当前处理的文本块
    query_result: Dict                  # 查询结果
    
    # Memory Bank快照
    memory_bank_snapshot: Dict          # 当前记忆库状态
    
    # 错误处理
    last_error: Optional[str]
```

### 1.2 核心工作流节点

```python
# MVP工作流 - 5个核心节点
CORE_NODES = {
    "ingest": "文档摄入",
    "chunk": "文本分块", 
    "embed": "向量化",
    "retrieve": "检索",
    "respond": "生成响应"
}

# 简化的边连接
EDGES = [
    ("ingest", "chunk"),
    ("chunk", "embed"),
    ("embed", "retrieve"),
    ("retrieve", "respond")
]
```

## 2. Memory Bank MVP实现

### 2.1 目录结构（简化版）

```
memory-bank/
├── project_{id}/
│   ├── metadata.json         # 项目元数据
│   ├── context.md           # 当前上下文（最大10KB）
│   ├── concepts.json        # 关键概念列表
│   ├── summary.md          # 动态摘要（最大5KB）
│   └── changelog.jsonl     # 变更日志
```

### 2.2 核心API

```python
class MVPMemoryBank:
    """最小化Memory Bank实现"""
    
    def __init__(self, base_path: str = "./memory-bank"):
        self.base_path = Path(base_path)
        self.max_context_size = 10 * 1024  # 10KB
        self.max_summary_size = 5 * 1024   # 5KB
    
    async def init_project(self, project_id: str) -> None:
        """初始化项目记忆库"""
        project_path = self.base_path / f"project_{project_id}"
        project_path.mkdir(parents=True, exist_ok=True)
        
        # 创建初始文件
        metadata = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "status": "active"
        }
        
        await self.write_json(project_path / "metadata.json", metadata)
        await self.write_file(project_path / "context.md", "# Project Context\n")
        await self.write_file(project_path / "summary.md", "# Summary\n")
        await self.write_json(project_path / "concepts.json", [])
    
    async def update_context(self, project_id: str, new_content: str) -> None:
        """更新项目上下文（保持大小限制）"""
        context_path = self._get_path(project_id, "context.md")
        current = await self.read_file(context_path)
        
        # 简单的FIFO策略保持大小
        updated = self._merge_content(current, new_content, self.max_context_size)
        
        await self.write_file(context_path, updated)
        await self._log_change(project_id, "context_updated", len(updated))
    
    async def add_concepts(self, project_id: str, concepts: List[Dict]) -> None:
        """添加关键概念"""
        concepts_path = self._get_path(project_id, "concepts.json")
        current = await self.read_json(concepts_path)
        
        # 简单去重
        existing_names = {c["name"] for c in current}
        new_concepts = [c for c in concepts if c["name"] not in existing_names]
        
        updated = current + new_concepts
        # 限制概念数量
        if len(updated) > 100:
            updated = updated[-100:]  # 保留最新的100个
        
        await self.write_json(concepts_path, updated)
        await self._log_change(project_id, "concepts_added", len(new_concepts))
    
    async def update_summary(self, project_id: str, summary: str) -> None:
        """更新摘要（渐进式）"""
        summary_path = self._get_path(project_id, "summary.md")
        
        # 确保不超过大小限制
        if len(summary) > self.max_summary_size:
            summary = summary[:self.max_summary_size] + "\n\n[Truncated...]"
        
        await self.write_file(summary_path, summary)
        await self._log_change(project_id, "summary_updated", len(summary))
    
    async def get_snapshot(self, project_id: str) -> Dict:
        """获取记忆库快照"""
        project_path = self.base_path / f"project_{project_id}"
        
        if not project_path.exists():
            return {}
        
        return {
            "metadata": await self.read_json(project_path / "metadata.json"),
            "context": await self.read_file(project_path / "context.md"),
            "concepts": await self.read_json(project_path / "concepts.json"),
            "summary": await self.read_file(project_path / "summary.md"),
            "last_updated": self._get_last_modified(project_path)
        }
```

## 3. 三阶段检索MVP实现

### 3.1 简化的检索策略

```python
class MVPHybridRetriever:
    """MVP版混合检索器"""
    
    def __init__(self):
        self.vector_store = QdrantClient(url=settings.qdrant.url)
        self.graph_db = Neo4jDriver(uri=settings.neo4j.uri)
        self.memory_bank = MVPMemoryBank()
        
        # MVP限制
        self.max_vector_results = 10
        self.max_graph_hops = 1
        self.max_memory_items = 5
    
    async def retrieve(self, query: str, project_id: str) -> Dict:
        """三阶段检索"""
        
        # Stage 1: 向量检索（简单语义搜索）
        vector_results = await self.vector_search(
            query=query,
            collection=f"project_{project_id}",
            limit=self.max_vector_results
        )
        
        # Stage 2: 图扩展（仅1跳）
        if vector_results:
            entry_ids = [r["id"] for r in vector_results[:3]]  # 只用前3个
            graph_context = await self.graph_expand_simple(
                entry_ids=entry_ids,
                project_id=project_id
            )
        else:
            graph_context = []
        
        # Stage 3: Memory Bank增强
        memory_context = await self.memory_bank_enhance(
            query=query,
            project_id=project_id
        )
        
        # 简单融合
        return self.simple_fusion(vector_results, graph_context, memory_context)
    
    async def vector_search(self, query: str, collection: str, limit: int) -> List[Dict]:
        """基础向量搜索"""
        # 生成查询嵌入
        query_embedding = await self.embed_text(query)
        
        # Qdrant搜索
        results = self.vector_store.search(
            collection_name=collection,
            query_vector=query_embedding,
            limit=limit
        )
        
        return [
            {
                "id": r.id,
                "content": r.payload.get("content", ""),
                "score": r.score,
                "metadata": r.payload.get("metadata", {})
            }
            for r in results
        ]
    
    async def graph_expand_simple(self, entry_ids: List[str], project_id: str) -> List[Dict]:
        """简化的图扩展 - 仅1跳"""
        
        # 简单的Cypher查询
        query = """
        MATCH (n:Chunk {project_id: $project_id})
        WHERE n.id IN $entry_ids
        MATCH (n)-[r]-(neighbor:Chunk)
        WHERE neighbor.project_id = $project_id
        RETURN DISTINCT neighbor.id as id, 
               neighbor.content as content,
               type(r) as relationship,
               count(r) as connection_count
        ORDER BY connection_count DESC
        LIMIT 10
        """
        
        with self.graph_db.session() as session:
            results = session.run(query, {
                "project_id": project_id,
                "entry_ids": entry_ids
            })
            
            return [
                {
                    "id": record["id"],
                    "content": record["content"],
                    "relationship": record["relationship"],
                    "relevance": 0.5  # 固定相关性分数
                }
                for record in results
            ]
    
    async def memory_bank_enhance(self, query: str, project_id: str) -> Dict:
        """Memory Bank增强"""
        snapshot = await self.memory_bank.get_snapshot(project_id)
        
        if not snapshot:
            return {}
        
        # 简单的关键词匹配增强
        relevant_concepts = self._match_concepts(query, snapshot.get("concepts", []))
        
        return {
            "current_context": snapshot.get("context", "")[:500],  # 前500字符
            "relevant_concepts": relevant_concepts[:5],
            "summary_excerpt": snapshot.get("summary", "")[:300]
        }
    
    def simple_fusion(self, vector_results: List, graph_results: List, memory_context: Dict) -> Dict:
        """简单的结果融合"""
        
        # 合并所有内容
        all_chunks = []
        
        # 添加向量结果
        for r in vector_results[:5]:
            all_chunks.append({
                "content": r["content"],
                "score": r["score"],
                "source": "vector"
            })
        
        # 添加图结果
        for r in graph_results[:3]:
            all_chunks.append({
                "content": r["content"],
                "score": r["relevance"],
                "source": "graph"
            })
        
        # 按分数排序
        all_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "chunks": all_chunks[:5],  # 最多返回5个
            "memory_context": memory_context,
            "total_results": len(all_chunks)
        }
```

## 4. 文档处理MVP

### 4.1 简化的文档处理器

```python
class MVPDocumentProcessor:
    """MVP版文档处理器"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-small")  # 使用小模型
    
    async def process_document(self, file_path: str, project_id: str) -> Dict:
        """处理单个文档"""
        
        # 1. 加载文档
        content = await self.load_document(file_path)
        
        # 2. 基础元数据
        metadata = {
            "file_name": Path(file_path).name,
            "file_size": Path(file_path).stat().st_size,
            "processed_at": datetime.now().isoformat(),
            "project_id": project_id
        }
        
        # 3. 简单分块
        chunks = self.simple_chunk(content)
        
        # 4. 批量嵌入
        embeddings = await self.batch_embed(chunks)
        
        # 5. 存储
        stored_ids = await self.store_chunks(chunks, embeddings, metadata)
        
        # 6. 更新Memory Bank
        await self.update_memory_bank(project_id, metadata, chunks[:5])  # 只记录前5个块
        
        return {
            "success": True,
            "document_id": metadata["file_name"],
            "chunks_created": len(chunks),
            "storage_ids": stored_ids
        }
    
    def simple_chunk(self, content: str) -> List[str]:
        """简单的固定大小分块"""
        chunks = []
        
        # 使用RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        return splitter.split_text(content)
    
    async def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        # 分批处理避免超时
        batch_size = 20
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.embedder.aembed_documents(batch)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
```

## 5. API接口设计

### 5.1 最小化API

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="DPA Memory System MVP")

class ProcessDocumentRequest(BaseModel):
    file_path: str
    project_id: str

class QueryRequest(BaseModel):
    query: str
    project_id: str

class ProjectInitRequest(BaseModel):
    project_id: str
    project_name: str

@app.post("/api/v1/projects/init")
async def init_project(request: ProjectInitRequest):
    """初始化项目"""
    try:
        memory_bank = MVPMemoryBank()
        await memory_bank.init_project(request.project_id)
        return {"status": "success", "project_id": request.project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/documents/process")
async def process_document(request: ProcessDocumentRequest):
    """处理文档"""
    processor = MVPDocumentProcessor()
    result = await processor.process_document(
        request.file_path, 
        request.project_id
    )
    return result

@app.post("/api/v1/query")
async def query(request: QueryRequest):
    """查询接口"""
    # 创建工作流
    app = build_mvp_workflow()
    
    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content=request.query)],
        "project_id": request.project_id,
        "thread_id": str(uuid.uuid4())
    }
    
    # 执行查询
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}
    result = await app.ainvoke(initial_state, config)
    
    return {
        "answer": result["messages"][-1].content,
        "sources": result.get("query_result", {}).get("chunks", []),
        "thread_id": initial_state["thread_id"]
    }

@app.get("/api/v1/projects/{project_id}/memory")
async def get_memory_snapshot(project_id: str):
    """获取记忆快照"""
    memory_bank = MVPMemoryBank()
    snapshot = await memory_bank.get_snapshot(project_id)
    return snapshot
```

## 6. 测试策略

### 6.1 核心测试用例

```python
# tests/test_mvp_integration.py

async def test_end_to_end_flow():
    """端到端测试"""
    
    # 1. 初始化项目
    project_id = "test_project"
    memory_bank = MVPMemoryBank()
    await memory_bank.init_project(project_id)
    
    # 2. 处理文档
    processor = MVPDocumentProcessor()
    result = await processor.process_document(
        "tests/fixtures/sample.txt",
        project_id
    )
    assert result["success"]
    
    # 3. 执行查询
    retriever = MVPHybridRetriever()
    results = await retriever.retrieve(
        "What is the main topic?",
        project_id
    )
    assert len(results["chunks"]) > 0
    
    # 4. 检查Memory Bank
    snapshot = await memory_bank.get_snapshot(project_id)
    assert "concepts" in snapshot
    assert len(snapshot["concepts"]) > 0
```

### 6.2 性能基准

```python
# benchmarks/mvp_performance.py

async def benchmark_document_processing():
    """文档处理性能测试"""
    processor = MVPDocumentProcessor()
    
    # 测试不同大小的文档
    sizes = [1000, 5000, 10000, 50000]  # 字符数
    
    for size in sizes:
        content = "测试内容 " * (size // 8)
        start = time.time()
        
        chunks = processor.simple_chunk(content)
        embeddings = await processor.batch_embed(chunks)
        
        elapsed = time.time() - start
        rate = size / elapsed
        
        print(f"Size: {size}, Time: {elapsed:.2f}s, Rate: {rate:.0f} chars/s")

async def benchmark_retrieval():
    """检索性能测试"""
    retriever = MVPHybridRetriever()
    
    queries = [
        "简单查询",
        "这是一个更长的查询，包含更多的上下文信息",
        "深度学习 AND 自然语言处理 AND 应用"
    ]
    
    for query in queries:
        start = time.time()
        results = await retriever.retrieve(query, "test_project")
        elapsed = time.time() - start
        
        print(f"Query: {query[:20]}..., Time: {elapsed*1000:.0f}ms")
```

## 7. 部署配置

### 7.1 最小化Docker配置

```yaml
# docker-compose-mvp.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dpa_mvp
      POSTGRES_USER: dpa
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_dbms_memory_heap_max__size: 1G
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  
  dpa_mvp:
    build: 
      context: .
      dockerfile: Dockerfile.mvp
    environment:
      DATABASE_URL: postgresql://dpa:${POSTGRES_PASSWORD}@postgres:5432/dpa_mvp
      NEO4J_URI: bolt://neo4j:7687
      QDRANT_URL: http://qdrant:6333
    depends_on:
      - postgres
      - neo4j
      - qdrant
    ports:
      - "8000:8000"
    volumes:
      - ./memory-bank:/app/memory-bank

volumes:
  postgres_data:
  neo4j_data:
  qdrant_data:
```

## 8. 监控和日志

### 8.1 简单监控指标

```python
# monitoring/mvp_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 基础指标
document_processed = Counter(
    'dpa_documents_processed_total',
    'Total documents processed'
)

query_duration = Histogram(
    'dpa_query_duration_seconds',
    'Query duration in seconds'
)

memory_bank_size = Gauge(
    'dpa_memory_bank_size_bytes',
    'Memory bank size in bytes',
    ['project_id']
)

active_projects = Gauge(
    'dpa_active_projects',
    'Number of active projects'
)
```

## 9. 快速启动指南

```bash
# 1. 克隆代码
git clone <repo>
cd dpa-mvp

# 2. 创建环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements-mvp.txt

# 4. 启动服务
docker-compose -f docker-compose-mvp.yml up -d

# 5. 初始化数据库
python scripts/init_mvp_db.py

# 6. 运行API服务
uvicorn src.api.main:app --reload

# 7. 测试
curl -X POST http://localhost:8000/api/v1/projects/init \
  -H "Content-Type: application/json" \
  -d '{"project_id": "test", "project_name": "Test Project"}'
```

## 10. MVP限制说明

1. **内存限制**
   - 工作记忆：最多20项
   - Memory Bank：每个文件最大10KB
   - 概念列表：最多100个

2. **功能限制**
   - 仅支持1跳图遍历
   - 使用标准文本分块
   - 简单的结果融合
   - 基础错误处理

3. **性能目标**
   - 文档处理：>1K tokens/秒
   - 查询响应：<500ms
   - 并发用户：10

通过这个MVP实现，我们可以在5天内交付一个功能完整的认知记忆系统原型，验证核心概念的可行性。