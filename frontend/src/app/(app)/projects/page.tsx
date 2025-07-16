"use client"

import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { projectService } from "@/services/projects"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Plus, Search, FolderOpen, FileText, Clock } from "lucide-react"
import Link from "next/link"
import { useStore } from "@/store/useStore"
import { Project } from "@/types"

export default function ProjectsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const setCurrentProject = useStore((state) => state.setCurrentProject)

  const { data, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectService.getProjects(),
  })

  const filteredProjects = data?.items.filter((project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const handleSelectProject = (project: Project) => {
    setCurrentProject(project)
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">我的项目</h1>
        <div className="flex gap-3">
          <Button variant="outline" asChild>
            <Link href="/aag">
              🧠 AAG分析引擎
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/copilot">
              🤖 AI副驾驶 Demo
            </Link>
          </Button>
          <Button asChild>
            <Link href="/projects/new">
              <Plus className="mr-2 h-4 w-4" />
              新建项目
            </Link>
          </Button>
        </div>
      </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="搜索项目..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {isLoading && (
        <div className="text-center py-10">
          <p className="text-muted-foreground">加载中...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-10">
          <p className="text-destructive">
            {(error as any)?.message || "加载失败，请重试"}
          </p>
          <Button 
            variant="outline" 
            className="mt-4"
            onClick={() => window.location.reload()}
          >
            重试
          </Button>
        </div>
      )}

      {!isLoading && !error && filteredProjects.length === 0 && (
        <div className="text-center py-10">
          <FolderOpen className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium mb-2">暂无项目</p>
          <p className="text-muted-foreground mb-4">创建您的第一个研究项目</p>
          <Button asChild>
            <Link href="/projects/new">
              <Plus className="mr-2 h-4 w-4" />
              新建项目
            </Link>
          </Button>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredProjects.map((project) => (
          <Card 
            key={project.id} 
            className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => handleSelectProject(project)}
          >
            <Link href={`/projects/${project.id}`}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="truncate">{project.name}</span>
                  <FolderOpen className="h-5 w-5 text-muted-foreground" />
                </CardTitle>
                <CardDescription className="line-clamp-2">
                  {project.description || "暂无描述"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    <span>{project.document_count || 0} 个文档</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    <span>
                      {new Date(project.updated_at).toLocaleDateString('zh-CN')}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Link>
          </Card>
        ))}
      </div>
    </div>
  )
}