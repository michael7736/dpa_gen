"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useStore } from "@/store/useStore"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, FolderOpen, MessageSquare, Network, ArrowRight } from "lucide-react"
import Link from "next/link"

export default function Home() {
  const router = useRouter()
  const user = useStore((state) => state.user)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('auth_token')
    if (!token) {
      router.push('/login')
    }
  }, [router])

  const features = [
    {
      icon: FolderOpen,
      title: "项目管理",
      description: "创建和管理研究项目，组织您的文档和知识",
      href: "/projects",
    },
    {
      icon: FileText,
      title: "文档处理",
      description: "上传PDF、Word等文档，自动解析和索引",
      href: "/documents",
    },
    {
      icon: MessageSquare,
      title: "智能问答",
      description: "基于文档内容的智能对话，精准溯源每个答案",
      href: "/chat",
    },
    {
      icon: Network,
      title: "知识图谱",
      description: "可视化文档间的知识关联，发现隐藏的洞察",
      href: "/knowledge-graph",
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto py-10">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold tracking-tight mb-4">
            欢迎使用 DPA 智能知识引擎
          </h1>
          <p className="text-xl text-muted-foreground">
            您的AI研究伙伴，将百篇论文提炼为一篇洞察报告
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-10">
          {features.map((feature) => (
            <Card key={feature.title} className="hover:shadow-lg transition-shadow cursor-pointer">
              <Link href={feature.href}>
                <CardHeader>
                  <feature.icon className="w-10 h-10 mb-2 text-primary" />
                  <CardTitle>{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{feature.description}</CardDescription>
                </CardContent>
              </Link>
            </Card>
          ))}
        </div>

        <div className="text-center">
          <Button size="lg" asChild>
            <Link href="/projects/new">
              开始新项目
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {/* Quick Stats */}
        <div className="mt-16 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">项目总数</CardTitle>
              <FolderOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">
                已创建的研究项目
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">文档总数</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">
                已处理的文档
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">对话总数</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">
                智能问答对话
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}