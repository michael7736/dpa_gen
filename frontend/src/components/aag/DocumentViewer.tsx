'use client'

import { useState, useEffect } from 'react'
import { 
  FileText, 
  X, 
  Download, 
  Printer, 
  Search, 
  ZoomIn, 
  ZoomOut,
  Maximize2,
  Minimize2,
  Eye,
  Edit3
} from 'lucide-react'

export interface TabItem {
  id: string
  name: string
  content: string
  type: string
  isDirty: boolean
  filePath?: string
  lastModified?: Date
}

interface DocumentViewerProps {
  tabs: TabItem[]
  activeTab: string | null
  onTabChange: (tabId: string) => void
  onTabClose: (tabId: string) => void
  onContentChange?: (tabId: string, content: string) => void
}

export default function DocumentViewer({
  tabs,
  activeTab,
  onTabChange,
  onTabClose,
  onContentChange
}: DocumentViewerProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState<number[]>([])
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [viewMode, setViewMode] = useState<'view' | 'edit'>('view')
  const [zoom, setZoom] = useState(100)

  // 获取当前活动标签页
  const currentTab = tabs.find(tab => tab.id === activeTab)

  // 搜索功能
  const handleSearch = (term: string) => {
    setSearchTerm(term)
    if (!term || !currentTab) {
      setSearchResults([])
      return
    }

    const content = currentTab.content.toLowerCase()
    const searchTerm = term.toLowerCase()
    const results: number[] = []
    let index = 0

    while (index < content.length) {
      const foundIndex = content.indexOf(searchTerm, index)
      if (foundIndex === -1) break
      results.push(foundIndex)
      index = foundIndex + 1
    }

    setSearchResults(results)
    setCurrentSearchIndex(0)
  }

  // 高亮搜索结果
  const highlightSearchResults = (content: string) => {
    if (!searchTerm || searchResults.length === 0) {
      return content
    }

    let highlightedContent = content
    const regex = new RegExp(`(${searchTerm})`, 'gi')
    highlightedContent = highlightedContent.replace(
      regex,
      '<mark class="bg-yellow-200 px-1 rounded">$1</mark>'
    )

    return highlightedContent
  }

  // 渲染文档内容
  const renderDocumentContent = (tab: TabItem) => {
    const baseClasses = "w-full h-full p-6 bg-white rounded-lg shadow-sm border border-gray-200"
    const zoomStyle = { transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }

    switch (tab.type) {
      case 'pdf':
        return (
          <div className={baseClasses} style={zoomStyle}>
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 text-red-500" />
                <h3 className="text-lg font-semibold mb-2">{tab.name}</h3>
                <p className="text-gray-600 mb-4">PDF文档预览</p>
                <button className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
                  在新窗口中打开
                </button>
              </div>
            </div>
          </div>
        )

      case 'md':
        return (
          <div className={baseClasses} style={zoomStyle}>
            {viewMode === 'edit' ? (
              <textarea
                className="w-full h-full p-4 border border-gray-200 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={tab.content}
                onChange={(e) => onContentChange?.(tab.id, e.target.value)}
                placeholder="在此输入Markdown内容..."
              />
            ) : (
              <div className="prose prose-sm max-w-none h-full overflow-y-auto">
                <div
                  dangerouslySetInnerHTML={{
                    __html: highlightSearchResults(tab.content.replace(/\n/g, '<br>'))
                  }}
                />
              </div>
            )}
          </div>
        )

      default:
        return (
          <div className={baseClasses} style={zoomStyle}>
            <div className="h-full overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                {highlightSearchResults(tab.content)}
              </pre>
            </div>
          </div>
        )
    }
  }

  return (
    <div className={`flex flex-col h-full ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>
      {/* 标签页栏 */}
      <div className="bg-white border-b border-gray-200 min-h-[48px] flex items-center">
        <div className="flex-1 flex items-center overflow-x-auto">
          {tabs.map(tab => (
            <div
              key={tab.id}
              className={`flex items-center px-4 py-3 text-sm border-r border-gray-200 cursor-pointer min-w-0 group transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => onTabChange(tab.id)}
            >
              <FileText className="w-4 h-4 mr-2 flex-shrink-0" />
              <span className="truncate max-w-[180px] font-medium">{tab.name}</span>
              {tab.isDirty && <span className="ml-2 text-orange-500">●</span>}
              <button
                className="ml-2 p-1 hover:bg-gray-200 rounded flex-shrink-0 opacity-0 group-hover:opacity-100 transition-all duration-200"
                onClick={(e) => {
                  e.stopPropagation()
                  onTabClose(tab.id)
                }}
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>

        {/* 工具栏 */}
        {currentTab && (
          <div className="flex items-center space-x-1 px-4 py-2 border-l border-gray-200 bg-gray-50">
            {/* 搜索 */}
            <div className="flex items-center space-x-2">
              <Search className="w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="搜索..."
                className="w-36 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
              />
              {searchResults.length > 0 && (
                <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {currentSearchIndex + 1}/{searchResults.length}
                </span>
              )}
            </div>

            {/* 查看模式切换 */}
            {currentTab.type === 'md' && (
              <button
                className={`p-2 rounded-lg transition-all duration-200 ${
                  viewMode === 'edit' 
                    ? 'bg-blue-100 text-blue-600 shadow-sm' 
                    : 'hover:bg-white hover:shadow-sm text-gray-600'
                }`}
                onClick={() => setViewMode(viewMode === 'edit' ? 'view' : 'edit')}
                title={viewMode === 'edit' ? '预览模式' : '编辑模式'}
              >
                {viewMode === 'edit' ? <Eye className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
              </button>
            )}

            {/* 缩放控制 */}
            <div className="flex items-center space-x-1 bg-white rounded-lg shadow-sm px-2 py-1">
              <button
                className="p-1 hover:bg-gray-100 rounded transition-all duration-200"
                onClick={() => setZoom(Math.max(50, zoom - 10))}
                title="缩小"
              >
                <ZoomOut className="w-4 h-4 text-gray-600" />
              </button>
              <span className="text-sm text-gray-600 w-12 text-center font-medium">{zoom}%</span>
              <button
                className="p-1 hover:bg-gray-100 rounded transition-all duration-200"
                onClick={() => setZoom(Math.min(200, zoom + 10))}
                title="放大"
              >
                <ZoomIn className="w-4 h-4 text-gray-600" />
              </button>
            </div>

            {/* 全屏切换 */}
            <button
              className="p-2 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-200"
              onClick={() => setIsFullscreen(!isFullscreen)}
              title={isFullscreen ? '退出全屏' : '全屏'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4 text-gray-600" /> : <Maximize2 className="w-4 h-4 text-gray-600" />}
            </button>

            {/* 下载 */}
            <button
              className="p-2 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-200"
              onClick={() => {
                const element = document.createElement('a')
                const file = new Blob([currentTab.content], { type: 'text/plain' })
                element.href = URL.createObjectURL(file)
                element.download = currentTab.name
                document.body.appendChild(element)
                element.click()
                document.body.removeChild(element)
              }}
              title="下载"
            >
              <Download className="w-4 h-4 text-gray-600" />
            </button>

            {/* 打印 */}
            <button
              className="p-2 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-200"
              onClick={() => window.print()}
              title="打印"
            >
              <Printer className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        )}
      </div>

      {/* 文档内容区域 */}
      <div className="flex-1 overflow-hidden p-6 bg-gray-50">
        {currentTab ? (
          <div className="h-full">
            {renderDocumentContent(currentTab)}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center bg-white rounded-lg shadow-sm p-12 max-w-md">
              <div className="w-20 h-20 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
                <FileText className="w-10 h-10 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 text-gray-700">选择一个文件来查看</h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                从左侧文件列表中选择要查看的文档，<br />
                或者上传新的文档开始分析
              </p>
              <div className="mt-6 flex items-center justify-center space-x-4 text-xs text-gray-400">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
                  PDF
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  Markdown
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  Word
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 状态栏 */}
      {currentTab && (
        <div className="bg-gray-50 border-t border-gray-200 px-4 py-1 text-xs text-gray-600 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span>类型: {currentTab.type?.toUpperCase() || 'TEXT'}</span>
            <span>字符数: {currentTab.content.length}</span>
            <span>行数: {currentTab.content.split('\n').length}</span>
          </div>
          <div className="flex items-center space-x-4">
            {currentTab.lastModified && (
              <span>最后修改: {currentTab.lastModified.toLocaleString()}</span>
            )}
            <span>缩放: {zoom}%</span>
          </div>
        </div>
      )}
    </div>
  )
}