'use client'

import { useState } from 'react'
import { 
  FileText, 
  Folder, 
  FolderOpen, 
  Plus, 
  RefreshCw,
  Search,
  Upload,
  MoreVertical,
  Download,
  Trash2,
  Settings,
  CheckCircle
} from 'lucide-react'
import { ProcessingOptions, PipelineProgressResponse } from '@/services/documentsV2'

export interface FileItem {
  id: string
  name: string
  type: 'file' | 'folder'
  category: 'original' | 'process' | 'notes'
  extension?: string
  size?: number
  lastModified?: Date
  children?: FileItem[]
  content?: string
  path?: string
}

interface FileExplorerProps {
  files: FileItem[]
  onFileSelect: (file: FileItem) => void
  selectedFile?: FileItem | null
  onFileUpload?: (file: File) => void
  onFileCreate?: (name: string, type: 'file' | 'folder', category: string) => void
  onFileDelete?: (fileId: string) => void
  uploadingFile?: {
    name: string
    progress: number
    status: 'uploading' | 'processing' | 'completed' | 'error'
  } | null
  processingOptions?: ProcessingOptions
  onProcessingOptionsChange?: (options: ProcessingOptions) => void
  processingProgress?: PipelineProgressResponse | null
}

export default function FileExplorer({ 
  files, 
  onFileSelect, 
  selectedFile,
  onFileUpload,
  onFileCreate,
  onFileDelete,
  uploadingFile,
  processingOptions,
  onProcessingOptionsChange,
  processingProgress
}: FileExplorerProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(['original', 'process', 'notes'])
  )
  const [searchTerm, setSearchTerm] = useState('')
  const [showContextMenu, setShowContextMenu] = useState<{
    x: number
    y: number
    file: FileItem
  } | null>(null)

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

  // 搜索文件
  const filterFiles = (items: FileItem[]): FileItem[] => {
    if (!searchTerm) return items
    
    return items.filter(item => {
      if (item.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return true
      }
      if (item.type === 'folder' && item.children) {
        return filterFiles(item.children).length > 0
      }
      return false
    }).map(item => ({
      ...item,
      children: item.children ? filterFiles(item.children) : undefined
    }))
  }

  // 获取文件图标
  const getFileIcon = (file: FileItem) => {
    if (file.type === 'folder') {
      return expandedFolders.has(file.id) ? 
        <FolderOpen className="w-4 h-4 text-blue-500" /> : 
        <Folder className="w-4 h-4 text-blue-500" />
    }
    
    const iconClass = "w-4 h-4"
    switch (file.extension) {
      case 'pdf': return <FileText className={`${iconClass} text-red-500`} />
      case 'md': return <FileText className={`${iconClass} text-blue-500`} />
      case 'doc':
      case 'docx': return <FileText className={`${iconClass} text-blue-600`} />
      default: return <FileText className={`${iconClass} text-gray-500`} />
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 处理右键菜单
  const handleContextMenu = (e: React.MouseEvent, file: FileItem) => {
    e.preventDefault()
    setShowContextMenu({
      x: e.clientX,
      y: e.clientY,
      file
    })
  }

  // 关闭右键菜单
  const closeContextMenu = () => {
    setShowContextMenu(null)
  }

  // 渲染文件树
  const renderFileTree = (items: FileItem[], level: number = 0) => {
    return items.map(item => (
      <div key={item.id} className="select-none">
        {item.type === 'folder' ? (
          <div>
            <div
              className={`flex items-center py-2 px-3 hover:bg-gray-50 cursor-pointer text-sm group rounded-lg mx-1 transition-all duration-200`}
              style={{ paddingLeft: `${level * 16 + 12}px` }}
              onClick={() => toggleFolder(item.id)}
              onContextMenu={(e) => handleContextMenu(e, item)}
            >
              {getFileIcon(item)}
              <span className="font-medium ml-2 flex-1 text-gray-700">{item.name}</span>
              <button
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded transition-all duration-200"
                onClick={(e) => {
                  e.stopPropagation()
                  // 处理文件夹操作
                }}
              >
                <MoreVertical className="w-3 h-3 text-gray-500" />
              </button>
            </div>
            {expandedFolders.has(item.id) && item.children && (
              <div>
                {renderFileTree(item.children, level + 1)}
              </div>
            )}
          </div>
        ) : (
          <div
            className={`flex items-center py-2 px-3 hover:bg-gray-50 cursor-pointer text-sm group rounded-lg mx-1 transition-all duration-200 ${
              selectedFile?.id === item.id ? 'bg-blue-50 text-blue-700 border border-blue-200' : ''
            }`}
            style={{ paddingLeft: `${level * 16 + 12}px` }}
            onClick={() => onFileSelect(item)}
            onContextMenu={(e) => handleContextMenu(e, item)}
          >
            {getFileIcon(item)}
            <div className="flex-1 min-w-0 ml-2">
              <div className="truncate font-medium">{item.name}</div>
              {item.size && (
                <div className="text-xs text-gray-400 mt-0.5">
                  {formatFileSize(item.size)}
                </div>
              )}
            </div>
            <button
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded transition-all duration-200"
              onClick={(e) => {
                e.stopPropagation()
                // 处理文件操作
              }}
            >
              <MoreVertical className="w-3 h-3 text-gray-500" />
            </button>
          </div>
        )}
      </div>
    ))
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 头部工具栏 */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5a2 2 0 012-2h4a2 2 0 012 2v2H8V5z" />
            </svg>
            项目文件
          </h2>
          <div className="flex items-center space-x-1">
            <button 
              className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-200"
              title="新建文件"
              onClick={() => onFileCreate?.('新建文件.md', 'file', 'notes')}
            >
              <Plus className="w-4 h-4 text-gray-600" />
            </button>
            <button 
              className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-200"
              title="上传文件"
              onClick={() => {
                const input = document.createElement('input')
                input.type = 'file'
                input.accept = '.pdf,.doc,.docx,.md,.txt'
                input.onchange = (e) => {
                  const file = (e.target as HTMLInputElement).files?.[0]
                  if (file && onFileUpload) {
                    onFileUpload(file)
                  }
                }
                input.click()
              }}
            >
              <Upload className="w-4 h-4 text-gray-600" />
            </button>
            <button 
              className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg transition-all duration-200"
              title="刷新"
            >
              <RefreshCw className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>
        
        {/* 搜索框 */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
          <input
            type="text"
            placeholder="搜索文件..."
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        {/* 处理选项 */}
        {processingOptions && onProcessingOptionsChange && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center mb-2">
              <Settings className="w-4 h-4 text-gray-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">上传处理选项</span>
            </div>
            <div className="space-y-2">
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={processingOptions.upload_only}
                  disabled={true}
                  className="rounded border-gray-300"
                />
                <span className="text-gray-600">仅上传（必选）</span>
              </label>
              <label className="flex items-center space-x-2 text-sm hover:bg-white p-1 rounded transition-colors">
                <input
                  type="checkbox"
                  checked={processingOptions.generate_summary}
                  onChange={(e) => onProcessingOptionsChange({
                    ...processingOptions,
                    generate_summary: e.target.checked
                  })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-gray-700">生成摘要</span>
              </label>
              <label className="flex items-center space-x-2 text-sm hover:bg-white p-1 rounded transition-colors">
                <input
                  type="checkbox"
                  checked={processingOptions.create_index}
                  onChange={(e) => onProcessingOptionsChange({
                    ...processingOptions,
                    create_index: e.target.checked
                  })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-gray-700">创建索引</span>
              </label>
              <label className="flex items-center space-x-2 text-sm hover:bg-white p-1 rounded transition-colors">
                <input
                  type="checkbox"
                  checked={processingOptions.deep_analysis}
                  onChange={(e) => onProcessingOptionsChange({
                    ...processingOptions,
                    deep_analysis: e.target.checked
                  })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-gray-700">深度分析</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* 文件列表 */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* 上传进度显示 */}
        {uploadingFile && (
          <div className="mx-2 mb-3 p-3 bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium truncate text-blue-800">{uploadingFile.name}</span>
              <span className="text-blue-600 font-medium">
                {uploadingFile.status === 'uploading' && `${uploadingFile.progress}%`}
                {uploadingFile.status === 'processing' && '处理中...'}
                {uploadingFile.status === 'completed' && '完成'}
                {uploadingFile.status === 'error' && '错误'}
              </span>
            </div>
            <div className="w-full bg-white rounded-full h-2 shadow-inner">
              <div 
                className={`h-2 rounded-full transition-all duration-500 ${
                  uploadingFile.status === 'error' ? 'bg-red-500' : 
                  uploadingFile.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                }`}
                style={{ width: `${uploadingFile.status === 'processing' ? 100 : uploadingFile.progress}%` }}
              />
            </div>
            {uploadingFile.status === 'processing' && (
              <div className="mt-2 text-blue-700 text-sm flex items-center">
                <div className="animate-spin rounded-full h-3 w-3 border-2 border-blue-600 border-t-transparent mr-2"></div>
                正在分析文档内容...
              </div>
            )}
          </div>
        )}
        
        {/* 处理进度详情 */}
        {processingProgress && (
          <div className="mx-2 mb-3 p-3 bg-gradient-to-r from-purple-50 to-purple-100 border border-purple-200 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-purple-800">处理进度</span>
              <span className="text-purple-600 font-medium">
                {processingProgress.overall_progress.toFixed(1)}%
              </span>
            </div>
            
            {/* 当前阶段 */}
            {processingProgress.current_stage && (
              <div className="mb-2 p-2 bg-yellow-100 border border-yellow-300 rounded text-sm">
                <span className="font-medium text-yellow-900">正在执行: </span>
                <span className="text-yellow-800">{processingProgress.current_stage}</span>
              </div>
            )}
            
            {/* 各阶段进度 */}
            <div className="space-y-1">
              {processingProgress.stages.map((stage) => (
                <div key={stage.id} className="flex items-center space-x-2 text-sm">
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center ${
                    stage.status === 'completed' ? 'bg-green-500' :
                    stage.status === 'processing' ? 'bg-blue-500' :
                    stage.status === 'failed' ? 'bg-red-500' :
                    'bg-gray-300'
                  }`}>
                    {stage.status === 'completed' && (
                      <CheckCircle className="w-3 h-3 text-white" />
                    )}
                    {stage.status === 'processing' && (
                      <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                    )}
                  </div>
                  <span className={`flex-1 ${
                    stage.status === 'processing' ? 'font-medium text-blue-700' : 'text-gray-700'
                  }`}>
                    {stage.name}
                  </span>
                  {stage.duration && (
                    <span className="text-gray-500 text-xs">
                      {stage.duration.toFixed(1)}s
                    </span>
                  )}
                </div>
              ))}
            </div>
            
            {processingProgress.completed && (
              <div className="mt-2 text-green-700 text-sm font-medium">
                ✓ 处理完成
              </div>
            )}
          </div>
        )}
        
        {renderFileTree(filterFiles(files))}
      </div>

      {/* 右键菜单 */}
      {showContextMenu && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={closeContextMenu}
          />
          <div
            className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[150px]"
            style={{
              left: showContextMenu.x,
              top: showContextMenu.y
            }}
          >
            <button
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center"
              onClick={() => {
                // 处理下载
                closeContextMenu()
              }}
            >
              <Download className="w-4 h-4 mr-2" />
              下载
            </button>
            <button
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center text-red-600"
              onClick={() => {
                if (onFileDelete) {
                  onFileDelete(showContextMenu.file.id)
                }
                closeContextMenu()
              }}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </button>
          </div>
        </>
      )}
    </div>
  )
}