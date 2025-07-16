"use client"

import { useState, useEffect, useRef } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { qaService } from "@/services/qa"
import { conversationService } from "@/services/conversations"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
// import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
  ChevronRight,
} from "lucide-react"

export default function QAPage() {
  const [input, setInput] = useState("")
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const currentProject = useStore((state) => state.currentProject)

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

  // 创建新对话
  const createConversationMutation = useMutation({
    mutationFn: (title: string) => {
      if (!currentProject) throw new Error("请先选择项目")
      return conversationService.createConversation({
        project_id: currentProject.id,
        title
      })
    },
    onSuccess: (data) => {
      setCurrentConversationId(data.id)
      setMessages([])
      refetchConversations()
    }
  })

  // 发送消息
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!currentProject) throw new Error("请先选择项目")
      
      // 如果没有当前对话，先创建一个
      let conversationId = currentConversationId
      if (!conversationId) {
        const newConversation = await conversationService.createConversation({
          project_id: currentProject.id,
          title: content.slice(0, 50) + "..."
        })
        conversationId = newConversation.id
        setCurrentConversationId(conversationId)
        refetchConversations()
      }
      
      // 添加用户消息到界面
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        conversation_id: conversationId,
        role: 'user',
        content,
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, userMessage])
      
      // 发送请求 - 使用后端期望的格式
      return qaService.askQuestion({
        project_id: currentProject.id,
        question: content,
        include_sources: true
      })
    },
    onSuccess: (data) => {
      // 添加AI回复到界面
      const aiMessage: Message = {
        id: `ai-${Date.now()}`,
        conversation_id: currentConversationId || '',
        role: 'assistant',
        content: data.answer,
        sources: data.context_used?.map(s => ({
          chunk_id: s.doc_id || '',
          document_name: s.metadata?.filename || '未知文档',
          content_preview: s.content || '',
          page_number: s.metadata?.page_number,
          similarity_score: s.score || 0
        })) || data.sources?.map(s => ({
          chunk_id: s.chunk_id || '',
          document_name: s.document_name || s.metadata?.filename || '未知文档',
          content_preview: s.content || '',
          page_number: s.metadata?.page_number,
          similarity_score: s.similarity_score || s.score || 0
        })),
        created_at: new Date().toISOString()
      }
      setMessages(prev => [...prev, aiMessage])
      // 不需要refetchMessages因为没有真实的对话存储
    },
    onError: (error) => {
      console.error("发送消息失败:", error)
      // 可以添加错误提示
    }
  })

  // 删除对话
  const deleteConversationMutation = useMutation({
    mutationFn: conversationService.deleteConversation,
    onSuccess: () => {
      if (currentConversationId === deleteConversationMutation.variables) {
        setCurrentConversationId(null)
        setMessages([])
      }
      refetchConversations()
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
  }

  // 创建新对话
  const createNewConversation = () => {
    setCurrentConversationId(null)
    setMessages([])
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
              <h2 className="text-lg font-semibold">对话历史</h2>
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
                      <p className="text-xs text-muted-foreground">
                        {conversation.message_count} 条消息
                      </p>
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
            <h1 className="text-2xl font-bold">知识问答</h1>
            <p className="text-muted-foreground">
              基于项目文档的智能问答
            </p>
          </div>

          {/* 消息区域 */}
          <div className="flex-1 p-4 overflow-y-auto" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <Bot className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">开始新的对话</p>
                  <p className="text-muted-foreground">
                    输入您的问题，我会基于项目文档为您解答
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
                          <p className="text-xs font-medium mb-2">参考来源：</p>
                          <div className="space-y-2">
                            {message.sources.map((source, index) => (
                              <div
                                key={source.chunk_id}
                                className="text-xs p-2 rounded bg-background/50"
                              >
                                <div className="flex items-center gap-2">
                                  <FileText className="h-3 w-3" />
                                  <span className="font-medium">
                                    {source.document_name}
                                  </span>
                                  {source.page_number && (
                                    <span className="text-muted-foreground">
                                      第{source.page_number}页
                                    </span>
                                  )}
                                </div>
                                <p className="mt-1 text-muted-foreground line-clamp-2">
                                  {source.content_preview}
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
                        <span className="text-sm">正在思考...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

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
            <p className="text-xs text-muted-foreground mt-2">
              按 Enter 发送，Shift + Enter 换行
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}