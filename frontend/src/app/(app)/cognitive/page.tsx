"use client"

import { useState, useRef, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
// import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useStore } from "@/store/useStore"
import { cognitiveService } from "@/services/cognitive"
import {
  Send,
  Brain,
  Zap,
  Database,
  Network,
  BarChart3,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Info,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface CognitiveMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  strategy?: string
  confidence?: number
  sources?: Array<{
    id: string
    content: string
    score: number
    source: string
  }>
  metacognitive?: {
    current_strategy: string
    confidence_level: string
    attention_focus: Record<string, number>
  }
  processing_time?: number
  created_at: string
}

export default function CognitivePage() {
  const [message, setMessage] = useState("")
  const [messages, setMessages] = useState<CognitiveMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const currentProject = useStore((state) => state.currentProject)
  const queryClient = useQueryClient()

  // 获取认知系统健康状态
  const { data: healthStatus } = useQuery({
    queryKey: ['cognitive-health'],
    queryFn: cognitiveService.getHealth,
    refetchInterval: 30000, // 每30秒刷新一次
  })

  // 认知对话mutation
  const chatMutation = useMutation({
    mutationFn: cognitiveService.chat,
    onMutate: async (data) => {
      // 立即添加用户消息
      const tempMessage: CognitiveMessage = {
        id: 'temp-' + Date.now(),
        role: 'user',
        content: data.message,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, tempMessage])
    },
    onSuccess: (response) => {
      // 更新对话ID
      if (!conversationId) {
        setConversationId(response.conversation_id)
      }
      
      // 添加助手消息
      const assistantMessage: CognitiveMessage = {
        id: response.conversation_id + '-' + Date.now(),
        role: 'assistant',
        content: response.response,
        strategy: response.strategy_used,
        confidence: response.confidence_score,
        sources: response.sources,
        metacognitive: response.metacognitive_state,
        processing_time: response.processing_time,
        created_at: new Date().toISOString(),
      }
      
      setMessages(prev => {
        // 移除临时消息并添加真实消息
        const filtered = prev.filter(m => !m.id.startsWith('temp-'))
        return [...filtered, assistantMessage]
      })
    },
    onError: (error) => {
      // 移除临时消息
      setMessages(prev => prev.filter(m => !m.id.startsWith('temp-')))
      // 添加错误消息
      const errorMessage: CognitiveMessage = {
        id: 'error-' + Date.now(),
        role: 'assistant',
        content: `抱歉，发生错误：${(error as any)?.message || '请稍后重试'}`,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
    }
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    chatMutation.mutate({
      message: message.trim(),
      project_id: currentProject?.id || 'test_project',
      conversation_id: conversationId,
      use_memory: true,
      max_results: 10,
    })

    setMessage("")
  }

  const getStrategyIcon = (strategy?: string) => {
    switch (strategy) {
      case 'exploration':
        return <Zap className="h-4 w-4" />
      case 'exploitation':
        return <Database className="h-4 w-4" />
      case 'verification':
        return <CheckCircle2 className="h-4 w-4" />
      case 'reflection':
        return <Brain className="h-4 w-4" />
      case 'adaptation':
        return <Network className="h-4 w-4" />
      default:
        return <Info className="h-4 w-4" />
    }
  }

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return "default"
    if (confidence >= 0.8) return "success"
    if (confidence >= 0.6) return "warning"
    return "destructive"
  }

  // 暂时注释掉项目检查，允许直接使用
  // if (!currentProject) {
  //   return (
  //     <div className="container mx-auto py-6">
  //       <div className="text-center py-10">
  //         <Brain className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
  //         <p className="text-lg text-muted-foreground">请先选择一个项目</p>
  //       </div>
  //     </div>
  //   )
  // }

  return (
    <div className="flex h-full">
      {/* 左侧：系统状态面板 */}
      <div className="w-80 border-r bg-gradient-to-b from-background to-muted/30 p-4 space-y-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2 bg-gradient-to-r from-primary/10 to-transparent p-3 rounded-lg">
              <Brain className="h-5 w-5" />
              认知系统状态
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {healthStatus ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm">系统状态</span>
                  <Badge variant={healthStatus.status === 'healthy' ? 'success' : 'destructive'}>
                    {healthStatus.status === 'healthy' ? '正常' : '异常'}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <p className="text-sm font-medium">组件状态</p>
                  {Object.entries(healthStatus.components || {}).map(([name, status]) => (
                    <div key={name} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{name}</span>
                      <Badge 
                        variant={status === 'online' ? 'success' : 'secondary'}
                        className="text-xs"
                      >
                        {status === 'online' ? '在线' : '离线'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-4">
                <Loader2 className="h-5 w-5 animate-spin mx-auto" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* 认知策略说明 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">认知策略</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-start gap-2">
              <Zap className="h-4 w-4 mt-0.5 text-yellow-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">探索 (Exploration)</p>
                <p className="text-xs text-muted-foreground">发现新知识和模式</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Database className="h-4 w-4 mt-0.5 text-blue-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">利用 (Exploitation)</p>
                <p className="text-xs text-muted-foreground">使用已有知识回答</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">验证 (Verification)</p>
                <p className="text-xs text-muted-foreground">确认和验证信息</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Brain className="h-4 w-4 mt-0.5 text-purple-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">反思 (Reflection)</p>
                <p className="text-xs text-muted-foreground">深度思考和总结</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Network className="h-4 w-4 mt-0.5 text-orange-500" />
              <div className="flex-1">
                <p className="text-sm font-medium">适应 (Adaptation)</p>
                <p className="text-xs text-muted-foreground">调整策略和方法</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 右侧：对话区域 */}
      <div className="flex-1 flex flex-col">
        <div className="border-b p-4">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6" />
            认知对话
          </h1>
          <p className="text-muted-foreground">
            基于V3认知系统的深度智能对话
          </p>
        </div>

        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-10">
              <Brain className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">开始认知对话</p>
              <p className="text-muted-foreground">
                我将使用四层记忆模型和元认知引擎为您提供深度分析
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex",
                msg.role === 'user' ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[70%]",
                  msg.role === 'user' ? "bg-primary text-primary-foreground rounded-lg p-4" : ""
                )}
              >
                {msg.role === 'assistant' && (
                  <Card>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStrategyIcon(msg.strategy)}
                          <span className="text-sm font-medium">
                            {msg.strategy ? `${msg.strategy} 策略` : '认知系统'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {msg.confidence !== undefined && (
                            <Badge variant={getConfidenceColor(msg.confidence) as any}>
                              置信度: {(msg.confidence * 100).toFixed(0)}%
                            </Badge>
                          )}
                          {msg.processing_time && (
                            <Badge variant="outline">
                              {msg.processing_time.toFixed(1)}s
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      
                      {/* 信息来源 */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="pt-4 border-t">
                          <p className="text-sm font-medium mb-2">信息来源：</p>
                          <div className="space-y-2">
                            {msg.sources.slice(0, 3).map((source, idx) => (
                              <div key={idx} className="bg-muted rounded p-2">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-xs font-medium">{source.source}</span>
                                  <Badge variant="secondary" className="text-xs">
                                    相关度: {(source.score * 100).toFixed(0)}%
                                  </Badge>
                                </div>
                                <p className="text-xs text-muted-foreground line-clamp-2">
                                  {source.content}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* 元认知状态 */}
                      {msg.metacognitive && (
                        <div className="pt-4 border-t">
                          <p className="text-sm font-medium mb-2">元认知状态：</p>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <span className="text-muted-foreground">当前策略：</span>
                              <span className="ml-1">{msg.metacognitive.current_strategy}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">置信水平：</span>
                              <span className="ml-1">{msg.metacognitive.confidence_level}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
                
                {msg.role === 'user' && (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          
          {chatMutation.isPending && (
            <div className="flex justify-start">
              <Card className="max-w-[70%]">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span className="text-sm text-muted-foreground">
                      认知系统正在思考...
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <form onSubmit={handleSubmit} className="border-t p-4">
          <div className="flex gap-2">
            <Input
              placeholder="输入您的问题，我将进行深度认知分析..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={chatMutation.isPending}
              className="flex-1"
            />
            <Button
              type="submit"
              disabled={!message.trim() || chatMutation.isPending}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}