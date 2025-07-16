import api from './api';
import { API_ENDPOINTS } from '@/lib/config';
import { Message, Conversation, Source } from '@/types';

export interface AskQuestionRequest {
  project_id: string;
  question: string;
  include_sources?: boolean;
  include_follow_ups?: boolean;
}

export interface AskQuestionResponse {
  answer: string;
  confidence_score: number;
  context_used?: any[];
  retrieval_breakdown?: any;
  processing_time: number;
  metadata?: any;
  // 兼容性字段
  confidence?: number;
  sources?: any[];
  response_time?: number;
  from_cache?: boolean;
}

export const qaService = {
  // Ask a question
  async askQuestion(data: AskQuestionRequest): Promise<AskQuestionResponse> {
    const response = await api.post(API_ENDPOINTS.ask, data);
    return response.data;
  },

  // Get conversations for a project
  async getConversations(projectId: string): Promise<Conversation[]> {
    const response = await api.get(API_ENDPOINTS.conversations, {
      params: { 
        user_id: 'u1', // 添加必需的user_id参数
        project_id: projectId 
      }
    });
    return response.data.items || [];
  },

  // Get conversation details with messages
  async getConversation(conversationId: string): Promise<{
    conversation: Conversation;
    messages: Message[];
  }> {
    const response = await api.get(API_ENDPOINTS.conversation(conversationId));
    return response.data;
  },

  // Create new conversation
  async createConversation(projectId: string, title: string): Promise<Conversation> {
    const response = await api.post(API_ENDPOINTS.conversations, { 
      project_id: projectId,
      title 
    });
    return response.data;
  },

  // Delete conversation
  async deleteConversation(conversationId: string): Promise<void> {
    await api.delete(API_ENDPOINTS.conversation(conversationId));
  }
};