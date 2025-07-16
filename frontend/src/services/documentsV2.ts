import api from './api';
import { API_BASE_URL } from '@/lib/config';

// V2文档处理相关类型
export interface ProcessingOptions {
  upload_only: boolean;
  generate_summary: boolean;
  create_index: boolean;
  deep_analysis: boolean;
}

export interface PipelineStage {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'interrupted';
  progress: number;
  estimated_time?: number;
  message?: string;
  can_interrupt: boolean;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  error?: string;
  result?: any;
}

export interface ProcessingPipeline {
  pipeline_id: string;
  stages: PipelineStage[];
}

export interface DocumentUploadResponseV2 {
  document_id: string;
  filename: string;
  size: number;
  status: string;
  message: string;
  processing_pipeline?: ProcessingPipeline;
}

export interface PipelineProgressResponse {
  pipeline_id: string;
  overall_progress: number;
  current_stage?: string;
  stages: PipelineStage[];
  can_resume: boolean;
  interrupted: boolean;
}

// 文档列表响应类型
export interface DocumentListResponse {
  items: Array<{
    id: string;
    project_id: string;
    filename: string;
    file_type: string;
    file_size: number;
    status: string;
    page_count: number;
    word_count: number;
    created_at: string;
    updated_at: string;
  }>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const documentServiceV2 = {
  // V2文档上传 - 支持处理选项
  async uploadDocument(
    file: File, 
    options: ProcessingOptions,
    projectId?: string,
    onProgress?: (progress: number) => void
  ): Promise<DocumentUploadResponseV2> {
    const formData = new FormData();
    formData.append('file', file);
    
    // 添加处理选项
    formData.append('upload_only', options.upload_only.toString());
    formData.append('generate_summary', options.generate_summary.toString());
    formData.append('create_index', options.create_index.toString());
    formData.append('deep_analysis', options.deep_analysis.toString());
    
    if (projectId) {
      formData.append('project_id', projectId);
    }

    const response = await api.post('/api/v2/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // 获取处理管道进度
  async getProcessingProgress(
    documentId: string, 
    pipelineId: string
  ): Promise<PipelineProgressResponse> {
    const response = await api.get(
      `/api/v2/documents/${documentId}/pipeline/${pipelineId}/progress`
    );
    return response.data;
  },

  // 中断处理管道
  async interruptProcessing(
    documentId: string, 
    pipelineId: string
  ): Promise<{ message: string; pipeline_id: string }> {
    const response = await api.post(
      `/api/v2/documents/${documentId}/pipeline/${pipelineId}/interrupt`
    );
    return response.data;
  },

  // 恢复处理管道
  async resumeProcessing(
    documentId: string, 
    pipelineId: string
  ): Promise<{ message: string; pipeline_id: string }> {
    const response = await api.post(
      `/api/v2/documents/${documentId}/pipeline/${pipelineId}/resume`
    );
    return response.data;
  },

  // 轮询处理进度（辅助函数）
  async pollProcessingProgress(
    documentId: string,
    pipelineId: string,
    onProgress: (progress: PipelineProgressResponse) => void,
    intervalMs = 2000,
    maxAttempts = 150 // 5分钟最大轮询时间
  ): Promise<PipelineProgressResponse> {
    let attempts = 0;
    
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          attempts++;
          const progress = await this.getProcessingProgress(documentId, pipelineId);
          onProgress(progress);
          
          // 检查是否完成
          if (progress.overall_progress >= 100 || 
              progress.stages.every(stage => 
                ['completed', 'failed', 'interrupted'].includes(stage.status)
              )) {
            resolve(progress);
            return;
          }
          
          // 检查是否超时
          if (attempts >= maxAttempts) {
            reject(new Error('Processing progress polling timeout'));
            return;
          }
          
          // 继续轮询
          setTimeout(poll, intervalMs);
        } catch (error) {
          reject(error);
        }
      };
      
      poll();
    });
  },

  // 获取文档列表 (使用V1 API)
  async getDocuments(
    projectId?: string,
    limit = 50,
    offset = 0
  ): Promise<DocumentListResponse> {
    const params = new URLSearchParams();
    if (projectId) {
      params.append('project_id', projectId);
    }
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await api.get(`/api/v1/documents?${params.toString()}`);
    return response.data;
  },

  // 启动文档处理操作
  async startProcessing(
    documentId: string,
    options: ProcessingOptions
  ): Promise<{ success: boolean; message: string; pipeline_id?: string }> {
    const response = await api.post(
      `/api/v1/documents/${documentId}/operations/start`,
      options
    );
    return response.data;
  },

  // 获取文档操作状态
  async getOperationStatus(documentId: string): Promise<any> {
    const response = await api.get(
      `/api/v1/documents/${documentId}/operations/status`
    );
    return response.data;
  },

  // 执行单个操作
  async executeSingleOperation(
    documentId: string,
    operation: 'summary' | 'index' | 'analysis'
  ): Promise<any> {
    const response = await api.post(
      `/api/v1/documents/${documentId}/operations/${operation}/execute`
    );
    return response.data;
  }
};