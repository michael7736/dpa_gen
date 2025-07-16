"use client"

import { useState, useRef, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { qaService } from "@/services/qa"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useStore } from "@/store/useStore"
import { Message, Source } from "@/types"
import {
  Send,
  MessageSquare,
  FileText,
  ExternalLink,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function ChatPage() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const currentProject = useStore((state) => state.currentProject)
  const currentConversation = useStore((state) => state.currentConversation)
  const setCurrentConversation = useStore((state) => state.setCurrentConversation)
  
  const queryClient = useQueryClient()

  // Get conversations
  const { data: conversations } = useQuery({
    queryKey: ['conversations', currentProject?.id],
    queryFn: () => currentProject ? qaService.getConversations(currentProject.id) : Promise.resolve([]),
    enabled: !!currentProject,
  })

  // Get conversation messages
  const { data: conversationData } = useQuery({
    queryKey: ['conversation', currentConversation?.id],
    queryFn: () => 
      currentConversation 
        ? qaService.getConversation(currentConversation.id)
        : Promise.resolve(null),
    enabled: !!currentConversation,
  })

  // Update messages when conversation data changes
  useEffect(() => {
    if (conversationData?.messages) {
      setMessages(conversationData.messages)
    }
  }, [conversationData])

  // Ask question mutation
  const askMutation = useMutation({
    mutationFn: qaService.askQuestion,
    onMutate: async (data) => {
      // Add user message immediately
      const tempMessage: Message = {
        id: 'temp-' + Date.now(),
        conversation_id: currentConversation?.id || '',
        role: 'user',
        content: data.question,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, tempMessage])
    },
    onSuccess: (response) => {
      // Add assistant message
      const assistantMessage: Message = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        created_at: new Date().toISOString(),
      }
      
      setMessages(prev => {
        // Remove temp message and add real messages
        const filtered = prev.filter(m => !m.id.startsWith('temp-'))
        return [...filtered, assistantMessage]
      })
      
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['conversations', currentProject?.id] })
      queryClient.invalidateQueries({ queryKey: ['conversation', currentConversation?.id] })
    },
    onError: (error) => {
      // Remove temp message on error
      setMessages(prev => prev.filter(m => !m.id.startsWith('temp-')))
      // Add error message
      const errorMessage: Message = {
        id: 'error-' + Date.now(),
        conversation_id: currentConversation?.id || '',
        role: 'assistant',
        content: `抱歉，发生错误：${(error as any)?.message || '请稍后重试'}`,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
    }
  })

  // Create conversation mutation
  const createConversationMutation = useMutation({
    mutationFn: (title: string) => {
      if (!currentProject) throw new Error("No project selected")
      return qaService.createConversation(currentProject.id, title)
    },
    onSuccess: (conversation) => {
      setCurrentConversation(conversation)
      queryClient.invalidateQueries({ queryKey: ['conversations', currentProject?.id] })
    },
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || !currentProject) return

    // Create new conversation if none selected
    if (!currentConversation) {
      createConversationMutation.mutate(question.substring(0, 50))
    }

    askMutation.mutate({
      project_id: currentProject.id,
      question: question.trim(),
      conversation_id: currentConversation?.id,
    })

    setQuestion("")
  }

  if (!currentProject) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-10">
          <p className="text-lg text-muted-foreground">请先选择一个项目</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full">
      {/* Conversations Sidebar */}
      <div className="w-64 border-r bg-muted/10 p-4">
        <div className="mb-4">
          <Button
            onClick={() => {
              setCurrentConversation(null)
              setMessages([])
              createConversationMutation.mutate("新对话")
            }}
            className="w-full"
            size="sm"
          >
            <Plus className="mr-2 h-4 w-4" />
            新对话
          </Button>
        </div>
        
        <div className="space-y-2">
          {conversations?.map((conv) => (
            <Card
              key={conv.id}
              className={cn(
                "cursor-pointer hover:bg-accent",
                currentConversation?.id === conv.id && "bg-accent"
              )}
              onClick={() => setCurrentConversation(conv)}
            >
              <CardContent className="p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <MessageSquare className="h-4 w-4 shrink-0" />
                    <p className="text-sm font-medium truncate">{conv.title}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {conv.message_count}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className="border-b p-4">
          <h1 className="text-2xl font-bold">智能问答</h1>
          <p className="text-muted-foreground">
            基于项目文档的智能对话
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-10">
              <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">开始新对话</p>
              <p className="text-muted-foreground">
                输入您的问题，我将基于项目文档为您解答
              </p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex",
                message.role === 'user' ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[70%] rounded-lg p-4",
                  message.role === 'user'
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                )}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                
                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-muted-foreground/20">
                    <p className="text-sm font-medium mb-2">参考来源：</p>
                    <div className="space-y-2">
                      {message.sources.map((source, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2 text-sm"
                        >
                          <FileText className="h-4 w-4 mt-0.5 shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">
                              {source.document_name}
                            </p>
                            {source.page_number && (
                              <p className="text-xs opacity-70">
                                第 {source.page_number} 页
                              </p>
                            )}
                            <p className="text-xs opacity-70 line-clamp-2">
                              {source.content_preview}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="shrink-0"
                          >
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {askMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg p-4">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="border-t p-4">
          <div className="flex gap-2">
            <Input
              placeholder="输入您的问题..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={askMutation.isPending}
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={!question.trim() || askMutation.isPending}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}