'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { 
  FileText, 
  Search, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Loader2, 
  Trash2, 
  Eye,
  FileSearch,
  FileCheck,
  Brain,
  RefreshCw,
  FileUp,
  Download,
  MoreVertical,
  ExternalLink
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Document, ProcessingStatus } from '@/types';
import { documentServiceV2 } from '@/services/documentsV2';
import { documentProcessingService } from '@/services/documentProcessing';

interface DocumentListEnhancedProps {
  documents: Document[];
  onRefresh?: () => void;
  onProcessDocument?: (docId: string, options: any) => void;
}

const DocumentListEnhanced: React.FC<DocumentListEnhancedProps> = ({
  documents,
  onRefresh,
  onProcessDocument
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTab, setSelectedTab] = useState('all');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showSummary, setShowSummary] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const { toast } = useToast();

  // 获取状态图标
  const getStatusIcon = (status: ProcessingStatus) => {
    switch (status) {
      case 'uploaded':
        return <FileUp className="h-5 w-5 text-gray-500" />;
      case 'summarized':
        return <FileCheck className="h-5 w-5 text-blue-500" />;
      case 'indexed':
        return <FileSearch className="h-5 w-5 text-green-500" />;
      case 'analyzed':
        return <Brain className="h-5 w-5 text-purple-500" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
      case 'summarizing':
      case 'indexing':
      case 'analyzing':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  // 获取状态文本
  const getStatusText = (status: ProcessingStatus) => {
    const statusMap: Record<ProcessingStatus, string> = {
      'uploaded': '仅上传',
      'pending': '待处理',
      'processing': '处理中',
      'summarizing': '生成摘要中',
      'summarized': '已生成摘要',
      'indexing': '创建索引中',
      'indexed': '已创建索引',
      'analyzing': '深度分析中',
      'analyzed': '已深度分析',
      'completed': '全部完成',
      'failed': '处理失败',
      'cancelled': '已取消'
    };
    return statusMap[status] || status;
  };

  // 获取状态颜色
  const getStatusColor = (status: ProcessingStatus) => {
    const colorMap: Record<ProcessingStatus, string> = {
      'uploaded': 'secondary',
      'pending': 'secondary',
      'processing': 'default',
      'summarizing': 'default',
      'summarized': 'blue',
      'indexing': 'default',
      'indexed': 'green',
      'analyzing': 'default',
      'analyzed': 'purple',
      'completed': 'green',
      'failed': 'destructive',
      'cancelled': 'secondary'
    };
    return colorMap[status] || 'secondary';
  };

  // 过滤文档
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (selectedTab === 'all') return matchesSearch;
    if (selectedTab === 'uploaded') return matchesSearch && doc.processing_status === 'uploaded';
    if (selectedTab === 'summarized') return matchesSearch && 
      ['summarized', 'indexed', 'analyzed', 'completed'].includes(doc.processing_status);
    if (selectedTab === 'indexed') return matchesSearch && 
      ['indexed', 'analyzed', 'completed'].includes(doc.processing_status);
    if (selectedTab === 'analyzed') return matchesSearch && 
      ['analyzed', 'completed'].includes(doc.processing_status);
    return matchesSearch;
  });

  // 处理文档操作
  const handleProcessAction = async (doc: Document, action: 'summary' | 'index' | 'analysis') => {
    const options = {
      upload_only: true,
      generate_summary: action === 'summary',
      create_index: action === 'index',
      deep_analysis: action === 'analysis'
    };

    if (onProcessDocument) {
      onProcessDocument(doc.id, options);
    } else {
      toast({
        title: "处理请求已发送",
        description: `正在${action === 'summary' ? '生成摘要' : action === 'index' ? '创建索引' : '深度分析'}...`,
      });
    }
  };

  // 查看摘要
  const handleViewSummary = async (doc: Document) => {
    setSelectedDocument(doc);
    setShowSummary(true);
    setLoadingSummary(true);
    
    try {
      const summary = await documentProcessingService.getDocumentSummary(doc.id);
      setSummaryData(summary);
    } catch (error) {
      toast({
        title: "获取摘要失败",
        description: "无法加载文档摘要",
        variant: "destructive"
      });
    } finally {
      setLoadingSummary(false);
    }
  };

  // 查看分析结果
  const handleViewAnalysis = async (doc: Document) => {
    setSelectedDocument(doc);
    setShowAnalysis(true);
    setLoadingAnalysis(true);
    
    try {
      const analysis = await documentProcessingService.getDocumentAnalysis(doc.id);
      setAnalysisData(analysis);
    } catch (error) {
      toast({
        title: "获取分析结果失败",
        description: "无法加载文档分析结果",
        variant: "destructive"
      });
    } finally {
      setLoadingAnalysis(false);
    }
  };

  // 检查是否可以执行某个操作
  const canPerformAction = (doc: Document, action: 'summary' | 'index' | 'analysis') => {
    const processingStatuses = ['processing', 'summarizing', 'indexing', 'analyzing'];
    if (processingStatuses.includes(doc.processing_status)) return false;

    switch (action) {
      case 'summary':
        // 摘要只能在上传后生成一次
        return doc.processing_status === 'uploaded' && !doc.summary;
      case 'index':
        // 索引只能创建一次，在上传或摘要后
        return ['uploaded', 'summarized'].includes(doc.processing_status) && 
               !['indexed', 'analyzed', 'completed'].includes(doc.processing_status);
      case 'analysis':
        // 分析可以在任何时候进行（除了处理中）
        return !processingStatuses.includes(doc.processing_status) && 
               doc.processing_status !== 'uploaded'; // 至少需要先生成摘要
      default:
        return false;
    }
  };
  
  // 检查是否可以重新分析
  const canReanalyze = (doc: Document) => {
    return ['analyzed', 'completed'].includes(doc.processing_status);
  };

  return (
    <div className="space-y-6">
      {/* 搜索和筛选 */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            placeholder="搜索文档..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          刷新
        </Button>
      </div>

      {/* 状态筛选标签 */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid grid-cols-5 w-full">
          <TabsTrigger value="all">全部 ({documents.length})</TabsTrigger>
          <TabsTrigger value="uploaded">
            仅上传 ({documents.filter(d => d.processing_status === 'uploaded').length})
          </TabsTrigger>
          <TabsTrigger value="summarized">
            已摘要 ({documents.filter(d => ['summarized', 'indexed', 'analyzed', 'completed'].includes(d.processing_status)).length})
          </TabsTrigger>
          <TabsTrigger value="indexed">
            已索引 ({documents.filter(d => ['indexed', 'analyzed', 'completed'].includes(d.processing_status)).length})
          </TabsTrigger>
          <TabsTrigger value="analyzed">
            已分析 ({documents.filter(d => ['analyzed', 'completed'].includes(d.processing_status)).length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={selectedTab} className="mt-6">
          {filteredDocuments.length === 0 ? (
            <div className="text-center py-10">
              <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">暂无文档</p>
              <p className="text-muted-foreground">上传文档开始构建知识库</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {filteredDocuments.map((doc) => (
                <Card key={doc.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1">
                        <FileText className="h-10 w-10 text-muted-foreground mt-1" />
                        <div className="flex-1">
                          <h3 className="font-medium text-lg">{doc.filename}</h3>
                          <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                            <span>{(doc.file_size / 1024 / 1024).toFixed(2)} MB</span>
                            {doc.page_count && <span>{doc.page_count} 页</span>}
                            {doc.word_count && <span>{doc.word_count.toLocaleString()} 字</span>}
                            <span>{new Date(doc.created_at).toLocaleDateString('zh-CN')}</span>
                          </div>
                          
                          {/* 状态标签 */}
                          <div className="flex items-center gap-2 mt-3">
                            <Badge variant={getStatusColor(doc.processing_status) as any}>
                              {getStatusIcon(doc.processing_status)}
                              <span className="ml-1">{getStatusText(doc.processing_status)}</span>
                            </Badge>
                            
                            {/* 显示已完成的处理 */}
                            {['summarized', 'indexed', 'analyzed', 'completed'].includes(doc.processing_status) && (
                              <Badge variant="outline" className="bg-blue-50">
                                <FileCheck className="h-3 w-3 mr-1" />
                                已摘要
                              </Badge>
                            )}
                            {['indexed', 'analyzed', 'completed'].includes(doc.processing_status) && (
                              <Badge variant="outline" className="bg-green-50">
                                <FileSearch className="h-3 w-3 mr-1" />
                                已索引
                              </Badge>
                            )}
                            {['analyzed', 'completed'].includes(doc.processing_status) && (
                              <Badge variant="outline" className="bg-purple-50">
                                <Brain className="h-3 w-3 mr-1" />
                                已分析
                              </Badge>
                            )}
                          </div>

                          {/* 操作按钮 */}
                          <div className="flex items-center gap-2 mt-4">
                            {/* 生成摘要 */}
                            {canPerformAction(doc, 'summary') && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleProcessAction(doc, 'summary')}
                              >
                                <FileCheck className="h-4 w-4 mr-1" />
                                生成摘要
                              </Button>
                            )}

                            {/* 创建索引 */}
                            {canPerformAction(doc, 'index') && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleProcessAction(doc, 'index')}
                              >
                                <FileSearch className="h-4 w-4 mr-1" />
                                创建索引
                              </Button>
                            )}

                            {/* 深度分析 */}
                            {canPerformAction(doc, 'analysis') && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleProcessAction(doc, 'analysis')}
                              >
                                <Brain className="h-4 w-4 mr-1" />
                                深度分析
                              </Button>
                            )}

                            {/* 重新分析（已分析的文档） */}
                            {canReanalyze(doc) && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleProcessAction(doc, 'analysis')}
                              >
                                <RefreshCw className="h-4 w-4 mr-1" />
                                重新分析
                              </Button>
                            )}

                            {/* 查看结果 */}
                            {['summarized', 'indexed', 'analyzed', 'completed'].includes(doc.processing_status) && (
                              <>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleViewSummary(doc)}
                                >
                                  <Eye className="h-4 w-4 mr-1" />
                                  查看摘要
                                </Button>
                                {['analyzed', 'completed'].includes(doc.processing_status) && (
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleViewAnalysis(doc)}
                                  >
                                    <Eye className="h-4 w-4 mr-1" />
                                    查看分析
                                  </Button>
                                )}
                              </>
                            )}
                            
                            {/* 查看详情按钮 - 始终显示 */}
                            <div className="flex-1" />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => window.location.href = `/documents/${doc.id}`}
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              查看详情
                            </Button>
                          </div>
                        </div>
                      </div>

                      {/* 更多操作菜单 */}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-48">
                          <DropdownMenuLabel>文档操作</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => window.location.href = `/documents/${doc.id}`}>
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Download className="h-4 w-4 mr-2" />
                            下载原文档
                          </DropdownMenuItem>
                          {doc.summary && (
                            <DropdownMenuItem>
                              <Download className="h-4 w-4 mr-2" />
                              下载摘要
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-destructive">
                            <Trash2 className="h-4 w-4 mr-2" />
                            删除文档
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* 摘要对话框 */}
      <Dialog open={showSummary} onOpenChange={setShowSummary}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>文档摘要</DialogTitle>
            <DialogDescription>
              {selectedDocument?.filename}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            {loadingSummary ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="prose prose-sm max-w-none">
                <p className="text-muted-foreground whitespace-pre-wrap">
                  {summaryData?.summary || selectedDocument?.summary || '暂无摘要内容'}
                </p>
                {summaryData?.generated_at && (
                  <p className="text-xs text-muted-foreground mt-4">
                    生成时间：{new Date(summaryData.generated_at).toLocaleString('zh-CN')}
                  </p>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* 分析结果对话框 */}
      <Dialog open={showAnalysis} onOpenChange={setShowAnalysis}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>深度分析结果</DialogTitle>
            <DialogDescription>
              {selectedDocument?.filename}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 space-y-4">
            {loadingAnalysis ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : analysisData ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">执行摘要</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground whitespace-pre-wrap">
                      {analysisData.executive_summary}
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">关键洞察</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      {analysisData.key_insights?.map((insight: string, idx: number) => (
                        <li key={idx}>{insight}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">行动建议</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="list-decimal list-inside space-y-2 text-muted-foreground">
                      {analysisData.action_items?.map((item: any, idx: number) => (
                        <li key={idx}>
                          <span className="font-medium">{item.action}</span>
                          {item.priority && (
                            <Badge variant="outline" className="ml-2 text-xs">
                              {item.priority}
                            </Badge>
                          )}
                          {item.rationale && (
                            <p className="text-xs text-gray-500 mt-1 ml-5">{item.rationale}</p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
                
                {analysisData.created_at && (
                  <p className="text-xs text-muted-foreground text-center">
                    分析时间：{new Date(analysisData.created_at).toLocaleString('zh-CN')} | 
                    深度级别：{analysisData.depth_level}
                  </p>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                暂无分析结果
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DocumentListEnhanced;