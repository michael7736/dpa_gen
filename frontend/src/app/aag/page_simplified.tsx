'use client'

import { useState, useEffect } from 'react'
import { 
  FileText, 
  Folder, 
  FolderOpen, 
  Plus, 
  X, 
  MessageCircle,
  Settings,
  Search,
  RefreshCw
} from 'lucide-react'

// 文件类型定义
interface FileItem {
  id: string
  name: string
  type: 'file' | 'folder'
  category: 'original' | 'process' | 'notes'
  extension?: string
  size?: number
  lastModified?: Date
  children?: FileItem[]
  content?: string
}

// 标签页定义
interface TabItem {
  id: string
  name: string
  content: string
  type: string
  isDirty: boolean
}

// 对话定义
interface Conversation {
  id: string
  title: string
  isActive: boolean
  lastMessage?: string
  createdAt: Date
}

export default function SimplifiedAAGPage() {
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const [openTabs, setOpenTabs] = useState<TabItem[]>([])
  const [activeTab, setActiveTab] = useState<string | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversation, setActiveConversation] = useState<string | null>(null)
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true)
  const [rightPanelPosition, setRightPanelPosition] = useState<'right' | 'bottom'>('right')

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
          content: 'PDF文档内容预览...'
        },
        {
          id: 'doc2',
          name: 'AI药物发现研究.pdf',
          type: 'file',
          category: 'original',
          extension: 'pdf',
          size: 2.1 * 1024 * 1024,
          lastModified: new Date('2024-01-10'),
          content: 'PDF文档内容预览...'
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
              content: '# 用户需求分析\n\n## 核心需求\n- 文档智能分析\n- 知识提取\n- 问答系统'
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
              content: '# 系统架构设计\n\n## 整体架构\n- 前端: React + Next.js\n- 后端: FastAPI + LangChain'
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
              content: '# 开发计划\n\n## 里程碑\n- MVP版本: 2024-02-01\n- 正式版本: 2024-03-15'
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
          content: '# 技术调研\n\n## LangChain框架\n- 优势: 模块化设计\n- 劣势: 学习曲线陡峭'
        },
        {
          id: 'note2',
          name: '会议记录.md',
          type: 'file',
          category: 'notes',
          extension: 'md',
          content: '# 会议记录\n\n## 2024-01-15 项目启动会\n- 参与人员: 张三, 李四\n- 决议: 采用敏捷开发'
        }
      ]
    }
  ])

  // 文件夹展开状态
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['original', 'process', 'notes']))

  // 切换文件夹展开状态
  const toggleFolder = (folderId: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev)
      if (newSet.has(folderId)) {
        newSet.delete(folderId)
      } else {
        newSet.add(folderId)
      }
      return newSet
    })
  }

  // 打开文件
  const openFile = (file: FileItem) => {
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
        isDirty: false
      }
      setOpenTabs(prev => [...prev, newTab])
      setActiveTab(file.id)
    }
  }

  // 关闭标签页
  const closeTab = (tabId: string) => {
    setOpenTabs(prev => prev.filter(tab => tab.id !== tabId))
    if (activeTab === tabId) {
      const remainingTabs = openTabs.filter(tab => tab.id !== tabId)
      setActiveTab(remainingTabs.length > 0 ? remainingTabs[remainingTabs.length - 1].id : null)
    }
  }

  // 创建新对话
  const createConversation = () => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: `新对话 ${conversations.length + 1}`,
      isActive: true,
      createdAt: new Date()
    }
    setConversations(prev => [...prev, newConversation])
    setActiveConversation(newConversation.id)
  }

  // 渲染文件树
  const renderFileTree = (items: FileItem[], level: number = 0) => {
    return items.map(item => (
      <div key={item.id} className="select-none">
        {item.type === 'folder' ? (
          <div>
            <div
              className={`flex items-center py-1 px-2 hover:bg-gray-100 cursor-pointer text-sm`}
              style={{ paddingLeft: `${level * 16 + 8}px` }}
              onClick={() => toggleFolder(item.id)}
            >
              {expandedFolders.has(item.id) ? (
                <FolderOpen className="w-4 h-4 mr-2 text-blue-500" />
              ) : (
                <Folder className="w-4 h-4 mr-2 text-blue-500" />
              )}
              <span className="font-medium">{item.name}</span>
            </div>
            {expandedFolders.has(item.id) && item.children && (
              <div>
                {renderFileTree(item.children, level + 1)}
              </div>
            )}
          </div>
        ) : (
          <div
            className={`flex items-center py-1 px-2 hover:bg-gray-100 cursor-pointer text-sm ${
              selectedFile?.id === item.id ? 'bg-blue-50 text-blue-700' : ''
            }`}
            style={{ paddingLeft: `${level * 16 + 8}px` }}
            onClick={() => openFile(item)}
          >
            <FileText className="w-4 h-4 mr-2 text-gray-500" />
            <span className="truncate">{item.name}</span>
          </div>
        )}
      </div>
    ))
  }

  // 获取当前活动标签页内容
  const activeTabContent = openTabs.find(tab => tab.id === activeTab)

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 左侧文件目录 */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-3 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-800">项目文件</h2>
            <div className="flex items-center space-x-1">
              <button className="p-1 hover:bg-gray-100 rounded">
                <Plus className="w-4 h-4 text-gray-500" />
              </button>
              <button className="p-1 hover:bg-gray-100 rounded">
                <RefreshCw className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          </div>
          <div className="mt-2 relative">
            <Search className="w-4 h-4 absolute left-2 top-2 text-gray-400" />
            <input
              type="text"
              placeholder="搜索文件..."
              className="w-full pl-8 pr-3 py-1 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {renderFileTree(fileTree)}
        </div>
      </div>

      {/* 中间内容区域 */}
      <div className="flex-1 flex flex-col">
        {/* 标签页栏 */}
        <div className="bg-white border-b border-gray-200 min-h-[40px] flex items-center">
          <div className="flex-1 flex items-center overflow-x-auto">
            {openTabs.map(tab => (
              <div
                key={tab.id}
                className={`flex items-center px-3 py-2 text-sm border-r border-gray-200 cursor-pointer min-w-0 ${
                  activeTab === tab.id
                    ? 'bg-gray-50 text-blue-600'
                    : 'hover:bg-gray-50'
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                <FileText className="w-4 h-4 mr-2 flex-shrink-0" />
                <span className="truncate max-w-[150px]">{tab.name}</span>
                {tab.isDirty && <span className="ml-1 text-orange-500">●</span>}
                <button
                  className="ml-2 p-0.5 hover:bg-gray-200 rounded flex-shrink-0"
                  onClick={(e) => {
                    e.stopPropagation()
                    closeTab(tab.id)
                  }}
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* 文档内容区域 */}
        <div className="flex-1 overflow-auto p-4">
          {activeTabContent ? (
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h1 className="text-2xl font-bold mb-4">{activeTabContent.name}</h1>
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700">
                    {activeTabContent.content}
                  </pre>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>选择一个文件来查看内容</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 右侧对话区域 */}
      {isRightPanelOpen && (
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
          <div className="p-3 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-800">AI助手</h2>
              <div className="flex items-center space-x-1">
                <button
                  className="p-1 hover:bg-gray-100 rounded"
                  onClick={() => setRightPanelPosition(rightPanelPosition === 'right' ? 'bottom' : 'right')}
                >
                  <Settings className="w-4 h-4 text-gray-500" />
                </button>
                <button
                  className="p-1 hover:bg-gray-100 rounded"
                  onClick={() => setIsRightPanelOpen(false)}
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            </div>
            <button
              className="w-full mt-2 px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
              onClick={createConversation}
            >
              新建对话
            </button>
          </div>

          {/* 对话列表 */}
          <div className="border-b border-gray-200 max-h-32 overflow-y-auto">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className={`p-2 text-sm cursor-pointer hover:bg-gray-50 ${
                  activeConversation === conv.id ? 'bg-blue-50 text-blue-700' : ''
                }`}
                onClick={() => setActiveConversation(conv.id)}
              >
                <div className="flex items-center">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  <span className="truncate">{conv.title}</span>
                </div>
              </div>
            ))}
          </div>

          {/* 对话区域 */}
          <div className="flex-1 flex flex-col">
            {activeConversation ? (
              <>
                <div className="flex-1 p-3 overflow-y-auto">
                  <div className="space-y-4">
                    {/* 示例消息 */}
                    <div className="bg-gray-100 rounded-lg p-3 text-sm">
                      <div className="font-medium text-gray-800 mb-1">AI助手</div>
                      <div className="text-gray-700">
                        您好！我是您的AI助手，可以帮助您分析文档、回答问题、生成报告等。请问有什么可以帮助您的吗？
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* 输入区域 */}
                <div className="p-3 border-t border-gray-200">
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      placeholder="输入您的问题..."
                      className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <button className="px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600">
                      发送
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-sm">选择或创建一个对话</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 右侧面板关闭时的切换按钮 */}
      {!isRightPanelOpen && (
        <button
          className="fixed right-4 top-4 p-2 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600"
          onClick={() => setIsRightPanelOpen(true)}
        >
          <MessageCircle className="w-5 h-5" />
        </button>
      )}
    </div>
  )
}