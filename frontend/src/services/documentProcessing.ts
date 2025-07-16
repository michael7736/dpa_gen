import axios from 'axios';
import { API_BASE_URL } from '@/config/api';

export interface ProcessingRequest {
  generate_summary?: boolean;
  create_index?: boolean;
  deep_analysis?: boolean;
  analysis_depth?: 'basic' | 'standard' | 'deep' | 'expert' | 'comprehensive';
  analysis_goal?: string;
}

export interface ProcessingResponse {
  document_id: string;
  pipeline_id: string | null;
  message: string;
  processing_tasks: string[];
}

export interface DocumentSummary {
  document_id: string;
  filename: string;
  summary: string;
  generated_at: string;
}

export interface DocumentAnalysis {
  document_id: string;
  analysis_id: string;
  analysis_type: string;
  depth_level: string;
  executive_summary: string;
  key_insights: string[];
  action_items: Array<{
    priority: string;
    action: string;
    rationale: string;
  }>;
  detailed_report: string;
  visualizations: any[];
  metadata: any;
  created_at: string;
}

class DocumentProcessingService {
  private baseURL = `${API_BASE_URL}/api/v1/documents`;

  /**
   * 处理文档（生成摘要、创建索引、深度分析）
   */
  async processDocument(
    documentId: string,
    options: ProcessingRequest
  ): Promise<ProcessingResponse> {
    try {
      const response = await axios.post<ProcessingResponse>(
        `${this.baseURL}/${documentId}/process`,
        options,
        {
          headers: {
            'X-USER-ID': 'u1'
          }
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Process document failed:', error);
      throw error;
    }
  }

  /**
   * 获取文档摘要
   */
  async getDocumentSummary(documentId: string): Promise<DocumentSummary> {
    try {
      const response = await axios.get<DocumentSummary>(
        `${this.baseURL}/${documentId}/summary`,
        {
          headers: {
            'X-USER-ID': 'u1'
          }
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Get document summary failed:', error);
      throw error;
    }
  }

  /**
   * 获取文档分析结果
   */
  async getDocumentAnalysis(documentId: string): Promise<DocumentAnalysis> {
    try {
      const response = await axios.get<DocumentAnalysis>(
        `${this.baseURL}/${documentId}/analysis`,
        {
          headers: {
            'X-USER-ID': 'u1'
          }
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Get document analysis failed:', error);
      throw error;
    }
  }

  /**
   * 获取文档处理历史
   */
  async getProcessingHistory(documentId: string): Promise<any[]> {
    try {
      const response = await axios.get<any[]>(
        `${this.baseURL}/${documentId}/processing-history`,
        {
          headers: {
            'X-USER-ID': 'u1'
          }
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Get processing history failed:', error);
      throw error;
    }
  }
}

export const documentProcessingService = new DocumentProcessingService();