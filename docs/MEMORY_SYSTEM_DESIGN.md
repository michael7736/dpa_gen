# DPA记忆系统设计文档

## 1. 系统概述

DPA记忆系统是一个多层次、可扩展的智能记忆管理系统，旨在为文档处理和知识问答提供持久化的上下文记忆能力。系统支持项目级、用户级和会话级的记忆存储，并实现基于时间衰减的记忆管理机制。

## 2. 核心设计理念

### 2.1 多层次记忆架构
- **长期记忆（Long-term Memory）**：存储重要的项目知识、用户偏好
- **工作记忆（Working Memory）**：当前会话的上下文信息
- **情节记忆（Episodic Memory）**：具体的对话历史和事件
- **语义记忆（Semantic Memory）**：抽象的概念和知识

### 2.2 时间衰减机制
- 基于艾宾浩斯遗忘曲线的记忆衰减模型
- 重要性加权的记忆保留策略
- 访问频率驱动的记忆强化

### 2.3 智能记忆管理
- 自动记忆压缩和摘要
- 记忆关联和知识图谱构建
- 个性化记忆检索和推荐

## 3. 技术架构

### 3.1 数据存储层
```
PostgreSQL (结构化记忆)
├── memories (通用记忆表)
├── project_memories (项目记忆)
├── user_memories (用户记忆)
└── conversation_memories (对话记忆)

Neo4j (知识图谱)
├── 概念节点
├── 实体关系
└── 记忆关联

Redis (缓存层)
├── 热点记忆缓存
├── 会话状态
└── 临时计算结果
```

### 3.2 核心组件

#### 3.2.1 记忆管理器（MemoryManager）
- 统一的记忆CRUD接口
- 记忆生命周期管理
- 跨存储的记忆同步

#### 3.2.2 记忆索引器（MemoryIndexer）
- 记忆向量化和索引
- 相似记忆检索
- 记忆聚类和分类

#### 3.2.3 时间衰减引擎（DecayEngine）
- 记忆重要性计算
- 衰减曲线实现
- 记忆清理和归档

#### 3.2.4 知识图谱构建器（GraphBuilder）
- 实体抽取和关系识别
- 图谱增量更新
- 路径查询和推理

## 4. 记忆类型详解

### 4.1 项目记忆（Project Memory）
```python
{
    "context_summary": "项目整体背景和目标",
    "key_concepts": ["核心概念1", "核心概念2"],
    "research_goals": [
        {"goal": "目标描述", "progress": 0.7, "deadline": "2024-12-31"}
    ],
    "learned_facts": [
        {"fact": "发现的事实", "confidence": 0.9, "source": "doc_id"}
    ],
    "important_documents": ["doc_id_1", "doc_id_2"],
    "milestones": [
        {"name": "里程碑", "achieved": true, "date": "2024-01-15"}
    ]
}
```

### 4.2 用户记忆（User Memory）
```python
{
    "preferences": {
        "language": "zh",
        "response_style": "detailed",
        "expertise_level": "expert"
    },
    "interests": ["深度学习", "自然语言处理"],
    "query_patterns": [
        {"pattern": "比较.*区别", "frequency": 15}
    ],
    "interaction_history": {
        "total_queries": 156,
        "avg_session_duration": 1200,  # 秒
        "preferred_times": ["09:00-11:00", "14:00-17:00"]
    }
}
```

### 4.3 会话记忆（Session Memory）
```python
{
    "current_topic": "Transformer架构",
    "context_stack": [
        {"query": "什么是注意力机制", "timestamp": "2024-01-15T10:00:00"},
        {"query": "Self-attention的计算过程", "timestamp": "2024-01-15T10:05:00"}
    ],
    "entities_in_focus": ["BERT", "GPT", "Attention"],
    "pending_clarifications": ["位置编码的具体实现"]
}
```

## 5. 时间衰减算法

### 5.1 记忆强度计算
```python
def calculate_memory_strength(memory):
    """
    记忆强度 = 初始强度 × 衰减因子 × 重要性权重 × 访问强化
    """
    # 时间衰减（艾宾浩斯曲线）
    time_elapsed = now() - memory.created_at
    decay_factor = exp(-time_elapsed / decay_constant)
    
    # 重要性权重
    importance_weight = memory.importance
    
    # 访问强化（每次访问增强记忆）
    access_boost = 1 + log(1 + memory.access_count) * 0.1
    
    # 最终强度
    strength = initial_strength * decay_factor * importance_weight * access_boost
    
    return min(1.0, strength)
```

### 5.2 记忆清理策略
- 强度低于阈值（0.1）的记忆标记为待清理
- 重要记忆（importance > 0.8）永不清理
- 最近访问的记忆延迟清理

## 6. 知识图谱集成

### 6.1 图谱结构
```cypher
// 概念节点
(c:Concept {name: "深度学习", type: "技术"})

// 文档节点
(d:Document {id: "doc_123", title: "深度学习入门"})

// 用户节点
(u:User {id: "user_456", name: "张三"})

// 关系
(u)-[:INTERESTED_IN]->(c)
(d)-[:CONTAINS_CONCEPT]->(c)
(c1)-[:RELATED_TO {strength: 0.8}]->(c2)
```

### 6.2 图谱更新机制
- 实时更新：用户查询时动态添加节点和关系
- 批量更新：文档处理完成后批量导入
- 增量学习：基于用户反馈调整关系权重

## 7. 个性化推荐系统

### 7.1 推荐算法
```python
def recommend_content(user_id, context):
    """
    基于用户记忆的个性化推荐
    """
    # 1. 获取用户兴趣图谱
    user_interests = get_user_interest_graph(user_id)
    
    # 2. 分析当前上下文
    context_entities = extract_entities(context)
    
    # 3. 计算相关度分数
    recommendations = []
    for doc in candidate_documents:
        score = calculate_relevance(
            doc, 
            user_interests, 
            context_entities,
            user_query_history
        )
        recommendations.append((doc, score))
    
    # 4. 返回Top-K推荐
    return sorted(recommendations, key=lambda x: x[1], reverse=True)[:k]
```

### 7.2 推荐维度
- **内容相关性**：基于当前查询的语义相似度
- **兴趣匹配度**：与用户历史兴趣的匹配程度
- **知识进阶性**：符合用户当前知识水平的内容
- **时效性**：优先推荐最新或最近访问的内容

## 8. 实现计划

### 第1阶段：基础记忆管理（Week 2 - Day 1-2）
- [ ] 实现MemoryManager基础CRUD
- [ ] 实现记忆存储和检索API
- [ ] 集成到现有的问答系统

### 第2阶段：时间衰减机制（Week 2 - Day 3-4）
- [ ] 实现衰减算法
- [ ] 创建后台定时任务
- [ ] 实现记忆强化机制

### 第3阶段：知识图谱集成（Week 2 - Day 5-6）
- [ ] 设计图谱schema
- [ ] 实现实体抽取
- [ ] 实现图谱查询接口

### 第4阶段：个性化推荐（Week 2 - Day 7）
- [ ] 实现推荐算法
- [ ] 集成到API
- [ ] 性能优化

## 9. 性能考虑

### 9.1 缓存策略
- 热点记忆缓存在Redis
- LRU淘汰策略
- 预加载用户常用记忆

### 9.2 查询优化
- 记忆索引优化
- 批量查询支持
- 异步记忆更新

### 9.3 存储优化
- 记忆压缩存储
- 冷数据归档
- 分片存储策略

## 10. 监控指标

### 10.1 系统指标
- 记忆存储量
- 查询响应时间
- 缓存命中率

### 10.2 业务指标
- 记忆利用率
- 推荐准确度
- 用户满意度

## 11. 未来扩展

### 11.1 多模态记忆
- 支持图像、音频记忆
- 跨模态记忆关联

### 11.2 协作记忆
- 团队共享记忆
- 记忆权限管理

### 11.3 记忆迁移
- 跨项目记忆迁移
- 记忆导入导出