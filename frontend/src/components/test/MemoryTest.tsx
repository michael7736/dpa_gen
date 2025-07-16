'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, XCircle, Brain, Save, Search } from 'lucide-react';
import { useApi } from '@/hooks/use-api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function MemoryTest() {
  const api = useApi();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // 表单状态
  const [projectId, setProjectId] = useState('');
  const [memoryType, setMemoryType] = useState<'working' | 'task' | 'project'>('project');
  const [memoryContent, setMemoryContent] = useState('');
  const [insights, setInsights] = useState('');
  const [ttl, setTtl] = useState('86400'); // 24小时
  const [query, setQuery] = useState('');

  // 测试保存记忆
  const testSaveMemory = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    if (!memoryContent.trim()) {
      setError('请输入记忆内容');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const memoryData: any = {
        memory_type: memoryType,
        content: {
          text: memoryContent,
          timestamp: new Date().toISOString()
        }
      };

      // 根据记忆类型添加额外数据
      if (memoryType === 'project') {
        memoryData.content.key_findings = memoryContent.split('\n').filter(l => l.trim());
        if (insights) {
          memoryData.insights = insights.split('\n').map(i => ({
            type: 'observation',
            content: i.trim()
          })).filter(i => i.content);
        }
      }

      if (ttl && ttl !== '0') {
        memoryData.ttl = parseInt(ttl);
      }

      const response = await api.post(`/projects/${projectId}/memories`, memoryData);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '保存记忆失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试查询记忆
  const testQueryMemory = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let url = `/projects/${projectId}/memories?memory_type=${memoryType}`;
      if (query) {
        url += `&query=${encodeURIComponent(query)}`;
      }
      
      const response = await api.get(url);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '查询记忆失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试更新记忆
  const testUpdateMemory = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    if (!result || !result[0]?.id) {
      setError('请先查询记忆，选择要更新的记忆ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const memoryId = result[0].id; // 使用第一个查询结果的ID
      const response = await api.put(`/projects/${projectId}/memories/${memoryId}`, {
        content: {
          text: memoryContent + ' (已更新)',
          updated_at: new Date().toISOString()
        }
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || '更新记忆失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试删除记忆
  const testDeleteMemory = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    if (!result || !result[0]?.id) {
      setError('请先查询记忆，选择要删除的记忆ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const memoryId = result[0].id;
      const response = await api.delete(`/projects/${projectId}/memories/${memoryId}`);
      setResult({ message: '记忆删除成功', ...response });
    } catch (err: any) {
      setError(err.message || '删除记忆失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试记忆统计
  const testMemoryStats = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/projects/${projectId}/memories/stats`);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取记忆统计失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试记忆压缩
  const testCompressMemory = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/projects/${projectId}/memories/compress`, {
        memory_type: memoryType,
        compression_ratio: 0.7
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || '压缩记忆失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="basic">基础操作</TabsTrigger>
          <TabsTrigger value="advanced">高级功能</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4">
          {/* 基础表单 */}
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
              <Label htmlFor="memoryType">记忆类型</Label>
              <Select value={memoryType} onValueChange={(v: any) => setMemoryType(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="working">
                    <div className="flex items-center gap-2">
                      <Brain className="h-4 w-4" />
                      <span>工作记忆（1小时）</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="task">
                    <div className="flex items-center gap-2">
                      <Brain className="h-4 w-4" />
                      <span>任务记忆（24小时）</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="project">
                    <div className="flex items-center gap-2">
                      <Brain className="h-4 w-4" />
                      <span>项目记忆（永久）</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="memoryContent">记忆内容</Label>
              <Textarea
                id="memoryContent"
                value={memoryContent}
                onChange={(e) => setMemoryContent(e.target.value)}
                placeholder="输入要保存的记忆内容"
                rows={4}
              />
            </div>

            {memoryType === 'project' && (
              <div className="grid gap-2">
                <Label htmlFor="insights">洞察（可选）</Label>
                <Textarea
                  id="insights"
                  value={insights}
                  onChange={(e) => setInsights(e.target.value)}
                  placeholder="每行一个洞察"
                  rows={3}
                />
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="ttl">TTL（秒，0表示永久）</Label>
              <Input
                id="ttl"
                value={ttl}
                onChange={(e) => setTtl(e.target.value)}
                placeholder="生存时间"
                type="number"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="query">查询关键词（可选）</Label>
              <Input
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="用于查询记忆的关键词"
              />
            </div>
          </div>

          {/* 基础操作按钮 */}
          <div className="flex flex-wrap gap-2">
            <Button onClick={testSaveMemory} disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Save className="mr-2 h-4 w-4" />
              保存记忆
            </Button>
            <Button onClick={testQueryMemory} disabled={loading} variant="secondary">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Search className="mr-2 h-4 w-4" />
              查询记忆
            </Button>
            <Button onClick={testUpdateMemory} disabled={loading} variant="secondary">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              更新记忆
            </Button>
            <Button onClick={testDeleteMemory} disabled={loading} variant="destructive">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              删除记忆
            </Button>
          </div>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4">
          {/* 高级功能按钮 */}
          <div className="flex flex-wrap gap-2">
            <Button onClick={testMemoryStats} disabled={loading} variant="secondary">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              记忆统计
            </Button>
            <Button onClick={testCompressMemory} disabled={loading} variant="secondary">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              压缩记忆
            </Button>
          </div>

          <Alert>
            <Brain className="h-4 w-4" />
            <AlertDescription>
              <strong>记忆系统说明：</strong>
              <ul className="mt-2 space-y-1 text-sm">
                <li>• 工作记忆：当前会话的临时信息，1小时后自动清理</li>
                <li>• 任务记忆：任务执行的中间结果，24小时保留</li>
                <li>• 项目记忆：项目级的长期知识，永久保存</li>
                <li>• 压缩功能：自动整理和优化记忆存储</li>
              </ul>
            </AlertDescription>
          </Alert>
        </TabsContent>
      </Tabs>

      {/* 错误显示 */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* 结果显示 */}
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