# DPA V3认知系统前端集成指南

## 概述

本文档介绍如何在前端使用V3认知系统的功能，包括认知对话、系统状态监控和记忆库查询等。

## 快速开始

### 1. 环境准备

```bash
# 确保后端API运行在8001端口
cd /Users/mdwong001/Desktop/code/rag/DPA
conda activate dpa_gen
uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload

# 启动前端开发服务器（8031端口）
cd frontend
npm install
npm run dev
```

### 2. 访问认知对话页面

1. 打开浏览器访问 http://localhost:8031
2. 在侧边栏点击"认知对话"
3. 选择一个项目开始对话

## 认知对话功能

### 主要特性

1. **智能对话**
   - 基于四层记忆模型的深度理解
   - 三阶段混合检索（向量+图谱+记忆库）
   - 元认知引擎自动选择最佳策略

2. **认知策略**
   - 🔆 探索(Exploration): 发现新知识和模式
   - 💾 利用(Exploitation): 使用已有知识回答
   - ✓ 验证(Verification): 确认和验证信息
   - 🧠 反思(Reflection): 深度思考和总结
   - 🔗 适应(Adaptation): 调整策略和方法

3. **实时状态监控**
   - 系统健康状态
   - 组件在线状态
   - 处理时间统计
   - 置信度评估

### 使用示例

```javascript
// 发送认知对话请求
const response = await cognitiveService.chat({
  message: "请分析这个技术方案的优缺点",
  project_id: "proj_123",
  use_memory: true,
  max_results: 10
});

// 响应包含
{
  conversation_id: "conv_abc123",
  response: "基于深度分析...",
  strategy_used: "reflection",
  confidence_score: 0.85,
  sources: [...],
  metacognitive_state: {...},
  processing_time: 3.2
}
```

## API接口说明

### 1. 认知对话

```typescript
POST /api/v1/cognitive/chat
{
  "request": {
    "message": "你的问题",
    "project_id": "项目ID",
    "conversation_id": "会话ID（可选）",
    "use_memory": true,
    "strategy": "exploration",  // 可选，指定策略
    "max_results": 10
  }
}
```

### 2. 系统健康检查

```typescript
GET /api/v1/cognitive/health

// 返回
{
  "status": "healthy",
  "components": {
    "storage": "online",
    "memory_bank": "online",
    "workflow": "online",
    "s2_chunker": "online",
    "retrieval_system": "online",
    "metacognitive_engine": "online"
  }
}
```

### 3. 认知分析

```typescript
POST /api/v1/cognitive/analyze
{
  "request": {
    "document_text": "文档内容",
    "project_id": "项目ID",
    "analysis_type": "deep",
    "analysis_goal": "提取关键技术点",
    "enable_metacognition": true
  }
}
```

### 4. 记忆库查询

```typescript
POST /api/v1/cognitive/memory/query
{
  "request": {
    "query": "查询内容",
    "project_id": "项目ID",
    "memory_types": ["concepts", "insights", "hypotheses"],
    "limit": 20
  }
}
```

## 前端组件说明

### CognitivePage组件

主要认知对话页面，包含：
- 左侧：系统状态面板和策略说明
- 右侧：对话区域
- 底部：输入框

### 关键状态管理

```typescript
// 消息状态
const [messages, setMessages] = useState<CognitiveMessage[]>([])

// 会话ID
const [conversationId, setConversationId] = useState<string | null>(null)

// 使用React Query管理API调用
const chatMutation = useMutation({
  mutationFn: cognitiveService.chat,
  // ...
})
```

## 测试方法

### 手动测试

1. 访问认知对话页面
2. 输入测试问题：
   - "你好，请介绍一下认知系统"
   - "帮我分析这个项目的技术架构"
   - "总结一下最近的研究进展"
3. 观察响应内容、策略选择和置信度

### 自动化测试

```bash
# 运行前端E2E测试
cd frontend
node test_cognitive_frontend.js
```

## 常见问题

### 1. 认知对话无响应

- 检查后端API是否运行（端口8001）
- 查看浏览器控制台错误信息
- 确认已选择项目

### 2. 系统状态显示离线

- 检查数据库连接（PostgreSQL, Neo4j, Qdrant, Redis）
- 查看后端日志 `tail -f api_server.log`

### 3. 响应速度慢

- 首次请求需要初始化组件（约5-10秒）
- 复杂查询可能需要更长时间
- 检查网络连接

## 最佳实践

1. **问题表述**
   - 清晰具体的问题获得更好的回答
   - 提供上下文信息有助于理解

2. **策略选择**
   - 让系统自动选择策略通常效果最好
   - 特定场景可以手动指定策略

3. **性能优化**
   - 限制检索结果数量（max_results）
   - 对长文档先进行分析再提问

## 后续开发计划

1. **功能增强**
   - [ ] 支持多轮对话上下文
   - [ ] 添加语音输入支持
   - [ ] 实现对话历史导出

2. **可视化改进**
   - [ ] 知识图谱可视化
   - [ ] 认知过程动画展示
   - [ ] 注意力权重热图

3. **性能优化**
   - [ ] 响应流式传输
   - [ ] 客户端缓存策略
   - [ ] 预加载常用数据