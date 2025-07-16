'use client'

import { useState } from 'react'
import DocumentViewer from './DocumentViewer'
import AnalysisResults from './AnalysisResults'

export default function WorkSpace() {
  const [activeTab, setActiveTab] = useState<'document' | 'analysis'>('document')

  return (
    <div className="flex-1 flex flex-col bg-gray-900">
      {/* 工作区标签栏 */}
      <div className="border-b border-gray-700 bg-gray-800">
        <div className="flex items-center px-4">
          <button
            onClick={() => setActiveTab('document')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'document'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            📄 文档预览
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'analysis'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            📊 分析结果
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'document' && <DocumentViewer />}
        {activeTab === 'analysis' && <AnalysisResults />}
      </div>
    </div>
  )
}