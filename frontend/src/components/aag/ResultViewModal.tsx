'use client'

import { useState, useEffect } from 'react'
import { X, FileText, Search, Brain, Calendar, Clock, CheckCircle, AlertCircle, Copy, Download } from 'lucide-react'
import { documentResultsService, DocumentSummary, DocumentAnalysis } from '@/services/documentResults'

interface ResultViewModalProps {
  isOpen: boolean
  onClose: () => void
  documentId: string
  documentName: string
  actionType: 'summary' | 'index' | 'analysis'
}

export default function ResultViewModal({
  isOpen,
  onClose,
  documentId,
  documentName,
  actionType
}: ResultViewModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [summaryData, setSummaryData] = useState<DocumentSummary | null>(null)
  const [analysisData, setAnalysisData] = useState<DocumentAnalysis | null>(null)
  const [indexData, setIndexData] = useState<any>(null)

  useEffect(() => {
    if (isOpen && documentId) {
      loadResultData()
    }
  }, [isOpen, documentId, actionType])

  const loadResultData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      switch (actionType) {
        case 'summary':
          const summary = await documentResultsService.getSummary(documentId)
          setSummaryData(summary)
          break
        case 'index':
          const indexStats = await documentResultsService.getIndexStats(documentId)
          setIndexData(indexStats)
          break
        case 'analysis':
          const analysis = await documentResultsService.getAnalysis(documentId)
          setAnalysisData(analysis)
          break
      }
    } catch (err: any) {
      setError(err.message || '加载结果失败')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // 可以添加成功提示
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  const getModalTitle = () => {
    switch (actionType) {
      case 'summary':
        return '文档摘要'
      case 'index':
        return '索引信息'
      case 'analysis':
        return '深度分析结果'
      default:
        return '查看结果'
    }
  }

  const getModalIcon = () => {
    switch (actionType) {
      case 'summary':
        return <FileText className="w-6 h-6 text-blue-600" />
      case 'index':
        return <Search className="w-6 h-6 text-green-600" />
      case 'analysis':
        return <Brain className="w-6 h-6 text-purple-600" />
      default:
        return <FileText className="w-6 h-6 text-gray-600" />
    }
  }

  const renderSummaryContent = () => {
    if (!summaryData) return null

    return (
      <div className="space-y-4">
        {/* 元信息 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">生成时间</span>
            <span className="text-sm text-gray-500">{formatDateTime(summaryData.generated_at)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">文档名称</span>
            <span className="text-sm text-gray-500">{summaryData.filename}</span>
          </div>
        </div>

        {/* 摘要内容 */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-lg font-semibold text-gray-900">摘要内容</h4>
            <button
              onClick={() => copyToClipboard(summaryData.summary)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="复制摘要"
            >
              <Copy className="w-4 h-4" />
            </button>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {summaryData.summary}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const renderIndexContent = () => {
    if (!indexData) return null

    return (
      <div className="space-y-4">
        {/* 状态信息 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">索引状态</span>
            <div className="flex items-center space-x-2">
              {indexData.completed ? (
                <CheckCircle className="w-4 h-4 text-green-500" />
              ) : (
                <AlertCircle className="w-4 h-4 text-yellow-500" />
              )}
              <span className={`text-sm ${indexData.completed ? 'text-green-600' : 'text-yellow-600'}`}>
                {indexData.completed ? '已完成' : '处理中'}
              </span>
            </div>
          </div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">完成进度</span>
            <span className="text-sm text-gray-500">{indexData.progress}%</span>
          </div>
          {indexData.message && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">状态信息</span>
              <span className="text-sm text-gray-500">{indexData.message}</span>
            </div>
          )}
        </div>

        {/* 索引详情 */}
        <div>
          <h4 className="text-lg font-semibold text-gray-900 mb-3">索引详情</h4>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            {indexData.completed ? (
              <div className="space-y-2">
                <p className="text-gray-700">✅ 文档已成功建立向量索引</p>
                <p className="text-gray-700">✅ 支持语义搜索和智能检索</p>
                <p className="text-gray-700">✅ 可用于问答和知识查询</p>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-gray-600">⏳ 正在创建文档索引...</p>
                <p className="text-gray-600">⏳ 分析文档结构和内容</p>
                <p className="text-gray-600">⏳ 生成向量表示</p>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderAnalysisContent = () => {
    if (!analysisData) return null

    return (
      <div className="space-y-4">
        {/* 分析元信息 */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-700">分析ID</span>
              <p className="text-sm text-gray-500">{analysisData.analysis_id}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-700">分析深度</span>
              <p className="text-sm text-gray-500">{analysisData.analysis_depth}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-700">状态</span>
              <p className="text-sm text-gray-500">{analysisData.status}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-700">创建时间</span>
              <p className="text-sm text-gray-500">{formatDateTime(analysisData.created_at)}</p>
            </div>
          </div>
        </div>

        {/* 执行摘要 */}
        {analysisData.result.executive_summary && (
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-3">执行摘要</h4>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <p className="text-gray-700 leading-relaxed">
                {analysisData.result.executive_summary}
              </p>
            </div>
          </div>
        )}

        {/* 关键洞察 */}
        {analysisData.result.key_insights && analysisData.result.key_insights.length > 0 && (
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-3">关键洞察</h4>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <ul className="space-y-2">
                {analysisData.result.key_insights.map((insight, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span className="text-gray-700">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 行动建议 */}
        {analysisData.result.action_items && analysisData.result.action_items.length > 0 && (
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-3">行动建议</h4>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <ul className="space-y-2">
                {analysisData.result.action_items.map((item, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-green-500 mt-1">→</span>
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">加载中...</p>
          </div>
        </div>
      )
    }

    if (error) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={loadResultData}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              重试
            </button>
          </div>
        </div>
      )
    }

    switch (actionType) {
      case 'summary':
        return renderSummaryContent()
      case 'index':
        return renderIndexContent()
      case 'analysis':
        return renderAnalysisContent()
      default:
        return <p className="text-gray-500">暂无数据</p>
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            {getModalIcon()}
            <div>
              <h3 className="text-xl font-semibold text-gray-900">{getModalTitle()}</h3>
              <p className="text-sm text-gray-500">{documentName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {renderContent()}
        </div>

        {/* 底部 */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  )
}