"use client"

import { useState, useCallback } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { documentService } from "@/services/documents"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { useStore } from "@/store/useStore"
import { Document } from "@/types"
import DocumentListEnhanced from "@/components/documents/DocumentListEnhanced"
import { useToast } from "@/hooks/use-toast"
import { documentProcessingService } from "@/services/documentProcessing"
import {
  FileText,
  Upload,
  Search,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Trash2,
  Eye,
} from "lucide-react"

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  
  const currentProject = useStore((state) => state.currentProject)
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents', currentProject?.id],
    queryFn: () => documentService.getDocuments(currentProject?.id),
    enabled: !!currentProject,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      if (!currentProject) throw new Error("No project selected")
      return documentService.uploadDocument(file, currentProject.id, setUploadProgress)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', currentProject?.id] })
      setSelectedFile(null)
      setUploadProgress(0)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: documentService.deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', currentProject?.id] })
    },
  })

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = () => {
    if (selectedFile && currentProject) {
      uploadMutation.mutate(selectedFile)
    }
  }

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'processing':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'completed':
        return '处理完成'
      case 'failed':
        return '处理失败'
      case 'processing':
        return '处理中'
      default:
        return '等待处理'
    }
  }

  const filteredDocuments = data?.items.filter((doc) =>
    doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

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
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">文档管理</h1>
          <p className="text-muted-foreground mt-1">
            项目: {currentProject.name}
          </p>
        </div>
      </div>

      {/* Upload Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>上传文档</CardTitle>
          <CardDescription>
            支持 PDF、Word、Markdown 等格式
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <Input
                type="file"
                accept=".pdf,.doc,.docx,.md,.txt"
                onChange={handleFileSelect}
                disabled={uploadMutation.isPending}
              />
              {selectedFile && (
                <p className="text-sm text-muted-foreground mt-1">
                  已选择: {selectedFile.name}
                </p>
              )}
            </div>
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  上传中 {uploadProgress}%
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  上传
                </>
              )}
            </Button>
          </div>
          {uploadMutation.error && (
            <p className="text-sm text-destructive mt-2">
              {(uploadMutation.error as any)?.message || "上传失败，请重试"}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="搜索文档..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Documents List */}
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
        </div>
      )}

      {!isLoading && !error && (
        <DocumentListEnhanced
          documents={data?.items || []}
          onRefresh={() => queryClient.invalidateQueries({ queryKey: ['documents', currentProject?.id] })}
          onProcessDocument={async (docId, options) => {
            try {
              const response = await documentProcessingService.processDocument(docId, options);
              
              toast({
                title: "处理已开始",
                description: response.message,
              });
              
              // 刷新文档列表
              queryClient.invalidateQueries({ queryKey: ['documents', currentProject?.id] });
            } catch (error: any) {
              toast({
                title: "处理失败",
                description: error.response?.data?.detail || "文档处理失败",
                variant: "destructive"
              });
            }
          }}
        />
      )}
    </div>
  )
}