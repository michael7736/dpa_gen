'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, XCircle, Send, MessageSquare } from 'lucide-react';
import { useApi } from '@/hooks/use-api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: any;
}

export default function CognitiveTest() {
  const api = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 表单状态
  const [projectId, setProjectId] = useState('');
  const [message, setMessage] = useState('请总结一下这个项目的主要内容');
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingResponse, setStreamingResponse] = useState('');

  // 测试认知对话
  const testCognitiveChat = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }
    
    if (!message.trim()) {
      setError('请输入消息内容');
      return;
    }

    setLoading(true);
    setError(null);
    
    // 添加用户消息
    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.post('/cognitive/chat', {
        message: message,
        project_id: projectId,
        context: {
          use_project_memory: true,
          search_depth: 'deep',
          include_sources: true
        }
      });
      
      // 添加助手响应
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        metadata: {
          sources: response.sources,
          confidence: response.confidence,
          strategies_used: response.strategies_used
        }
      };
      setMessages(prev => [...prev, assistantMessage]);
      setMessage(''); // 清空输入
    } catch (err: any) {
      setError(err.message || '认知对话失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试流式对话
  const testStreamingChat = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }
    
    if (!message.trim()) {
      setError('请输入消息内容');
      return;
    }

    setLoading(true);
    setError(null);
    setStreamingResponse('');
    
    // 添加用户消息
    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // 模拟流式响应
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/cognitive/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          message: message,
          project_id: projectId,
          stream: true
        })
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          fullResponse += chunk;
          setStreamingResponse(fullResponse);
        }
      }

      // 添加完整的助手响应
      const assistantMessage: Message = {
        role: 'assistant',
        content: fullResponse,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setMessage('');
      setStreamingResponse('');
    } catch (err: any) {
      setError(err.message || '流式对话失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试文档分析
  const testAnalyzeDocument = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/cognitive/analyze', {
        project_id: projectId,
        analysis_type: 'deep',
        options: {
          extract_entities: true,
          generate_summary: true,
          identify_themes: true,
          extract_key_insights: true
        }
      });
      
      // 显示分析结果
      const analysisMessage: Message = {
        role: 'assistant',
        content: `文档分析完成：
- 摘要：${response.results.summary}
- 识别实体：${response.results.entities?.length || 0}个
- 主题：${response.results.themes?.join(', ') || '无'}
- 关键洞察：${response.results.key_insights?.join('\n') || '无'}`,
        timestamp: new Date(),
        metadata: response
      };
      setMessages(prev => [...prev, analysisMessage]);
    } catch (err: any) {
      setError(err.message || '文档分析失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试知识图谱查询
  const testQueryKnowledgeGraph = async () => {
    if (!projectId) {
      setError('请输入项目ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/knowledge/graph/${projectId}`);
      
      // 显示图谱信息
      const graphMessage: Message = {
        role: 'assistant',
        content: `知识图谱统计：
- 节点总数：${response.nodes?.length || 0}
- 关系总数：${response.edges?.length || 0}
- 主要概念：${response.main_concepts?.join(', ') || '无'}`,
        timestamp: new Date(),
        metadata: response
      };
      setMessages(prev => [...prev, graphMessage]);
    } catch (err: any) {
      setError(err.message || '查询知识图谱失败');
    } finally {
      setLoading(false);
    }
  };

  // 清空对话历史
  const clearMessages = () => {
    setMessages([]);
    setStreamingResponse('');
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
          <Label htmlFor="message">消息内容</Label>
          <div className="flex gap-2">
            <Textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="输入你的问题或指令"
              rows={3}
              className="flex-1"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.metaKey) {
                  testCognitiveChat();
                }
              }}
            />
          </div>
          <p className="text-sm text-muted-foreground">
            按 Cmd+Enter 快速发送
          </p>
        </div>
      </div>

      {/* 测试按钮 */}
      <div className="flex flex-wrap gap-2">
        <Button onClick={testCognitiveChat} disabled={loading}>
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <Send className="mr-2 h-4 w-4" />
          发送消息
        </Button>
        <Button onClick={testStreamingChat} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          流式对话
        </Button>
        <Button onClick={testAnalyzeDocument} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          分析文档
        </Button>
        <Button onClick={testQueryKnowledgeGraph} disabled={loading} variant="secondary">
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          查询图谱
        </Button>
        <Button onClick={clearMessages} variant="outline">
          清空对话
        </Button>
      </div>

      {/* 错误显示 */}
      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* 对话历史 */}
      {messages.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">对话历史</h3>
            <Badge variant="secondary">{messages.length} 条消息</Badge>
          </div>
          <ScrollArea className="h-96 border rounded-lg p-4">
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex gap-3 ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <MessageSquare className="h-4 w-4" />
                      <span className="text-xs opacity-70">
                        {msg.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                    {msg.metadata && (
                      <details className="mt-2">
                        <summary className="text-xs cursor-pointer opacity-70">
                          元数据
                        </summary>
                        <pre className="text-xs mt-1 opacity-70">
                          {JSON.stringify(msg.metadata, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              ))}
              {streamingResponse && (
                <div className="flex gap-3">
                  <div className="max-w-[80%] rounded-lg p-3 bg-muted">
                    <div className="flex items-center gap-2 mb-1">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-xs opacity-70">生成中...</span>
                    </div>
                    <div className="whitespace-pre-wrap">{streamingResponse}</div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}