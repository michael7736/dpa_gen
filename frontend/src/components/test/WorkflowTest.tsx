'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, XCircle, Play, Pause, RotateCcw, Activity } from 'lucide-react';
import { useApi } from '@/hooks/use-api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface WorkflowState {
  phase: string;
  status: string;
  progress: number;
  tasks: any[];
  errors: string[];
}

export default function WorkflowTest() {
  const api = useApi();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [polling, setPolling] = useState(false);

  // 表单状态
  const [projectId, setProjectId] = useState('');
  const [workflowType, setWorkflowType] = useState('document_processing');
  const [workflowConfig, setWorkflowConfig] = useState(`{
  "max_iterations": 10,
  "timeout": 300,
  "parallel_tasks": 3
}`);

  // 测试启动工作流
  const testStartWorkflow = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const config = JSON.parse(workflowConfig);
      const response = await api.post('/workflow/start', {
        project_id: projectId,
        workflow_type: workflowType,
        config: config
      });
      
      setResult(response);
      if (response.workflow_id) {
        // 开始轮询状态
        startPollingStatus(response.workflow_id);
      }
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setError('配置JSON格式错误');
      } else {
        setError(err.message || '启动工作流失败');
      }
    } finally {
      setLoading(false);
    }
  };

  // 测试获取工作流状态
  const testGetWorkflowStatus = async () => {
    if (!result?.workflow_id) {
      setError('请先启动工作流');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/workflow/${result.workflow_id}/status`);
      setWorkflowState(response);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取工作流状态失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试暂停工作流
  const testPauseWorkflow = async () => {
    if (!result?.workflow_id) {
      setError('请先启动工作流');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/workflow/${result.workflow_id}/pause`);
      setResult(response);
      stopPolling();
    } catch (err: any) {
      setError(err.message || '暂停工作流失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试恢复工作流
  const testResumeWorkflow = async () => {
    if (!result?.workflow_id) {
      setError('请先启动工作流');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/workflow/${result.workflow_id}/resume`);
      setResult(response);
      startPollingStatus(result.workflow_id);
    } catch (err: any) {
      setError(err.message || '恢复工作流失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试取消工作流
  const testCancelWorkflow = async () => {
    if (!result?.workflow_id) {
      setError('请先启动工作流');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/workflow/${result.workflow_id}/cancel`);
      setResult(response);
      stopPolling();
    } catch (err: any) {
      setError(err.message || '取消工作流失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试获取工作流历史
  const testGetWorkflowHistory = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/workflow/history?project_id=${projectId}&limit=10`);
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取工作流历史失败');
    } finally {
      setLoading(false);
    }
  };

  // 轮询工作流状态
  const startPollingStatus = (workflowId: string) => {
    setPolling(true);
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/workflow/${workflowId}/status`);
        setWorkflowState(response);
        
        // 如果工作流完成或失败，停止轮询
        if (response.status === 'completed' || response.status === 'failed') {
          clearInterval(pollInterval);
          setPolling(false);
        }
      } catch (err) {
        console.error('轮询状态失败:', err);
      }
    }, 2000); // 每2秒轮询一次

    // 保存interval ID以便停止
    (window as any).workflowPollInterval = pollInterval;
  };

  // 停止轮询
  const stopPolling = () => {
    if ((window as any).workflowPollInterval) {
      clearInterval((window as any).workflowPollInterval);
      (window as any).workflowPollInterval = null;
    }
    setPolling(false);
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'paused':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
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
          <Label htmlFor="workflowType">工作流类型</Label>
          <Select value={workflowType} onValueChange={setWorkflowType}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="document_processing">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  <span>文档处理</span>
                </div>
              </SelectItem>
              <SelectItem value="research_planning">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  <span>研究规划</span>
                </div>
              </SelectItem>
              <SelectItem value="knowledge_extraction">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  <span>知识提取</span>
                </div>
              </SelectItem>
              <SelectItem value="report_generation">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  <span>报告生成</span>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="workflowConfig">工作流配置（JSON）</Label>
          <Textarea
            id="workflowConfig"
            value={workflowConfig}
            onChange={(e) => setWorkflowConfig(e.target.value)}
            placeholder="输入工作流配置"
            rows={5}
            className="font-mono text-sm"
          />
        </div>
      </div>

      {/* 测试按钮 */}
      <div className="flex flex-wrap gap-2">
        <Button onClick={testStartWorkflow} disabled={loading}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <Play className="mr-2 h-4 w-4" />
          启动工作流
        </Button>
        <Button onClick={testGetWorkflowStatus} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          获取状态
        </Button>
        <Button onClick={testPauseWorkflow} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <Pause className="mr-2 h-4 w-4" />
          暂停
        </Button>
        <Button onClick={testResumeWorkflow} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <RotateCcw className="mr-2 h-4 w-4" />
          恢复
        </Button>
        <Button onClick={testCancelWorkflow} disabled={loading} variant="destructive">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          取消
        </Button>
        <Button onClick={testGetWorkflowHistory} disabled={loading} variant="outline">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          历史记录
        </Button>
      </div>

      {/* 轮询状态指示 */}
      {polling && (
        <Alert>
          <Activity className="h-4 w-4 animate-pulse" />
          <AlertDescription>
            正在自动更新工作流状态...
          </AlertDescription>
        </Alert>
      )}

      {/* 工作流状态显示 */}
      {workflowState && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">工作流状态</h3>
            <Badge className={getStatusColor(workflowState.status)}>
              {workflowState.status}
            </Badge>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>当前阶段：{workflowState.phase}</span>
              <span>{workflowState.progress}%</span>
            </div>
            <Progress value={workflowState.progress} />
          </div>

          {workflowState.tasks && workflowState.tasks.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-sm">任务列表</h4>
              <div className="space-y-1">
                {workflowState.tasks.map((task: any, index: number) => (
                  <div key={index} className="flex items-center justify-between text-sm p-2 bg-muted rounded">
                    <span>{task.name}</span>
                    <Badge variant={task.status === 'completed' ? 'default' : 'secondary'}>
                      {task.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {workflowState.errors && workflowState.errors.length > 0 && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-1">
                  {workflowState.errors.map((err: string, index: number) => (
                    <div key={index}>{err}</div>
                  ))}
                </div>
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      {/* 错误显示 */}
      {error && !workflowState?.errors?.length && (
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