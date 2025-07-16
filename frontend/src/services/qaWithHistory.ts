import api from './api';
import { API_ENDPOINTS } from '@/lib/config';
import { Message } from '@/types';

export interface AskWithHistoryRequest {
  question: string;
  project_id: string;
  conversation_id?: string | null;
  use_conversation_context?: boolean;
  max_history_messages?: number;
  include_sources?: boolean;
}

export interface AskWithHistoryResponse {
  answer: string;
  confidence: number;
  sources?: any[];
  conversation_id: string;
  message_id: string;
  response_time: number;
  from_cache: boolean;
  context_used?: any[];
}

export interface ContinueConversationResponse {
  success: boolean;
  conversation_id: string;
  summary: any;
  recent_messages: Array<{
    id: string;
    role: string;
    content: string;
    timestamp: string;
  }>;
  suggested_questions: string[];
}

export interface SummarizeConversationResponse {
  success: boolean;
  summary: string;
  message_count: number;
  updated_title?: string | null;
}

export const qaWithHistoryService = {
  // 带历史的问答
  async askWithHistory(data: AskWithHistoryRequest): Promise<AskWithHistoryResponse> {
    const response = await api.post('/api/v1/qa-history/answer', data);
    return response.data;
  },

  // 继续对话
  async continueConversation(conversationId: string): Promise<ContinueConversationResponse> {
    const response = await api.get(`/api/v1/qa-history/conversations/${conversationId}/continue`);
    return response.data;
  },

  // 总结对话
  async summarizeConversation(conversationId: string): Promise<SummarizeConversationResponse> {
    const response = await api.post(`/api/v1/qa-history/conversations/${conversationId}/summarize`);
    return response.data;
  },

  // 健康检查
  async healthCheck(): Promise<{ status: string; service: string; features: string[] }> {
    const response = await api.get('/api/v1/qa-history/health');
    return response.data;
  }
};