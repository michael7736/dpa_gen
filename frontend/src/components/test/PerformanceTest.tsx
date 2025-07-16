'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, XCircle, Zap, Timer, BarChart3 } from 'lucide-react';
import { useApi } from '@/hooks/use-api';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface PerformanceMetrics {
  endpoint: string;
  method: string;
  averageTime: number;
  p95Time: number;
  p99Time: number;
  requestsPerSecond: number;
  errorRate: number;
  successCount: number;
  errorCount: number;
}

export default function PerformanceTest() {
  const api = useApi();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);

  // 表单状态
  const [testType, setTestType] = useState('api');
  const [concurrent, setConcurrent] = useState('10');
  const [duration, setDuration] = useState('30');
  const [requestsPerTest, setRequestsPerTest] = useState('100');

  // 测试API性能
  const testAPIPerformance = async () => {
    setLoading(true);
    setError(null);
    setProgress(0);
    setMetrics([]);

    try {
      const endpoints = [
        { path: '/health', method: 'GET' },
        { path: '/projects', method: 'GET' },
        { path: '/documents', method: 'GET' },
        { path: '/knowledge/search', method: 'POST' }
      ];

      const results: PerformanceMetrics[] = [];
      const totalEndpoints = endpoints.length;

      for (let i = 0; i < totalEndpoints; i++) {
        const endpoint = endpoints[i];
        setProgress((i / totalEndpoints) * 100);

        const response = await api.post('/performance/test/api', {
          endpoint: endpoint.path,
          method: endpoint.method,
          concurrent_requests: parseInt(concurrent),
          total_requests: parseInt(requestsPerTest)
        });

        results.push({
          endpoint: endpoint.path,
          method: endpoint.method,
          averageTime: response.metrics.average_time,
          p95Time: response.metrics.p95_time,
          p99Time: response.metrics.p99_time,
          requestsPerSecond: response.metrics.requests_per_second,
          errorRate: response.metrics.error_rate,
          successCount: response.metrics.success_count,
          errorCount: response.metrics.error_count
        });
      }

      setProgress(100);
      setMetrics(results);
      setResult({ summary: 'API性能测试完成', metrics: results });
    } catch (err: any) {
      setError(err.message || 'API性能测试失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试数据库性能
  const testDatabasePerformance = async () => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      const databases = ['postgresql', 'neo4j', 'qdrant', 'redis'];
      const results: any[] = [];
      const totalDatabases = databases.length;

      for (let i = 0; i < totalDatabases; i++) {
        const db = databases[i];
        setProgress((i / totalDatabases) * 100);

        const response = await api.post('/performance/test/database', {
          database: db,
          operations: ['read', 'write', 'update', 'delete'],
          iterations: parseInt(requestsPerTest)
        });

        results.push({
          database: db,
          ...response.metrics
        });
      }

      setProgress(100);
      setResult({ summary: '数据库性能测试完成', results });
    } catch (err: any) {
      setError(err.message || '数据库性能测试失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试负载能力
  const testLoadCapacity = async () => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      // 模拟逐步增加负载
      const loadLevels = [10, 50, 100, 200, 500];
      const results: any[] = [];

      for (let i = 0; i < loadLevels.length; i++) {
        const load = loadLevels[i];
        setProgress((i / loadLevels.length) * 100);

        const response = await api.post('/performance/test/load', {
          concurrent_users: load,
          duration_seconds: parseInt(duration),
          scenario: 'mixed' // 混合场景：读写操作
        });

        results.push({
          load,
          ...response.metrics
        });

        // 如果错误率太高，停止测试
        if (response.metrics.error_rate > 0.1) {
          break;
        }
      }

      setProgress(100);
      setResult({ summary: '负载测试完成', results });
    } catch (err: any) {
      setError(err.message || '负载测试失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试AI模型性能
  const testModelPerformance = async () => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      const models = [
        { name: 'GPT-4o', provider: 'openai' },
        { name: 'Claude-3.5', provider: 'anthropic' },
        { name: 'DeepSeek-V3', provider: 'deepseek' }
      ];
      
      const results: any[] = [];
      const totalModels = models.length;

      for (let i = 0; i < totalModels; i++) {
        const model = models[i];
        setProgress((i / totalModels) * 100);

        const response = await api.post('/performance/test/model', {
          model: model.name,
          provider: model.provider,
          test_cases: [
            { type: 'completion', tokens: 100 },
            { type: 'completion', tokens: 500 },
            { type: 'completion', tokens: 1000 }
          ]
        });

        results.push({
          model: model.name,
          provider: model.provider,
          ...response.metrics
        });
      }

      setProgress(100);
      setResult({ summary: 'AI模型性能测试完成', results });
    } catch (err: any) {
      setError(err.message || 'AI模型性能测试失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试内存使用
  const testMemoryUsage = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/performance/metrics/memory');
      setResult(response);
    } catch (err: any) {
      setError(err.message || '获取内存使用情况失败');
    } finally {
      setLoading(false);
    }
  };

  // 生成性能报告
  const generateReport = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/performance/report', {
        test_type: testType,
        include_metrics: true,
        include_recommendations: true
      });
      
      // 下载报告
      if (response.report_url) {
        window.open(response.report_url, '_blank');
      }
      
      setResult(response);
    } catch (err: any) {
      setError(err.message || '生成性能报告失败');
    } finally {
      setLoading(false);
    }
  };

  // 格式化时间
  const formatTime = (ms: number) => {
    if (ms < 1) return `${(ms * 1000).toFixed(0)}μs`;
    if (ms < 1000) return `${ms.toFixed(1)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="space-y-6">
      {/* 表单输入 */}
      <div className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="testType">测试类型</Label>
          <Select value={testType} onValueChange={setTestType}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="api">API性能测试</SelectItem>
              <SelectItem value="database">数据库性能测试</SelectItem>
              <SelectItem value="load">负载能力测试</SelectItem>
              <SelectItem value="model">AI模型性能测试</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="grid gap-2">
            <Label htmlFor="concurrent">并发数</Label>
            <Input
              id="concurrent"
              value={concurrent}
              onChange={(e) => setConcurrent(e.target.value)}
              placeholder="并发请求数"
              type="number"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="duration">持续时间（秒）</Label>
            <Input
              id="duration"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              placeholder="测试持续时间"
              type="number"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="requestsPerTest">每项测试请求数</Label>
            <Input
              id="requestsPerTest"
              value={requestsPerTest}
              onChange={(e) => setRequestsPerTest(e.target.value)}
              placeholder="请求总数"
              type="number"
            />
          </div>
        </div>
      </div>

      {/* 测试按钮 */}
      <div className="flex flex-wrap gap-2">
        <Button 
          onClick={testType === 'api' ? testAPIPerformance : 
                  testType === 'database' ? testDatabasePerformance :
                  testType === 'load' ? testLoadCapacity :
                  testModelPerformance} 
          disabled={loading}
        >
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <Zap className="mr-2 h-4 w-4" />
          开始测试
        </Button>
        <Button onClick={testMemoryUsage} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          内存使用
        </Button>
        <Button onClick={generateReport} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <BarChart3 className="mr-2 h-4 w-4" />
          生成报告
        </Button>
      </div>

      {/* 进度条 */}
      {loading && progress > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>测试进度</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} />
        </div>
      )}

      {/* API性能指标显示 */}
      {metrics.length > 0 && (
        <div className="grid gap-4">
          {metrics.map((metric, index) => (
            <Card key={index}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">
                  {metric.method} {metric.endpoint}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">平均响应时间</p>
                    <p className="font-medium">{formatTime(metric.averageTime)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">P95响应时间</p>
                    <p className="font-medium">{formatTime(metric.p95Time)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">请求/秒</p>
                    <p className="font-medium">{metric.requestsPerSecond.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">错误率</p>
                    <p className={`font-medium ${metric.errorRate > 0.01 ? 'text-red-600' : 'text-green-600'}`}>
                      {(metric.errorRate * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 错误显示 */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* 结果显示 */}
      {result && !metrics.length && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle className="h-4 w-4" />
            <span className="font-medium">测试完成</span>
          </div>
          <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}

      {/* 性能建议 */}
      <Alert>
        <Timer className="h-4 w-4" />
        <AlertDescription>
          <strong>性能测试说明：</strong>
          <ul className="mt-2 space-y-1 text-sm">
            <li>• API测试：检测各端点的响应时间和吞吐量</li>
            <li>• 数据库测试：评估不同数据库的读写性能</li>
            <li>• 负载测试：找出系统的极限承载能力</li>
            <li>• 模型测试：比较不同AI模型的推理速度</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
}