"use client"

import { useState, useEffect, useRef } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { qaWithHistoryService } from "@/services/qaWithHistory"
import { conversationService } from "@/services/conversations"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useStore } from "@/store/useStore"
import { Message, Conversation } from "@/types"
import {
  Send,
  MessageSquare,
  Plus,
  Bot,
  User,
  FileText,
  Loader2,
  Trash2,
  History,
  Sparkles,
  RefreshCw,
  ClipboardList,
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"

export default function QAHistoryPage() {
  const [input, setInput] = useState("")
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([])
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const currentProject = useStore((state) => state.currentProject)
  const { toast } = useToast()

  // 获取对话列表
  const { data: conversationsData, refetch: refetchConversations } = useQuery({
    queryKey: ['conversations', currentProject?.id],
    queryFn: () => conversationService.getConversations(currentProject?.id),
    enabled: !!currentProject,
  })

  // 获取当前对话的消息
  const { refetch: refetchMessages } = useQuery({
    queryKey: ['messages', currentConversationId],
    queryFn: async () => {
      if (!currentConversationId) return { items: [] }
      return conversationService.getMessages(currentConversationId)
    },
    enabled: !!currentConversationId,
    onSuccess: (data) => {
      setMessages(data.items || [])
    }
  })

  // 发送带历史的消息
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!currentProject) throw new Error("请先选择项目")
      
      // 添加用户消息到界面（临时）
      const tempUserMessage: Message = {
        id: `temp-${Date.now()}`,
        conversation_id: currentConversationId || '',
        role: 'user',
        content,
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, tempUserMessage])
      
      // 使用带历史的问答API
      return qaWithHistoryService.askWithHistory({
        question: content,
        project_id: currentProject.id,
        conversation_id: currentConversationId,
        use_conversation_context: true,
        max_history_messages: 10,
        include_sources: true
      })
    },
    onSuccess: (data) => {
      // 更新对话ID（如果是新对话）
      if (!currentConversationId && data.conversation_id) {
        setCurrentConversationId(data.conversation_id)
        refetchConversations()
      }
      
      // 移除临时消息，添加真实消息
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.id.startsWith('temp-'))
        return [
          ...filtered,
          {
            id: data.message_id,
            conversation_id: data.conversation_id,
            role: 'user',
            content: sendMessageMutation.variables!,
            created_at: new Date().toISOString()
          },
          {
            id: `ai-${Date.now()}`,
            conversation_id: data.conversation_id,
            role: 'assistant',
            content: data.answer,
            sources: data.sources,
            created_at: new Date().toISOString()
          }
        ]
      })
      
      // 刷新消息列表
      if (currentConversationId) {
        refetchMessages()
      }
      
      // 显示置信度
      if (data.confidence < 0.5) {
        toast({
          title: "回答置信度较低",
          description: "该回答的置信度较低，建议提供更多上下文或重新表述问题",
          variant: "default"
        })
      }
    },
    onError: (error) => {
      // 移除临时消息
      setMessages(prev => prev.filter(msg => !msg.id.startsWith('temp-')))
      
      toast({
        title: "发送失败",
        description: error instanceof Error ? error.message : "发送消息时发生错误",
        variant: "destructive"
      })
    }
  })

  // 继续对话
  const continueConversationMutation = useMutation({
    mutationFn: (conversationId: string) => 
      qaWithHistoryService.continueConversation(conversationId),
    onSuccess: (data) => {
      setSuggestedQuestions(data.suggested_questions || [])
      toast({
        title: "对话已加载",
        description: `已加载 ${data.recent_messages.length} 条历史消息`,
      })
    }
  })

  // 总结对话
  const summarizeConversationMutation = useMutation({
    mutationFn: () => {
      if (!currentConversationId) throw new Error("请先选择对话")
      return qaWithHistoryService.summarizeConversation(currentConversationId)
    },
    onSuccess: (data) => {
      toast({
        title: "对话总结",
        description: data.summary,
      })
      
      if (data.updated_title) {
        refetchConversations()
      }
    }
  })

  // 删除对话
  const deleteConversationMutation = useMutation({
    mutationFn: conversationService.deleteConversation,
    onSuccess: () => {
      if (currentConversationId === deleteConversationMutation.variables) {
        setCurrentConversationId(null)
        setMessages([])
        setSuggestedQuestions([])
      }
      refetchConversations()
      toast({
        title: "对话已删除",
        description: "对话历史已成功删除",
      })
    }
  })

  // 处理发送消息
  const handleSend = () => {
    if (input.trim() && !sendMessageMutation.isPending) {
      sendMessageMutation.mutate(input.trim())
      setInput("")
    }
  }

  // 选择对话
  const selectConversation = (conversationId: string) => {
    setCurrentConversationId(conversationId)
    setMessages([])
    setSuggestedQuestions([])
    continueConversationMutation.mutate(conversationId)
  }

  // 创建新对话
  const createNewConversation = () => {
    setCurrentConversationId(null)
    setMessages([])
    setSuggestedQuestions([])
  }

  // 使用建议问题
  const useSuggestedQuestion = (question: string) => {
    setInput(question)
  }

  // 自动滚动到底部
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  if (!currentProject) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-10">
          <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg text-muted-foreground">请先选择一个项目</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 h-[calc(100vh-8rem)]">
      <div className="flex gap-6 h-full">
        {/* 左侧：对话列表 */}
        <Card className="w-80 flex flex-col">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <History className="h-5 w-5" />
                <h2 className="text-lg font-semibold">对话历史</h2>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={createNewConversation}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 space-y-2">
              {conversationsData?.items.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentConversationId === conversation.id
                      ? 'bg-primary/10 border border-primary/20'
                      : 'hover:bg-muted'
                  }`}
                  onClick={() => selectConversation(conversation.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{conversation.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-xs">
                          {conversation.message_count} 条消息
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(conversation.updated_at).toLocaleDateString('zh-CN')}
                        </span>
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6 opacity-0 hover:opacity-100"
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteConversationMutation.mutate(conversation.id)
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
              
              {(!conversationsData || conversationsData.items.length === 0) && (
                <div className="text-center py-8">
                  <History className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">
                    暂无对话记录
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    发送第一条消息开始对话
                  </p>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* 右侧：对话区域 */}
        <Card className="flex-1 flex flex-col">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  智能问答
                  <Badge variant="secondary">
                    <Sparkles className="h-3 w-3 mr-1" />
                    增强版
                  </Badge>
                </h1>
                <p className="text-muted-foreground">
                  基于对话历史的上下文感知问答
                </p>
              </div>
              
              {currentConversationId && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => summarizeConversationMutation.mutate()}
                  disabled={summarizeConversationMutation.isPending}
                >
                  {summarizeConversationMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <ClipboardList className="h-4 w-4 mr-2" />
                  )}
                  总结对话
                </Button>
              )}
            </div>
          </div>

          {/* 消息区域 */}
          <div className="flex-1 p-4 overflow-y-auto" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">开始新的对话</p>
                  <p className="text-muted-foreground">
                    我会记住我们的对话内容，为您提供更准确的回答
                  </p>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-4 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[70%] ${
                      message.role === 'user' ? 'order-2' : 'order-1'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {message.role === 'user' ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                      <span className="text-sm font-medium">
                        {message.role === 'user' ? '您' : 'AI助手'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(message.created_at).toLocaleTimeString('zh-CN')}
                      </span>
                    </div>
                    
                    <div
                      className={`rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      
                      {/* 显示来源 */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-border/50">
                          <p className="text-xs font-medium mb-2 flex items-center gap-1">
                            <FileText className="h-3 w-3" />
                            参考来源：
                          </p>
                          <div className="space-y-2">
                            {message.sources.map((source, index) => (
                              <div
                                key={index}
                                className="text-xs p-2 rounded bg-background/50"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">
                                    {source.document_name || '未知文档'}
                                  </span>
                                  {source.page_number && (
                                    <span className="text-muted-foreground">
                                      第{source.page_number}页
                                    </span>
                                  )}
                                  <Badge variant="outline" className="text-xs">
                                    相似度: {(source.similarity_score || source.score || 0).toFixed(2)}
                                  </Badge>
                                </div>
                                <p className="mt-1 text-muted-foreground line-clamp-2">
                                  {source.content_preview || source.content || ''}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {sendMessageMutation.isPending && (
                <div className="flex gap-4">
                  <div className="max-w-[70%]">
                    <div className="flex items-center gap-2 mb-2">
                      <Bot className="h-4 w-4" />
                      <span className="text-sm font-medium">AI助手</span>
                    </div>
                    <div className="rounded-lg p-4 bg-muted">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">正在分析对话历史并思考...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 建议问题 */}
          {suggestedQuestions.length > 0 && (
            <div className="px-4 pb-2">
              <p className="text-xs text-muted-foreground mb-2">建议的后续问题：</p>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((question, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => useSuggestedQuestion(question)}
                    className="text-xs"
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* 输入区域 */}
          <div className="p-4 border-t">
            <div className="flex gap-2">
              <Input
                placeholder="输入您的问题..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                disabled={sendMessageMutation.isPending}
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || sendMessageMutation.isPending}
              >
                {sendMessageMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-muted-foreground">
                按 Enter 发送，Shift + Enter 换行
              </p>
              {currentConversationId && (
                <Badge variant="outline" className="text-xs">
                  <History className="h-3 w-3 mr-1" />
                  使用对话历史
                </Badge>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}