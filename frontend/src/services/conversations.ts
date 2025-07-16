import api from './api';
import { API_ENDPOINTS } from '@/lib/config';
import { Conversation, Message, ApiResponse, PaginatedResponse } from '@/types';

export const conversationService = {
  // Get all conversations
  async getConversations(projectId?: string, page = 1, pageSize = 10): Promise<PaginatedResponse<Conversation>> {
    const response = await api.get(API_ENDPOINTS.conversations, {
      params: { 
        user_id: 'u1', // 添加必需的user_id参数
        project_id: projectId,
        page, 
        page_size: pageSize 
      }
    });
    return response.data;
  },

  // Get single conversation
  async getConversation(id: string): Promise<Conversation> {
    const response = await api.get(API_ENDPOINTS.conversation(id), {
      params: { user_id: 'u1' }
    });
    return response.data;
  },

  // Create conversation
  async createConversation(data: {
    project_id: string;
    title?: string;
  }): Promise<Conversation> {
    const response = await api.post(API_ENDPOINTS.conversations, data);
    return response.data;
  },

  // Get messages in conversation
  async getMessages(conversationId: string, page = 1, pageSize = 20): Promise<PaginatedResponse<Message>> {
    const response = await api.get(API_ENDPOINTS.messages(conversationId), {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  // Send message
  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const response = await api.post(API_ENDPOINTS.sendMessage(conversationId), {
      content,
      role: 'user'
    });
    return response.data;
  },

  // Delete conversation
  async deleteConversation(id: string): Promise<void> {
    await api.delete(API_ENDPOINTS.conversation(id));
  }
};