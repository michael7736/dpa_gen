"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { projectService } from "@/services/projects"
import { documentService } from "@/services/documents"
import { conversationService } from "@/services/conversations"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { useStore } from "@/store/useStore"
import {
  FileText,
  MessageSquare,
  Settings,
  ArrowLeft,
  Calendar,
  Hash,
  FileSearch,
  Brain,
  ChevronRight,
} from "lucide-react"
import Link from "next/link"

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const setCurrentProject = useStore((state) => state.setCurrentProject)

  // 获取项目详情
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectService.getProject(projectId),
  })

  // 获取项目文档统计
  const { data: documents } = useQuery({
    queryKey: ['documents', projectId],
    queryFn: () => documentService.getDocuments(projectId, 1, 5),
    enabled: !!projectId,
  })

  // 获取项目对话统计
  const { data: conversations } = useQuery({
    queryKey: ['conversations', projectId],
    queryFn: () => conversationService.getConversations(projectId, 1, 5),
    enabled: !!projectId,
  })

  // 设置当前项目
  useEffect(() => {
    if (project) {
      setCurrentProject(project)
    }
  }, [project, setCurrentProject])

  if (projectLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-10">
          <p className="text-muted-foreground">加载中...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-10">
          <p className="text-muted-foreground">项目不存在</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => router.push('/projects')}
          >
            返回项目列表
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6">
      {/* 头部 */}
      <div className="mb-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/projects')}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回项目列表
        </Button>
        
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold mb-2">{project.name}</h1>
            <p className="text-muted-foreground">{project.description}</p>
            <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>创建于 {new Date(project.created_at).toLocaleDateString('zh-CN')}</span>
              </div>
              <div className="flex items-center gap-1">
                <Hash className="h-4 w-4" />
                <span>{project.id.slice(0, 8)}</span>
              </div>
            </div>
          </div>
          <Button asChild>
            <Link href={`/projects/${projectId}/settings`}>
              <Settings className="mr-2 h-4 w-4" />
              项目设置
            </Link>
          </Button>
        </div>
      </div>

      {/* 快捷操作 */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/documents')}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">文档管理</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{documents?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              已上传文档
            </p>
            <ChevronRight className="h-4 w-4 mt-2 text-muted-foreground" />
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/qa')}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">知识问答</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{conversations?.total || 0}</div>
            <p className="text-xs text-muted-foreground">
              对话记录
            </p>
            <ChevronRight className="h-4 w-4 mt-2 text-muted-foreground" />
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/research')}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">深度研究</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">
              研究报告
            </p>
            <ChevronRight className="h-4 w-4 mt-2 text-muted-foreground" />
          </CardContent>
        </Card>
      </div>

      {/* 详细信息标签页 */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="documents">最近文档</TabsTrigger>
          <TabsTrigger value="conversations">最近对话</TabsTrigger>
          <TabsTrigger value="stats">统计信息</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>项目概览</CardTitle>
              <CardDescription>
                项目的基本信息和当前状态
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">项目目标</h4>
                  <p className="text-muted-foreground">
                    {project.objectives || "暂未设置项目目标"}
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">关键词</h4>
                  <div className="flex flex-wrap gap-2">
                    {project.keywords?.map((keyword: string, index: number) => (
                      <Badge key={index} variant="secondary">
                        {keyword}
                      </Badge>
                    )) || <span className="text-muted-foreground">暂无关键词</span>}
                  </div>
                </div>

                <div>
                  <h4 className="font-medium mb-2">项目状态</h4>
                  <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                    {project.status === 'active' ? '活跃' : '已归档'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>最近上传的文档</CardTitle>
              <CardDescription>
                查看项目中最新的文档
              </CardDescription>
            </CardHeader>
            <CardContent>
              {documents && documents.items.length > 0 ? (
                <div className="space-y-4">
                  {documents.items.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{doc.filename}</p>
                          <p className="text-sm text-muted-foreground">
                            {(doc.file_size / 1024 / 1024).toFixed(2)} MB • {doc.page_count} 页
                          </p>
                        </div>
                      </div>
                      <Badge variant={doc.status === 'completed' ? 'default' : 'secondary'}>
                        {doc.status === 'completed' ? '已完成' : '处理中'}
                      </Badge>
                    </div>
                  ))}
                  <Button variant="outline" className="w-full" asChild>
                    <Link href="/documents">
                      查看所有文档
                    </Link>
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileSearch className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground mb-4">暂无文档</p>
                  <Button asChild>
                    <Link href="/documents">
                      上传文档
                    </Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="conversations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>最近的对话</CardTitle>
              <CardDescription>
                查看项目中的对话记录
              </CardDescription>
            </CardHeader>
            <CardContent>
              {conversations && conversations.items.length > 0 ? (
                <div className="space-y-4">
                  {conversations.items.map((conv) => (
                    <div key={conv.id} className="p-4 border rounded-lg">
                      <p className="font-medium mb-1">{conv.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {conv.message_count} 条消息 • {new Date(conv.updated_at).toLocaleDateString('zh-CN')}
                      </p>
                    </div>
                  ))}
                  <Button variant="outline" className="w-full" asChild>
                    <Link href="/qa">
                      查看所有对话
                    </Link>
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground mb-4">暂无对话</p>
                  <Button asChild>
                    <Link href="/qa">
                      开始对话
                    </Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>项目统计</CardTitle>
              <CardDescription>
                项目的详细统计信息
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-sm font-medium">文档统计</p>
                  <p className="text-2xl font-bold">{documents?.total || 0} 个文档</p>
                  <p className="text-xs text-muted-foreground">
                    总计 {project.total_chunks || 0} 个文本块
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">知识图谱</p>
                  <p className="text-2xl font-bold">{project.total_entities || 0} 个实体</p>
                  <p className="text-xs text-muted-foreground">
                    {project.total_relations || 0} 个关系
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">对话统计</p>
                  <p className="text-2xl font-bold">{conversations?.total || 0} 个对话</p>
                  <p className="text-xs text-muted-foreground">
                    总计 {project.total_messages || 0} 条消息
                  </p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm font-medium">存储使用</p>
                  <p className="text-2xl font-bold">{((project.storage_used || 0) / 1024 / 1024).toFixed(1)} MB</p>
                  <p className="text-xs text-muted-foreground">
                    向量数据库使用量
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}