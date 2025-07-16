'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { useApi } from '@/hooks/use-api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function ProjectTest() {
  const api = useApi();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // 表单状态
  const [projectName, setProjectName] = useState('测试项目-' + Date.now());
  const [projectDescription, setProjectDescription] = useState('这是一个测试项目，用于验证系统功能');
  const [projectType, setProjectType] = useState('research');
  const [projectId, setProjectId] = useState('');

  // 测试创建项目
  const testCreateProject = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/projects', {
        name: projectName,
        description: projectDescription,
        type: projectType,
        config: {
          max_tasks: 20,
          auto_execute: true,
          parallel_tasks: 3
        },
        objectives: ['测试目标1', '测试目标2'],
        constraints: ['时间限制：1周', '资源限制：使用免费API']
      });
      
      setResult(response);
      if (response.id) {
        setProjectId(response.id);
      }
    } catch (err: any) {
      setError(err.message || '创建项目失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试获取项目列表
  const testListProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/projects?limit=10');
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取项目列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试获取项目详情
  const testGetProject = async () => {
    if (!projectId) {
      setError('请先创建项目或输入项目ID');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/projects/${projectId}`);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取项目详情失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试更新项目
  const testUpdateProject = async () => {
    if (!projectId) {
      setError('请先创建项目或输入项目ID');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.put(`/projects/${projectId}`, {
        name: projectName + ' (已更新)',
        status: 'planning',
        quality_gates: {
          accuracy: 0.85,
          completeness: 0.9
        }
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || '更新项目失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试执行项目
  const testExecuteProject = async () => {
    if (!projectId) {
      setError('请先创建项目或输入项目ID');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(`/projects/${projectId}/execute`, {
        initial_context: {
          focus_areas: ['技术实现', '应用场景']
        },
        user_preferences: {
          language: 'zh-CN',
          detail_level: 'high'
        }
      });
      setResult(response);
    } catch (err: any) {
      setError(err.message || '执行项目失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试删除项目
  const testDeleteProject = async () => {
    if (!projectId) {
      setError('请先创建项目或输入项目ID');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const response = await api.delete(`/projects/${projectId}`);
      setResult({ message: '项目删除成功', ...response });
      setProjectId(''); // 清空项目ID
    } catch (err: any) {
      setError(err.message || '删除项目失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 表单输入 */}
      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="projectName">项目名称</Label>
          <Input
            id="projectName"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="输入项目名称"
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="projectDescription">项目描述</Label>
          <Textarea
            id="projectDescription"
            value={projectDescription}
            onChange={(e) => setProjectDescription(e.target.value)}
            placeholder="输入项目描述"
            rows={3}
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="projectType">项目类型</Label>
          <Select value={projectType} onValueChange={setProjectType}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="research">研究项目</SelectItem>
              <SelectItem value="analysis">分析项目</SelectItem>
              <SelectItem value="report">报告项目</SelectItem>
              <SelectItem value="documentation">文档项目</SelectItem>
              <SelectItem value="custom">自定义项目</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="projectId">项目ID（用于查询/更新/删除）</Label>
          <Input
            id="projectId"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            placeholder="项目ID会在创建后自动填充"
          />
        </div>
      </div>

      {/* 测试按钮 */}
      <div className="flex flex-wrap gap-2">
        <Button onClick={testCreateProject} disabled={loading}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          创建项目
        </Button>
        <Button onClick={testListProjects} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          获取项目列表
        </Button>
        <Button onClick={testGetProject} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          获取项目详情
        </Button>
        <Button onClick={testUpdateProject} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          更新项目
        </Button>
        <Button onClick={testExecuteProject} disabled={loading} variant="default">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          执行项目
        </Button>
        <Button onClick={testDeleteProject} disabled={loading} variant="destructive">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          删除项目
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