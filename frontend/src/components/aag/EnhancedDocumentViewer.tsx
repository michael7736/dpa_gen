'use client'

import { useState } from 'react'
import { 
  FileText, 
  X, 
  Download, 
  Printer, 
  Search, 
  ZoomIn, 
  ZoomOut,
  Maximize2,
  Eye,
  Settings,
  ChevronRight,
  ChevronLeft
} from 'lucide-react'
import DocumentActions from './DocumentActions'

export interface TabItem {
  id: string
  name: string
  content: string
  type: string
  isDirty: boolean
  filePath?: string
  lastModified?: Date
  status?: string
}

interface EnhancedDocumentViewerProps {
  tabs: TabItem[]
  activeTab: string | null
  onTabChange: (tabId: string) => void
  onTabClose: (tabId: string) => void
  onContentChange?: (tabId: string, content: string) => void
  showActions?: boolean
  onViewResult?: (action: 'summary' | 'index' | 'analysis', documentId: string) => void
}

export default function EnhancedDocumentViewer({
  tabs,
  activeTab,
  onTabChange,
  onTabClose,
  onContentChange,
  showActions = true,
  onViewResult
}: EnhancedDocumentViewerProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [zoom, setZoom] = useState(100)
  const [showActionsPanel, setShowActionsPanel] = useState(true)
  const [actionsWidth, setActionsWidth] = useState(400)

  // 获取当前活动标签页
  const currentTab = tabs.find(tab => tab.id === activeTab)

  // 搜索功能
  const handleSearch = () => {
    if (!searchTerm || !currentTab) return
    
    // 在文档内容中搜索
    const content = currentTab.content.toLowerCase()
    const term = searchTerm.toLowerCase()
    const index = content.indexOf(term)
    
    if (index !== -1) {
      // 滚动到搜索结果
      // 这里可以实现更复杂的搜索逻辑
    }
  }

  // 缩放处理
  const handleZoom = (delta: number) => {
    const newZoom = Math.max(50, Math.min(200, zoom + delta))
    setZoom(newZoom)
  }

  // 下载文档
  const handleDownload = () => {
    if (!currentTab) return
    
    const blob = new Blob([currentTab.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = currentTab.name
    a.click()
    URL.revokeObjectURL(url)
  }

  // 打印文档
  const handlePrint = () => {
    if (!currentTab) return
    window.print()
  }

  return (
    <div className="flex h-full bg-gray-50">
      {/* 主文档查看区域 */}
      <div className={`flex-1 flex flex-col transition-all duration-300`}>
        {/* 标签栏 */}
        <div className="bg-white border-b border-gray-200 flex items-center justify-between">
          <div className="flex-1 flex items-center min-w-0">
            <div className="flex items-center space-x-1 p-2 overflow-x-auto">
              {tabs.map(tab => (
                <div
                  key={tab.id}
                  className={`
                    flex items-center px-3 py-1.5 rounded-lg cursor-pointer transition-all
                    ${activeTab === tab.id 
                      ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                  onClick={() => onTabChange(tab.id)}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium max-w-[150px] truncate">
                    {tab.name}
                  </span>
                  {tab.isDirty && <span className="ml-1 text-orange-500">•</span>}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onTabClose(tab.id)
                    }}
                    className="ml-2 p-0.5 hover:bg-gray-300 rounded transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* 工具栏 */}
          <div className="flex items-center space-x-2 px-4">
            {/* 搜索 */}
            <div className="relative">
              <input
                type="text"
                placeholder="搜索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-8 pr-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Search className="absolute left-2.5 top-2 w-4 h-4 text-gray-400" />
            </div>
            
            {/* 缩放控制 */}
            <div className="flex items-center space-x-1 border border-gray-300 rounded-lg p-1">
              <button
                onClick={() => handleZoom(-10)}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="px-2 text-sm font-medium">{zoom}%</span>
              <button
                onClick={() => handleZoom(10)}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>
            
            {/* 其他工具 */}
            <button
              onClick={handleDownload}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="下载"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={handlePrint}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              title="打印"
            >
              <Printer className="w-4 h-4" />
            </button>
            
            {/* 切换操作面板 */}
            {showActions && (
              <button
                onClick={() => setShowActionsPanel(!showActionsPanel)}
                className={`p-2 rounded-lg transition-colors ${
                  showActionsPanel ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'
                }`}
                title="文档操作"
              >
                <Settings className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* 文档内容区域 */}
        <div className="flex-1 overflow-auto bg-white">
          {currentTab ? (
            <div 
              className="p-8 max-w-4xl mx-auto"
              style={{ zoom: `${zoom}%` }}
            >
              <div className="prose prose-gray max-w-none">
                <pre className="whitespace-pre-wrap font-sans">
                  {currentTab.content}
                </pre>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">选择一个文档开始查看</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 操作面板 */}
      {showActions && showActionsPanel && currentTab && (
        <>
          {/* 分隔条 */}
          <div
            className="w-1 bg-gray-200 hover:bg-blue-400 cursor-col-resize transition-colors"
            onMouseDown={(e) => {
              const startX = e.clientX
              const startWidth = actionsWidth
              
              const handleMouseMove = (e: MouseEvent) => {
                const delta = startX - e.clientX
                const newWidth = Math.max(300, Math.min(600, startWidth + delta))
                setActionsWidth(newWidth)
              }
              
              const handleMouseUp = () => {
                document.removeEventListener('mousemove', handleMouseMove)
                document.removeEventListener('mouseup', handleMouseUp)
              }
              
              document.addEventListener('mousemove', handleMouseMove)
              document.addEventListener('mouseup', handleMouseUp)
            }}
          />
          
          {/* 操作面板内容 */}
          <div 
            className="bg-gray-50 border-l border-gray-200 overflow-y-auto"
            style={{ width: `${actionsWidth}px` }}
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">文档操作</h3>
                <button
                  onClick={() => setShowActionsPanel(false)}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              
              <DocumentActions
                documentId={currentTab.id}
                documentName={currentTab.name}
                documentStatus={currentTab.status || 'uploaded'}
                onActionComplete={(action, result) => {
                  console.log(`操作 ${action} 完成:`, result)
                  // 可以在这里更新文档状态或刷新内容
                }}
                onViewResult={onViewResult}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}