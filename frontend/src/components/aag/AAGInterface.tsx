'use client'

import { useState, useEffect } from 'react'
import { FiUpload, FiPlay, FiPause, FiDownload, FiSettings } from 'react-icons/fi'
import DocumentUpload from './DocumentUpload'
import AnalysisWorkflow from './AnalysisWorkflow'
import AICopilot from '../copilot/AICopilot'
import ResultsDisplay from './ResultsDisplay'
import DocumentActions from './DocumentActions'
import ResultViewModal from './ResultViewModal'

interface AAGInterfaceProps {
  projectId: string
}

export default function AAGInterface({ projectId }: AAGInterfaceProps) {
  const [activeDocument, setActiveDocument] = useState<string | null>(null)
  const [activeDocumentName, setActiveDocumentName] = useState<string>('')
  const [activeDocumentStatus, setActiveDocumentStatus] = useState<string>('')
  const [analysisRunning, setAnalysisRunning] = useState(false)
  const [analysisResults, setAnalysisResults] = useState<any>(null)
  const [copilotOpen, setCopilotOpen] = useState(true)
  const [resultModalOpen, setResultModalOpen] = useState(false)
  const [resultModalAction, setResultModalAction] = useState<'summary' | 'index' | 'analysis'>('summary')

  const handleDocumentSelect = (documentId: string, documentName?: string, documentStatus?: string) => {
    setActiveDocument(documentId)
    setActiveDocumentName(documentName || '')
    setActiveDocumentStatus(documentStatus || '')
  }

  const handleViewResult = (actionType: string, documentId: string) => {
    setResultModalAction(actionType as 'summary' | 'index' | 'analysis')
    setResultModalOpen(true)
  }

  const handleActionComplete = (action: string, result: any) => {
    console.log(`操作 ${action} 完成:`, result)
    // 可以添加成功提示或其他逻辑
  }

  return (
    <div className="h-screen bg-gray-900 text-gray-100 flex flex-col">
      {/* 移动端响应式处理 */}
      <style jsx>{`
        @media (max-width: 768px) {
          .desktop-layout { display: none; }
          .mobile-layout { display: flex; }
        }
        @media (min-width: 769px) {
          .desktop-layout { display: flex; }
          .mobile-layout { display: none; }
        }
      `}</style>
      {/* 顶部工具栏 */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">AAG 智能分析引擎</h1>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-400">系统就绪</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-sm font-medium">
              <FiUpload size={16} />
              <span>上传文档</span>
            </button>
            
            <button 
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors text-sm font-medium ${
                analysisRunning 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-green-600 hover:bg-green-700'
              }`}
              onClick={() => setAnalysisRunning(!analysisRunning)}
            >
              {analysisRunning ? <FiPause size={16} /> : <FiPlay size={16} />}
              <span>{analysisRunning ? '暂停分析' : '开始分析'}</span>
            </button>
            
            <button className="p-2 text-gray-400 hover:text-gray-200 rounded-lg hover:bg-gray-700 transition-colors">
              <FiSettings size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* 主内容区域 - 桌面版 */}
      <div className="desktop-layout flex-1 flex overflow-hidden gap-2">
        {/* 左侧：文档和工作流 */}
        <div className="w-1/4 border-r border-gray-700 flex flex-col">
          {/* 文档上传区域 */}
          <div className="border-b border-gray-700">
            <DocumentUpload 
              projectId={projectId}
              onDocumentSelect={handleDocumentSelect}
            />
          </div>
          
          {/* 文档操作面板 */}
          {activeDocument && (
            <div className="border-b border-gray-700 p-4">
              <DocumentActions
                documentId={activeDocument}
                documentName={activeDocumentName}
                documentStatus={activeDocumentStatus}
                onActionComplete={handleActionComplete}
                onViewResult={handleViewResult}
              />
            </div>
          )}
          
          {/* 分析工作流 */}
          <div className="flex-1">
            <AnalysisWorkflow 
              documentId={activeDocument}
              isRunning={analysisRunning}
              onResultsUpdate={setAnalysisResults}
            />
          </div>
        </div>

        {/* 中间：结果展示 */}
        <div className="flex-1 flex flex-col">
          <ResultsDisplay 
            results={analysisResults}
            documentId={activeDocument}
          />
        </div>

        {/* 右侧：AI副驾驶 */}
        <div className="w-80">
          <AICopilot 
            isOpen={copilotOpen}
            onToggle={() => setCopilotOpen(!copilotOpen)}
            context={{
              activeDocument,
              analysisResults,
              projectId
            }}
          />
        </div>
      </div>

      {/* 移动端布局 */}
      <div className="mobile-layout flex-1 flex flex-col">
        {/* 移动端标签切换 */}
        <div className="bg-gray-800 border-b border-gray-700 flex">
          <button className="flex-1 p-3 text-center text-sm border-r border-gray-700 bg-gray-700">
            📄 文档
          </button>
          <button className="flex-1 p-3 text-center text-sm border-r border-gray-700">
            📊 结果
          </button>
          <button className="flex-1 p-3 text-center text-sm">
            🤖 AI助手
          </button>
        </div>
        
        {/* 移动端内容区域 */}
        <div className="flex-1 overflow-hidden">
          <div className="p-4">
            <DocumentUpload 
              projectId={projectId}
              onDocumentSelect={handleDocumentSelect}
            />
            <div className="mt-4">
              <AnalysisWorkflow 
                documentId={activeDocument}
                isRunning={analysisRunning}
                onResultsUpdate={setAnalysisResults}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 结果查看模态框 */}
      <ResultViewModal
        isOpen={resultModalOpen}
        onClose={() => setResultModalOpen(false)}
        documentId={activeDocument || ''}
        documentName={activeDocumentName}
        actionType={resultModalAction}
      />
    </div>
  )
}