'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { 
  documentServiceV2, 
  ProcessingOptions, 
  DocumentUploadResponseV2,
  PipelineProgressResponse,
  PipelineStage 
} from '@/services/documentsV2';
import { webSocketService, PipelineProgressMessage } from '@/services/websocket';

interface DocumentUploadV2Props {
  projectId?: string;
  onUploadComplete?: (result: DocumentUploadResponseV2) => void;
}

const DocumentUploadV2: React.FC<DocumentUploadV2Props> = ({
  projectId,
  onUploadComplete
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingProgress, setProcessingProgress] = useState<PipelineProgressResponse | null>(null);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponseV2 | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [options, setOptions] = useState<ProcessingOptions>({
    upload_only: true,
    generate_summary: false,
    create_index: false,
    deep_analysis: false
  });
  
  const { toast } = useToast();

  // 处理中断函数
  const handleInterrupt = useCallback(async () => {
    if (!uploadResult?.processing_pipeline) return;

    try {
      await documentServiceV2.interruptProcessing(
        uploadResult.document_id,
        uploadResult.processing_pipeline.pipeline_id
      );
      
      toast({
        title: "已中断",
        description: "文档处理已中断",
      });
    } catch (error: any) {
      toast({
        title: "中断失败",
        description: error.response?.data?.error || "无法中断处理",
        variant: "destructive"
      });
    }
  }, [uploadResult, toast]);

  // WebSocket连接管理
  useEffect(() => {
    const userId = '243588ff-459d-45b8-b77b-09aec3946a64'; // 使用固定用户ID
    
    // 连接WebSocket
    webSocketService.connect(userId).catch(error => {
      console.error('WebSocket连接失败:', error);
    });

    // 监听连接状态
    const handleConnectionChange = (connected: boolean) => {
      setWsConnected(connected);
      if (connected) {
        console.log('WebSocket已连接');
      } else {
        console.log('WebSocket已断开');
      }
    };

    webSocketService.onConnectionChange(handleConnectionChange);

    return () => {
      webSocketService.offConnectionChange(handleConnectionChange);
      // 清理订阅，但不断开连接（其他组件可能在使用）
      if (uploadResult?.processing_pipeline?.pipeline_id) {
        webSocketService.unsubscribePipelineProgress(uploadResult.processing_pipeline.pipeline_id);
      }
    };
  }, []);

  // ESC键监听
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && processingProgress && !processingProgress.completed && !processingProgress.interrupted) {
        handleInterrupt();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [processingProgress, handleInterrupt]);

  // 处理WebSocket进度更新
  const handleWebSocketProgress = useCallback((progress: PipelineProgressMessage) => {
    console.log('收到WebSocket进度更新:', progress);
    
    // 转换为组件期望的格式
    const convertedProgress: PipelineProgressResponse = {
      pipeline_id: progress.pipeline_id,
      document_id: progress.document_id,
      overall_progress: progress.overall_progress,
      current_stage: progress.current_stage,
      stages: progress.stages.map(stage => ({
        id: stage.id,
        name: stage.name,
        status: stage.status,
        progress: stage.progress,
        message: stage.message,
        can_interrupt: stage.can_interrupt,
        started_at: stage.started_at,
        completed_at: stage.completed_at,
        duration: stage.duration,
        error: stage.error
      })),
      can_resume: progress.can_resume,
      interrupted: progress.interrupted,
      completed: progress.completed,
      timestamp: progress.timestamp
    };

    setProcessingProgress(convertedProgress);

    // 检查是否完成
    if (progress.completed) {
      toast({
        title: "处理完成",
        description: "文档处理已完成",
      });
      
      // 取消订阅
      webSocketService.unsubscribePipelineProgress(progress.pipeline_id);
    }
  }, [toast]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      // 重置状态
      setUploadResult(null);
      setProcessingProgress(null);
      setUploadProgress(0);
    }
  }, []);

  const handleOptionChange = useCallback((option: keyof ProcessingOptions, value: boolean) => {
    setOptions(prev => {
      const newOptions = { ...prev, [option]: value };
      
      // 注意：仅上传选项必须始终被选中（根据后端要求）
      // 如果试图取消仅上传，不允许
      if (option === 'upload_only' && !value) {
        console.log('警告：仅上传选项必须保持选中状态');
        return prev; // 保持原状态不变
      }
      
      console.log('选项变更:', option, '=', value, '新状态:', newOptions);
      
      return newOptions;
    });
  }, []);

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: "错误",
        description: "请选择要上传的文件",
        variant: "destructive"
      });
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    // 添加调试日志
    console.log('上传时的处理选项:', options);
    console.log('各选项值:', {
      upload_only: options.upload_only,
      generate_summary: options.generate_summary,
      create_index: options.create_index,
      deep_analysis: options.deep_analysis
    });

    try {
      // 上传文档
      const result = await documentServiceV2.uploadDocument(
        file,
        options,
        projectId,
        setUploadProgress
      );

      setUploadResult(result);
      onUploadComplete?.(result);

      toast({
        title: "上传成功",
        description: `文档 ${result.filename} 上传成功`,
      });

      // 如果有处理管道，订阅WebSocket进度更新
      if (result.processing_pipeline) {
        if (wsConnected) {
          webSocketService.subscribePipelineProgress(
            result.processing_pipeline.pipeline_id,
            handleWebSocketProgress
          );
        } else {
          // WebSocket未连接，回退到轮询
          startProgressPolling(result.document_id, result.processing_pipeline.pipeline_id);
        }
      }

    } catch (error: any) {
      console.error('Upload failed:', error);
      toast({
        title: "上传失败",
        description: error.response?.data?.error || error.message || "未知错误",
        variant: "destructive"
      });
    } finally {
      setUploading(false);
    }
  };

  const startProgressPolling = async (documentId: string, pipelineId: string) => {
    try {
      await documentServiceV2.pollProcessingProgress(
        documentId,
        pipelineId,
        (progress) => {
          setProcessingProgress(progress);
        }
      );
      
      toast({
        title: "处理完成",
        description: "文档处理已完成",
      });
    } catch (error: any) {
      console.error('Progress polling failed:', error);
      toast({
        title: "进度获取失败",
        description: error.message || "无法获取处理进度",
        variant: "destructive"
      });
    }
  };

  const handleResume = async () => {
    if (!uploadResult?.processing_pipeline) return;

    try {
      await documentServiceV2.resumeProcessing(
        uploadResult.document_id,
        uploadResult.processing_pipeline.pipeline_id
      );
      
      // 重新订阅WebSocket或开始轮询
      if (wsConnected) {
        webSocketService.subscribePipelineProgress(
          uploadResult.processing_pipeline.pipeline_id,
          handleWebSocketProgress
        );
      } else {
        startProgressPolling(
          uploadResult.document_id,
          uploadResult.processing_pipeline.pipeline_id
        );
      }
      
      toast({
        title: "已恢复",
        description: "文档处理已恢复",
      });
    } catch (error: any) {
      toast({
        title: "恢复失败",
        description: error.response?.data?.error || "无法恢复处理",
        variant: "destructive"
      });
    }
  };

  const getStageStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'processing': return 'bg-blue-500';
      case 'failed': return 'bg-red-500';
      case 'interrupted': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getStageStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '等待中';
      case 'processing': return '处理中';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      case 'interrupted': return '已中断';
      default: return status;
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>文档上传 V2</CardTitle>
          <div className="flex items-center space-x-2">
            <div 
              className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}
              title={wsConnected ? 'WebSocket已连接' : 'WebSocket未连接'}
            />
            <span className="text-xs text-gray-500">
              {wsConnected ? '实时更新' : '轮询模式'}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 文件选择 */}
        <div className="space-y-2">
          <Label htmlFor="file">选择文档</Label>
          <Input
            id="file"
            type="file"
            accept=".pdf,.docx,.doc,.txt,.md"
            onChange={handleFileChange}
            disabled={uploading}
          />
          {file && (
            <p className="text-sm text-gray-600">
              已选择: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}
        </div>

        {/* 处理选项 */}
        <div className="space-y-3">
          <Label>处理选项</Label>
          <div className="grid grid-cols-2 gap-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.upload_only}
                onChange={(e) => handleOptionChange('upload_only', e.target.checked)}
                disabled={true} // 始终禁用，因为必须选中
              />
              <span className="text-gray-600">仅上传（必选）</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.generate_summary}
                onChange={(e) => handleOptionChange('generate_summary', e.target.checked)}
                disabled={uploading}
              />
              <span>生成摘要</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.create_index}
                onChange={(e) => handleOptionChange('create_index', e.target.checked)}
                disabled={uploading}
              />
              <span>创建索引</span>
            </label>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={options.deep_analysis}
                onChange={(e) => handleOptionChange('deep_analysis', e.target.checked)}
                disabled={uploading}
              />
              <span>深度分析</span>
            </label>
          </div>
        </div>

        {/* 显示待处理任务列表 */}
        {file && !uploading && !uploadResult && (
          <div className="space-y-2 p-3 bg-blue-50 border border-blue-200 rounded">
            <p className="font-medium text-blue-900">待处理任务：</p>
            <ul className="space-y-1 text-sm text-blue-800">
              <li className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                <span>文件上传到存储服务器</span>
              </li>
              {options.generate_summary && (
                <li className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  <span>生成文档摘要</span>
                </li>
              )}
              {options.create_index && (
                <li className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  <span>创建向量索引</span>
                </li>
              )}
              {options.deep_analysis && (
                <li className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  <span>执行深度分析</span>
                </li>
              )}
            </ul>
          </div>
        )}

        {/* 上传按钮 */}
        <Button 
          onClick={handleUpload} 
          disabled={!file || uploading}
          className="w-full"
        >
          {uploading ? `上传中... ${uploadProgress}%` : '开始上传'}
        </Button>

        {/* 上传结果 */}
        {uploadResult && (
          <div className="space-y-3">
            <div className="p-3 bg-green-50 border border-green-200 rounded">
              <p className="text-green-800">
                ✓ {uploadResult.message}
              </p>
              <p className="text-sm text-green-600">
                文档ID: {uploadResult.document_id}
              </p>
            </div>

            {/* 处理进度 */}
            {processingProgress && (
              <div className="space-y-3 border-2 border-blue-300 rounded-lg p-4 bg-blue-50">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-lg">处理进度</h4>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="bg-white">
                      {processingProgress.overall_progress.toFixed(1)}%
                    </Badge>
                    {!processingProgress.completed && !processingProgress.interrupted && (
                      <span className="text-xs text-gray-600">按 ESC 键取消</span>
                    )}
                  </div>
                </div>

                {/* 当前执行的任务 */}
                {processingProgress.current_stage && (
                  <div className="p-2 bg-yellow-100 border border-yellow-300 rounded">
                    <p className="text-sm font-medium text-yellow-900">
                      正在执行: {processingProgress.current_stage}
                    </p>
                  </div>
                )}

                {/* 处理阶段 */}
                <div className="space-y-2">
                  {processingProgress.stages.map((stage: PipelineStage) => (
                    <div key={stage.id} className={`flex items-center space-x-3 p-3 border rounded-lg transition-all duration-300 ${
                      stage.status === 'processing' ? 'bg-blue-100 border-blue-400' : 'bg-white'
                    }`}>
                      <div className={`w-4 h-4 rounded-full ${getStageStatusColor(stage.status)} ${
                        stage.status === 'processing' ? 'animate-pulse' : ''
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{stage.name}</span>
                          <span className={`text-sm font-medium ${
                            stage.status === 'completed' ? 'text-green-600' :
                            stage.status === 'failed' ? 'text-red-600' :
                            stage.status === 'processing' ? 'text-blue-600' :
                            'text-gray-500'
                          }`}>
                            {getStageStatusText(stage.status)}
                          </span>
                        </div>
                        {stage.status === 'processing' && (
                          <div className="w-full bg-gray-200 rounded-full h-2 mt-2 overflow-hidden">
                            <div 
                              className="bg-blue-500 h-2 rounded-full transition-all duration-300 relative"
                              style={{ width: `${stage.progress}%` }}
                            >
                              <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
                            </div>
                          </div>
                        )}
                        {stage.message && (
                          <p className="text-xs text-gray-600 mt-1">{stage.message}</p>
                        )}
                        {stage.duration && stage.status === 'completed' && (
                          <p className="text-xs text-green-600 mt-1">
                            ✓ 完成，耗时: {stage.duration.toFixed(1)}秒
                          </p>
                        )}
                        {stage.error && (
                          <p className="text-xs text-red-600 mt-1">
                            ✗ 错误: {stage.error}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* 控制按钮 */}
                {processingProgress.overall_progress < 100 && (
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleInterrupt}
                      disabled={processingProgress.interrupted}
                    >
                      中断处理
                    </Button>
                    {processingProgress.interrupted && processingProgress.can_resume && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleResume}
                      >
                        恢复处理
                      </Button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DocumentUploadV2;