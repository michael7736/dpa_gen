'use client'

import { useState, useEffect } from 'react'
import FileExplorer, { FileItem } from '@/components/aag/FileExplorer'
import EnhancedDocumentViewer, { TabItem } from '@/components/aag/EnhancedDocumentViewer'
import AIChat, { Conversation, Message } from '@/components/aag/AIChat'
import ResultViewModal from '@/components/aag/ResultViewModal'
import { useStore } from '@/store/useStore'
import { 
  documentServiceV2, 
  ProcessingOptions, 
  DocumentUploadResponseV2,
  PipelineProgressResponse,
  PipelineStage,
  DocumentListResponse 
} from '@/services/documentsV2'
import { webSocketService, PipelineProgressMessage } from '@/services/websocket'

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
  
  // 文件树数据
  const [fileTree, setFileTree] = useState<FileItem[]>([
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
          content: '# 技术调研笔记\n\n## LangChain框架调研\n\n### 优势\n- **模块化设计**: 组件可复用，易于扩展\n- **丰富的集成**: 支持多种LLM和工具\n- **活跃社区**: 更新频繁，文档完善\n- **开发效率**: 提供高级抽象，减少重复工作\n\n### 劣势\n- **学习曲线**: 概念较多，需要时间掌握\n- **版本变化**: 更新较快，可能存在兼容性问题\n- **性能开销**: 抽象层可能带来额外开销\n- **调试复杂**: 链式调用增加调试难度\n\n## 向量数据库对比\n\n### Qdrant\n- **优点**: 高性能，支持多种距离度量\n- **缺点**: 相对较新，生态系统不够成熟\n- **适用场景**: 大规模向量检索\n\n### Pinecone\n- **优点**: 云原生，易于使用\n- **缺点**: 费用较高，依赖外部服务\n- **适用场景**: 快速原型和小型应用\n\n### Weaviate\n- **优点**: 支持多模态，功能丰富\n- **缺点**: 部署复杂，资源消耗大\n- **适用场景**: 复杂知识图谱应用\n\n## 推荐技术栈\n\n基于调研结果，推荐以下技术栈:\n\n1. **文档处理**: Unstructured + pdfplumber\n2. **向量数据库**: Qdrant\n3. **AI框架**: LangChain\n4. **知识图谱**: Neo4j\n5. **API框架**: FastAPI\n6. **前端框架**: Next.js + React'
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
        content: `基于您当前查看的文档"${selectedFile?.name || '未选择文档'}"，我来回答您的问题：${message}\n\n这是一个模拟的AI回复，展示了如何基于文档内容进行智能问答。`,
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

  // 文件上传状态
  const [uploadingFile, setUploadingFile] = useState<{
    name: string
    progress: number
    status: 'uploading' | 'processing' | 'completed' | 'error'
  } | null>(null)
  
  // V2上传相关状态
  const [processingOptions, setProcessingOptions] = useState<ProcessingOptions>({
    upload_only: true,
    generate_summary: true,
    create_index: true,
    deep_analysis: false
  })
  const [processingProgress, setProcessingProgress] = useState<PipelineProgressResponse | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  
  // 结果查看模态框状态
  const [resultModalOpen, setResultModalOpen] = useState(false)
  const [resultModalType, setResultModalType] = useState<'summary' | 'index' | 'analysis'>('summary')
  const [resultModalDocumentId, setResultModalDocumentId] = useState<string>('')

  // 处理WebSocket进度更新
  const handleWebSocketProgress = (progress: PipelineProgressMessage) => {
    console.log('收到WebSocket进度更新:', progress)
    
    // 转换为组件期望的格式
    const convertedProgress: PipelineProgressResponse = {
      pipeline_id: progress.pipeline_id,
      document_id: progress.document_id,
      overall_progress: progress.overall_progress,
      current_stage: progress.current_stage,
      stages: progress.stages.map(stage => ({
        id: stage.id,
        name: stage.name,
        status: stage.status,
        progress: stage.progress,
        message: stage.message,
        can_interrupt: stage.can_interrupt,
        started_at: stage.started_at,
        completed_at: stage.completed_at,
        duration: stage.duration,
        error: stage.error
      })),
      can_resume: progress.can_resume,
      interrupted: progress.interrupted,
      completed: progress.completed,
      timestamp: progress.timestamp
    }

    setProcessingProgress(convertedProgress)

    // 更新上传状态
    if (progress.current_stage) {
      setUploadingFile(prev => prev ? { 
        ...prev, 
        progress: Math.round(progress.overall_progress),
        status: 'processing' 
      } : null)
    }

    // 检查是否完成
    if (progress.completed) {
      // 处理完成，创建新的文件项
      const newFile: FileItem = {
        id: progress.document_id || Date.now().toString(),
        name: uploadingFile?.name || 'unknown.pdf',
        type: 'file',
        category: 'original',
        extension: uploadingFile?.name.split('.').pop() || 'unknown',
        size: 0, // 文件大小可以从上传响应中获取
        lastModified: new Date(),
        content: `# ${uploadingFile?.name}\n\n文档已成功上传和处理！\n\n**文档ID:** ${progress.document_id}\n**处理管道ID:** ${progress.pipeline_id}\n**处理状态:** 已完成\n\n## 处理阶段\n\n${progress.stages.map(stage => 
          `- ${stage.name}: ${stage.status === 'completed' ? '✓' : '✗'} ${stage.duration ? `(${stage.duration.toFixed(1)}秒)` : ''}`
        ).join('\n')}\n\n您现在可以在右侧AI助手中询问关于这个文档的问题。`
      }
      
      // 更新文件树中的文件
      addFileToTree(newFile)
      
      // 自动打开上传的文件
      handleFileSelect(newFile)
      
      // 清除上传状态
      setUploadingFile(null)
      setProcessingProgress(null)
      
      // 重新加载文档列表以获取最新状态
      loadDocuments()
      
      // 显示成功消息
      alert(`文档 "${uploadingFile?.name}" 上传并处理成功！`)
      
      // 取消订阅
      webSocketService.unsubscribePipelineProgress(progress.pipeline_id)
    }
  }

  // 文件上传处理（使用V2服务）
  const handleFileUpload = async (file: File) => {
    console.log('文件上传:', file.name)
    console.log('处理选项:', processingOptions)
    
    // 设置上传状态
    setUploadingFile({
      name: file.name,
      progress: 0,
      status: 'uploading'
    })
    setProcessingProgress(null)
    
    try {
      // 使用当前项目ID，如果没有则不传递（让后端创建默认项目）
      const projectId = currentProject?.id
      
      // 调用V2上传服务
      const result = await documentServiceV2.uploadDocument(
        file,
        processingOptions,
        projectId,
        (progress) => {
          console.log('上传进度:', progress + '%')
          setUploadingFile(prev => prev ? { ...prev, progress } : null)
        }
      )
      
      console.log('文件上传成功:', result)
      
      // 立即创建文件项（不管是否有处理管道）
      const statusMessage = result.status === 'exists' ? '文档已存在' : 
                           result.processing_pipeline ? '处理中...' : '已完成'
      const contentMessage = result.status === 'exists' ? 
        '该文档已存在于系统中，您可以直接使用。' :
        result.processing_pipeline ? '文档正在后台处理，请关注进度更新。' : '文档已上传到服务器，您可以开始使用。'
      
      const newFile: FileItem = {
        id: result.document_id || Date.now().toString(),
        name: file.name,
        type: 'file',
        category: 'original',
        extension: file.name.split('.').pop() || 'unknown',
        size: file.size,
        lastModified: new Date(),
        content: `# ${file.name}\n\n文档处理完成！\n\n**文档ID:** ${result.document_id}\n**文件名:** ${result.filename}\n**状态:** ${statusMessage}\n\n${contentMessage}`
      }
      
      // 添加文件到文件树
      addFileToTree(newFile)
      
      // 自动打开上传的文件
      handleFileSelect(newFile)
      
      // 如果只是上传，没有处理管道
      if (!result.processing_pipeline) {
        // 清除上传状态
        setUploadingFile(null)
        // 重新加载文档列表
        loadDocuments()
        alert(`文档 "${file.name}" 上传成功！`)
        return
      }
      
      // 更新状态为处理中
      setUploadingFile(prev => prev ? { ...prev, status: 'processing', progress: 100 } : null)
      
      // 如果有处理管道，订阅WebSocket进度更新
      if (result.processing_pipeline) {
        if (wsConnected && webSocketService.isAvailable()) {
          console.log('订阅管道进度:', result.processing_pipeline.pipeline_id)
          webSocketService.subscribePipelineProgress(
            result.processing_pipeline.pipeline_id,
            handleWebSocketProgress
          )
        } else {
          // WebSocket未连接或不可用，回退到轮询
          console.log('WebSocket不可用，使用轮询模式')
          startProgressPolling(result.document_id, result.processing_pipeline.pipeline_id)
        }
      }
      
    } catch (error: any) {
      console.error('文件上传失败:', error)
      setUploadingFile(prev => prev ? { ...prev, status: 'error' } : null)
      alert(error.response?.data?.error || error.message || '文件上传失败，请重试')
    }
  }
  
  // 轮询处理进度（备用方案）
  const startProgressPolling = async (documentId: string, pipelineId: string) => {
    try {
      await documentServiceV2.pollProcessingProgress(
        documentId,
        pipelineId,
        (progress) => {
          setProcessingProgress(progress)
          
          // 更新上传状态
          if (progress.current_stage) {
            setUploadingFile(prev => prev ? { 
              ...prev, 
              progress: Math.round(progress.overall_progress),
              status: 'processing' 
            } : null)
          }
          
          // 检查是否完成
          if (progress.completed) {
            // 处理完成逻辑
            const newFile: FileItem = {
              id: documentId,
              name: uploadingFile?.name || 'unknown.pdf',
              type: 'file',
              category: 'original',
              extension: uploadingFile?.name.split('.').pop() || 'unknown',
              size: 0,
              lastModified: new Date(),
              content: `# ${uploadingFile?.name}\n\n文档已成功上传和处理！\n\n**文档ID:** ${documentId}\n**处理状态:** 已完成\n\n您现在可以在右侧AI助手中询问关于这个文档的问题。`
            }
            
            handleFileSelect(newFile)
            setUploadingFile(null)
            setProcessingProgress(null)
            // 重新加载文档列表
            loadDocuments()
            alert(`文档 "${uploadingFile?.name}" 上传并处理成功！`)
          }
        }
      )
    } catch (error: any) {
      console.error('进度轮询失败:', error)
      setUploadingFile(prev => prev ? { ...prev, status: 'error' } : null)
    }
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
  
  // 处理查看结果
  const handleViewResult = (action: 'summary' | 'index' | 'analysis', documentId: string) => {
    setResultModalType(action)
    setResultModalDocumentId(documentId)
    setResultModalOpen(true)
  }
  
  // 添加文件到文件树
  const addFileToTree = (newFile: FileItem) => {
    setFileTree(prevTree => {
      return prevTree.map(folder => {
        if (folder.id === 'original' && folder.children) {
          // 检查文件是否已存在
          const existingFile = folder.children.find(file => file.id === newFile.id)
          if (existingFile) {
            // 更新现有文件
            return {
              ...folder,
              children: folder.children.map(file => 
                file.id === newFile.id ? newFile : file
              )
            }
          } else {
            // 添加新文件
            return {
              ...folder,
              children: [...folder.children, newFile]
            }
          }
        }
        return folder
      })
    })
  }
  
  // 从API获取文档列表
  const loadDocuments = async () => {
    try {
      const projectId = currentProject?.id || 'default'
      const response = await documentServiceV2.getDocuments(projectId, 50, 0)
      
      // 转换API响应为FileItem格式
      const apiDocuments: FileItem[] = response.items.map(doc => ({
        id: doc.id,
        name: doc.filename,
        type: 'file',
        category: 'original',
        extension: doc.file_type,
        size: doc.file_size,
        lastModified: new Date(doc.created_at),
        content: `# ${doc.filename}\n\n文档信息：\n- 文件大小: ${(doc.file_size / 1024).toFixed(1)} KB\n- 文件类型: ${doc.file_type}\n- 状态: ${doc.status}\n- 创建时间: ${doc.created_at}\n- 更新时间: ${doc.updated_at}\n\n您可以在右侧AI助手中询问关于这个文档的问题。`
      }))
      
      // 更新文件树中的原始文件
      setFileTree(prevTree => 
        prevTree.map(folder => 
          folder.id === 'original' 
            ? { ...folder, children: apiDocuments }
            : folder
        )
      )
    } catch (error) {
      console.error('获取文档列表失败:', error)
    }
  }
  
  // 页面加载时获取文档列表
  useEffect(() => {
    loadDocuments()
  }, [currentProject?.id])
  
  // WebSocket连接管理
  useEffect(() => {
    const userId = '243588ff-459d-45b8-b77b-09aec3946a64' // 使用默认用户UUID
    
    // 连接WebSocket（静默失败）
    webSocketService.connect(userId).catch(error => {
      console.warn('WebSocket连接失败，将使用轮询模式:', error.message)
      // 不需要显示给用户，系统会自动降级到轮询
    })

    // 监听连接状态
    const handleConnectionChange = (connected: boolean) => {
      setWsConnected(connected)
      console.log('WebSocket连接状态:', connected ? '已连接' : '已断开')
      
      if (connected) {
        console.log('WebSocket连接恢复，可以使用实时推送')
      } else {
        console.log('WebSocket连接断开，将使用轮询模式')
      }
    }

    webSocketService.onConnectionChange(handleConnectionChange)

    return () => {
      webSocketService.offConnectionChange(handleConnectionChange)
    }
  }, [])

  // 检查项目是否存在 - 临时注释掉用于演示
  // if (!currentProject) {
  //   return (
  //     <div className="flex items-center justify-center h-screen bg-gray-50">
  //       <div className="text-center">
  //         <h2 className="text-2xl font-bold mb-4">请先选择一个项目</h2>
  //         <p className="text-gray-600">AAG需要在项目环境中运行</p>
  //       </div>
  //     </div>
  //   )
  // }

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* 左侧文件浏览器 */}
      <div className="w-80 min-w-80 bg-white border-r border-gray-200 shadow-sm">
        <FileExplorer
          files={fileTree}
          onFileSelect={handleFileSelect}
          selectedFile={selectedFile}
          onFileUpload={handleFileUpload}
          onFileCreate={handleFileCreate}
          onFileDelete={handleFileDelete}
          uploadingFile={uploadingFile}
          processingOptions={processingOptions}
          onProcessingOptionsChange={setProcessingOptions}
          processingProgress={processingProgress}
        />
      </div>

      {/* 中间文档查看器 */}
      <div className={`flex-1 min-w-0 ${chatPosition === 'bottom' && isChatVisible ? 'pb-64' : ''}`}>
        <div className="h-full bg-white shadow-sm border-r border-gray-200">
          <EnhancedDocumentViewer
            tabs={openTabs}
            activeTab={activeTab}
            onTabChange={handleTabChange}
            onTabClose={handleTabClose}
            onContentChange={handleContentChange}
            showActions={true}
            onViewResult={handleViewResult}
          />
        </div>
      </div>

      {/* 右侧/底部AI对话 */}
      <div className={chatPosition === 'bottom' ? 'fixed bottom-0 left-80 right-0 z-20' : ''}>
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
      
      {/* 结果查看模态框 */}
      <ResultViewModal
        isOpen={resultModalOpen}
        onClose={() => setResultModalOpen(false)}
        documentId={resultModalDocumentId}
        documentName={openTabs.find(tab => tab.id === resultModalDocumentId)?.name || '文档'}
        actionType={resultModalType}
      />
    </div>
  )
}