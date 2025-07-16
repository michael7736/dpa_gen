'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import ProjectTest from '@/components/test/ProjectTest';
import DocumentTest from '@/components/test/DocumentTest';
import CognitiveTest from '@/components/test/CognitiveTest';
import MemoryTest from '@/components/test/MemoryTest';
import WorkflowTest from '@/components/test/WorkflowTest';
import PerformanceTest from '@/components/test/PerformanceTest';

export default function TestPage() {
  const [activeTab, setActiveTab] = useState('project');

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">DPA 系统测试中心</h1>
        <p className="text-muted-foreground mt-2">
          测试和验证系统的各项功能
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="project">项目管理</TabsTrigger>
          <TabsTrigger value="document">文档处理</TabsTrigger>
          <TabsTrigger value="cognitive">认知对话</TabsTrigger>
          <TabsTrigger value="memory">记忆系统</TabsTrigger>
          <TabsTrigger value="workflow">工作流</TabsTrigger>
          <TabsTrigger value="performance">性能测试</TabsTrigger>
        </TabsList>

        <TabsContent value="project">
          <Card>
            <CardHeader>
              <CardTitle>项目管理测试</CardTitle>
              <CardDescription>
                测试项目的创建、更新、删除和执行功能
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProjectTest />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="document">
          <Card>
            <CardHeader>
              <CardTitle>文档处理测试</CardTitle>
              <CardDescription>
                测试文档上传、解析、向量化和检索功能
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DocumentTest />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cognitive">
          <Card>
            <CardHeader>
              <CardTitle>认知对话测试</CardTitle>
              <CardDescription>
                测试智能问答和认知分析功能
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CognitiveTest />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="memory">
          <Card>
            <CardHeader>
              <CardTitle>记忆系统测试</CardTitle>
              <CardDescription>
                测试工作记忆、任务记忆和项目记忆功能
              </CardDescription>
            </CardHeader>
            <CardContent>
              <MemoryTest />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workflow">
          <Card>
            <CardHeader>
              <CardTitle>工作流测试</CardTitle>
              <CardDescription>
                测试LangGraph工作流执行和状态管理
              </CardDescription>
            </CardHeader>
            <CardContent>
              <WorkflowTest />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle>性能测试</CardTitle>
              <CardDescription>
                测试系统响应时间、并发能力和资源使用
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PerformanceTest />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}