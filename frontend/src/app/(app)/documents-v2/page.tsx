'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import DocumentUploadV2 from '@/components/documents/DocumentUploadV2';
import { DocumentUploadResponseV2 } from '@/services/documentsV2';

const DocumentsV2Page: React.FC = () => {
  const [uploadedDocuments, setUploadedDocuments] = useState<DocumentUploadResponseV2[]>([]);

  const handleUploadComplete = (result: DocumentUploadResponseV2) => {
    setUploadedDocuments(prev => [result, ...prev]);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">智能文档处理 V2</h1>
          <p className="text-gray-600 mt-2">
            新一代文档处理系统，支持用户自定义处理选项和实时进度跟踪
          </p>
        </div>
        <Badge variant="outline" className="bg-blue-50 text-blue-700">
          V2.0
        </Badge>
      </div>

      <Tabs defaultValue="upload" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload">文档上传</TabsTrigger>
          <TabsTrigger value="features">功能介绍</TabsTrigger>
          <TabsTrigger value="history">上传历史</TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          <DocumentUploadV2 onUploadComplete={handleUploadComplete} />
        </TabsContent>

        <TabsContent value="features" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span>🚀</span>
                  <span>灵活的处理选项</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">仅上传</Badge>
                    <span className="text-sm">将文档安全存储到MinIO，不进行任何处理</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">生成摘要</Badge>
                    <span className="text-sm">快速生成文档摘要，帮助决定后续处理</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">创建索引</Badge>
                    <span className="text-sm">向量化文档内容，支持语义搜索和问答</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">深度分析</Badge>
                    <span className="text-sm">六阶段深度分析，提取核心洞察</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span>📊</span>
                  <span>实时进度跟踪</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    <span>实时显示每个处理阶段的进度</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    <span>显示每个阶段的耗时和状态</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                    <span>支持随时中断和恢复处理</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                    <span>详细的错误信息和处理建议</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span>⚡</span>
                  <span>高性能处理</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-2 text-sm">
                  <li>• <strong>摘要生成</strong>: 5-10秒（使用GPT-4o-mini）</li>
                  <li>• <strong>向量索引</strong>: 3-6秒（包含完整向量化）</li>
                  <li>• <strong>深度分析</strong>: 0.5-2秒（六阶段分析）</li>
                  <li>• <strong>并发处理</strong>: 支持多文档同时处理</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span>🔒</span>
                  <span>安全可靠</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <ul className="space-y-2 text-sm">
                  <li>• <strong>MinIO对象存储</strong>: 企业级文件存储</li>
                  <li>• <strong>数据隔离</strong>: 用户数据完全隔离</li>
                  <li>• <strong>错误恢复</strong>: 自动重试和错误处理</li>
                  <li>• <strong>文件验证</strong>: 支持格式和大小限制</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>最近上传的文档</CardTitle>
            </CardHeader>
            <CardContent>
              {uploadedDocuments.length > 0 ? (
                <div className="space-y-3">
                  {uploadedDocuments.map((doc, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <p className="font-medium">{doc.filename}</p>
                        <p className="text-sm text-gray-600">
                          大小: {(doc.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                        <p className="text-xs text-gray-500">
                          文档ID: {doc.document_id}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge 
                          variant={doc.status === 'uploaded' ? 'default' : 'secondary'}
                        >
                          {doc.status}
                        </Badge>
                        {doc.processing_pipeline && (
                          <p className="text-xs text-gray-500 mt-1">
                            管道: {doc.processing_pipeline.pipeline_id.slice(0, 8)}...
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>还没有上传任何文档</p>
                  <p className="text-sm">使用"文档上传"标签页开始上传您的第一个文档</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DocumentsV2Page;