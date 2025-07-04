# API限流和版本控制指南

## 概述

DPA智能知识引擎实现了完善的API限流和版本控制机制，确保系统稳定性和向后兼容性。

## 限流机制

### 限流策略

系统支持三种限流维度：
- **每分钟请求数**：默认60次
- **每小时请求数**：默认1000次
- **每天请求数**：默认10000次

### 限流级别

预定义了四种限流策略：

```python
RATE_LIMITS = {
    "strict": create_rate_limiter(10, 100, 1000),      # 严格限制
    "normal": create_rate_limiter(60, 1000, 10000),    # 正常限制
    "relaxed": create_rate_limiter(120, 2000, 20000),  # 宽松限制
    "unlimited": lambda request: True                    # 无限制
}
```

### 使用方法

1. **全局限流**（通过中间件自动应用）：
```python
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000
)
```

2. **路由级限流**：
```python
@router.get("/limited", dependencies=[Depends(RATE_LIMITS["strict"])])
async def limited_endpoint():
    return {"message": "This endpoint has strict rate limits"}
```

### 限流响应

当触发限流时，API将返回：
- **状态码**：429 (Too Many Requests)
- **响应体**：
```json
{
    "error": "Rate limit exceeded",
    "message": "请求过于频繁，请稍后再试",
    "retry_after": 45
}
```
- **响应头**：
  - `Retry-After`：建议的重试时间（秒）
  - `X-RateLimit-Limit`：限流阈值
  - `X-RateLimit-Window`：时间窗口

## 版本控制

### 版本定义

系统支持多个API版本：
- **v1**：基础版本（当前版本）
- **v2**：增强版本（规划中）

### 版本特性

每个版本定义了不同的特性集：

**V1特性**：
- `basic_auth`：基础认证
- `document_processing`：文档处理
- `vector_search`：向量搜索

**V2特性**（包含V1所有特性）：
- `knowledge_graph`：知识图谱
- `advanced_rag`：高级RAG
- `streaming_response`：流式响应

### 指定API版本

有三种方式指定API版本：

1. **URL路径**：
```
GET /api/v2/documents
```

2. **请求头**：
```
X-API-Version: v2
```

3. **查询参数**：
```
GET /api/documents?api_version=v2
```

### 版本要求

某些端点可能需要特定版本：

```python
@require_api_version(min_version="v2", features=["advanced_rag"])
async def advanced_endpoint():
    return {"message": "This requires v2 with advanced_rag feature"}
```

### 弃用管理

标记端点为已弃用：

```python
@deprecated_endpoint(sunset_date="2025-12-31", alternative="/api/v2/new-endpoint")
async def old_endpoint():
    return {"message": "This endpoint is deprecated"}
```

弃用端点的响应头：
- `X-API-Deprecated: true`
- `X-API-Sunset: 2025-12-31`
- `X-API-Alternative: /api/v2/new-endpoint`

## 示例代码

### Python客户端示例

```python
import httpx

# 创建客户端
client = httpx.Client(base_url="http://localhost:8000")

# 1. 基础请求
response = client.get("/api/v1/demo/basic")

# 2. 带版本头的请求
response = client.get(
    "/api/demo/endpoint",
    headers={"X-API-Version": "v2"}
)

# 3. 处理限流
try:
    response = client.get("/api/v1/demo/limited")
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        print(f"Rate limited. Retry after {retry_after} seconds")
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        print("Too many requests")
```

### JavaScript客户端示例

```javascript
// 基础请求
const response = await fetch('http://localhost:8000/api/v1/demo/basic');

// 带版本头的请求
const response = await fetch('http://localhost:8000/api/demo/endpoint', {
    headers: {
        'X-API-Version': 'v2'
    }
});

// 处理限流
if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    console.log(`Rate limited. Retry after ${retryAfter} seconds`);
}
```

## 最佳实践

1. **客户端限流处理**：
   - 实现指数退避算法
   - 尊重Retry-After头部
   - 本地缓存请求结果

2. **版本迁移**：
   - 监控弃用警告
   - 提前测试新版本
   - 逐步迁移端点

3. **性能优化**：
   - 批量请求代替多次单独请求
   - 使用条件请求（If-Modified-Since）
   - 实现客户端缓存

## 监控和调试

### 查看限流状态

```bash
# 使用Redis CLI查看限流计数
redis-cli -h rtx4080
> KEYS rate_limit:*
> GET rate_limit:ip:192.168.1.100:minute
```

### 测试脚本

运行测试脚本验证功能：

```bash
python tests/test_rate_limit_and_versioning.py
```

## 配置参考

### 环境变量

```env
# 限流配置
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# 版本配置
API_CURRENT_VERSION=v1
API_MINIMUM_VERSION=v1
```

### 动态调整

限流参数可以通过管理API动态调整（需要管理员权限）。