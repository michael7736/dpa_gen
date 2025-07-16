'use client'

import { useState, useCallback } from 'react'
import { FiUpload, FiFile, FiX, FiCheck, FiClock, FiAlertCircle } from 'react-icons/fi'

interface Document {
  id: string
  name: string
  size: number
  status: 'uploading' | 'processing' | 'ready' | 'error'
  progress?: number
  skimResult?: any
}

interface DocumentUploadProps {
  projectId: string
  onDocumentSelect: (documentId: string, documentName?: string, documentStatus?: string) => void
}

export default function DocumentUpload({ projectId, onDocumentSelect }: DocumentUploadProps) {
  const [documents, setDocuments] = useState<Document[]>([
    {
      id: 'doc1',
      name: '量子计算医疗应用.pdf',
      size: 2048000,
      status: 'ready',
      skimResult: {
        document_type: '学术论文',
        quality_level: '高',
        core_value: '量子计算在医疗诊断中的突破性应用'
      }
    },
    {
      id: 'doc2', 
      name: 'AI药物发现研究.pdf',
      size: 1536000,
      status: 'ready',
      skimResult: {
        document_type: '研究报告',
        quality_level: '中',
        core_value: 'AI技术在新药研发中的应用现状'
      }
    }
  ])
  const [dragOver, setDragOver] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    files.forEach(file => {
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        handleFileUpload(file)
      }
    })
  }, [])

  const handleFileUpload = (file: File) => {
    const newDoc: Document = {
      id: `doc_${Date.now()}`,
      name: file.name,
      size: file.size,
      status: 'uploading',
      progress: 0
    }

    setDocuments(prev => [...prev, newDoc])

    // 模拟上传进度
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 20
      if (progress >= 100) {
        clearInterval(interval)
        setDocuments(prev => prev.map(doc => 
          doc.id === newDoc.id 
            ? { ...doc, status: 'processing', progress: 100 }
            : doc
        ))
        
        // 模拟处理完成
        setTimeout(() => {
          setDocuments(prev => prev.map(doc => 
            doc.id === newDoc.id 
              ? { 
                  ...doc, 
                  status: 'ready',
                  skimResult: {
                    document_type: '技术文档',
                    quality_level: '中',
                    core_value: '新上传文档的快速分析结果'
                  }
                }
              : doc
          ))
        }, 2000)
      } else {
        setDocuments(prev => prev.map(doc => 
          doc.id === newDoc.id 
            ? { ...doc, progress }
            : doc
        ))
      }
    }, 500)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <FiClock className="text-yellow-400 animate-spin" size={16} />
      case 'ready':
        return <FiCheck className="text-green-400" size={16} />
      case 'error':
        return <FiAlertCircle className="text-red-400" size={16} />
      default:
        return <FiFile className="text-gray-400" size={16} />
    }
  }

  return (
    <div className="p-4">
      {/* 上传区域 */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          dragOver 
            ? 'border-blue-500 bg-blue-500/10' 
            : 'border-gray-600 hover:border-gray-500'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <FiUpload className="mx-auto mb-4 text-gray-400" size={32} />
        <p className="text-gray-300 mb-2">拖拽文档到此处或点击上传</p>
        <p className="text-sm text-gray-500">支持 PDF、Word、Markdown 格式</p>
        <input
          type="file"
          accept=".pdf,.doc,.docx,.md"
          multiple
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files || [])
            files.forEach(handleFileUpload)
          }}
        />
        <button 
          className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          onClick={() => {
            const input = document.querySelector('input[type="file"]') as HTMLInputElement
            input?.click()
          }}
        >
          选择文件
        </button>
      </div>

      {/* 文档列表 */}
      <div className="mt-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">项目文档</h3>
        <div className="space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                doc.status === 'ready' 
                  ? 'border-gray-600 hover:border-blue-500 hover:bg-gray-800' 
                  : 'border-gray-700 bg-gray-800'
              }`}
              onClick={() => doc.status === 'ready' && onDocumentSelect(doc.id, doc.name, doc.status)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  {getStatusIcon(doc.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate">
                      {doc.name}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatFileSize(doc.size)}
                    </p>
                    
                    {/* 上传/处理进度 */}
                    {(doc.status === 'uploading' || doc.status === 'processing') && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                          <span>
                            {doc.status === 'uploading' ? '上传中...' : '分析中...'}
                          </span>
                          <span>{Math.round(doc.progress || 0)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1">
                          <div 
                            className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                            style={{ width: `${doc.progress || 0}%` }}
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* 快速略读结果 */}
                    {doc.status === 'ready' && doc.skimResult && (
                      <div className="mt-2 text-xs">
                        <div className="flex items-center space-x-2">
                          <span className="text-blue-400">{doc.skimResult.document_type}</span>
                          <span className="text-gray-500">•</span>
                          <span className={`${
                            doc.skimResult.quality_level === '高' ? 'text-green-400' :
                            doc.skimResult.quality_level === '中' ? 'text-yellow-400' :
                            'text-red-400'
                          }`}>
                            质量: {doc.skimResult.quality_level}
                          </span>
                        </div>
                        <p className="text-gray-400 mt-1 line-clamp-2">
                          {doc.skimResult.core_value}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                
                {doc.status === 'ready' && (
                  <button 
                    className="text-gray-400 hover:text-red-400 ml-2"
                    onClick={(e) => {
                      e.stopPropagation()
                      setDocuments(prev => prev.filter(d => d.id !== doc.id))
                    }}
                  >
                    <FiX size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}