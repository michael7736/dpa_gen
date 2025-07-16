'use client'

import { useState, useRef, useEffect } from 'react'
import { FiSend, FiMic, FiPaperclip, FiZap, FiX, FiMaximize2, FiMinimize2 } from 'react-icons/fi'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
  actions?: Array<{
    label: string
    action: () => void
  }>
}

interface AICopilotProps {
  isOpen: boolean
  onToggle: () => void
  context?: {
    activeDocument?: string | null
    analysisResults?: any
    projectId?: string
  }
}

export default function AICopilot({ isOpen, onToggle, context }: AICopilotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: '我已经快速浏览了《量子计算在医疗中的应用》这篇文档。\n\n📊 文档概况：\n- 类型：学术论文\n- 质量：⭐⭐⭐⭐ 高\n- 篇幅：45页\n\n🎯 核心发现：\n1. 量子算法可将药物筛选效率提升100倍\n2. 在蛋白质折叠预测上有突破性进展 \n3. 商业化仍面临技术和成本挑战\n\n建议深入分析哪个方向？',
      timestamp: new Date(),
      actions: [
        { label: '构建知识图谱', action: () => console.log('构建知识图谱') },
        { label: '生成执行摘要', action: () => console.log('生成执行摘要') },
        { label: '查找相关研究', action: () => console.log('查找相关研究') }
      ]
    }
  ])
  const [input, setInput] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsAnalyzing(true)

    // 模拟AI响应
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: getAIResponse(input),
        timestamp: new Date(),
        actions: getActionsForResponse(input)
      }
      setMessages(prev => [...prev, aiMessage])
      setIsAnalyzing(false)
    }, 2000)
  }

  const getAIResponse = (userInput: string): string => {
    if (userInput.includes('深入分析') || userInput.includes('详细分析')) {
      return '正在执行深度分析...\n\n🔍 证据链分析结果：\n- 发现3个核心论点，证据强度较高\n- Google的90.3%准确率有充分实验支撑\n- 商业化时间预测缺乏具体证据\n\n💭 批判性思维分析：\n- 检测到对大型科技公司研究的过度依赖\n- 建议补充更多独立研究机构的数据\n\n需要我生成详细的分析报告吗？'
    }
    
    if (userInput.includes('报告') || userInput.includes('总结')) {
      return '正在生成研究报告...\n\n📝 已完成：\n- 执行摘要（500字）\n- 技术分析章节\n- 商业应用前景\n- 风险评估\n\n报告已在工作区展示，您可以：\n- 编辑和自定义内容\n- 导出为PDF或Word格式\n- 添加图表和可视化'
    }

    return '我理解您的请求。让我分析一下...\n\n基于当前文档内容，我建议：\n1. 首先明确分析目标\n2. 选择合适的分析方法\n3. 关注关键数据点\n\n您希望我如何协助？'
  }

  const getActionsForResponse = (userInput: string) => {
    if (userInput.includes('深入分析')) {
      return [
        { label: '生成详细报告', action: () => console.log('生成详细报告') },
        { label: '查看证据详情', action: () => console.log('查看证据详情') }
      ]
    }
    return [
      { label: '继续分析', action: () => console.log('继续分析') },
      { label: '切换视角', action: () => console.log('切换视角') }
    ]
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed right-4 bottom-4 w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center shadow-lg transition-all duration-200 z-50"
      >
        🤖
      </button>
    )
  }

  return (
    <div className={`${isExpanded ? 'fixed inset-4 z-50' : 'w-96'} flex flex-col bg-gray-800 border-l border-gray-700 transition-all duration-300`}>
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            🤖
          </div>
          <div>
            <div className="text-sm font-medium text-gray-200">AI助手</div>
            <div className="text-xs text-gray-400">
              {isAnalyzing ? '正在思考...' : '在线'}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-200"
          >
            {isExpanded ? <FiMinimize2 size={16} /> : <FiMaximize2 size={16} />}
          </button>
          <button
            onClick={onToggle}
            className="text-gray-400 hover:text-gray-200"
          >
            <FiX size={16} />
          </button>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] ${message.type === 'user' ? 'bg-blue-600' : 'bg-gray-700'} rounded-lg p-3`}>
              <div className={`text-sm ${message.type === 'user' ? 'text-white' : 'text-gray-200'} whitespace-pre-wrap`}>
                {message.content}
              </div>
              {message.actions && (
                <div className="mt-3 space-y-2">
                  {message.actions.map((action, index) => (
                    <button
                      key={index}
                      onClick={action.action}
                      className="block w-full text-left text-xs bg-gray-600 hover:bg-gray-500 text-gray-200 px-3 py-2 rounded transition-colors"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
              <div className="text-xs text-gray-400 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isAnalyzing && (
          <div className="flex justify-start">
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 快捷操作按钮 */}
      <div className="px-4 py-2 border-t border-gray-700">
        <div className="grid grid-cols-2 gap-2">
          <button className="flex items-center justify-center space-x-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs px-3 py-2 rounded transition-colors">
            <FiZap size={12} />
            <span>深度分析</span>
          </button>
          <button className="flex items-center justify-center space-x-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs px-3 py-2 rounded transition-colors">
            <span>📊</span>
            <span>生成报告</span>
          </button>
        </div>
      </div>

      {/* 输入区域 */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-end space-x-2">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="问点什么..."
              className="w-full bg-gray-700 text-gray-200 text-sm px-3 py-2 pr-16 rounded border border-gray-600 focus:border-blue-500 focus:outline-none resize-none"
              disabled={isAnalyzing}
            />
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
              <button className="text-gray-400 hover:text-gray-200 p-1">
                <FiPaperclip size={14} />
              </button>
              <button className="text-gray-400 hover:text-gray-200 p-1">
                <FiMic size={14} />
              </button>
            </div>
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isAnalyzing}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white p-2 rounded transition-colors"
          >
            <FiSend size={16} />
          </button>
        </div>
        <div className="text-xs text-gray-400 mt-2">
          回车发送，Shift+回车换行
        </div>
      </div>
    </div>
  )
}