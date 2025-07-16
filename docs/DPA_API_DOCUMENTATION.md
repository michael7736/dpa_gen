# DPA Next API 文档

## 概述

DPA Next 提供了一套完整的 RESTful API，支持项目生命周期管理、智能文档处理、认知分析等功能。

### 基础信息

- **基础URL**: `http://localhost:8001/api/v1`
- **认证方式**: JWT Bearer Token
- **请求格式**: JSON
- **响应格式**: JSON
- **API版本**: v1.0

### 认证

所有API请求（除了认证端点）都需要在请求头中包含JWT令牌：

```http
Authorization: Bearer <your-jwt-token>
```

### 错误响应格式

```json
{
  "detail": "错误描述",
  "status_code": 400,
  "error_code": "ERROR_CODE"
}
```

## API端点

### 1. 认证管理

#### 1.1 用户注册

```http
POST /auth/register
```

**请求体**：
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "张三"
}
```

**响应**：
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "张三",
  "is_active": true,
  "created_at": "2024-12-20T10:00:00Z"
}
```

#### 1.2 用户登录

```http
POST /auth/login
```

**请求体**：
```json
{
  "username": "user@example.com",
  "password": "securepassword"
}
```

**响应**：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2. 项目管理

#### 2.1 创建项目

```http
POST /projects
```

**请求体**：
```json
{
  "name": "AI技术研究",
  "description": "研究最新的AI技术趋势和应用",
  "type": "research",
  "config": {
    "max_tasks": 20,
    "auto_execute": false
  },
  "objectives": [
    "了解GPT-4的技术原理",
    "分析AI在各行业的应用案例"
  ],
  "constraints": [
    "时间限制：2周内完成",
    "预算限制：使用免费资源"
  ]
}
```

**响应**：
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "AI技术研究",
  "description": "研究最新的AI技术趋势和应用",
  "type": "research",
  "status": "draft",
  "config": {
    "max_tasks": 20,
    "auto_execute": false
  },
  "objectives": ["了解GPT-4的技术原理", "分析AI在各行业的应用案例"],
  "constraints": ["时间限制：2周内完成", "预算限制：使用免费资源"],
  "quality_gates": {
    "accuracy": 0.8,
    "completeness": 0.9,
    "relevance": 0.85
  },
  "progress": 0.0,
  "quality_score": 0.0,
  "success_rate": 0.0,
  "created_at": "2024-12-20T10:00:00Z",
  "updated_at": "2024-12-20T10:00:00Z",
  "started_at": null,
  "completed_at": null,
  "user_id": "user-uuid"
}
```

#### 2.2 获取项目列表

```http
GET /projects?skip=0&limit=20&status=executing&project_type=research
```

**查询参数**：
- `skip`: 跳过的记录数（分页）
- `limit`: 返回的记录数（1-100）
- `status`: 项目状态过滤（draft, planning, executing, paused, completed, archived, cancelled）
- `project_type`: 项目类型过滤（research, analysis, report, documentation, custom）

**响应**：
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "AI技术研究",
    "type": "research",
    "status": "executing",
    "progress": 0.35,
    "created_at": "2024-12-20T10:00:00Z",
    "updated_at": "2024-12-20T12:00:00Z"
  }
]
```

#### 2.3 获取项目详情

```http
GET /projects/{project_id}
```

**路径参数**：
- `project_id`: 项目UUID

**响应**：完整的项目信息（同创建项目响应）

#### 2.4 更新项目

```http
PUT /projects/{project_id}
```

**请求体**（部分更新）：
```json
{
  "name": "AI技术深度研究",
  "status": "executing",
  "quality_gates": {
    "accuracy": 0.85,
    "completeness": 0.95
  }
}
```

#### 2.5 删除项目

```http
DELETE /projects/{project_id}
```

**响应**：
```json
{
  "message": "Project deleted successfully"
}
```

### 3. 任务管理

#### 3.1 创建任务

```http
POST /projects/{project_id}/tasks
```

**请求体**：
```json
{
  "title": "收集GPT-4技术文档",
  "description": "搜集OpenAI官方文档和技术论文",
  "type": "data_collection",
  "priority": 5,
  "dependencies": [],
  "estimated_time": 120,
  "plan": {
    "sources": ["OpenAI官网", "arXiv", "Google Scholar"],
    "keywords": ["GPT-4", "transformer", "language model"]
  }
}
```

**响应**：
```json
{
  "id": "task-uuid",
  "project_id": "project-uuid",
  "title": "收集GPT-4技术文档",
  "type": "data_collection",
  "status": "pending",
  "priority": 5,
  "order": 0,
  "dependencies": [],
  "estimated_time": 120,
  "plan": {
    "sources": ["OpenAI官网", "arXiv", "Google Scholar"],
    "keywords": ["GPT-4", "transformer", "language model"]
  },
  "created_at": "2024-12-20T10:00:00Z"
}
```

#### 3.2 获取任务列表

```http
GET /projects/{project_id}/tasks
```

**响应**：
```json
[
  {
    "id": "task-uuid-1",
    "title": "收集GPT-4技术文档",
    "type": "data_collection",
    "status": "completed",
    "progress": 1.0
  },
  {
    "id": "task-uuid-2",
    "title": "分析技术原理",
    "type": "deep_analysis",
    "status": "in_progress",
    "progress": 0.6
  }
]
```

#### 3.3 更新任务

```http
PUT /projects/{project_id}/tasks/{task_id}
```

**请求体**：
```json
{
  "status": "in_progress",
  "progress": 0.5,
  "result": {
    "documents_collected": 15,
    "total_pages": 450
  }
}
```

### 4. 项目执行控制

#### 4.1 开始执行项目

```http
POST /projects/{project_id}/execute
```

**请求体**（可选）：
```json
{
  "initial_context": {
    "focus_areas": ["技术原理", "应用案例"]
  },
  "user_preferences": {
    "language": "zh-CN",
    "detail_level": "high"
  }
}
```

**响应**：
```json
{
  "message": "Project execution started",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "executing",
  "execution_id": "exec-uuid"
}
```

#### 4.2 暂停项目

```http
POST /projects/{project_id}/pause
```

#### 4.3 恢复项目

```http
POST /projects/{project_id}/resume
```

### 5. 文档管理

#### 5.1 上传文档

```http
POST /documents/upload
```

**请求格式**: multipart/form-data

**表单字段**：
- `file`: 文档文件
- `project_id`: 项目ID
- `title`: 文档标题（可选）
- `description`: 文档描述（可选）
- `tags`: 标签，逗号分隔（可选）

**响应**：
```json
{
  "id": "doc-uuid",
  "project_id": "project-uuid",
  "title": "GPT-4 Technical Report",
  "file_type": "pdf",
  "file_size": 2048576,
  "status": "processing",
  "created_at": "2024-12-20T10:00:00Z"
}
```

#### 5.2 获取文档列表

```http
GET /documents?project_id={project_id}&skip=0&limit=20
```

#### 5.3 获取文档详情

```http
GET /documents/{document_id}
```

**响应**：
```json
{
  "id": "doc-uuid",
  "project_id": "project-uuid",
  "title": "GPT-4 Technical Report",
  "content": "文档内容（如果已处理）",
  "chunks": [
    {
      "id": "chunk-1",
      "content": "分块内容",
      "metadata": {
        "page": 1,
        "section": "Introduction"
      }
    }
  ],
  "metadata": {
    "pages": 98,
    "language": "en",
    "processed_at": "2024-12-20T10:30:00Z"
  }
}
```

### 6. 认知分析

#### 6.1 文档深度分析

```http
POST /cognitive/analyze
```

**请求体**：
```json
{
  "document_id": "doc-uuid",
  "analysis_type": "deep",
  "options": {
    "extract_entities": true,
    "generate_summary": true,
    "identify_themes": true
  }
}
```

**响应**：
```json
{
  "analysis_id": "analysis-uuid",
  "document_id": "doc-uuid",
  "results": {
    "summary": "文档摘要...",
    "entities": [
      {"name": "GPT-4", "type": "MODEL", "frequency": 45},
      {"name": "OpenAI", "type": "ORGANIZATION", "frequency": 23}
    ],
    "themes": ["人工智能", "自然语言处理", "深度学习"],
    "key_insights": [
      "GPT-4采用了新的训练方法...",
      "模型规模达到了1.76万亿参数..."
    ]
  },
  "confidence": 0.92,
  "processing_time": 5.2
}
```

#### 6.2 认知对话

```http
POST /cognitive/chat
```

**请求体**：
```json
{
  "message": "GPT-4相比GPT-3.5有哪些主要改进？",
  "project_id": "project-uuid",
  "context": {
    "use_project_memory": true,
    "search_depth": "deep"
  }
}
```

**响应**：
```json
{
  "response": "根据分析的文档，GPT-4相比GPT-3.5有以下主要改进：\n1. 模型规模：参数量增加了10倍\n2. 多模态能力：支持图像输入\n3. 推理能力：在复杂任务上表现显著提升...",
  "sources": [
    {
      "document_id": "doc-uuid",
      "chunk_id": "chunk-123",
      "relevance": 0.95
    }
  ],
  "confidence": 0.88,
  "strategies_used": ["semantic_search", "reasoning", "synthesis"]
}
```

### 7. 记忆系统

#### 7.1 保存项目记忆

```http
POST /projects/{project_id}/memories
```

**请求体**：
```json
{
  "memory_type": "project",
  "content": {
    "key_findings": ["发现1", "发现2"],
    "decisions": ["决策1", "决策2"]
  },
  "insights": [
    {
      "type": "pattern",
      "content": "所有分析的AI模型都遵循Transformer架构"
    }
  ],
  "ttl": 86400
}
```

#### 7.2 查询项目记忆

```http
GET /projects/{project_id}/memories?memory_type=project
```

### 8. 可交付成果

#### 8.1 生成报告

```http
POST /projects/{project_id}/deliverables
```

**请求体**：
```json
{
  "name": "AI技术研究报告",
  "type": "report",
  "format": "pdf",
  "content": {
    "template": "research_report",
    "include_sections": ["executive_summary", "findings", "recommendations"]
  }
}
```

**响应**：
```json
{
  "id": "deliverable-uuid",
  "name": "AI技术研究报告",
  "type": "report",
  "format": "pdf",
  "file_path": "/deliverables/report-2024-12-20.pdf",
  "file_size": 1048576,
  "download_url": "/api/v1/deliverables/deliverable-uuid/download",
  "created_at": "2024-12-20T15:00:00Z"
}
```

#### 8.2 下载成果

```http
GET /deliverables/{deliverable_id}/download
```

**响应**: 文件流（application/pdf, application/json等）

### 9. WebSocket 实时通信

#### 9.1 项目执行监控

```javascript
// WebSocket连接
const ws = new WebSocket('ws://localhost:8001/ws/projects/{project_id}');

// 接收消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

// 消息类型
{
  "type": "execution_update",
  "timestamp": "2024-12-20T10:00:00Z",
  "data": {
    "phase": "execution",
    "current_task": "task-uuid",
    "progress": 0.45,
    "active_tasks": ["task-1", "task-2"],
    "completed_tasks": ["task-0"],
    "metrics": {
      "accuracy": 0.85,
      "velocity": 2.5
    }
  }
}
```

## 使用示例

### 完整的项目执行流程

```python
import requests
import json

# 配置
BASE_URL = "http://localhost:8001/api/v1"
TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# 1. 创建项目
project_data = {
    "name": "AI技术研究",
    "type": "research",
    "objectives": ["研究GPT-4技术"]
}
response = requests.post(f"{BASE_URL}/projects", 
                         json=project_data, 
                         headers=headers)
project = response.json()
project_id = project["id"]

# 2. 上传文档
files = {"file": open("gpt4-paper.pdf", "rb")}
data = {"project_id": project_id, "title": "GPT-4 Paper"}
response = requests.post(f"{BASE_URL}/documents/upload", 
                        files=files, 
                        data=data,
                        headers=headers)

# 3. 创建任务
task_data = {
    "title": "分析GPT-4架构",
    "type": "deep_analysis",
    "priority": 5
}
response = requests.post(f"{BASE_URL}/projects/{project_id}/tasks",
                        json=task_data,
                        headers=headers)

# 4. 执行项目
response = requests.post(f"{BASE_URL}/projects/{project_id}/execute",
                        headers=headers)

# 5. 监控进度（通过WebSocket或轮询）
response = requests.get(f"{BASE_URL}/projects/{project_id}",
                       headers=headers)
progress = response.json()["progress"]

# 6. 认知对话
chat_data = {
    "message": "总结GPT-4的主要创新点",
    "project_id": project_id
}
response = requests.post(f"{BASE_URL}/cognitive/chat",
                        json=chat_data,
                        headers=headers)
answer = response.json()["response"]

# 7. 生成报告
report_data = {
    "name": "GPT-4研究报告",
    "type": "report",
    "format": "pdf"
}
response = requests.post(f"{BASE_URL}/projects/{project_id}/deliverables",
                        json=report_data,
                        headers=headers)
report_url = response.json()["download_url"]
```

## 错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| AUTH_INVALID_TOKEN | 401 | 无效的认证令牌 |
| AUTH_TOKEN_EXPIRED | 401 | 令牌已过期 |
| PROJECT_NOT_FOUND | 404 | 项目不存在 |
| TASK_NOT_FOUND | 404 | 任务不存在 |
| DOCUMENT_NOT_FOUND | 404 | 文档不存在 |
| PROJECT_NAME_EXISTS | 400 | 项目名称已存在 |
| INVALID_PROJECT_STATUS | 400 | 无效的项目状态 |
| TASK_DEPENDENCY_CYCLE | 400 | 任务依赖存在循环 |
| FILE_TOO_LARGE | 413 | 文件大小超过限制 |
| UNSUPPORTED_FILE_TYPE | 400 | 不支持的文件类型 |
| PROCESSING_ERROR | 500 | 处理过程中发生错误 |

## 限制和配额

- **文件上传**: 单文件最大 50MB
- **支持的文件类型**: PDF, DOCX, TXT, MD, JSON, CSV
- **并发请求**: 每用户最多 10 个并发请求
- **API调用频率**: 每分钟 60 次
- **项目数量**: 每用户最多 100 个活跃项目
- **文档数量**: 每项目最多 1000 个文档

## SDK支持

### Python SDK

```python
from dpa_sdk import DPAClient

# 初始化客户端
client = DPAClient(
    base_url="http://localhost:8001",
    api_key="your-api-key"
)

# 创建项目
project = client.projects.create(
    name="AI研究",
    type="research"
)

# 执行项目
execution = client.projects.execute(project.id)

# 认知对话
response = client.cognitive.chat(
    message="分析结果如何？",
    project_id=project.id
)
```

### JavaScript/TypeScript SDK

```typescript
import { DPAClient } from 'dpa-sdk';

// 初始化客户端
const client = new DPAClient({
  baseUrl: 'http://localhost:8001',
  apiKey: 'your-api-key'
});

// 创建项目
const project = await client.projects.create({
  name: 'AI研究',
  type: 'research'
});

// 执行项目
const execution = await client.projects.execute(project.id);

// 认知对话
const response = await client.cognitive.chat({
  message: '分析结果如何？',
  projectId: project.id
});
```

## 更新日志

### v1.0.0 (2024-12-20)
- 初始版本发布
- 完整的项目生命周期管理
- 认知分析和对话功能
- 三层记忆系统
- WebSocket实时通信

---

*最后更新：2024-12-20*