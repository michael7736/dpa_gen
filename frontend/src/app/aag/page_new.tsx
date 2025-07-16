'use client'

import { useState, useEffect } from 'react'
import FileExplorer, { FileItem } from '@/components/aag/FileExplorer'
import DocumentViewer, { TabItem } from '@/components/aag/DocumentViewer'
import AIChat, { Conversation, Message } from '@/components/aag/AIChat'
import { useStore } from '@/store/useStore'

export default function AAGPage() {
  const currentProject = useStore((state) => state.currentProject)
  
  // 文件相关状态
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const [openTabs, setOpenTabs] = useState<TabItem[]>([])
  const [activeTab, setActiveTab] = useState<string | null>(null)
  
  // 对话相关状态
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversation, setActiveConversation] = useState<string | null>(null)
  const [isChatVisible, setIsChatVisible] = useState(true)
  const [chatPosition, setChatPosition] = useState<'right' | 'bottom'>('right')
  
  // 模拟文件数据
  const [fileTree] = useState<FileItem[]>([
    {
      id: 'original',
      name: '原始文件',
      type: 'folder',
      category: 'original',
      children: [
        {
          id: 'doc1',
          name: '量子计算在医疗中的应用.pdf',
          type: 'file',
          category: 'original',
          extension: 'pdf',
          size: 1.46 * 1024 * 1024,
          lastModified: new Date('2024-01-15'),
          content: '# 量子计算在医疗中的应用\n\n## 摘要\n\n本研究探讨了量子计算技术在医疗诊断领域的应用现状和未来发展趋势。通过对2018-2023年间发表的150篇相关文献进行系统综述，我们发现量子计算在医学影像诊断、病理分析和临床决策支持方面展现出巨大潜力。\n\n## 1. 引言\n\n量子计算技术的快速发展为医疗诊断带来了革命性的变化。传统的医疗诊断依赖于医生的经验和知识，存在主观性强、效率低下等问题。量子计算的引入为医疗诊断提供了新的解决方案。\n\n## 2. 量子计算在医疗诊断中的主要应用\n\n### 2.1 医学影像诊断\n\n深度学习，特别是卷积神经网络（CNN）在医学影像分析中表现出色。例如，Google的研究团队开发的AI系统在检测糖尿病视网膜病变方面的准确率达到了90.3%，超过了许多专科医生。\n\n### 2.2 病理分析\n\nAI在病理切片分析中的应用日益广泛。斯坦福大学的研究人员开发的算法能够以91%的准确率区分皮肤癌和良性病变，这一准确率与2位认证皮肤科医生的平均水平相当。\n\n## 3. 挑战与限制\n\n高质量标注数据缺乏是训练AI模型的主要障碍。然而，医疗数据的获取和标注技术难度高，且涉及患者隐私保护等法律和伦理问题。量子计算相关方法还需要解决技术挑战。\n\n⚠️ 技术挑战：量子退相干问题等待解决方案'
        },
        {
          id: 'doc2',
          name: 'AI药物发现研究.pdf',
          type: 'file',
          category: 'original',
          extension: 'pdf',
          size: 2.1 * 1024 * 1024,
          lastModified: new Date('2024-01-10'),
          content: '# AI药物发现研究报告\n\n## 执行摘要\n\n人工智能在药物发现领域的应用正在快速发展，特别是在分子设计、药物筛选和临床试验优化方面。本报告分析了AI技术在药物发现中的现状、挑战和未来发展趋势。\n\n## 主要发现\n\n1. **加速药物发现过程**：AI技术能够将新药研发时间从传统的10-15年缩短至3-5年\n2. **提高成功率**：通过预测模型，AI可以提高药物候选物的成功率约30%\n3. **降低成本**：预计AI技术能够降低药物研发成本约40%\n\n## 技术应用案例\n\n### 深度学习在分子设计中的应用\n\n利用生成对抗网络（GAN）和变分自编码器（VAE）等深度学习技术，研究人员能够生成具有特定性质的分子结构。\n\n### 药物-靶点相互作用预测\n\n通过图神经网络（GNN）和Transformer模型，可以预测药物与蛋白质靶点的相互作用，为药物筛选提供指导。\n\n## 挑战与机遇\n\n**挑战：**\n- 数据质量和标准化问题\n- 监管合规性要求\n- 技术可解释性需求\n\n**机遇：**\n- 个性化药物设计\n- 药物重定位\n- 组合药物优化'
        }
      ]
    },
    {
      id: 'process',
      name: '项目过程文档',
      type: 'folder',
      category: 'process',
      children: [
        {
          id: 'requirements',
          name: '需求分析',
          type: 'folder',
          category: 'process',
          children: [
            {
              id: 'req1',
              name: '用户需求分析.md',
              type: 'file',
              category: 'process',
              extension: 'md',
              content: '# 用户需求分析\n\n## 核心需求\n\n### 1. 文档智能分析\n- 自动提取关键信息\n- 生成文档摘要\n- 识别重要概念和关系\n\n### 2. 知识提取与整理\n- 构建知识图谱\n- 识别实体和关系\n- 生成结构化数据\n\n### 3. 智能问答系统\n- 基于文档内容的精准问答\n- 多轮对话支持\n- 上下文理解能力\n\n## 用户角色\n\n### 研究人员\n- 需要快速理解大量文献\n- 希望获得研究洞察\n- 需要生成研究报告\n\n### 项目经理\n- 需要跟踪项目进度\n- 希望获得项目摘要\n- 需要风险评估\n\n### 决策者\n- 需要高层次的洞察\n- 希望获得可行性分析\n- 需要投资建议\n\n## 功能优先级\n\n1. **高优先级**\n   - 文档上传和预处理\n   - 基础问答功能\n   - 文档摘要生成\n\n2. **中优先级**\n   - 知识图谱构建\n   - 多文档分析\n   - 报告生成\n\n3. **低优先级**\n   - 高级可视化\n   - 协作功能\n   - 个性化推荐'
            }
          ]
        },
        {
          id: 'design',
          name: '方案设计',
          type: 'folder',
          category: 'process',
          children: [
            {
              id: 'design1',
              name: '系统架构设计.md',
              type: 'file',
              category: 'process',
              extension: 'md',
              content: '# 系统架构设计\n\n## 整体架构\n\n### 前端架构\n- **框架**: React 18 + Next.js 14\n- **状态管理**: Zustand\n- **UI组件**: Tailwind CSS + shadcn/ui\n- **类型检查**: TypeScript\n\n### 后端架构\n- **API框架**: FastAPI\n- **AI框架**: LangChain + LangGraph\n- **数据库**: PostgreSQL + Qdrant + Neo4j\n- **缓存**: Redis\n\n## 技术选型理由\n\n### 前端技术选型\n\n**Next.js 14**\n- 服务端渲染支持\n- 优秀的开发体验\n- 内置优化功能\n\n**Zustand**\n- 轻量级状态管理\n- TypeScript友好\n- 简单易用\n\n### 后端技术选型\n\n**FastAPI**\n- 高性能异步框架\n- 自动API文档生成\n- 优秀的类型支持\n\n**LangChain**\n- 丰富的AI工具生态\n- 模块化设计\n- 活跃的社区\n\n## 系统组件\n\n### 1. 文档处理组件\n- PDF解析器\n- 文本预处理\n- 分块策略\n\n### 2. 知识提取组件\n- 实体识别\n- 关系抽取\n- 概念提取\n\n### 3. 问答组件\n- 查询理解\n- 检索增强\n- 答案生成\n\n### 4. 可视化组件\n- 知识图谱展示\n- 分析结果可视化\n- 交互式界面\n\n## 部署架构\n\n### 容器化部署\n- Docker容器\n- Kubernetes编排\n- 微服务架构\n\n### 监控与运维\n- 日志收集\n- 性能监控\n- 错误追踪\n\n## 安全考虑\n\n### 数据安全\n- 数据加密\n- 访问控制\n- 审计日志\n\n### API安全\n- 身份认证\n- 速率限制\n- 输入验证'
            }
          ]
        },
        {
          id: 'planning',
          name: '项目规划',
          type: 'folder',
          category: 'process',
          children: [
            {
              id: 'plan1',
              name: '开发计划.md',
              type: 'file',
              category: 'process',
              extension: 'md',
              content: '# 开发计划\n\n## 项目里程碑\n\n### 阶段1: MVP版本 (2024-02-01)\n- 基础文档上传功能\n- 简单问答系统\n- 基础界面\n\n### 阶段2: 功能增强 (2024-02-15)\n- 文档分析功能\n- 知识图谱构建\n- 多文档支持\n\n### 阶段3: 正式版本 (2024-03-15)\n- 完整功能实现\n- 性能优化\n- 用户体验优化\n\n## 开发资源\n\n### 团队组成\n- 前端开发工程师 × 2\n- 后端开发工程师 × 2\n- AI算法工程师 × 1\n- 产品经理 × 1\n- 测试工程师 × 1\n\n### 技术栈\n- 前端: React + Next.js\n- 后端: Python + FastAPI\n- AI: LangChain + OpenAI\n- 数据库: PostgreSQL + Qdrant\n\n## 风险评估\n\n### 技术风险\n- AI模型性能不稳定\n- 大规模数据处理性能\n- 第三方API依赖\n\n### 项目风险\n- 需求变更频繁\n- 团队人员变动\n- 交付时间压力\n\n### 缓解措施\n- 技术调研和原型验证\n- 敏捷开发方法\n- 风险监控和预警\n\n## 质量保证\n\n### 测试策略\n- 单元测试覆盖率 > 80%\n- 集成测试\n- 端到端测试\n- 性能测试\n\n### 代码质量\n- 代码审查\n- 自动化检查\n- 文档规范\n\n## 部署计划\n\n### 环境准备\n- 开发环境\n- 测试环境\n- 生产环境\n\n### 发布策略\n- 灰度发布\n- 监控报警\n- 回滚方案'
            }
          ]
        }
      ]
    },
    {
      id: 'notes',
      name: '项目笔记',
      type: 'folder',
      category: 'notes',
      children: [
        {
          id: 'note1',
          name: '技术调研笔记.md',
          type: 'file',
          category: 'notes',
          extension: 'md',
          content: '# 技术调研笔记\n\n## LangChain框架调研\n\n### 优势\n- **模块化设计**: 组件可复用，易于扩展\n- **丰富的集成**: 支持多种LLM和工具\n- **活跃社区**: 更新频繁，文档完善\n- **开发效率**: 提供高级抽象，减少重复工作\n\n### 劣势\n- **学习曲线**: 概念较多，需要时间掌握\n- **版本变化**: 更新较快，可能存在兼容性问题\n- **性能开销**: 抽象层可能带来额外开销\n- **调试复杂**: 链式调用增加调试难度\n\n## 向量数据库对比\n\n### Qdrant\n- **优点**: 高性能，支持多种距离度量\n- **缺点**: 相对较新，生态系统不够成熟\n- **适用场景**: 大规模向量检索\n\n### Pinecone\n- **优点**: 云原生，易于使用\n- **缺点**: 费用较高，依赖外部服务\n- **适用场景**: 快速原型和小型应用\n\n### Weaviate\n- **优点**: 支持多模态，功能丰富\n- **缺点**: 部署复杂，资源消耗大\n- **适用场景**: 复杂知识图谱应用\n\n## 文档解析工具\n\n### PyPDF2\n- **优点**: 简单易用，支持基础操作\n- **缺点**: 对复杂PDF支持有限\n- **评价**: 适合简单PDF处理\n\n### pdfplumber\n- **优点**: 提取表格和布局信息\n- **缺点**: 处理速度较慢\n- **评价**: 适合需要结构化信息的场景\n\n### Unstructured\n- **优点**: 支持多种格式，处理能力强\n- **缺点**: 依赖较多，部署复杂\n- **评价**: 适合多格式文档处理\n\n## 推荐技术栈\n\n基于调研结果，推荐以下技术栈:\n\n1. **文档处理**: Unstructured + pdfplumber\n2. **向量数据库**: Qdrant\n3. **AI框架**: LangChain\n4. **知识图谱**: Neo4j\n5. **API框架**: FastAPI\n6. **前端框架**: Next.js + React'
        },
        {
          id: 'note2',
          name: '会议记录.md',
          type: 'file',
          category: 'notes',
          extension: 'md',
          content: '# 会议记录\n\n## 2024-01-15 项目启动会\n\n### 参会人员\n- 张三 (项目经理)\n- 李四 (技术负责人)\n- 王五 (前端开发)\n- 赵六 (后端开发)\n- 孙七 (AI算法)\n\n### 会议议程\n1. 项目背景介绍\n2. 技术方案讨论\n3. 开发计划制定\n4. 分工安排\n\n### 主要决议\n\n#### 技术方案\n- 采用前后端分离架构\n- 使用React + Next.js作为前端框架\n- 后端采用FastAPI + LangChain\n- 数据库选择PostgreSQL + Qdrant\n\n#### 开发方法\n- 采用敏捷开发方法\n- 2周为一个迭代周期\n- 每日站会制度\n- 代码审查流程\n\n#### 分工安排\n- 前端: 王五负责UI组件和页面开发\n- 后端: 赵六负责API和数据库设计\n- AI: 孙七负责算法和模型集成\n- 项目管理: 张三负责进度跟踪和协调\n\n### 行动项\n1. 技术调研报告 (负责人: 李四, 截止日期: 2024-01-20)\n2. 原型设计 (负责人: 王五, 截止日期: 2024-01-25)\n3. 数据库设计 (负责人: 赵六, 截止日期: 2024-01-25)\n4. AI模型调研 (负责人: 孙七, 截止日期: 2024-01-22)\n\n### 下次会议\n- 时间: 2024-01-22 14:00\n- 地点: 会议室A\n- 议题: 技术方案评审\n\n---\n\n## 2024-01-22 技术方案评审会\n\n### 参会人员\n- 张三 (项目经理)\n- 李四 (技术负责人)\n- 王五 (前端开发)\n- 赵六 (后端开发)\n- 孙七 (AI算法)\n- 陈八 (产品经理)\n\n### 会议内容\n\n#### 技术调研结果\n李四汇报了技术调研结果，主要包括:\n- 前端框架对比分析\n- 后端框架性能评估\n- AI框架功能评估\n- 数据库选型建议\n\n#### 原型演示\n王五展示了前端原型，包括:\n- 主界面设计\n- 用户交互流程\n- 响应式布局\n- 组件库选择\n\n#### 数据库设计\n赵六介绍了数据库设计方案:\n- 关系型数据库结构\n- 向量数据库集成\n- 数据同步策略\n- 性能优化考虑\n\n#### AI模型评估\n孙七分享了AI模型调研:\n- 预训练模型对比\n- 微调策略\n- 推理性能评估\n- 成本效益分析\n\n### 决议事项\n1. 确认技术栈选择\n2. 批准数据库设计方案\n3. 确定AI模型选择\n4. 制定详细开发计划\n\n### 风险讨论\n- 第三方API稳定性风险\n- 数据处理性能风险\n- 模型推理成本风险\n- 用户体验一致性风险\n\n### 下次会议\n- 时间: 2024-01-29 14:00\n- 地点: 会议室B\n- 议题: 开发进度检查'
        }
      ]
    }
  ])

  // 打开文件
  const handleFileSelect = (file: FileItem) => {
    setSelectedFile(file)
    
    // 检查是否已经打开
    const existingTab = openTabs.find(tab => tab.id === file.id)
    if (existingTab) {
      setActiveTab(file.id)
    } else {
      // 创建新标签页
      const newTab: TabItem = {
        id: file.id,
        name: file.name,
        content: file.content || '',
        type: file.extension || 'unknown',
        isDirty: false,
        lastModified: file.lastModified
      }
      setOpenTabs(prev => [...prev, newTab])
      setActiveTab(file.id)
    }
  }

  // 关闭标签页
  const handleTabClose = (tabId: string) => {
    setOpenTabs(prev => prev.filter(tab => tab.id !== tabId))
    if (activeTab === tabId) {
      const remainingTabs = openTabs.filter(tab => tab.id !== tabId)
      setActiveTab(remainingTabs.length > 0 ? remainingTabs[remainingTabs.length - 1].id : null)
    }
  }

  // 切换标签页
  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId)
  }

  // 内容变化处理
  const handleContentChange = (tabId: string, content: string) => {
    setOpenTabs(prev => prev.map(tab => 
      tab.id === tabId ? { ...tab, content, isDirty: true } : tab
    ))
  }

  // 创建新对话
  const handleConversationCreate = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: `新对话 ${conversations.length + 1}`,
      isActive: true,
      createdAt: new Date(),
      messages: [],
      context: selectedFile?.name
    }
    setConversations(prev => [...prev, newConversation])
    setActiveConversation(newConversation.id)
  }

  // 切换对话
  const handleConversationChange = (conversationId: string) => {
    setActiveConversation(conversationId)
  }

  // 删除对话
  const handleConversationDelete = (conversationId: string) => {
    setConversations(prev => prev.filter(c => c.id !== conversationId))
    if (activeConversation === conversationId) {
      setActiveConversation(null)
    }
  }

  // 发送消息
  const handleMessageSend = (conversationId: string, message: string, attachments?: string[]) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date(),
      attachments
    }

    setConversations(prev => prev.map(conv => 
      conv.id === conversationId 
        ? { 
            ...conv, 
            messages: [...conv.messages, newMessage],
            lastMessage: message 
          }
        : conv
    ))

    // 模拟AI回复
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `这是一个模拟的AI回复，针对您的问题：${message}`,
        timestamp: new Date()
      }

      setConversations(prev => prev.map(conv => 
        conv.id === conversationId 
          ? { 
              ...conv, 
              messages: [...conv.messages, aiMessage],
              lastMessage: aiMessage.content 
            }
          : conv
      ))
    }, 1000)
  }

  // 文件上传处理
  const handleFileUpload = (file: File) => {
    console.log('文件上传:', file.name)
    // 这里实现文件上传逻辑
  }

  // 文件创建处理
  const handleFileCreate = (name: string, type: 'file' | 'folder', category: string) => {
    console.log('创建文件:', name, type, category)
    // 这里实现文件创建逻辑
  }

  // 文件删除处理
  const handleFileDelete = (fileId: string) => {
    console.log('删除文件:', fileId)
    // 这里实现文件删除逻辑
  }

  // 获取当前文档名称
  const getCurrentDocumentName = () => {
    return openTabs.find(tab => tab.id === activeTab)?.name || null
  }

  // 检查项目是否存在
  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">请先选择一个项目</h2>
          <p className="text-gray-600">AAG需要在项目环境中运行</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 左侧文件浏览器 */}
      <div className="w-64 border-r border-gray-200">
        <FileExplorer
          files={fileTree}
          onFileSelect={handleFileSelect}
          selectedFile={selectedFile}
          onFileUpload={handleFileUpload}
          onFileCreate={handleFileCreate}
          onFileDelete={handleFileDelete}
        />
      </div>

      {/* 中间文档查看器 */}
      <div className={`flex-1 ${chatPosition === 'bottom' && isChatVisible ? 'pb-64' : ''}`}>
        <DocumentViewer
          tabs={openTabs}
          activeTab={activeTab}
          onTabChange={handleTabChange}
          onTabClose={handleTabClose}
          onContentChange={handleContentChange}
        />
      </div>

      {/* 右侧/底部AI对话 */}
      <div className={chatPosition === 'bottom' ? 'fixed bottom-0 left-64 right-0' : ''}>
        <AIChat
          conversations={conversations}
          activeConversation={activeConversation}
          onConversationChange={handleConversationChange}
          onConversationCreate={handleConversationCreate}
          onConversationDelete={handleConversationDelete}
          onMessageSend={handleMessageSend}
          currentDocument={getCurrentDocumentName()}
          isVisible={isChatVisible}
          onToggleVisibility={() => setIsChatVisible(!isChatVisible)}
          position={chatPosition}
          onPositionChange={setChatPosition}
        />
      </div>
    </div>
  )
}