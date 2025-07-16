"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useMutation } from "@tanstack/react-query"
import { projectService } from "@/services/projects"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useStore } from "@/store/useStore"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

export default function NewProjectPage() {
  const router = useRouter()
  const setCurrentProject = useStore((state) => state.setCurrentProject)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")

  const createProjectMutation = useMutation({
    mutationFn: projectService.createProject,
    onSuccess: (project) => {
      setCurrentProject(project)
      router.push(`/projects/${project.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    createProjectMutation.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
    })
  }

  return (
    <div className="container mx-auto py-6 max-w-2xl">
      <div className="mb-6">
        <Button variant="ghost" asChild>
          <Link href="/projects">
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回项目列表
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>创建新项目</CardTitle>
          <CardDescription>
            创建一个新的研究项目来组织您的文档和知识
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {createProjectMutation.error && (
              <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md">
                {(createProjectMutation.error as any)?.message || "创建失败，请重试"}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="name">项目名称 *</Label>
              <Input
                id="name"
                placeholder="例如：深度学习研究"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                disabled={createProjectMutation.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">项目描述</Label>
              <Textarea
                id="description"
                placeholder="描述您的研究目标和范围..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                disabled={createProjectMutation.isPending}
              />
            </div>

            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={createProjectMutation.isPending || !name.trim()}
              >
                {createProjectMutation.isPending ? "创建中..." : "创建项目"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
                disabled={createProjectMutation.isPending}
              >
                取消
              </Button>
            </div>
          </CardContent>
        </form>
      </Card>
    </div>
  )
}