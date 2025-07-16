# AAG模块快速开始指南

## 概述

AAG (Analysis-Augmented Generation) 是DPA系统的核心分析模块，提供从快速预览到深度分析的完整文档处理能力。

## 快速开始

### 1. 环境准备

确保已激活conda环境：
```bash
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.zsh hook)" && conda activate dpa_gen
```

### 2. 启动API服务

```bash
# 在项目根目录
uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload
```

### 3. 基本使用示例

#### 快速略读文档

```bash
curl -X POST http://localhost:8200/api/v1/aag/skim \
  -H "X-USER-ID: u1" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_001",
    "document_content": "这里是您的文档内容...",
    "document_type": "academic_paper"
  }'
```

响应示例：
```json
{
  "success": true,
  "document_id": "doc_001",
  "result": {
    "document_type": "学术论文",
    "core_topic": "探讨人工智能在医疗诊断中的应用，准确率达95%",
    "key_points": [
      "AI诊断准确率达到95%",
      "可减少误诊率30%",
      "需要大量标注数据"
    ],
    "target_audience": "医疗AI研究人员、医院管理者",
    "quality_assessment": {
      "level": "高",
      "reason": "方法论严谨，数据充分"
    },
    "analysis_suggestions": [
      "深入分析AI模型的技术细节",
      "评估实际应用的可行性"
    ]
  }
}
```

#### 生成渐进式摘要

单级别摘要：
```bash
curl -X POST http://localhost:8200/api/v1/aag/summary \
  -H "X-USER-ID: u1" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_001",
    "document_content": "文档内容...",
    "summary_level": "level_2"
  }'
```

生成所有级别摘要：
```bash
curl -X POST http://localhost:8200/api/v1/aag/summary/all \
  -H "X-USER-ID: u1" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_001",
    "document_content": "文档内容..."
  }'
```

#### 构建知识图谱

```bash
curl -X POST http://localhost:8200/api/v1/aag/knowledge-graph \
  -H "X-USER-ID: u1" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_001",
    "document_content": "文档内容...",
    "extraction_mode": "comprehensive"
  }'
```

聚焦特定实体类型：
```bash
curl -X POST http://localhost:8200/api/v1/aag/knowledge-graph \
  -H "X-USER-ID: u1" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_001",
    "document_content": "文档内容...",
    "extraction_mode": "focused",
    "focus_types": ["person", "organization"]
  }'
```

### 4. Python SDK使用

```python
import requests
import json

class AAGClient:
    def __init__(self, base_url="http://localhost:8200", user_id="u1"):
        self.base_url = base_url
        self.headers = {
            "X-USER-ID": user_id,
            "Content-Type": "application/json"
        }
    
    def skim_document(self, document_id, content, doc_type=None):
        """快速略读文档"""
        response = requests.post(
            f"{self.base_url}/api/v1/aag/skim",
            headers=self.headers,
            json={
                "document_id": document_id,
                "document_content": content,
                "document_type": doc_type
            }
        )
        return response.json()
    
    def generate_summary(self, document_id, content, level="level_2"):
        """生成指定级别的摘要"""
        response = requests.post(
            f"{self.base_url}/api/v1/aag/summary",
            headers=self.headers,
            json={
                "document_id": document_id,
                "document_content": content,
                "summary_level": level
            }
        )
        return response.json()
    
    def build_knowledge_graph(self, document_id, content, mode="comprehensive"):
        """构建知识图谱"""
        response = requests.post(
            f"{self.base_url}/api/v1/aag/knowledge-graph",
            headers=self.headers,
            json={
                "document_id": document_id,
                "document_content": content,
                "extraction_mode": mode
            }
        )
        return response.json()
    
    def extract_outline(self, document_id, content, dimension="all"):
        """提取多维大纲"""
        response = requests.post(
            f"{self.base_url}/api/v1/aag/outline",
            headers=self.headers,
            json={
                "document_id": document_id,
                "document_content": content,
                "dimension": dimension
            }
        )
        return response.json()
    
    def deep_analyze(self, document_id, content, analysis_types=None):
        """执行深度分析"""
        response = requests.post(
            f"{self.base_url}/api/v1/aag/deep-analysis",
            headers=self.headers,
            json={
                "document_id": document_id,
                "document_content": content,
                "analysis_types": analysis_types
            }
        )
        return response.json()

# 使用示例
client = AAGClient()

# 读取文档
with open("research_paper.txt", "r") as f:
    content = f.read()

# 1. 快速略读
skim_result = client.skim_document("paper_001", content)
print(f"文档类型: {skim_result['result']['document_type']}")
print(f"核心主题: {skim_result['result']['core_topic']}")

# 2. 生成摘要
summary = client.generate_summary("paper_001", content, "level_3")
print(f"500字摘要: {summary['result']['summary']}")

# 3. 构建知识图谱
kg = client.build_knowledge_graph("paper_001", content, "quick")
print(f"提取实体数: {kg['result']['statistics']['total_entities']}")
```

## 完整分析工作流

```python
async def comprehensive_analysis(document_id, content):
    """执行完整的文档分析流程"""
    
    # Step 1: 快速略读，评估文档
    skim_result = client.skim_document(document_id, content)
    quality = skim_result['result']['quality_assessment']['level']
    
    print(f"文档质量: {quality}")
    print(f"核心价值: {skim_result['result']['core_topic']}")
    
    # Step 2: 根据质量决定分析深度
    if quality == "高":
        # 高质量文档，深度分析
        print("执行深度分析...")
        
        # 生成全部级别摘要
        summaries = client.generate_all_summaries(document_id, content)
        
        # 构建详细知识图谱
        kg = client.build_knowledge_graph(
            document_id, content, "comprehensive"
        )
        
        # 提取所有维度大纲
        outline = client.extract_outline(document_id, content, "all")
        
        # 执行深度分析
        deep_analysis = client.deep_analyze(
            document_id, content,
            analysis_types=["evidence_chain", "critical_thinking"]
        )
        
    else:
        # 一般文档，标准分析
        print("执行标准分析...")
        
        # 生成200字摘要
        summary = client.generate_summary(document_id, content, "level_2")
        
        # 快速知识图谱
        kg = client.build_knowledge_graph(document_id, content, "quick")
        
        # 提取逻辑大纲
        outline = client.extract_outline(document_id, content, "logical")
    
    # Step 3: 导出知识图谱
    export_data = client.export_knowledge_graph(document_id, "neo4j")
    
    return {
        "skim": skim_result,
        "summaries": summaries if quality == "高" else summary,
        "knowledge_graph": kg,
        "outline": outline,
        "deep_analysis": deep_analysis if quality == "高" else None,
        "export": export_data
    }
```

## 新功能使用示例

### 5. 多维大纲提取

```python
# 提取单个维度
logical_outline = client.extract_outline(document_id, content, "logical")
print(f"逻辑大纲: {logical_outline['result']['outline']}")

# 提取所有维度
all_outlines = client.extract_outline(document_id, content, "all")
print(f"逻辑大纲: {all_outlines['result']['logical_outline']}")
print(f"主题大纲: {all_outlines['result']['thematic_outline']}")
print(f"时间线: {all_outlines['result']['temporal_outline']}")
print(f"因果链: {all_outlines['result']['causal_chain_outline']}")
```

### 6. 深度分析功能

```python
# 证据链分析
evidence_result = client.deep_analyze(
    document_id, content,
    analysis_types=["evidence_chain"]
)

# 批判性思维分析
critical_result = client.deep_analyze(
    document_id, content,
    analysis_types=["critical_thinking"]
)

# 综合深度分析（所有类型）
full_analysis = client.deep_analyze(
    document_id, content,
    analysis_types=["evidence_chain", "cross_reference", "critical_thinking"]
)

# 查看分析结果
for analysis_type, result in full_analysis['analyses'].items():
    print(f"\n{analysis_type}分析:")
    if analysis_type == "evidence_chain":
        print(f"  声明数量: {len(result.get('claims', []))}")
        assessment = result.get('overall_assessment', {})
        print(f"  证据完整性: {assessment.get('evidence_completeness')}/10")
    elif analysis_type == "critical_thinking":
        assessment = result.get('critical_assessment', {})
        print(f"  逻辑严密性: {assessment.get('logical_rigor')}/10")
        print(f"  客观性: {assessment.get('objectivity')}/10")
```

## 性能优化建议

### 1. 使用缓存
AAG自动缓存分析结果。相同的文档和分析参数会直接返回缓存结果。

### 2. 选择合适的模式
- **Quick模式**: 适合快速预览和大批量处理
- **Focused模式**: 适合有明确目标的分析
- **Comprehensive模式**: 适合需要深度理解的重要文档

### 3. 批量处理
```python
# 批量分析多个文档
documents = ["doc1.txt", "doc2.txt", "doc3.txt"]

for doc_path in documents:
    with open(doc_path, "r") as f:
        content = f.read()
    
    # 使用quick模式批量处理
    result = client.skim_document(
        f"batch_{doc_path}", 
        content
    )
    print(f"{doc_path}: {result['result']['core_topic']}")
```

## 常见问题

### Q: 知识图谱提取的关系数量为0？
A: 这是已知问题，正在优化中。临时解决方案：
1. 确保文档中有明确的实体关系描述
2. 使用comprehensive模式可能获得更好的结果

### Q: 如何处理超长文档？
A: AAG会自动处理长文档：
- 略读：截取前8000字符
- 摘要：根据级别调整截取长度
- 知识图谱：自动分块处理

### Q: API调用失败？
A: 检查以下内容：
1. API服务是否运行在端口8200
2. 是否包含X-USER-ID头
3. 文档内容是否为空

## 下一步

1. 查看[完整API文档](http://localhost:8200/docs)
2. 阅读[AAG架构设计](./AAG_ARCHITECTURE.md)
3. 了解[高级功能开发计划](./AAG_IMPLEMENTATION_ROADMAP.md)