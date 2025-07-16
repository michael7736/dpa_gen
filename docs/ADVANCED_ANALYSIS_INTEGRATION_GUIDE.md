# 高级文档分析器集成指南

## 概述

本指南说明了如何将高级文档深度分析器（Advanced Document Analyzer）集成到DPA系统中，以及如何使用新的API端点。

## 集成完成的功能

### 1. 核心模块

- **AdvancedDocumentAnalyzer** (`src/graphs/advanced_document_analyzer.py`)
  - 实现六阶段分析方法论
  - 支持五种分析深度级别
  - 集成智能分块和缓存机制

### 2. 数据模型

- **DocumentAnalysis** (`src/models/analysis.py`)
  - SQLAlchemy模型用于持久化分析结果
  - 包含完整的分析状态跟踪
  - 支持JSON格式的详细报告存储

### 3. API端点

- **Analysis Routes** (`src/api/routes/analysis.py`)
  - POST `/api/v1/analysis/start` - 启动文档分析
  - GET `/api/v1/analysis/status/{id}` - 获取分析状态
  - GET `/api/v1/analysis/results/{id}` - 获取分析结果
  - POST `/api/v1/analysis/analyze-text` - 快速文本分析
  - GET `/api/v1/analysis/list` - 列出分析任务
  - GET `/api/v1/analysis/templates` - 获取分析模板

## 使用指南

### 1. 启动服务

```bash
# 确保数据库已初始化
python scripts/create_analysis_tables.sql

# 启动API服务
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 快速文本分析

```python
import requests

# 分析文本内容
response = requests.post(
    "http://localhost:8000/api/v1/analysis/analyze-text?user_id=test_user",
    json={
        "content": "要分析的文本内容...",
        "title": "测试分析",
        "analysis_depth": "basic",
        "analysis_goal": "理解文本主要内容"
    }
)

result = response.json()
print(result["executive_summary"])
```

### 3. 文档深度分析

```python
# 启动文档分析
response = requests.post(
    "http://localhost:8000/api/v1/analysis/start?user_id=test_user",
    json={
        "document_id": "your-document-id",
        "project_id": "your-project-id",
        "analysis_depth": "comprehensive",
        "analysis_goal": "深入理解文档内容并提取可行动的洞察"
    }
)

analysis_id = response.json()["analysis_id"]

# 查询分析进度
status_response = requests.get(
    f"http://localhost:8000/api/v1/analysis/status/{analysis_id}"
)
print(status_response.json())

# 获取分析结果
results_response = requests.get(
    f"http://localhost:8000/api/v1/analysis/results/{analysis_id}?include_details=true"
)
analysis_results = results_response.json()
```

### 4. 使用分析模板

```python
# 获取可用模板
templates_response = requests.get(
    "http://localhost:8000/api/v1/analysis/templates"
)
templates = templates_response.json()["templates"]

# 使用学术论文模板
academic_template = next(t for t in templates if t["id"] == "academic_paper")
response = requests.post(
    "http://localhost:8000/api/v1/analysis/start?user_id=test_user",
    json={
        "document_id": "your-document-id",
        "project_id": "your-project-id",
        "analysis_depth": academic_template["analysis_depth"],
        "analysis_goal": "分析研究方法和主要贡献"
    }
)
```

## 分析深度级别说明

### 1. Basic（基础）
- 时间：10-30秒
- 功能：元数据提取、基本摘要
- 适用：快速预览

### 2. Standard（标准）
- 时间：30-60秒
- 功能：结构分析、主题提取、关键概念
- 适用：常规文档理解

### 3. Deep（深度）
- 时间：1-2分钟
- 功能：语义分析、主题建模、实体关系
- 适用：研究性阅读

### 4. Expert（专家）
- 时间：2-5分钟
- 功能：批判性分析、洞察生成、跨文档关联
- 适用：决策支持

### 5. Comprehensive（全面）
- 时间：5-10分钟
- 功能：完整六阶段分析、行动方案生成
- 适用：重要文档的深度研究

## 测试方法

### 1. 运行API测试

```bash
# 运行测试脚本
python scripts/test_advanced_analysis_api.py
```

### 2. 使用Swagger UI

访问 http://localhost:8000/docs 使用交互式API文档测试各个端点。

### 3. 集成测试

```python
# 运行完整的集成测试
pytest tests/test_advanced_analysis_integration.py -v
```

## 性能优化建议

### 1. 缓存配置

```python
# 在.env文件中配置
ANALYSIS_CACHE_ENABLED=true
ANALYSIS_CACHE_TTL=86400  # 24小时
ANALYSIS_CACHE_BACKEND=redis
```

### 2. 并发控制

```python
# 限制并发分析任务数
MAX_CONCURRENT_ANALYSIS=5
ANALYSIS_QUEUE_SIZE=100
```

### 3. 资源管理

```python
# 根据分析深度分配资源
ANALYSIS_RESOURCE_LIMITS = {
    "basic": {"cpu": 1, "memory": "512MB", "timeout": 60},
    "standard": {"cpu": 2, "memory": "1GB", "timeout": 120},
    "deep": {"cpu": 2, "memory": "2GB", "timeout": 300},
    "expert": {"cpu": 4, "memory": "4GB", "timeout": 600},
    "comprehensive": {"cpu": 4, "memory": "8GB", "timeout": 1200}
}
```

## 故障排查

### 1. 常见错误

#### 分析超时
```python
# 增加超时时间
analyzer = AdvancedDocumentAnalyzer(config={
    "timeout": 600,  # 10分钟
    "retry_count": 3
})
```

#### 内存不足
```python
# 减小批处理大小
analyzer = AdvancedDocumentAnalyzer(config={
    "batch_size": 5,  # 默认10
    "max_chunk_size": 500  # 默认1000
})
```

### 2. 日志查看

```bash
# 查看分析日志
tail -f data/logs/analysis.log

# 查看错误日志
grep ERROR data/logs/app.log | tail -20
```

### 3. 数据库检查

```sql
-- 检查分析任务状态
SELECT id, status, current_stage, error_message 
FROM document_analyses 
WHERE status IN ('failed', 'running')
ORDER BY created_at DESC;

-- 清理失败的任务
UPDATE document_analyses 
SET status = 'cancelled' 
WHERE status = 'running' 
AND created_at < NOW() - INTERVAL '1 hour';
```

## 扩展开发

### 1. 自定义分析阶段

```python
from src.graphs.advanced_document_analyzer import AdvancedDocumentAnalyzer

class CustomAnalyzer(AdvancedDocumentAnalyzer):
    async def custom_analysis_stage(self, state):
        # 实现自定义分析逻辑
        state["custom_results"] = await self.perform_custom_analysis(
            state["content"]
        )
        return state
    
    def _build_six_stage_graph(self):
        graph = super()._build_six_stage_graph()
        # 在知识整合后添加自定义阶段
        graph.add_node("custom_analysis", self.custom_analysis_stage)
        graph.add_edge("knowledge_integration", "custom_analysis")
        graph.add_edge("custom_analysis", "output_generation")
        return graph
```

### 2. 集成外部服务

```python
# 集成外部NLP服务
class EnhancedAnalyzer(AdvancedDocumentAnalyzer):
    async def _extract_entities(self, text):
        # 调用外部NER服务
        response = await self.external_ner_service.analyze(text)
        return response.entities
```

### 3. 自定义输出格式

```python
# 添加自定义输出格式
def custom_report_formatter(analysis_results):
    return {
        "executive_briefing": {
            "key_points": analysis_results["key_insights"][:3],
            "recommendations": analysis_results["recommendations"][:3],
            "next_steps": generate_next_steps(analysis_results)
        },
        "detailed_findings": format_detailed_findings(analysis_results),
        "risk_assessment": assess_risks(analysis_results)
    }
```

## 最佳实践

### 1. 批量处理

```python
# 批量分析多个文档
async def batch_analyze_documents(document_ids, analysis_depth="standard"):
    tasks = []
    for doc_id in document_ids:
        task = analyzer.analyze_document({
            "document_id": doc_id,
            "analysis_depth": analysis_depth
        })
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 2. 进度监控

```python
# 实时监控分析进度
async def monitor_analysis_progress(analysis_id):
    while True:
        progress = analyzer.get_analysis_progress(analysis_id)
        print(f"进度: {progress['progress']}% - {progress['current_stage']}")
        
        if progress['progress'] >= 100:
            break
            
        await asyncio.sleep(5)  # 每5秒检查一次
```

### 3. 结果缓存

```python
# 缓存分析结果以提高性能
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_analysis(document_id, analysis_depth):
    # 检查缓存
    cache_key = f"analysis_{document_id}_{analysis_depth}"
    cached_result = cache_service.get(cache_key)
    
    if cached_result:
        return cached_result
    
    # 执行分析并缓存结果
    result = analyzer.analyze_document_sync({
        "document_id": document_id,
        "analysis_depth": analysis_depth
    })
    
    cache_service.set(cache_key, result, ttl=86400)
    return result
```

## 总结

高级文档分析器的集成为DPA系统带来了强大的文档理解能力。通过六阶段分析方法论和五种分析深度级别，系统可以满足从快速预览到深度研究的各种需求。合理使用缓存、批处理和异步处理等优化技术，可以确保系统在处理大量文档时保持高性能。