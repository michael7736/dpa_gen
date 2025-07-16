# DPA记忆系统架构图

## 系统总体架构

```mermaid
graph TB
    subgraph "用户交互层"
        U[用户] --> API[API Gateway]
        API --> WF[LangGraph Workflow]
    end
    
    subgraph "认知处理层"
        WF --> CE[认知引擎]
        
        subgraph "认知循环"
            CE --> P[感知 Perceive]
            P --> A[注意 Attend]
            A --> E[编码 Encode]
            E --> S[存储 Store]
            S --> R[检索 Retrieve]
            R --> RS[推理 Reason]
            RS --> PL[规划 Plan]
            PL --> EX[执行 Execute]
            EX --> RF[反思 Reflect]
            RF --> P
        end
    end
    
    subgraph "记忆层次"
        SM[感觉记忆<br/>Sensory Memory<br/><1秒]
        WM[工作记忆<br/>Working Memory<br/>7±2项]
        EM[情节记忆<br/>Episodic Memory<br/>中期存储]
        LTM[语义记忆<br/>Semantic Memory<br/>长期知识]
        
        SM --> WM
        WM --> EM
        EM --> LTM
    end
    
    subgraph "存储后端"
        PG[(PostgreSQL<br/>检查点/状态)]
        NEO[(Neo4j<br/>知识图谱)]
        QD[(Qdrant<br/>向量索引)]
        RD[(Redis<br/>缓存层)]
    end
    
    subgraph "记忆库文件系统"
        MB[Memory Bank]
        MB --> MD[metadata.json]
        MB --> SD[source_documents.md]
        MB --> KC[key_concepts.md]
        MB --> DS[dynamic_summary.md]
        MB --> LJ[learning_journal/]
        MB --> HY[hypotheses/]
    end
    
    CE --> SM
    CE --> WM
    CE --> EM
    CE --> LTM
    
    WM --> PG
    EM --> PG
    LTM --> NEO
    LTM --> QD
    SM --> RD
    
    CE --> MB
```

## 数据流架构

```mermaid
sequenceDiagram
    participant U as 用户
    participant LG as LangGraph
    participant HR as 混合检索
    participant GNN as GNN学习
    participant MB as 记忆库
    participant KG as 知识图谱
    
    U->>LG: 输入查询/文档
    LG->>LG: 状态初始化
    
    alt 文档处理
        LG->>LG: S2语义分块
        LG->>KG: 抽取实体关系
        LG->>MB: 更新source_documents.md
    else 查询处理
        LG->>HR: 三阶段检索
        HR->>HR: 1.向量搜索入口点
        HR->>KG: 2.图遍历扩展
        HR->>MB: 3.记忆库增强
        HR-->>LG: 融合结果
    end
    
    LG->>GNN: 识别知识盲点
    GNN->>GNN: 链接预测
    GNN-->>LG: 生成假设
    
    LG->>MB: 更新动态摘要
    LG->>MB: 记录学习计划
    LG-->>U: 返回结果
```

## 核心组件交互

```mermaid
graph LR
    subgraph "LangGraph状态机"
        S[State] --> N1[感知节点]
        N1 --> N2[处理节点]
        N2 --> N3[推理节点]
        N3 --> N4[学习节点]
        N4 --> N5[执行节点]
        N5 --> S
    end
    
    subgraph "混合检索系统"
        Q[查询] --> VE[向量嵌入]
        VE --> VS[向量搜索]
        VS --> GS[图搜索]
        GS --> MBS[记忆库搜索]
        MBS --> F[结果融合]
    end
    
    subgraph "GNN主动学习"
        KG2[知识图谱] --> GE[图嵌入]
        GE --> LP[链接预测]
        LP --> HG[假设生成]
        HG --> VH[假设验证]
        VH --> KG2
    end
```

## 记忆生命周期

```mermaid
stateDiagram-v2
    [*] --> 感觉缓冲: 输入
    感觉缓冲 --> 工作记忆: 注意力选择
    
    state 工作记忆 {
        [*] --> 活跃
        活跃 --> 压缩: 超过容量
        压缩 --> 活跃: 保留重要项
    }
    
    工作记忆 --> 情节记忆: 整合
    
    state 情节记忆 {
        [*] --> 新记忆
        新记忆 --> 巩固中: 访问强化
        巩固中 --> 成熟: 时间+重复
    }
    
    情节记忆 --> 语义记忆: 抽象化
    
    state 语义记忆 {
        [*] --> 概念
        概念 --> 关系: 链接
        关系 --> 网络: 图谱化
    }
    
    语义记忆 --> 衰减: 长期未访问
    衰减 --> 归档: 低于阈值
    归档 --> [*]
```

## 技术栈分层

```mermaid
graph TD
    subgraph "应用层"
        API[FastAPI]
        WEB[Web界面]
    end
    
    subgraph "智能层"
        LG[LangGraph 0.2+]
        LC[LangChain 0.3.26]
        OAI[OpenAI GPT-4]
    end
    
    subgraph "处理层"
        S2[S2分块算法]
        EMB[Embedding模型]
        GNN[PyTorch Geometric]
    end
    
    subgraph "数据层"
        PG[PostgreSQL 15+]
        NEO[Neo4j 5.0+]
        QD[Qdrant 1.7+]
        RD[Redis 7.0+]
    end
    
    subgraph "基础设施"
        DOC[Docker]
        K8S[Kubernetes]
        PROM[Prometheus]
    end
    
    API --> LG
    WEB --> API
    LG --> LC
    LC --> OAI
    LG --> S2
    S2 --> EMB
    LG --> GNN
    
    LG --> PG
    LC --> NEO
    EMB --> QD
    LG --> RD
    
    PG --> DOC
    NEO --> DOC
    QD --> DOC
    RD --> DOC
    DOC --> K8S
    K8S --> PROM
```

## 性能指标监控

```mermaid
graph LR
    subgraph "监控指标"
        M1[内存使用率]
        M2[查询延迟]
        M3[文档处理速度]
        M4[知识增长率]
        M5[假设准确率]
    end
    
    subgraph "告警阈值"
        A1[内存 > 80%]
        A2[P99延迟 > 200ms]
        A3[处理 < 5K tokens/s]
        A4[增长率 < 10%/天]
        A5[准确率 < 70%]
    end
    
    subgraph "优化动作"
        O1[触发GC]
        O2[扩容缓存]
        O3[并行处理]
        O4[调整学习策略]
        O5[人工审核]
    end
    
    M1 --> A1 --> O1
    M2 --> A2 --> O2
    M3 --> A3 --> O3
    M4 --> A4 --> O4
    M5 --> A5 --> O5
```

## 部署拓扑

```mermaid
graph TB
    subgraph "前端"
        LB[负载均衡器]
        API1[API实例1]
        API2[API实例2]
        API3[API实例3]
    end
    
    subgraph "处理集群"
        W1[Worker 1<br/>文档处理]
        W2[Worker 2<br/>查询处理]
        W3[Worker 3<br/>学习任务]
    end
    
    subgraph "数据集群"
        PG_M[PostgreSQL主]
        PG_S[PostgreSQL从]
        NEO_C[Neo4j集群]
        QD_C[Qdrant集群]
        RD_C[Redis集群]
    end
    
    subgraph "存储"
        S3[对象存储<br/>记忆库备份]
        NFS[共享存储<br/>记忆库文件]
    end
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> W1
    API2 --> W2
    API3 --> W3
    
    W1 --> PG_M
    W2 --> NEO_C
    W3 --> QD_C
    
    PG_M --> PG_S
    W1 --> NFS
    NFS --> S3
```

---

这些架构图展示了DPA记忆系统的：
- 🏗️ **总体架构**：从用户交互到存储后端的完整视图
- 🔄 **数据流程**：文档处理和查询处理的序列
- 🔗 **组件交互**：核心组件之间的协作关系
- 📊 **生命周期**：记忆在不同层次间的流转
- 🛠️ **技术栈**：各层使用的具体技术
- 📈 **监控体系**：性能指标和优化策略
- 🌐 **部署架构**：生产环境的部署拓扑