'use client'

import { useState, useEffect, useRef } from 'react'
import { 
  MessageCircle, 
  Send, 
  Bot, 
  User, 
  Plus, 
  Settings, 
  X,
  Trash2,
  Edit3,
  FileText,
  Loader2,
  Paperclip,
  Mic,
  MicOff
} from 'lucide-react'

export interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  attachments?: string[]
  isTyping?: boolean
}

export interface Conversation {
  id: string
  title: string
  isActive: boolean
  lastMessage?: string
  createdAt: Date
  messages: Message[]
  context?: string // 当前文档上下文
}

interface AIChatProps {
  conversations: Conversation[]
  activeConversation: string | null
  onConversationChange: (conversationId: string) => void
  onConversationCreate: () => void
  onConversationDelete: (conversationId: string) => void
  onMessageSend: (conversationId: string, message: string, attachments?: string[]) => void
  currentDocument?: string // 当前查看的文档
  isVisible: boolean
  onToggleVisibility: () => void
  position: 'right' | 'bottom'
  onPositionChange: (position: 'right' | 'bottom') => void
}

export default function AIChat({
  conversations,
  activeConversation,
  onConversationChange,
  onConversationCreate,
  onConversationDelete,
  onMessageSend,
  currentDocument,
  isVisible,
  onToggleVisibility,
  position,
  onPositionChange
}: AIChatProps) {
  const [inputMessage, setInputMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [attachments, setAttachments] = useState<string[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [editingConversation, setEditingConversation] = useState<string | null>(null)
  const [newConversationTitle, setNewConversationTitle] = useState('')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 获取当前活动的对话
  const currentConversation = conversations.find(c => c.id === activeConversation)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [currentConversation?.messages])

  // 发送消息
  const handleSendMessage = () => {
    if (!inputMessage.trim() || !activeConversation) return

    onMessageSend(activeConversation, inputMessage, attachments)
    setInputMessage('')
    setAttachments([])
    
    // 模拟AI正在输入
    setIsTyping(true)
    setTimeout(() => setIsTyping(false), 2000)
  }

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 编辑对话标题
  const handleEditConversationTitle = (conversationId: string, newTitle: string) => {
    // 这里应该调用更新对话标题的API
    setEditingConversation(null)
    setNewConversationTitle('')
  }

  // 语音录制功能
  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // 这里实现语音转文字功能
  }

  // 渲染消息
  const renderMessage = (message: Message) => {
    const isUser = message.type === 'user'
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
          <div className="flex items-center gap-2 mb-1">
            {isUser ? (
              <User className="w-4 h-4 text-blue-600" />
            ) : (
              <Bot className="w-4 h-4 text-green-600" />
            )}
            <span className="text-xs text-gray-500">
              {isUser ? '您' : 'AI助手'}
            </span>
            <span className="text-xs text-gray-400">
              {message.timestamp.toLocaleTimeString()}
            </span>
          </div>
          
          <div
            className={`rounded-lg p-3 ${
              isUser
                ? 'bg-blue-500 text-white ml-8'
                : 'bg-gray-100 text-gray-800 mr-8'
            }`}
          >
            <div className="whitespace-pre-wrap">{message.content}</div>
            
            {/* 附件 */}
            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-2 space-y-1">
                {message.attachments.map((attachment, index) => (
                  <div key={index} className="flex items-center gap-2 text-sm">
                    <FileText className="w-4 h-4" />
                    <span>{attachment}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // 渲染对话列表
  const renderConversationList = () => (
    <div className="border-b border-gray-200 max-h-48 overflow-y-auto bg-gray-50">
      {conversations.map(conversation => (
        <div
          key={conversation.id}
          className={`p-3 cursor-pointer hover:bg-white border-b border-gray-100 group transition-all duration-200 ${
            activeConversation === conversation.id ? 'bg-blue-50 border-blue-200 shadow-sm' : ''
          }`}
          onClick={() => onConversationChange(conversation.id)}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              {editingConversation === conversation.id ? (
                <input
                  type="text"
                  value={newConversationTitle}
                  onChange={(e) => setNewConversationTitle(e.target.value)}
                  onBlur={() => handleEditConversationTitle(conversation.id, newConversationTitle)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleEditConversationTitle(conversation.id, newConversationTitle)
                    }
                  }}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              ) : (
                <h4 className="font-medium text-sm truncate text-gray-800">{conversation.title}</h4>
              )}
              
              {conversation.lastMessage && (
                <p className="text-xs text-gray-500 truncate mt-1">
                  {conversation.lastMessage}
                </p>
              )}
            </div>
            
            <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-all duration-200">
              <button
                className="p-1.5 hover:bg-gray-200 rounded-lg transition-all duration-200"
                onClick={(e) => {
                  e.stopPropagation()
                  setEditingConversation(conversation.id)
                  setNewConversationTitle(conversation.title)
                }}
                title="编辑标题"
              >
                <Edit3 className="w-3 h-3 text-gray-600" />
              </button>
              <button
                className="p-1.5 hover:bg-red-100 rounded-lg text-red-500 transition-all duration-200"
                onClick={(e) => {
                  e.stopPropagation()
                  onConversationDelete(conversation.id)
                }}
                title="删除对话"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-gray-400">
              {conversation.createdAt.toLocaleDateString()}
            </span>
            <span className="text-xs text-blue-500 bg-blue-100 px-2 py-0.5 rounded-full">
              {conversation.messages.length} 条消息
            </span>
          </div>
        </div>
      ))}
    </div>
  )

  if (!isVisible) {
    return (
      <button
        className="fixed right-4 bottom-4 p-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 z-50"
        onClick={onToggleVisibility}
      >
        <MessageCircle className="w-6 h-6" />
      </button>
    )
  }

  const containerClass = position === 'right' 
    ? 'w-96 h-full border-l border-gray-200 shadow-lg' 
    : 'w-full h-64 border-t border-gray-200'

  return (
    <div className={`bg-white flex flex-col ${containerClass}`}>
      {/* 头部 */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-blue-100">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800 flex items-center">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center mr-3">
              <Bot className="w-5 h-5 text-white" />
            </div>
            AI助手
          </h2>
          <div className="flex items-center space-x-1">
            <button
              className="p-2 hover:bg-white/50 rounded-lg transition-all duration-200"
              onClick={() => onPositionChange(position === 'right' ? 'bottom' : 'right')}
              title="切换位置"
            >
              <Settings className="w-4 h-4 text-gray-600" />
            </button>
            <button
              className="p-2 hover:bg-white/50 rounded-lg transition-all duration-200"
              onClick={onToggleVisibility}
              title="关闭"
            >
              <X className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>
        
        <button
          className="w-full mt-3 px-4 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 flex items-center justify-center transition-all duration-200 shadow-sm"
          onClick={onConversationCreate}
        >
          <Plus className="w-4 h-4 mr-2" />
          新建对话
        </button>
      </div>

      {/* 对话列表 */}
      {conversations.length > 0 && renderConversationList()}

      {/* 消息区域 */}
      <div className="flex-1 flex flex-col">
        {currentConversation ? (
          <>
            {/* 上下文提示 */}
            {currentDocument && (
              <div className="p-2 bg-blue-50 border-b border-blue-200 text-xs">
                <span className="text-blue-700">当前文档: {currentDocument}</span>
              </div>
            )}
            
            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {currentConversation.messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <Bot className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">开始新的对话</p>
                  <p className="text-xs text-gray-400 mt-1">
                    我可以帮助您分析文档、回答问题
                  </p>
                </div>
              ) : (
                currentConversation.messages.map(renderMessage)
              )}
              
              {/* AI正在输入指示器 */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3 mr-8">
                    <div className="flex items-center space-x-1">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm text-gray-500">AI正在思考...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            
            {/* 输入区域 */}
            <div className="p-3 border-t border-gray-200">
              {/* 附件预览 */}
              {attachments.length > 0 && (
                <div className="mb-2 flex flex-wrap gap-2">
                  {attachments.map((attachment, index) => (
                    <div key={index} className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded text-xs">
                      <FileText className="w-3 h-3" />
                      <span>{attachment}</span>
                      <button
                        onClick={() => setAttachments(prev => prev.filter((_, i) => i !== index))}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              {/* 输入框 */}
              <div className="flex items-end space-x-2">
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="输入您的问题..."
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 max-h-20"
                    rows={1}
                    disabled={isTyping}
                  />
                  
                  {/* 工具按钮 */}
                  <div className="absolute right-2 bottom-2 flex items-center space-x-1">
                    <button
                      className="p-1 hover:bg-gray-100 rounded"
                      onClick={() => {
                        // 添加当前文档为附件
                        if (currentDocument) {
                          setAttachments(prev => [...prev, currentDocument])
                        }
                      }}
                      title="添加当前文档"
                    >
                      <Paperclip className="w-3 h-3 text-gray-500" />
                    </button>
                    
                    <button
                      className={`p-1 hover:bg-gray-100 rounded ${isRecording ? 'text-red-500' : 'text-gray-500'}`}
                      onClick={toggleRecording}
                      title={isRecording ? '停止录音' : '开始录音'}
                    >
                      {isRecording ? <MicOff className="w-3 h-3" /> : <Mic className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
                
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isTyping}
                  className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              
              <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                <span>Enter 发送, Shift+Enter 换行</span>
                <span>{inputMessage.length}/1000</span>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-sm">选择或创建一个对话</p>
              <p className="text-xs text-gray-400 mt-1">
                开始与AI助手交流
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}