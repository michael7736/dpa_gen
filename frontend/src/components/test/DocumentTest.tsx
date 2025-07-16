'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, XCircle, Upload } from 'lucide-react';
import { useApi } from '@/hooks/use-api';
import { Progress } from '@/components/ui/progress';

export default function DocumentTest() {
  const api = useApi();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  // 表单状态
  const [projectId, setProjectId] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [searchQuery, setSearchQuery] = useState('什么是机器学习？');

  // 处理文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  // 测试上传文档
  const testUploadDocument = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }
    
    if (!selectedFile) {
      setError('请选择要上传的文件');
      return;
    }

    setLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('project_id', projectId);
      formData.append('title', selectedFile.name);
      formData.append('description', '测试文档上传');
      formData.append('tags', '测试,文档');

      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const response = await api.uploadFile('/documents/upload', formData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setResult(response);
      if (response.id) {
        setDocumentId(response.id);
      }
    } catch (err: any) {
      setError(err.message || '上传文档失败');
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  // 测试获取文档列表
  const testListDocuments = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/documents?project_id=${projectId}&limit=10`);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取文档列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试获取文档详情
  const testGetDocument = async () => {
    if (!documentId) {
      setError('请先上传文档或输入文档ID');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/documents/${documentId}`);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取文档详情失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试文档处理状态
  const testDocumentStatus = async () => {
    if (!documentId) {
      setError('请先上传文档或输入文档ID');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/documents/${documentId}/status`);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取处理状态失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试文档搜索
  const testSearchDocuments = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    if (!searchQuery) {
      setError('请输入搜索查询');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/knowledge/search', {
        query: searchQuery,
        project_id: projectId,
        limit: 5,
        search_type: 'hybrid'
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || '搜索文档失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试删除文档
  const testDeleteDocument = async () => {
    if (!documentId) {
      setError('请先上传文档或输入文档ID');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.delete(`/documents/${documentId}`);
      setResult({ message: '文档删除成功', ...response });
      setDocumentId(''); // 清空文档ID
    } catch (err: any) {
      setError(err.message || '删除文档失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 表单输入 */}
      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="projectId">项目ID</Label>
          <Input
            id="projectId"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            placeholder="输入项目ID（必填）"
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="file">选择文件</Label>
          <div className="flex gap-2">
            <Input
              ref={fileInputRef}
              id="file"
              type="file"
              onChange={handleFileSelect}
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              className="w-full"
            >
              <Upload className="mr-2 h-4 w-4" />
              {selectedFile ? selectedFile.name : '选择文件'}
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            支持 PDF, DOCX, TXT, MD 格式
          </p>
        </div>

        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>上传进度</span>
              <span>{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} />
          </div>
        )}

        <div className="grid gap-2">
          <Label htmlFor="documentId">文档ID（用于查询/删除）</Label>
          <Input
            id="documentId"
            value={documentId}
            onChange={(e) => setDocumentId(e.target.value)}
            placeholder="文档ID会在上传后自动填充"
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="searchQuery">搜索查询</Label>
          <Input
            id="searchQuery"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="输入搜索关键词"
          />
        </div>
      </div>

      {/* 测试按钮 */}
      <div className="flex flex-wrap gap-2">
        <Button onClick={testUploadDocument} disabled={loading}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          上传文档
        </Button>
        <Button onClick={testListDocuments} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          获取文档列表
        </Button>
        <Button onClick={testGetDocument} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          获取文档详情
        </Button>
        <Button onClick={testDocumentStatus} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          处理状态
        </Button>
        <Button onClick={testSearchDocuments} disabled={loading} variant="default">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          搜索文档
        </Button>
        <Button onClick={testDeleteDocument} disabled={loading} variant="destructive">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          删除文档
        </Button>
      </div>

      {/* 结果显示 */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle className="h-4 w-4" />
            <span className="font-medium">操作成功</span>
          </div>
          <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}