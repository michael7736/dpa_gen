# DPA Next 快速参考

## 🚀 快速命令

### 启动服务
```bash
# 一键启动所有服务
./start-all.sh

# 单独启动后端
uvicorn src.api.main:app --reload

# 单独启动前端
cd frontend && npm run dev
```

### 常用API调用

#### 创建项目
```bash
curl -X POST http://localhost:8001/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "项目名称",
    "type": "research"
  }'
```

#### 上传文档
```bash
curl -X POST http://localhost:8001/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" \
  -F "project_id=$PROJECT_ID"
```

#### 执行项目
```bash
curl -X POST http://localhost:8001/api/v1/projects/$PROJECT_ID/execute \
  -H "Authorization: Bearer $TOKEN"
```

#### 认知对话
```bash
curl -X POST http://localhost:8001/api/v1/cognitive/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你的问题",
    "project_id": "$PROJECT_ID"
  }'
```

## 📋 项目生命周期

```
创建 → 草稿 → 规划 → 执行 → 完成
        ↓       ↓       ↓
      可编辑  生成任务  自动运行
```

## 🔧 任务类型

| 类型 | 用途 | 典型时长 |
|-----|------|----------|
| data_collection | 收集数据 | 5-15分钟 |
| data_indexing | 建立索引 | 2-5分钟 |
| deep_analysis | 深度分析 | 10-30分钟 |
| verification | 验证结果 | 5-10分钟 |
| report_writing | 生成报告 | 5-15分钟 |

## 💾 记忆系统

| 类型 | 生命周期 | 用途 |
|-----|---------|------|
| working | 1小时 | 会话上下文 |
| task | 24小时 | 任务状态 |
| project | 永久 | 项目知识 |

## 🎯 质量指标

- **准确性** (accuracy): 0.0-1.0
- **完整性** (completeness): 0.0-1.0
- **相关性** (relevance): 0.0-1.0
- **一致性** (consistency): 0.0-1.0

## 📊 项目配置

```json
{
  "max_tasks": 20,        // 最大任务数
  "auto_execute": true,   // 自动执行
  "parallel_tasks": 3,    // 并行数
  "quality_threshold": 0.8, // 质量阈值
  "language": "zh-CN",    // 输出语言
  "enable_cache": true,   // 启用缓存
  "max_retries": 3       // 最大重试
}
```

## 🔍 搜索语法

```
# 基础搜索
keyword

# 短语搜索
"exact phrase"

# 布尔搜索
keyword1 AND keyword2
keyword1 OR keyword2
NOT keyword

# 字段搜索
title:keyword
content:keyword
tag:keyword

# 范围搜索
date:[2024-01-01 TO 2024-12-31]
score:[0.8 TO 1.0]
```

## 🛠️ 调试命令

```bash
# 查看日志
tail -f data/logs/app.log

# 检查服务状态
curl http://localhost:8001/health

# 数据库状态
python scripts/check_databases.py

# 清理缓存
redis-cli FLUSHALL

# 重置项目
python scripts/reset_project.py $PROJECT_ID
```

## 📈 性能优化

### 批量操作
```python
# 批量上传
files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
upload_batch(project_id, files)

# 批量查询
questions = ["问题1", "问题2", "问题3"]
batch_query(project_id, questions)
```

### 并行处理
```python
# 设置并行任务数
project_config = {
    "parallel_tasks": 5  # 根据CPU核心数调整
}
```

### 缓存策略
```python
# 启用Redis缓存
os.environ["ENABLE_CACHE"] = "true"
os.environ["CACHE_TTL"] = "3600"  # 秒
```

## 🔐 安全最佳实践

1. **定期更新令牌**
   ```bash
   # 每30天更新一次
   python scripts/rotate_tokens.py
   ```

2. **限制API访问**
   ```python
   # 配置速率限制
   RATE_LIMIT = "60/minute"
   ```

3. **数据加密**
   ```bash
   # 启用传输加密
   export ENABLE_SSL=true
   ```

## 📝 常用正则表达式

```python
# 提取邮箱
r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# 提取URL
r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'

# 提取中文
r'[\u4e00-\u9fa5]+'

# 提取数字
r'\d+\.?\d*'

# 提取日期
r'\d{4}-\d{2}-\d{2}'
```

## 🎨 输出格式

### Markdown报告
```markdown
# 项目报告

## 执行摘要
...

## 主要发现
1. 发现一
2. 发现二

## 详细分析
...

## 结论和建议
...
```

### JSON结构
```json
{
  "project_id": "uuid",
  "results": {
    "findings": [],
    "insights": [],
    "recommendations": []
  },
  "metadata": {
    "created_at": "2024-01-01T00:00:00Z",
    "quality_score": 0.85
  }
}
```

## 🔗 有用链接

- API文档: http://localhost:8001/docs
- 项目仓库: https://github.com/your-org/dpa
- 问题跟踪: https://github.com/your-org/dpa/issues
- 在线演示: https://demo.dpa.ai

## ⚡ 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建项目 |
| Ctrl+U | 上传文档 |
| Ctrl+Enter | 执行查询 |
| Ctrl+S | 保存当前状态 |
| Ctrl+/ | 显示帮助 |
| Esc | 取消操作 |

---

💡 **提示**: 将此页面打印或保存为PDF，方便随时查阅！