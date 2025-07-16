# DPA Next 集成指南

本指南帮助开发者将DPA集成到现有系统中，或基于DPA开发自定义应用。

## 目录

1. [SDK使用](#sdk使用)
2. [REST API集成](#rest-api集成)
3. [WebSocket实时通信](#websocket实时通信)
4. [自定义工作流](#自定义工作流)
5. [插件开发](#插件开发)
6. [数据导入导出](#数据导入导出)
7. [认证和授权](#认证和授权)
8. [错误处理](#错误处理)
9. [性能优化](#性能优化)
10. [部署指南](#部署指南)

## SDK使用

### Python SDK

#### 安装
```bash
pip install dpa-sdk
# 或从源码安装
pip install git+https://github.com/your-org/dpa-sdk-python.git
```

#### 基础使用
```python
from dpa_sdk import DPAClient
from dpa_sdk.models import ProjectType, TaskType

# 初始化客户端
client = DPAClient(
    base_url="http://localhost:8001",
    api_key="your-api-key",
    timeout=30
)

# 创建项目
project = client.projects.create(
    name="智能分析项目",
    description="使用SDK创建的项目",
    type=ProjectType.RESEARCH,
    config={
        "language": "zh-CN",
        "auto_execute": True
    }
)

# 上传文档
with open("document.pdf", "rb") as f:
    document = client.documents.upload(
        project_id=project.id,
        file=f,
        title="重要文档",
        tags=["研究", "AI"]
    )

# 执行项目
execution = client.projects.execute(
    project_id=project.id,
    wait_for_completion=True,
    callback=lambda status: print(f"进度: {status.progress}")
)

# 认知对话
response = client.cognitive.chat(
    message="总结主要发现",
    project_id=project.id,
    stream=True
)

for chunk in response:
    print(chunk.content, end="")
```

#### 高级功能
```python
# 批量操作
async def batch_process():
    async with client.batch() as batch:
        # 批量创建任务
        tasks = []
        for i in range(10):
            task = batch.tasks.create(
                project_id=project.id,
                title=f"任务{i}",
                type=TaskType.ANALYSIS
            )
            tasks.append(task)
        
        # 批量执行
        results = await batch.execute()

# 事件监听
@client.on("project.completed")
def on_project_complete(event):
    print(f"项目完成: {event.project_id}")
    # 自动生成报告
    report = client.deliverables.generate(
        project_id=event.project_id,
        format="pdf"
    )

# 自定义重试策略
from dpa_sdk.retry import RetryPolicy

client.retry_policy = RetryPolicy(
    max_attempts=3,
    backoff_factor=2.0,
    retry_on=[429, 500, 502, 503, 504]
)
```

### JavaScript/TypeScript SDK

#### 安装
```bash
npm install @dpa/sdk
# 或
yarn add @dpa/sdk
```

#### 基础使用
```typescript
import { DPAClient, ProjectType, TaskType } from '@dpa/sdk';

// 初始化客户端
const client = new DPAClient({
    baseUrl: 'http://localhost:8001',
    apiKey: 'your-api-key',
    timeout: 30000
});

// 创建项目
const project = await client.projects.create({
    name: '智能分析项目',
    description: '使用SDK创建的项目',
    type: ProjectType.Research,
    config: {
        language: 'zh-CN',
        autoExecute: true
    }
});

// 上传文档
const fileInput = document.getElementById('file-input') as HTMLInputElement;
const file = fileInput.files[0];

const document = await client.documents.upload({
    projectId: project.id,
    file: file,
    title: '重要文档',
    tags: ['研究', 'AI']
});

// 实时监控执行进度
const execution = await client.projects.execute(project.id);

execution.on('progress', (progress) => {
    console.log(`进度: ${progress.percent}%`);
});

execution.on('complete', (result) => {
    console.log('执行完成:', result);
});

// 流式对话
const stream = await client.cognitive.chatStream({
    message: '总结主要发现',
    projectId: project.id
});

for await (const chunk of stream) {
    process.stdout.write(chunk.content);
}
```

#### React集成
```tsx
import React, { useState, useEffect } from 'react';
import { useDPA } from '@dpa/react';

function ProjectDashboard({ projectId }) {
    const { client, loading, error } = useDPA();
    const [project, setProject] = useState(null);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        // 订阅项目更新
        const unsubscribe = client.projects.subscribe(projectId, (update) => {
            setProject(update.project);
            setProgress(update.progress);
        });

        return () => unsubscribe();
    }, [projectId]);

    const handleExecute = async () => {
        try {
            await client.projects.execute(projectId);
        } catch (err) {
            console.error('执行失败:', err);
        }
    };

    if (loading) return <div>加载中...</div>;
    if (error) return <div>错误: {error.message}</div>;

    return (
        <div>
            <h2>{project?.name}</h2>
            <ProgressBar value={progress} />
            <button onClick={handleExecute}>执行项目</button>
        </div>
    );
}
```

## REST API集成

### 认证
所有API请求需要在Header中包含JWT令牌：
```http
Authorization: Bearer <your-jwt-token>
```

### 基础请求示例
```python
import requests
import json

class DPAAPIClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_project(self, name, **kwargs):
        """创建新项目"""
        data = {"name": name, **kwargs}
        response = requests.post(
            f"{self.base_url}/projects",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def upload_document(self, project_id, file_path, **metadata):
        """上传文档"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'project_id': project_id, **metadata}
            
            # 注意：上传文件时不要设置Content-Type
            headers = {"Authorization": self.headers["Authorization"]}
            
            response = requests.post(
                f"{self.base_url}/documents/upload",
                headers=headers,
                files=files,
                data=data
            )
        
        response.raise_for_status()
        return response.json()
```

### 分页处理
```python
def get_all_projects(client):
    """获取所有项目（处理分页）"""
    all_projects = []
    skip = 0
    limit = 50
    
    while True:
        response = requests.get(
            f"{client.base_url}/projects",
            headers=client.headers,
            params={"skip": skip, "limit": limit}
        )
        
        projects = response.json()
        if not projects:
            break
            
        all_projects.extend(projects)
        
        # 如果返回的数量小于limit，说明已经是最后一页
        if len(projects) < limit:
            break
            
        skip += limit
    
    return all_projects
```

### 错误处理
```python
from enum import Enum

class DPAErrorCode(Enum):
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    TASK_DEPENDENCY_CYCLE = "TASK_DEPENDENCY_CYCLE"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"

def safe_api_call(func):
    """API调用错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.HTTPError as e:
            error_data = e.response.json()
            error_code = error_data.get("error_code")
            
            if error_code == DPAErrorCode.PROJECT_NOT_FOUND.value:
                raise ProjectNotFoundError(error_data["detail"])
            elif error_code == DPAErrorCode.QUOTA_EXCEEDED.value:
                raise QuotaExceededError(error_data["detail"])
            else:
                raise DPAAPIError(error_data["detail"], error_code)
        except requests.RequestException as e:
            raise NetworkError(f"网络错误: {str(e)}")
    
    return wrapper
```

## WebSocket实时通信

### 连接管理
```javascript
class DPAWebSocket {
    constructor(projectId, token) {
        this.projectId = projectId;
        this.token = token;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connect() {
        const wsUrl = `ws://localhost:8001/ws/projects/${this.projectId}?token=${this.token}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket连接建立');
            this.reconnectAttempts = 0;
            this.onConnect();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket错误:', error);
            this.onError(error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket连接关闭');
            this.attemptReconnect();
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.onMaxReconnectAttemptsReached();
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'execution_update':
                this.onExecutionUpdate(data.data);
                break;
            case 'task_completed':
                this.onTaskCompleted(data.data);
                break;
            case 'error':
                this.onError(data.data);
                break;
            default:
                console.log('未知消息类型:', data.type);
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket未连接');
        }
    }

    close() {
        if (this.ws) {
            this.ws.close();
        }
    }

    // 事件处理器（子类覆盖）
    onConnect() {}
    onExecutionUpdate(data) {}
    onTaskCompleted(data) {}
    onError(error) {}
    onMaxReconnectAttemptsReached() {}
}

// 使用示例
class ProjectMonitor extends DPAWebSocket {
    onExecutionUpdate(data) {
        console.log(`进度: ${data.progress * 100}%`);
        console.log(`当前任务: ${data.current_task}`);
        console.log(`已完成: ${data.completed_tasks.length}`);
        
        // 更新UI
        updateProgressBar(data.progress);
        updateTaskList(data.tasks);
    }

    onTaskCompleted(data) {
        console.log(`任务完成: ${data.task_title}`);
        showNotification(`✅ ${data.task_title} 已完成`);
    }

    onError(error) {
        console.error('执行错误:', error);
        showErrorAlert(error.message);
    }
}

// 创建监控实例
const monitor = new ProjectMonitor(projectId, token);
monitor.connect();
```

## 自定义工作流

### 定义工作流模板
```python
from dpa_sdk.workflow import WorkflowTemplate, TaskTemplate

# 创建自定义工作流模板
class ResearchWorkflow(WorkflowTemplate):
    """学术研究工作流"""
    
    def __init__(self):
        super().__init__(
            name="academic_research",
            description="标准学术研究流程"
        )
    
    def define_tasks(self):
        # 1. 文献搜索
        literature_search = TaskTemplate(
            name="literature_search",
            type="data_collection",
            config={
                "sources": ["Google Scholar", "PubMed", "arXiv"],
                "max_results": 100,
                "sort_by": "relevance"
            }
        )
        
        # 2. 文献筛选
        literature_filter = TaskTemplate(
            name="literature_filter",
            type="verification",
            dependencies=[literature_search],
            config={
                "criteria": {
                    "year": ">=2020",
                    "citations": ">=10",
                    "quality_score": ">=0.7"
                }
            }
        )
        
        # 3. 深度阅读和分析
        deep_analysis = TaskTemplate(
            name="deep_analysis",
            type="deep_analysis",
            dependencies=[literature_filter],
            config={
                "analysis_depth": "comprehensive",
                "extract_methodology": True,
                "identify_gaps": True
            }
        )
        
        # 4. 综合报告
        synthesis_report = TaskTemplate(
            name="synthesis_report",
            type="report_writing",
            dependencies=[deep_analysis],
            config={
                "sections": [
                    "introduction",
                    "methodology_review",
                    "findings_synthesis",
                    "research_gaps",
                    "future_directions"
                ],
                "format": "academic_paper"
            }
        )
        
        return [
            literature_search,
            literature_filter,
            deep_analysis,
            synthesis_report
        ]
    
    def define_quality_gates(self):
        return {
            "literature_coverage": 0.8,  # 覆盖80%的相关文献
            "analysis_depth": 0.85,      # 分析深度评分
            "synthesis_quality": 0.9     # 综合质量评分
        }

# 注册工作流
client.workflows.register(ResearchWorkflow())

# 使用工作流创建项目
project = client.projects.create_from_workflow(
    workflow_name="academic_research",
    project_name="量子计算研究综述",
    parameters={
        "keywords": ["quantum computing", "quantum algorithms"],
        "time_range": "2020-2024"
    }
)
```

### 自定义任务执行器
```python
from dpa_sdk.executors import TaskExecutor
import pandas as pd

class DataAnalysisExecutor(TaskExecutor):
    """自定义数据分析执行器"""
    
    def __init__(self):
        super().__init__(task_type="custom_data_analysis")
    
    async def execute(self, task, context):
        # 获取输入数据
        input_docs = await self.get_input_documents(task.project_id)
        
        # 执行自定义分析
        results = []
        for doc in input_docs:
            # 提取数据表格
            tables = self.extract_tables(doc)
            
            # 数据分析
            for table in tables:
                df = pd.DataFrame(table)
                
                # 统计分析
                stats = {
                    "mean": df.mean().to_dict(),
                    "std": df.std().to_dict(),
                    "correlation": df.corr().to_dict()
                }
                
                # 异常检测
                outliers = self.detect_outliers(df)
                
                results.append({
                    "document_id": doc.id,
                    "statistics": stats,
                    "outliers": outliers
                })
        
        # 生成可视化
        visualizations = await self.create_visualizations(results)
        
        # 返回结果
        return {
            "status": "completed",
            "results": results,
            "visualizations": visualizations,
            "summary": self.generate_summary(results)
        }
    
    def extract_tables(self, document):
        # 实现表格提取逻辑
        pass
    
    def detect_outliers(self, df):
        # 实现异常检测逻辑
        pass
    
    async def create_visualizations(self, results):
        # 生成图表
        pass

# 注册执行器
client.executors.register(DataAnalysisExecutor())
```

## 插件开发

### 插件结构
```
my-dpa-plugin/
├── __init__.py
├── plugin.yaml
├── handlers/
│   ├── __init__.py
│   └── custom_handler.py
├── models/
│   └── custom_models.py
├── ui/
│   └── components/
└── tests/
    └── test_plugin.py
```

### 插件配置 (plugin.yaml)
```yaml
name: my-dpa-plugin
version: 1.0.0
description: 自定义DPA插件
author: Your Name
dependencies:
  - dpa-sdk>=1.0.0
  - pandas>=1.3.0

handlers:
  - type: document_processor
    class: handlers.custom_handler.CustomDocumentProcessor
    file_types: [.xlsx, .xls]
  
  - type: task_executor
    class: handlers.custom_handler.CustomTaskExecutor
    task_types: [custom_analysis]

ui_components:
  - name: CustomDashboard
    path: ui/components/Dashboard.jsx
    route: /custom-dashboard

api_endpoints:
  - path: /api/v1/custom/analyze
    method: POST
    handler: handlers.api.analyze_handler

settings:
  max_file_size: 100MB
  enable_cache: true
```

### 插件实现
```python
# handlers/custom_handler.py
from dpa_sdk.plugins import DocumentProcessor, TaskExecutor
import pandas as pd

class CustomDocumentProcessor(DocumentProcessor):
    """处理Excel文件的自定义处理器"""
    
    supported_types = ['.xlsx', '.xls']
    
    async def process(self, file_path, metadata):
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 提取内容
        content = {
            "sheets": [],
            "total_rows": 0,
            "total_columns": 0
        }
        
        # 处理每个工作表
        excel_file = pd.ExcelFile(file_path)
        for sheet_name in excel_file.sheet_names:
            sheet_df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            sheet_info = {
                "name": sheet_name,
                "rows": len(sheet_df),
                "columns": len(sheet_df.columns),
                "columns_names": sheet_df.columns.tolist(),
                "data_types": sheet_df.dtypes.to_dict(),
                "sample_data": sheet_df.head(10).to_dict('records')
            }
            
            content["sheets"].append(sheet_info)
            content["total_rows"] += len(sheet_df)
        
        content["total_columns"] = max(
            len(sheet["columns_names"]) for sheet in content["sheets"]
        )
        
        # 生成文本表示
        text_content = self.generate_text_representation(content)
        
        # 提取实体
        entities = self.extract_entities(content)
        
        return {
            "content": content,
            "text": text_content,
            "entities": entities,
            "metadata": {
                **metadata,
                "processor": "CustomExcelProcessor",
                "file_type": "spreadsheet"
            }
        }
    
    def generate_text_representation(self, content):
        """生成文本表示用于搜索和分析"""
        text_parts = []
        
        for sheet in content["sheets"]:
            text_parts.append(f"工作表: {sheet['name']}")
            text_parts.append(f"列: {', '.join(sheet['columns_names'])}")
            
            # 添加示例数据
            if sheet['sample_data']:
                text_parts.append("示例数据:")
                for row in sheet['sample_data'][:5]:
                    text_parts.append(str(row))
        
        return "\n".join(text_parts)
    
    def extract_entities(self, content):
        """提取实体信息"""
        entities = {
            "tables": [],
            "columns": [],
            "metrics": []
        }
        
        for sheet in content["sheets"]:
            # 表格实体
            entities["tables"].append({
                "name": sheet["name"],
                "type": "excel_sheet",
                "size": f"{sheet['rows']}x{sheet['columns']}"
            })
            
            # 列实体
            for col in sheet["columns_names"]:
                if self.is_metric_column(col):
                    entities["metrics"].append(col)
                else:
                    entities["columns"].append(col)
        
        return entities
    
    def is_metric_column(self, column_name):
        """判断是否为指标列"""
        metric_keywords = [
            'amount', 'count', 'total', 'sum', 'avg', 'average',
            '金额', '数量', '总计', '平均', '总和'
        ]
        return any(keyword in column_name.lower() for keyword in metric_keywords)

# 注册插件
def register_plugin(client):
    client.plugins.register(CustomDocumentProcessor())
```

## 数据导入导出

### 批量导入
```python
import json
import csv
from pathlib import Path

class DataImporter:
    def __init__(self, client):
        self.client = client
    
    async def import_from_json(self, json_file):
        """从JSON文件导入项目数据"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 创建项目
        project = await self.client.projects.create(**data['project'])
        
        # 导入文档
        for doc_data in data.get('documents', []):
            if 'file_path' in doc_data:
                await self.client.documents.upload(
                    project_id=project.id,
                    file_path=doc_data['file_path'],
                    metadata=doc_data.get('metadata', {})
                )
        
        # 导入任务
        task_mapping = {}
        for task_data in data.get('tasks', []):
            # 处理依赖关系
            dependencies = []
            for dep_name in task_data.get('dependencies', []):
                if dep_name in task_mapping:
                    dependencies.append(task_mapping[dep_name])
            
            task = await self.client.tasks.create(
                project_id=project.id,
                **{**task_data, 'dependencies': dependencies}
            )
            task_mapping[task_data['name']] = task.id
        
        return project
    
    async def import_from_csv(self, csv_file, project_id):
        """从CSV文件导入任务"""
        tasks = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                task = {
                    "title": row['title'],
                    "type": row.get('type', 'custom'),
                    "description": row.get('description', ''),
                    "priority": int(row.get('priority', 5)),
                    "estimated_time": int(row.get('estimated_time', 60))
                }
                tasks.append(task)
        
        # 批量创建任务
        created_tasks = []
        for task in tasks:
            created_task = await self.client.tasks.create(
                project_id=project_id,
                **task
            )
            created_tasks.append(created_task)
        
        return created_tasks

# 使用示例
importer = DataImporter(client)

# 导入完整项目
project = await importer.import_from_json('project_export.json')

# 导入任务列表
tasks = await importer.import_from_csv('tasks.csv', project.id)
```

### 数据导出
```python
class DataExporter:
    def __init__(self, client):
        self.client = client
    
    async def export_project(self, project_id, output_dir):
        """导出完整项目"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 获取项目信息
        project = await self.client.projects.get(project_id)
        
        # 导出项目元数据
        project_data = {
            "project": {
                "name": project.name,
                "description": project.description,
                "type": project.type,
                "config": project.config,
                "objectives": project.objectives,
                "constraints": project.constraints
            },
            "documents": [],
            "tasks": [],
            "memories": [],
            "results": {}
        }
        
        # 导出文档
        documents = await self.client.documents.list(project_id=project_id)
        docs_dir = output_path / "documents"
        docs_dir.mkdir(exist_ok=True)
        
        for doc in documents:
            # 下载文档文件
            file_content = await self.client.documents.download(doc.id)
            file_path = docs_dir / f"{doc.id}_{doc.filename}"
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            project_data["documents"].append({
                "id": doc.id,
                "title": doc.title,
                "file_path": str(file_path.relative_to(output_path)),
                "metadata": doc.metadata
            })
        
        # 导出任务
        tasks = await self.client.tasks.list(project_id=project_id)
        for task in tasks:
            project_data["tasks"].append({
                "title": task.title,
                "type": task.type,
                "status": task.status,
                "dependencies": [dep.title for dep in task.dependencies],
                "result": task.result
            })
        
        # 导出记忆
        memories = await self.client.memories.list(
            project_id=project_id,
            memory_type="project"
        )
        project_data["memories"] = [
            {
                "type": mem.type,
                "content": mem.content,
                "created_at": mem.created_at.isoformat()
            }
            for mem in memories
        ]
        
        # 导出分析结果
        if project.status == "completed":
            # 获取最终报告
            deliverables = await self.client.deliverables.list(
                project_id=project_id
            )
            
            for deliverable in deliverables:
                if deliverable.type == "report":
                    report_content = await self.client.deliverables.download(
                        deliverable.id
                    )
                    report_path = output_path / f"report_{deliverable.format}"
                    
                    with open(report_path, 'wb') as f:
                        f.write(report_content)
                    
                    project_data["results"]["report"] = str(
                        report_path.relative_to(output_path)
                    )
        
        # 保存项目数据
        with open(output_path / "project.json", 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        # 生成README
        self.generate_readme(project, output_path)
        
        return output_path
    
    def generate_readme(self, project, output_path):
        """生成项目README"""
        readme_content = f"""# {project.name}

## 项目信息
- 类型: {project.type}
- 状态: {project.status}
- 创建时间: {project.created_at}
- 完成时间: {project.completed_at or '进行中'}

## 项目描述
{project.description}

## 目标
{chr(10).join(f"- {obj}" for obj in project.objectives)}

## 文件结构
- `project.json` - 项目元数据
- `documents/` - 原始文档
- `report.*` - 生成的报告

## 使用方法
```python
from dpa_sdk import DPAClient

client = DPAClient(...)
importer = DataImporter(client)
project = await importer.import_from_json('project.json')
```
"""
        
        with open(output_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
```

## 认证和授权

### OAuth2集成
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT配置
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return username

# API密钥管理
class APIKeyManager:
    def __init__(self, db):
        self.db = db
    
    async def create_api_key(self, user_id: str, name: str, scopes: List[str]):
        """创建API密钥"""
        api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        await self.db.api_keys.insert({
            "user_id": user_id,
            "name": name,
            "key_hash": key_hash,
            "scopes": scopes,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True
        })
        
        return api_key  # 只返回一次，用户需要保存
    
    async def validate_api_key(self, api_key: str):
        """验证API密钥"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        key_data = await self.db.api_keys.find_one({
            "key_hash": key_hash,
            "is_active": True
        })
        
        if not key_data:
            return None
        
        # 更新最后使用时间
        await self.db.api_keys.update_one(
            {"_id": key_data["_id"]},
            {"$set": {"last_used": datetime.utcnow()}}
        )
        
        return key_data

# 权限控制
class PermissionChecker:
    def __init__(self):
        self.permissions = {
            "read": ["projects.read", "documents.read"],
            "write": ["projects.write", "documents.write", "tasks.write"],
            "admin": ["*"]
        }
    
    def has_permission(self, user_scopes: List[str], required_permission: str):
        """检查用户是否有权限"""
        # 管理员有所有权限
        if "*" in user_scopes:
            return True
        
        # 检查具体权限
        return required_permission in user_scopes
    
    def require_permission(self, permission: str):
        """权限装饰器"""
        def decorator(func):
            async def wrapper(*args, user=Depends(get_current_user), **kwargs):
                if not self.has_permission(user.scopes, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission denied: {permission}"
                    )
                return await func(*args, user=user, **kwargs)
            return wrapper
        return decorator

# 使用示例
permission_checker = PermissionChecker()

@app.post("/api/v1/projects")
@permission_checker.require_permission("projects.write")
async def create_project(project_data: dict, user=Depends(get_current_user)):
    # 创建项目
    pass
```

### 多租户支持
```python
from typing import Optional

class TenantManager:
    def __init__(self, db):
        self.db = db
    
    async def create_tenant(self, name: str, owner_id: str):
        """创建租户"""
        tenant = {
            "name": name,
            "owner_id": owner_id,
            "members": [owner_id],
            "settings": {
                "max_projects": 100,
                "max_storage_gb": 100,
                "max_api_calls_per_month": 100000
            },
            "usage": {
                "projects": 0,
                "storage_gb": 0,
                "api_calls_this_month": 0
            },
            "created_at": datetime.utcnow()
        }
        
        result = await self.db.tenants.insert_one(tenant)
        return result.inserted_id
    
    async def add_member(self, tenant_id: str, user_id: str, role: str = "member"):
        """添加成员到租户"""
        await self.db.tenants.update_one(
            {"_id": tenant_id},
            {
                "$addToSet": {"members": user_id},
                "$set": {f"roles.{user_id}": role}
            }
        )
    
    async def check_quota(self, tenant_id: str, resource: str, amount: int = 1):
        """检查配额"""
        tenant = await self.db.tenants.find_one({"_id": tenant_id})
        
        if not tenant:
            raise TenantNotFoundError()
        
        settings = tenant["settings"]
        usage = tenant["usage"]
        
        if resource == "projects":
            return usage["projects"] + amount <= settings["max_projects"]
        elif resource == "storage_gb":
            return usage["storage_gb"] + amount <= settings["max_storage_gb"]
        elif resource == "api_calls":
            return usage["api_calls_this_month"] + amount <= settings["max_api_calls_per_month"]
        
        return False
    
    async def update_usage(self, tenant_id: str, resource: str, amount: int):
        """更新使用量"""
        await self.db.tenants.update_one(
            {"_id": tenant_id},
            {"$inc": {f"usage.{resource}": amount}}
        )

# 租户隔离中间件
class TenantMiddleware:
    def __init__(self, tenant_manager: TenantManager):
        self.tenant_manager = tenant_manager
    
    async def __call__(self, request, call_next):
        # 从请求头获取租户ID
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if not tenant_id and request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=400,
                content={"detail": "Tenant ID required"}
            )
        
        # 验证租户和配额
        if tenant_id:
            # 检查API调用配额
            can_proceed = await self.tenant_manager.check_quota(
                tenant_id, "api_calls", 1
            )
            
            if not can_proceed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "API quota exceeded"}
                )
            
            # 更新使用量
            await self.tenant_manager.update_usage(
                tenant_id, "api_calls", 1
            )
        
        # 将租户ID添加到请求状态
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response
```

## 错误处理

### 统一错误处理
```python
from typing import Union, Optional
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
    request_id: Optional[str] = None

class DPAException(Exception):
    """DPA基础异常类"""
    def __init__(self, error_code: str, message: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message)

class ValidationError(DPAException):
    """验证错误"""
    def __init__(self, field: str, message: str):
        super().__init__(
            "VALIDATION_ERROR",
            f"Validation failed for field '{field}': {message}",
            {"field": field, "message": message}
        )

class ResourceNotFoundError(DPAException):
    """资源不存在"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            "RESOURCE_NOT_FOUND",
            f"{resource_type} with id '{resource_id}' not found",
            {"resource_type": resource_type, "resource_id": resource_id}
        )

class QuotaExceededError(DPAException):
    """配额超限"""
    def __init__(self, resource: str, limit: int, current: int):
        super().__init__(
            "QUOTA_EXCEEDED",
            f"Quota exceeded for {resource}. Limit: {limit}, Current: {current}",
            {"resource": resource, "limit": limit, "current": current}
        )

# 全局错误处理器
@app.exception_handler(DPAException)
async def dpa_exception_handler(request, exc: DPAException):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request.state.request_id
        ).dict()
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request.state.request_id
        ).dict()
    )

# 重试机制
from tenacity import retry, stop_after_attempt, wait_exponential

class RetryableClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def call_external_api(self, url: str, **kwargs):
        """可重试的外部API调用"""
        async with aiohttp.ClientSession() as session:
            async with session.post(url, **kwargs) as response:
                if response.status >= 500:
                    raise ConnectionError(f"Server error: {response.status}")
                return await response.json()
```

## 性能优化

### 缓存策略
```python
from functools import lru_cache
import redis.asyncio as aioredis
from typing import Optional
import pickle

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = None
        self.redis_url = redis_url
        self.default_ttl = 3600  # 1小时
    
    async def connect(self):
        self.redis = await aioredis.from_url(self.redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        value = await self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        serialized = pickle.dumps(value)
        await self.redis.setex(key, ttl, serialized)
    
    async def delete(self, key: str):
        """删除缓存"""
        await self.redis.delete(key)
    
    async def clear_pattern(self, pattern: str):
        """清除匹配模式的缓存"""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
    
    def cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        parts = [prefix]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return ":".join(parts)

# 装饰器
def cached(prefix: str, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # 生成缓存键
            cache_key = self.cache_manager.cache_key(
                prefix,
                args=str(args),
                kwargs=str(kwargs)
            )
            
            # 尝试从缓存获取
            cached_value = await self.cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(self, *args, **kwargs)
            
            # 存入缓存
            await self.cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# 使用示例
class ProjectService:
    def __init__(self, db, cache_manager):
        self.db = db
        self.cache_manager = cache_manager
    
    @cached("project", ttl=300)
    async def get_project(self, project_id: str):
        """获取项目（带缓存）"""
        return await self.db.projects.find_one({"_id": project_id})
    
    async def update_project(self, project_id: str, data: dict):
        """更新项目（清除缓存）"""
        result = await self.db.projects.update_one(
            {"_id": project_id},
            {"$set": data}
        )
        
        # 清除相关缓存
        cache_key = self.cache_manager.cache_key(
            "project",
            args=f"('{project_id}',)",
            kwargs="{}"
        )
        await self.cache_manager.delete(cache_key)
        
        return result
```

### 批量操作优化
```python
from typing import List, Dict
import asyncio

class BatchProcessor:
    def __init__(self, batch_size: int = 100, max_concurrent: int = 10):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(self, items: List[Any], processor_func):
        """批量处理项目"""
        results = []
        
        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # 并发处理批次
            batch_tasks = []
            for item in batch:
                task = self._process_with_semaphore(processor_func, item)
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
        
        return results
    
    async def _process_with_semaphore(self, func, item):
        """使用信号量限制并发"""
        async with self.semaphore:
            try:
                return await func(item)
            except Exception as e:
                return {"error": str(e), "item": item}

# 数据库批量操作
class BatchDatabaseOperations:
    def __init__(self, db):
        self.db = db
    
    async def bulk_insert(self, collection: str, documents: List[Dict]):
        """批量插入"""
        if not documents:
            return []
        
        # 分批插入
        batch_size = 1000
        inserted_ids = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = await self.db[collection].insert_many(batch)
            inserted_ids.extend(result.inserted_ids)
        
        return inserted_ids
    
    async def bulk_update(self, collection: str, updates: List[Dict]):
        """批量更新"""
        # 使用bulk_write进行批量更新
        operations = []
        
        for update in updates:
            operation = {
                "update_one": {
                    "filter": update["filter"],
                    "update": update["update"],
                    "upsert": update.get("upsert", False)
                }
            }
            operations.append(operation)
        
        if operations:
            result = await self.db[collection].bulk_write(operations)
            return {
                "matched": result.matched_count,
                "modified": result.modified_count,
                "upserted": result.upserted_count
            }
        
        return {"matched": 0, "modified": 0, "upserted": 0}
```

### 查询优化
```python
class QueryOptimizer:
    def __init__(self, db):
        self.db = db
    
    async def create_indexes(self):
        """创建优化索引"""
        # 项目集合索引
        await self.db.projects.create_index([
            ("user_id", 1),
            ("status", 1),
            ("created_at", -1)
        ])
        
        await self.db.projects.create_index([
            ("name", "text"),
            ("description", "text")
        ])
        
        # 文档集合索引
        await self.db.documents.create_index([
            ("project_id", 1),
            ("status", 1)
        ])
        
        await self.db.documents.create_index([
            ("title", "text"),
            ("content", "text")
        ])
        
        # 任务集合索引
        await self.db.tasks.create_index([
            ("project_id", 1),
            ("status", 1),
            ("priority", -1)
        ])
    
    def optimize_query(self, query: Dict) -> Dict:
        """优化查询条件"""
        optimized = {}
        
        # 使用索引字段
        indexed_fields = ["user_id", "project_id", "status", "created_at"]
        for field in indexed_fields:
            if field in query:
                optimized[field] = query[field]
        
        # 优化文本搜索
        if "text_search" in query:
            optimized["$text"] = {"$search": query["text_search"]}
        
        # 优化日期范围查询
        if "date_from" in query or "date_to" in query:
            date_query = {}
            if "date_from" in query:
                date_query["$gte"] = query["date_from"]
            if "date_to" in query:
                date_query["$lte"] = query["date_to"]
            optimized["created_at"] = date_query
        
        return optimized
    
    async def explain_query(self, collection: str, query: Dict):
        """分析查询性能"""
        explanation = await self.db[collection].find(query).explain()
        
        return {
            "execution_time_ms": explanation.get("executionTimeMillis", 0),
            "documents_examined": explanation.get("totalDocsExamined", 0),
            "documents_returned": explanation.get("nReturned", 0),
            "index_used": explanation.get("winningPlan", {}).get("indexName"),
            "stage": explanation.get("winningPlan", {}).get("stage")
        }
```

## 部署指南

### Docker部署
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 dpa && chown -R dpa:dpa /app
USER dpa

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose配置
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://dpa:password@postgres:5432/dpa
      - REDIS_URL=redis://redis:6379
      - NEO4J_URI=bolt://neo4j:7687
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - neo4j
      - qdrant
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=dpa
      - POSTGRES_USER=dpa
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass password
    volumes:
      - redis_data:/data
    restart: unless-stopped

  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
    volumes:
      - neo4j_data:/data
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
  qdrant_data:
```

### Kubernetes部署
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dpa-api
  labels:
    app: dpa-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dpa-api
  template:
    metadata:
      labels:
        app: dpa-api
    spec:
      containers:
      - name: api
        image: your-registry/dpa-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: dpa-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: dpa-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: dpa-api-service
spec:
  selector:
    app: dpa-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: dpa-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: dpa-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 监控配置
```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dpa-api'
    static_configs:
      - targets: ['dpa-api:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

# grafana-dashboard.json
{
  "dashboard": {
    "title": "DPA Monitoring",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

## 总结

本集成指南涵盖了DPA系统的主要集成场景和最佳实践。根据您的具体需求，可以选择合适的集成方式：

1. **SDK集成**：适合快速开发和原型验证
2. **REST API**：适合跨语言集成和微服务架构
3. **WebSocket**：适合需要实时更新的应用
4. **自定义工作流**：适合特定领域的专业应用
5. **插件开发**：适合扩展系统功能

记住以下关键点：
- 始终使用适当的错误处理
- 实施缓存策略提高性能
- 使用批量操作处理大量数据
- 监控系统性能和健康状态
- 定期更新和维护

如需更多帮助，请参考API文档或联系技术支持团队。