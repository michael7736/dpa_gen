'use client'

import { useState, useEffect } from 'react'
import {
  FileText,
  Search,
  Brain,
  Play,
  Pause,
  RotateCcw,
  Check,
  X,
  Loader2,
  ChevronDown,
  ChevronRight,
  Info,
  Eye,
  Download
} from 'lucide-react'
import { documentServiceV2, PipelineStage } from '@/services/documentsV2'
import { webSocketService } from '@/services/websocket'

interface DocumentActionsProps {
  documentId: string
  documentName: string
  documentStatus: string
  onActionComplete?: (action: string, result: any) => void
  onViewResult?: (action: string, documentId: string) => void
}

interface ActionConfig {
  id: string
  name: string
  icon: React.ElementType
  description: string
  estimatedTime: string
  color: string
}

const actions: ActionConfig[] = [
  {
    id: 'summary',
    name: '生成摘要',
    icon: FileText,
    description: '快速提取文档核心内容和关键信息',
    estimatedTime: '约30秒',
    color: 'blue'
  },
  {
    id: 'index',
    name: '创建索引',
    icon: Search,
    description: '建立文档索引，支持快速搜索和精准定位',
    estimatedTime: '约2分钟',
    color: 'green'
  },
  {
    id: 'analysis',
    name: '深度分析',
    icon: Brain,
    description: '深入分析文档内容，提取洞察和建议',
    estimatedTime: '约5分钟',
    color: 'purple'
  }
]

export default function DocumentActions({
  documentId,
  documentName,
  documentStatus,
  onActionComplete,
  onViewResult
}: DocumentActionsProps) {
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const [actionStatus, setActionStatus] = useState<Record<string, 'idle' | 'running' | 'completed' | 'failed'>>({})
  const [progress, setProgress] = useState<Record<string, number>>({})
  const [currentStage, setCurrentStage] = useState<Record<string, string>>({})
  const [expandedAction, setExpandedAction] = useState<string | null>(null)
  const [stageDetails, setStageDetails] = useState<Record<string, PipelineStage[]>>({})
  const [pipelineIds, setPipelineIds] = useState<Record<string, string>>({})

  // 初始化动作状态
  useEffect(() => {
    const initialStatus: Record<string, any> = {}
    actions.forEach(action => {
      initialStatus[action.id] = 'idle'
    })
    setActionStatus(initialStatus)
  }, [])

  // 处理动作执行
  const handleAction = async (actionId: string) => {
    if (actionStatus[actionId] === 'running') {
      // 暂停
      await handlePause(actionId)
    } else if (actionStatus[actionId] === 'idle' || actionStatus[actionId] === 'failed') {
      // 开始
      await handleStart(actionId)
    }
  }

  // 开始处理
  const handleStart = async (actionId: string) => {
    try {
      setActiveAction(actionId)
      setActionStatus(prev => ({ ...prev, [actionId]: 'running' }))
      setProgress(prev => ({ ...prev, [actionId]: 0 }))

      // 构建处理选项
      const options = {
        upload_only: false,
        generate_summary: actionId === 'summary',
        create_index: actionId === 'index',
        deep_analysis: actionId === 'analysis'
      }

      // 调用API开始处理
      const response = await documentServiceV2.startProcessing(documentId, options)
      
      if (response.pipeline_id) {
        setPipelineIds(prev => ({ ...prev, [actionId]: response.pipeline_id }))
        
        // 订阅WebSocket进度更新
        webSocketService.subscribePipelineProgress(
          response.pipeline_id,
          (progressData) => {
            handleProgressUpdate(actionId, progressData)
          }
        )
      }
    } catch (error) {
      console.error(`启动${actionId}失败:`, error)
      setActionStatus(prev => ({ ...prev, [actionId]: 'failed' }))
      setActiveAction(null)
    }
  }

  // 暂停处理
  const handlePause = async (actionId: string) => {
    try {
      const pipelineId = pipelineIds[actionId]
      if (pipelineId) {
        await documentServiceV2.interruptProcessing(documentId, pipelineId)
        setActionStatus(prev => ({ ...prev, [actionId]: 'idle' }))
        setActiveAction(null)
      }
    } catch (error) {
      console.error(`暂停${actionId}失败:`, error)
    }
  }

  // 恢复处理
  const handleResume = async (actionId: string) => {
    try {
      const pipelineId = pipelineIds[actionId]
      if (pipelineId) {
        await documentServiceV2.resumeProcessing(documentId, pipelineId)
        setActionStatus(prev => ({ ...prev, [actionId]: 'running' }))
        setActiveAction(actionId)
      }
    } catch (error) {
      console.error(`恢复${actionId}失败:`, error)
    }
  }

  // 处理进度更新
  const handleProgressUpdate = (actionId: string, progressData: any) => {
    setProgress(prev => ({ ...prev, [actionId]: progressData.overall_progress }))
    setCurrentStage(prev => ({ ...prev, [actionId]: progressData.current_stage }))
    setStageDetails(prev => ({ ...prev, [actionId]: progressData.stages }))

    // 检查是否完成
    if (progressData.completed) {
      setActionStatus(prev => ({ ...prev, [actionId]: 'completed' }))
      setActiveAction(null)
      
      // 取消订阅
      webSocketService.unsubscribePipelineProgress(progressData.pipeline_id)
      
      // 通知完成
      if (onActionComplete) {
        onActionComplete(actionId, progressData)
      }
    }
  }

  // 渲染动作卡片
  const renderActionCard = (action: ActionConfig) => {
    const status = actionStatus[action.id] || 'idle'
    const currentProgress = progress[action.id] || 0
    const isExpanded = expandedAction === action.id
    const Icon = action.icon

    return (
      <div key={action.id} className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {/* 卡片头部 */}
        <div className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <div className={`p-2 rounded-lg bg-${action.color}-100`}>
                <Icon className={`w-5 h-5 text-${action.color}-600`} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{action.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{action.description}</p>
                <p className="text-xs text-gray-400 mt-1">{action.estimatedTime}</p>
              </div>
            </div>
            
            {/* 操作按钮 */}
            <div className="flex items-center space-x-2">
              {status === 'idle' && (
                <button
                  onClick={() => handleAction(action.id)}
                  className={`px-4 py-2 bg-${action.color}-500 text-white rounded-lg hover:bg-${action.color}-600 transition-colors flex items-center space-x-2`}
                  disabled={activeAction !== null && activeAction !== action.id}
                >
                  <Play className="w-4 h-4" />
                  <span>开始</span>
                </button>
              )}
              
              {status === 'running' && (
                <>
                  <button
                    onClick={() => handleAction(action.id)}
                    className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors flex items-center space-x-2"
                  >
                    <Pause className="w-4 h-4" />
                    <span>暂停</span>
                  </button>
                  <button
                    onClick={() => setExpandedAction(isExpanded ? null : action.id)}
                    className="p-2 text-gray-400 hover:text-gray-600"
                  >
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                </>
              )}
              
              {status === 'completed' && (
                <div className="flex items-center space-x-2">
                  <div className="flex items-center text-green-600">
                    <Check className="w-5 h-5 mr-1" />
                    <span className="text-sm font-medium">已完成</span>
                  </div>
                  <button
                    onClick={() => onViewResult?.(action.id, documentId)}
                    className={`px-3 py-1 bg-${action.color}-100 text-${action.color}-700 rounded-lg hover:bg-${action.color}-200 transition-colors flex items-center space-x-1 text-sm`}
                  >
                    <Eye className="w-4 h-4" />
                    <span>查看结果</span>
                  </button>
                </div>
              )}
              
              {status === 'failed' && (
                <button
                  onClick={() => handleAction(action.id)}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center space-x-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>重试</span>
                </button>
              )}
            </div>
          </div>

          {/* 进度条 */}
          {(status === 'running' || status === 'completed') && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>{currentStage[action.id] || '准备中...'}</span>
                <span>{currentProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`bg-${action.color}-500 h-2 rounded-full transition-all duration-300`}
                  style={{ width: `${currentProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* 展开的详细信息 */}
        {isExpanded && stageDetails[action.id] && (
          <div className="border-t border-gray-200 px-4 py-3 bg-gray-50">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">处理阶段详情</h4>
            <div className="space-y-2">
              {stageDetails[action.id].map((stage, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    {stage.status === 'completed' && <Check className="w-4 h-4 text-green-500" />}
                    {stage.status === 'processing' && <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />}
                    {stage.status === 'pending' && <div className="w-4 h-4 rounded-full bg-gray-300" />}
                    {stage.status === 'failed' && <X className="w-4 h-4 text-red-500" />}
                    <span className={stage.status === 'processing' ? 'font-medium' : ''}>
                      {stage.name}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {stage.message && (
                      <span className="text-gray-500">{stage.message}</span>
                    )}
                    {stage.duration && (
                      <span className="text-gray-400">{stage.duration.toFixed(1)}s</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 文档信息头部 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{documentName}</h2>
            <p className="text-sm text-gray-500 mt-1">文档ID: {documentId}</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">
              {documentStatus}
            </span>
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <Info className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 操作卡片列表 */}
      <div className="space-y-3">
        {actions.map(action => renderActionCard(action))}
      </div>

      {/* 提示信息 */}
      {activeAction && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <Info className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium">处理进行中</p>
              <p className="mt-1">您可以随时暂停当前处理，稍后继续。处理过程中的所有进度都会被保存。</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}