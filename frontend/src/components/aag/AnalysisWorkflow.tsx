'use client'

import { useState, useEffect } from 'react'
import { FiPlay, FiCheck, FiClock, FiSettings, FiChevronDown, FiChevronRight } from 'react-icons/fi'

interface WorkflowStep {
  id: string
  name: string
  description: string
  status: 'pending' | 'running' | 'completed' | 'error'
  duration?: number
  progress?: number
  result?: any
  dependencies?: string[]
}

interface AnalysisWorkflowProps {
  documentId: string | null
  isRunning: boolean
  onResultsUpdate: (results: any) => void
}

export default function AnalysisWorkflow({ documentId, isRunning, onResultsUpdate }: AnalysisWorkflowProps) {
  const [selectedWorkflow, setSelectedWorkflow] = useState('standard_analysis')
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([
    {
      id: 'skim',
      name: '快速略读',
      description: '提取文档核心信息和质量评估',
      status: 'completed',
      duration: 3,
      result: {
        document_type: '学术论文',
        quality_level: '高',
        core_value: '量子计算在医疗诊断中的革命性应用'
      }
    },
    {
      id: 'summary',
      name: '渐进式摘要',
      description: '生成多层次文档摘要',
      status: 'running',
      progress: 65,
      dependencies: ['skim']
    },
    {
      id: 'knowledge_graph',
      name: '知识图谱构建',
      description: '提取实体和关系网络',
      status: 'running',
      progress: 45,
      dependencies: ['skim']
    },
    {
      id: 'outline',
      name: '多维大纲',
      description: '提取逻辑、主题、时间、因果大纲',
      status: 'pending',
      dependencies: ['summary']
    },
    {
      id: 'deep_analysis',
      name: '深度分析',
      description: '证据链、交叉引用、批判性思维分析',
      status: 'pending',
      dependencies: ['outline']
    }
  ])

  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set(['skim']))

  const workflowTemplates = [
    {
      id: 'standard_analysis',
      name: '标准分析',
      description: '包含略读、摘要、知识图谱的标准流程',
      estimatedTime: '3-5分钟'
    },
    {
      id: 'critical_review',
      name: '批判性审查',
      description: '深度分析论证质量和逻辑严密性',
      estimatedTime: '5-10分钟'
    },
    {
      id: 'adaptive_analysis',
      name: '自适应分析',
      description: '根据文档质量动态调整分析深度',
      estimatedTime: '2-8分钟'
    }
  ]

  useEffect(() => {
    if (isRunning && documentId) {
      // 模拟工作流执行
      simulateWorkflowExecution()
    }
  }, [isRunning, documentId])

  const simulateWorkflowExecution = () => {
    // 模拟步骤执行进度
    const interval = setInterval(() => {
      setWorkflowSteps(prev => {
        const updated = [...prev]
        let hasUpdates = false

        for (let i = 0; i < updated.length; i++) {
          const step = updated[i]
          
          if (step.status === 'running' && step.progress !== undefined) {
            step.progress = Math.min(100, step.progress + Math.random() * 15)
            hasUpdates = true
            
            if (step.progress >= 100) {
              step.status = 'completed'
              step.duration = Math.floor(Math.random() * 10) + 5
              step.result = generateMockResult(step.id)
              
              // 启动下一个步骤
              const nextStep = updated.find(s => 
                s.status === 'pending' && 
                s.dependencies?.every(dep => 
                  updated.find(d => d.id === dep)?.status === 'completed'
                )
              )
              if (nextStep) {
                nextStep.status = 'running'
                nextStep.progress = 0
              }
            }
          }
        }

        if (!hasUpdates) {
          clearInterval(interval)
        }

        return updated
      })
    }, 1000)

    return () => clearInterval(interval)
  }

  const generateMockResult = (stepId: string) => {
    switch (stepId) {
      case 'summary':
        return {
          level_2: '量子计算技术在医疗诊断领域展现出巨大潜力...',
          level_3: '本研究深入探讨了量子计算在医学影像分析、病理诊断等领域的应用...',
          word_count: 500
        }
      case 'knowledge_graph':
        return {
          entities: 25,
          relations: 18,
          core_entities: ['量子计算', '医疗诊断', 'AI算法', '临床应用']
        }
      case 'outline':
        return {
          dimensions: ['逻辑', '主题', '时间', '因果'],
          structure_score: 0.85
        }
      default:
        return {}
    }
  }

  const getStatusIcon = (step: WorkflowStep) => {
    switch (step.status) {
      case 'completed':
        return <FiCheck className="text-green-400" size={16} />
      case 'running':
        return <FiClock className="text-blue-400 animate-spin" size={16} />
      case 'error':
        return <div className="w-4 h-4 bg-red-400 rounded-full" />
      default:
        return <div className="w-4 h-4 bg-gray-600 rounded-full" />
    }
  }

  const toggleStepExpansion = (stepId: string) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepId)) {
        newSet.delete(stepId)
      } else {
        newSet.add(stepId)
      }
      return newSet
    })
  }

  return (
    <div className="p-4 h-full flex flex-col">
      {/* 工作流选择 */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">分析工作流</h3>
        <select 
          value={selectedWorkflow}
          onChange={(e) => setSelectedWorkflow(e.target.value)}
          className="w-full bg-gray-700 text-gray-200 text-sm px-3 py-2 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
        >
          {workflowTemplates.map(template => (
            <option key={template.id} value={template.id}>
              {template.name} - {template.estimatedTime}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-400 mt-1">
          {workflowTemplates.find(t => t.id === selectedWorkflow)?.description}
        </p>
      </div>

      {/* 执行状态总览 */}
      <div className="mb-4 p-3 bg-gray-800 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-200">执行进度</span>
          <span className="text-xs text-gray-400">
            {workflowSteps.filter(s => s.status === 'completed').length} / {workflowSteps.length}
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ 
              width: `${(workflowSteps.filter(s => s.status === 'completed').length / workflowSteps.length) * 100}%` 
            }}
          />
        </div>
      </div>

      {/* 步骤列表 */}
      <div className="flex-1 overflow-y-auto">
        <h4 className="text-sm font-semibold text-gray-300 mb-3">分析步骤</h4>
        <div className="space-y-2">
          {workflowSteps.map((step, index) => (
            <div key={step.id} className="border border-gray-700 rounded-lg">
              <div 
                className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-800"
                onClick={() => toggleStepExpansion(step.id)}
              >
                <div className="flex items-center space-x-3 flex-1">
                  {getStatusIcon(step)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h5 className="text-sm font-medium text-gray-200">{step.name}</h5>
                      {step.duration && (
                        <span className="text-xs text-gray-400">{step.duration}s</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 truncate">{step.description}</p>
                    
                    {/* 进度条 */}
                    {step.status === 'running' && step.progress !== undefined && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                          <span>处理中...</span>
                          <span>{Math.round(step.progress)}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-1">
                          <div 
                            className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                            style={{ width: `${step.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {step.status === 'completed' && (
                    <button className="text-gray-400 hover:text-gray-200">
                      <FiSettings size={14} />
                    </button>
                  )}
                  {expandedSteps.has(step.id) ? (
                    <FiChevronDown className="text-gray-400" size={16} />
                  ) : (
                    <FiChevronRight className="text-gray-400" size={16} />
                  )}
                </div>
              </div>

              {/* 展开的详细信息 */}
              {expandedSteps.has(step.id) && step.result && (
                <div className="px-3 pb-3 border-t border-gray-700">
                  <div className="mt-2 text-xs">
                    <h6 className="text-gray-300 font-medium mb-2">分析结果</h6>
                    <div className="bg-gray-900 rounded p-2">
                      <pre className="text-gray-400 whitespace-pre-wrap">
                        {JSON.stringify(step.result, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 底部操作按钮 */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex space-x-2">
          <button 
            className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
            disabled={!documentId || isRunning}
          >
            <FiPlay size={16} />
            <span>开始分析</span>
          </button>
          <button className="px-3 py-2 text-gray-400 hover:text-gray-200 border border-gray-600 rounded-lg hover:border-gray-500 transition-colors">
            <FiSettings size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}