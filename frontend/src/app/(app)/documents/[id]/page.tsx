"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { documentService } from "@/services/documents"
import { documentProcessingService } from "@/services/documentProcessing"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useToast } from "@/hooks/use-toast"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import {
  FileText,
  ArrowLeft,
  Download,
  RefreshCw,
  Calendar,
  FileSize,
  Hash,
  Globe,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Brain,
  FileSearch,
  FileCheck,
  Eye,
  History,
  Database,
  ChevronRight
} from "lucide-react"
import {
  Timeline,
  TimelineContent,
  TimelineDot,
  TimelineHeading,
  TimelineItem,
  TimelineLine
} from "@/components/ui/timeline"

interface ProcessingHistoryItem {
  type: string;
  timestamp: string;
  duration?: number;
  result?: any;
}

export default function DocumentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { toast } = useToast()
  const documentId = params.id as string

  const [summaryData, setSummaryData] = useState<any>(null)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [processingHistory, setProcessingHistory] = useState<ProcessingHistoryItem[]>([])
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)

  // 获取文档详情
  const { data: document, isLoading, error } = useQuery({
    queryKey: ['document', documentId],
    queryFn: () => documentService.getDocument(documentId),
  })

  // 加载摘要
  const loadSummary = async () => {
    if (!document || document.processing_status === 'uploaded') return
    
    setLoadingSummary(true)
    try {
      const summary = await documentProcessingService.getDocumentSummary(documentId)
      setSummaryData(summary)
    } catch (error) {
      console.error('Failed to load summary:', error)
    } finally {
      setLoadingSummary(false)
    }
  }

  // 加载分析结果
  const loadAnalysis = async () => {
    if (!document || !['analyzed', 'completed'].includes(document.processing_status)) return
    
    setLoadingAnalysis(true)
    try {
      const analysis = await documentProcessingService.getDocumentAnalysis(documentId)
      setAnalysisData(analysis)
    } catch (error) {
      console.error('Failed to load analysis:', error)
    } finally {
      setLoadingAnalysis(false)
    }
  }

  // 加载处理历史
  const loadProcessingHistory = async () => {
    setLoadingHistory(true)
    try {
      const history = await documentProcessingService.getProcessingHistory(documentId)
      setProcessingHistory(history)
    } catch (error) {
      console.error('Failed to load processing history:', error)
    } finally {
      setLoadingHistory(false)
    }
  }

  // 初始化加载数据
  useEffect(() => {
    if (document) {
      loadSummary()
      loadAnalysis()
      loadProcessingHistory()
    }
  }, [document])

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded':
        return <FileText className="h-5 w-5 text-gray-500" />
      case 'summarized':
        return <FileCheck className="h-5 w-5 text-blue-500" />
      case 'indexed':
        return <FileSearch className="h-5 w-5 text-green-500" />
      case 'analyzed':
        return <Brain className="h-5 w-5 text-purple-500" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  // 获取处理类型的中文名称
  const getProcessingTypeName = (type: string) => {
    const typeMap: Record<string, string> = {
      'summary': '生成摘要',
      'index': '创建索引',
      'analysis': '深度分析',
      'upload': '文档上传'
    }
    return typeMap[type] || type
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-10">
          <p className="text-lg text-destructive mb-4">加载文档失败</p>
          <Button onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* 面包屑导航 */}
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/projects">项目管理</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink href="/documents">文档管理</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{document.filename}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push('/documents')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{document.filename}</h1>
            <p className="text-muted-foreground">文档详情</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            下载原文
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            刷新
          </Button>
        </div>
      </div>

      {/* 基本信息卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">文件类型</p>
              <p className="font-medium">{document.document_type?.toUpperCase()}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">文件大小</p>
              <p className="font-medium">{formatFileSize(document.file_size)}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">页数</p>
              <p className="font-medium">{document.page_count || '-'} 页</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">字数</p>
              <p className="font-medium">{document.word_count?.toLocaleString() || '-'} 字</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">语言</p>
              <p className="font-medium">{document.language === 'zh' ? '中文' : document.language}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">创建时间</p>
              <p className="font-medium">{new Date(document.created_at).toLocaleDateString('zh-CN')}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">文件哈希</p>
              <p className="font-medium text-xs font-mono">{document.file_hash?.substring(0, 12)}...</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">处理状态</p>
              <div className="flex items-center gap-2">
                {getStatusIcon(document.processing_status)}
                <span className="font-medium">{document.processing_status}</span>
              </div>
            </div>
          </div>

          {/* 处理状态标签 */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm text-muted-foreground mb-2">处理进度</p>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={document.processing_status !== 'uploaded' ? 'default' : 'secondary'}>
                <FileText className="h-3 w-3 mr-1" />
                已上传
              </Badge>
              {['summarized', 'indexed', 'analyzed', 'completed'].includes(document.processing_status) && (
                <Badge variant="default">
                  <FileCheck className="h-3 w-3 mr-1" />
                  已摘要
                </Badge>
              )}
              {['indexed', 'analyzed', 'completed'].includes(document.processing_status) && (
                <Badge variant="default">
                  <FileSearch className="h-3 w-3 mr-1" />
                  已索引
                </Badge>
              )}
              {['analyzed', 'completed'].includes(document.processing_status) && (
                <Badge variant="default">
                  <Brain className="h-3 w-3 mr-1" />
                  已分析
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 详细内容标签页 */}
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="summary">文档摘要</TabsTrigger>
          <TabsTrigger value="analysis">分析结果</TabsTrigger>
          <TabsTrigger value="metadata">元数据</TabsTrigger>
          <TabsTrigger value="history">处理历史</TabsTrigger>
        </TabsList>

        {/* 文档摘要 */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>文档摘要</CardTitle>
              <CardDescription>
                AI 生成的文档内容摘要
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingSummary ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : summaryData || document.summary ? (
                <div className="space-y-4">
                  <div className="prose prose-sm max-w-none">
                    <p className="whitespace-pre-wrap">
                      {summaryData?.summary || document.summary}
                    </p>
                  </div>
                  {summaryData?.generated_at && (
                    <div className="pt-4 border-t">
                      <p className="text-sm text-muted-foreground">
                        生成时间：{new Date(summaryData.generated_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <FileCheck className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>文档尚未生成摘要</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 分析结果 */}
        <TabsContent value="analysis" className="space-y-4">
          {loadingAnalysis ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : analysisData ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>执行摘要</CardTitle>
                  <CardDescription>
                    深度分析的核心发现
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="whitespace-pre-wrap">{analysisData.executive_summary}</p>
                </CardContent>
              </Card>

              <div className="grid md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle>关键洞察</CardTitle>
                    <CardDescription>
                      从文档中提取的重要见解
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysisData.key_insights?.map((insight: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2">
                          <ChevronRight className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{insight}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>行动建议</CardTitle>
                    <CardDescription>
                      基于分析的具体行动方案
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {analysisData.action_items?.map((item: any, idx: number) => (
                        <li key={idx} className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm">{idx + 1}. {item.action}</span>
                            {item.priority && (
                              <Badge variant="outline" className="text-xs">
                                {item.priority}
                              </Badge>
                            )}
                          </div>
                          {item.rationale && (
                            <p className="text-xs text-muted-foreground ml-5">
                              {item.rationale}
                            </p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>分析详情</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">分析类型</span>
                    <span>{analysisData.analysis_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">深度级别</span>
                    <span>{analysisData.depth_level}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">分析时间</span>
                    <span>{new Date(analysisData.created_at).toLocaleString('zh-CN')}</span>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="text-center py-8 text-muted-foreground">
                <Brain className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>文档尚未进行深度分析</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 元数据 */}
        <TabsContent value="metadata" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>文档元数据</CardTitle>
              <CardDescription>
                文档的所有元数据信息
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* 基础元数据 */}
                <div>
                  <h4 className="font-medium mb-2">基础信息</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">文档ID：</span>
                      <span className="font-mono ml-2">{document.id}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">项目ID：</span>
                      <span className="font-mono ml-2">{document.project_id}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">文件路径：</span>
                      <span className="ml-2 break-all">{document.file_path}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">作者：</span>
                      <span className="ml-2">{document.author || '-'}</span>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* 处理配置 */}
                <div>
                  <h4 className="font-medium mb-2">处理配置</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">分块大小：</span>
                      <span className="ml-2">{document.chunk_size}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">分块重叠：</span>
                      <span className="ml-2">{document.chunk_overlap}</span>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* 标签 */}
                {document.tags && document.tags.length > 0 && (
                  <>
                    <div>
                      <h4 className="font-medium mb-2">标签</h4>
                      <div className="flex flex-wrap gap-2">
                        {document.tags.map((tag: string, idx: number) => (
                          <Badge key={idx} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <Separator />
                  </>
                )}

                {/* 扩展元数据 */}
                {document.metadata_info && (
                  <div>
                    <h4 className="font-medium mb-2">扩展信息</h4>
                    <pre className="text-xs bg-muted p-3 rounded-md overflow-auto">
                      {JSON.stringify(document.metadata_info, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 处理历史 */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>处理历史</CardTitle>
              <CardDescription>
                文档的所有处理记录
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingHistory ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : processingHistory.length > 0 ? (
                <div className="relative">
                  {processingHistory.map((item, idx) => (
                    <div key={idx} className="flex gap-4 pb-8 last:pb-0">
                      {/* 时间线 */}
                      <div className="flex flex-col items-center">
                        <div className={`w-4 h-4 rounded-full flex-shrink-0 ${
                          item.type === 'upload' ? 'bg-gray-500' :
                          item.type === 'summary' ? 'bg-blue-500' :
                          item.type === 'index' ? 'bg-green-500' :
                          item.type === 'analysis' ? 'bg-purple-500' :
                          'bg-gray-400'
                        }`} />
                        {idx < processingHistory.length - 1 && (
                          <div className="w-0.5 h-full bg-gray-200 mt-2" />
                        )}
                      </div>

                      {/* 内容 */}
                      <div className="flex-1 pb-4">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-medium">{getProcessingTypeName(item.type)}</h4>
                          <span className="text-sm text-muted-foreground">
                            {new Date(item.timestamp).toLocaleString('zh-CN')}
                          </span>
                        </div>
                        {item.duration && (
                          <p className="text-sm text-muted-foreground">
                            耗时：{item.duration.toFixed(2)} 秒
                          </p>
                        )}
                        {item.result && (
                          <div className="mt-2 p-3 bg-muted rounded-md">
                            <pre className="text-xs overflow-auto">
                              {JSON.stringify(item.result, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <History className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>暂无处理历史记录</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}