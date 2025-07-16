# DPA Next API 快速入门指南

## 目录
1. [环境准备](#环境准备)
2. [获取访问令牌](#获取访问令牌)
3. [基础操作示例](#基础操作示例)
4. [常见用例](#常见用例)
5. [错误处理](#错误处理)
6. [最佳实践](#最佳实践)

## 环境准备

### 1. 启动服务

```bash
# 激活conda环境
conda activate dpa_gen

# 启动后端服务
cd /path/to/DPA
uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload

# 或使用一键启动脚本
./start-all.sh
```

### 2. 安装客户端工具

#### Python
```bash
pip install requests
# 或安装DPA SDK（如果可用）
pip install dpa-sdk
```

#### JavaScript/Node.js
```bash
npm install axios
# 或安装DPA SDK（如果可用）
npm install @dpa/sdk
```

#### 命令行 (curl)
```bash
# macOS/Linux 自带curl
# Windows可以使用Git Bash或WSL
```

## 获取访问令牌

### 1. 注册新用户

```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!",
    "full_name": "测试用户"
  }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test123456!"
```

响应示例：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 3. 设置环境变量

```bash
# Linux/macOS
export DPA_TOKEN="your-access-token"

# Windows (CMD)
set DPA_TOKEN=your-access-token

# Windows (PowerShell)
$env:DPA_TOKEN="your-access-token"
```

## 基础操作示例

### Python示例

```python
import requests
import json
import os

# 配置
BASE_URL = "http://localhost:8001/api/v1"
TOKEN = os.getenv("DPA_TOKEN")
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建项目
def create_project(name, description, project_type="research"):
    data = {
        "name": name,
        "description": description,
        "type": project_type,
        "objectives": ["研究目标1", "研究目标2"]
    }
    
    response = requests.post(
        f"{BASE_URL}/projects",
        headers=headers,
        json=data
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        print(f"错误: {response.status_code} - {response.text}")
        return None

# 使用示例
project = create_project(
    name="GPT-4技术研究",
    description="深入研究GPT-4的技术原理和应用"
)

if project:
    print(f"项目创建成功！ID: {project['id']}")
```

### JavaScript/Node.js示例

```javascript
const axios = require('axios');

// 配置
const BASE_URL = 'http://localhost:8001/api/v1';
const TOKEN = process.env.DPA_TOKEN;

// 创建axios实例
const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
    }
});

// 创建项目
async function createProject(name, description, type = 'research') {
    try {
        const response = await api.post('/projects', {
            name,
            description,
            type,
            objectives: ['研究目标1', '研究目标2']
        });
        
        return response.data;
    } catch (error) {
        console.error('错误:', error.response?.data || error.message);
        return null;
    }
}

// 使用示例
(async () => {
    const project = await createProject(
        'GPT-4技术研究',
        '深入研究GPT-4的技术原理和应用'
    );
    
    if (project) {
        console.log(`项目创建成功！ID: ${project.id}`);
    }
})();
```

### cURL示例

```bash
# 创建项目
curl -X POST "http://localhost:8001/api/v1/projects" \
  -H "Authorization: Bearer $DPA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-4技术研究",
    "description": "深入研究GPT-4的技术原理和应用",
    "type": "research",
    "objectives": ["研究目标1", "研究目标2"]
  }'
```

## 常见用例

### 1. 完整的研究项目流程

```python
import requests
import time

class DPAClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_project(self, name, description):
        """创建项目"""
        response = requests.post(
            f"{self.base_url}/projects",
            headers=self.headers,
            json={
                "name": name,
                "description": description,
                "type": "research"
            }
        )
        return response.json()
    
    def upload_document(self, project_id, file_path, title):
        """上传文档"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'project_id': project_id,
                'title': title
            }
            headers = {"Authorization": f"Bearer {self.headers['Authorization'].split()[1]}"}
            response = requests.post(
                f"{self.base_url}/documents/upload",
                headers=headers,
                files=files,
                data=data
            )
        return response.json()
    
    def create_task(self, project_id, title, task_type):
        """创建任务"""
        response = requests.post(
            f"{self.base_url}/projects/{project_id}/tasks",
            headers=self.headers,
            json={
                "title": title,
                "type": task_type,
                "priority": 5
            }
        )
        return response.json()
    
    def execute_project(self, project_id):
        """执行项目"""
        response = requests.post(
            f"{self.base_url}/projects/{project_id}/execute",
            headers=self.headers
        )
        return response.json()
    
    def get_project_status(self, project_id):
        """获取项目状态"""
        response = requests.get(
            f"{self.base_url}/projects/{project_id}",
            headers=self.headers
        )
        return response.json()
    
    def cognitive_chat(self, message, project_id):
        """认知对话"""
        response = requests.post(
            f"{self.base_url}/cognitive/chat",
            headers=self.headers,
            json={
                "message": message,
                "project_id": project_id
            }
        )
        return response.json()

# 使用示例
def run_research_project():
    # 初始化客户端
    client = DPAClient(
        base_url="http://localhost:8001/api/v1",
        token=os.getenv("DPA_TOKEN")
    )
    
    # 1. 创建项目
    print("1. 创建研究项目...")
    project = client.create_project(
        name="AI伦理研究",
        description="研究人工智能的伦理问题和社会影响"
    )
    project_id = project["id"]
    print(f"   项目ID: {project_id}")
    
    # 2. 上传文档
    print("\n2. 上传研究文档...")
    doc = client.upload_document(
        project_id=project_id,
        file_path="./documents/ai_ethics.pdf",
        title="AI伦理指南"
    )
    print(f"   文档ID: {doc['id']}")
    
    # 3. 创建任务
    print("\n3. 创建研究任务...")
    tasks = [
        ("收集AI伦理相关文献", "data_collection"),
        ("分析主要伦理问题", "deep_analysis"),
        ("撰写研究报告", "report_writing")
    ]
    
    for title, task_type in tasks:
        task = client.create_task(project_id, title, task_type)
        print(f"   创建任务: {title} (ID: {task['id']})")
    
    # 4. 执行项目
    print("\n4. 开始执行项目...")
    execution = client.execute_project(project_id)
    print(f"   执行状态: {execution['status']}")
    
    # 5. 监控进度
    print("\n5. 监控项目进度...")
    for i in range(5):
        time.sleep(2)  # 等待2秒
        status = client.get_project_status(project_id)
        print(f"   进度: {status['progress']:.1%} - 状态: {status['status']}")
        
        if status['progress'] >= 1.0:
            break
    
    # 6. 认知对话
    print("\n6. 进行认知对话...")
    questions = [
        "AI伦理的主要问题有哪些？",
        "如何平衡技术发展和伦理约束？",
        "请总结研究的主要发现"
    ]
    
    for question in questions:
        print(f"\n   问: {question}")
        response = client.cognitive_chat(question, project_id)
        print(f"   答: {response['response'][:200]}...")

# 运行完整流程
if __name__ == "__main__":
    run_research_project()
```

### 2. 批量文档处理

```python
import os
import glob

def batch_upload_documents(client, project_id, folder_path):
    """批量上传文档"""
    # 支持的文件类型
    patterns = ['*.pdf', '*.docx', '*.txt', '*.md']
    
    uploaded = []
    
    for pattern in patterns:
        files = glob.glob(os.path.join(folder_path, pattern))
        
        for file_path in files:
            try:
                filename = os.path.basename(file_path)
                print(f"上传: {filename}")
                
                doc = client.upload_document(
                    project_id=project_id,
                    file_path=file_path,
                    title=filename
                )
                
                uploaded.append(doc)
                print(f"  ✓ 成功 - ID: {doc['id']}")
                
            except Exception as e:
                print(f"  ✗ 失败 - {str(e)}")
    
    return uploaded

# 使用示例
uploaded_docs = batch_upload_documents(
    client,
    project_id,
    "./research_papers/"
)
print(f"\n总共上传 {len(uploaded_docs)} 个文档")
```

### 3. 实时进度监控

```javascript
// WebSocket连接监控项目执行
function monitorProjectExecution(projectId) {
    const ws = new WebSocket(`ws://localhost:8001/ws/projects/${projectId}`);
    
    ws.onopen = () => {
        console.log('WebSocket连接已建立');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'execution_update':
                console.log(`进度: ${(data.data.progress * 100).toFixed(1)}%`);
                console.log(`当前任务: ${data.data.current_task}`);
                break;
                
            case 'task_completed':
                console.log(`✓ 任务完成: ${data.data.task_title}`);
                break;
                
            case 'error':
                console.error(`错误: ${data.data.message}`);
                break;
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket连接已关闭');
    };
    
    return ws;
}

// 使用示例
const ws = monitorProjectExecution('550e8400-e29b-41d4-a716-446655440000');

// 清理
// ws.close();
```

## 错误处理

### Python错误处理示例

```python
import requests
from requests.exceptions import RequestException

def safe_api_call(func):
    """API调用装饰器，统一处理错误"""
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            response.raise_for_status()  # 检查HTTP错误
            return response.json()
        
        except requests.HTTPError as e:
            # HTTP错误（4xx, 5xx）
            error_data = e.response.json() if e.response else {}
            print(f"API错误 [{e.response.status_code}]: {error_data.get('detail', '未知错误')}")
            return None
            
        except RequestException as e:
            # 网络错误
            print(f"网络错误: {str(e)}")
            return None
            
        except Exception as e:
            # 其他错误
            print(f"未知错误: {str(e)}")
            return None
    
    return wrapper

# 使用装饰器
@safe_api_call
def get_project(project_id):
    return requests.get(
        f"{BASE_URL}/projects/{project_id}",
        headers=headers
    )

# 调用示例
project = get_project("invalid-uuid")
if project:
    print(f"项目名称: {project['name']}")
else:
    print("获取项目失败")
```

### JavaScript错误处理示例

```javascript
// 创建带有拦截器的axios实例
const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Authorization': `Bearer ${TOKEN}`
    }
});

// 响应拦截器
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response) {
            // 服务器响应了错误状态码
            const { status, data } = error.response;
            
            switch(status) {
                case 401:
                    console.error('认证失败，请重新登录');
                    // 可以触发重新登录流程
                    break;
                case 404:
                    console.error('资源不存在');
                    break;
                case 422:
                    console.error('请求参数错误:', data.detail);
                    break;
                default:
                    console.error(`API错误 [${status}]:`, data.detail || '未知错误');
            }
        } else if (error.request) {
            // 请求已发送但没有收到响应
            console.error('网络错误，请检查连接');
        } else {
            // 其他错误
            console.error('请求错误:', error.message);
        }
        
        return Promise.reject(error);
    }
);

// 使用示例
async function safeGetProject(projectId) {
    try {
        const response = await api.get(`/projects/${projectId}`);
        return response.data;
    } catch (error) {
        // 错误已经被拦截器处理
        return null;
    }
}
```

## 最佳实践

### 1. 使用环境变量管理配置

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_BASE_URL = os.getenv('DPA_API_URL', 'http://localhost:8001/api/v1')
    API_TOKEN = os.getenv('DPA_API_TOKEN')
    API_TIMEOUT = int(os.getenv('DPA_API_TIMEOUT', '30'))
    
    @classmethod
    def validate(cls):
        if not cls.API_TOKEN:
            raise ValueError("DPA_API_TOKEN环境变量未设置")

# 使用
Config.validate()
```

### 2. 实现重试机制

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1.0, backoff=2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise e
                    
                    print(f"请求失败 (尝试 {attempt}/{max_attempts})，{current_delay}秒后重试...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator

# 使用示例
@retry(max_attempts=3, delay=1.0)
def upload_large_document(file_path):
    # 上传大文件的代码
    pass
```

### 3. 分页处理大量数据

```python
def get_all_projects(client):
    """获取所有项目（自动处理分页）"""
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
        skip += limit
        
        # 防止无限循环
        if len(projects) < limit:
            break
    
    return all_projects
```

### 4. 异步并发请求

```python
import asyncio
import aiohttp

async def fetch_document(session, doc_id):
    """异步获取文档"""
    async with session.get(f"/documents/{doc_id}") as response:
        return await response.json()

async def batch_fetch_documents(doc_ids):
    """批量获取文档"""
    async with aiohttp.ClientSession(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {TOKEN}"}
    ) as session:
        tasks = [fetch_document(session, doc_id) for doc_id in doc_ids]
        return await asyncio.gather(*tasks)

# 使用示例
doc_ids = ["doc1", "doc2", "doc3", "doc4", "doc5"]
documents = asyncio.run(batch_fetch_documents(doc_ids))
```

### 5. 日志记录

```python
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'dpa_api_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('dpa_client')

class DPAClientWithLogging(DPAClient):
    def create_project(self, name, description):
        logger.info(f"创建项目: {name}")
        try:
            result = super().create_project(name, description)
            logger.info(f"项目创建成功: {result['id']}")
            return result
        except Exception as e:
            logger.error(f"项目创建失败: {str(e)}")
            raise
```

## 故障排除

### 常见问题

1. **401 Unauthorized**
   - 检查token是否过期
   - 确认token格式正确（Bearer前缀）
   
2. **连接被拒绝**
   - 确认服务已启动
   - 检查端口是否正确（8001）
   - 防火墙设置

3. **422 Unprocessable Entity**
   - 检查请求参数格式
   - 查看错误详情中的字段验证信息

4. **文件上传失败**
   - 确认文件大小未超限（50MB）
   - 检查文件格式是否支持
   - 使用multipart/form-data格式

## 更多资源

- [完整API文档](./DPA_API_DOCUMENTATION.md)
- [OpenAPI规范](../openapi.yaml)
- [SDK使用指南](#)（即将发布）
- [示例项目](https://github.com/dpa/examples)（即将发布）

---

需要帮助？请联系 support@dpa.ai