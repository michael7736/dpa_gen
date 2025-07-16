import api from './api';
import { API_ENDPOINTS } from '@/lib/config';
import { Document, ApiResponse, PaginatedResponse } from '@/types';

export const documentService = {
  // Get all documents
  async getDocuments(projectId?: string, page = 1, pageSize = 10): Promise<PaginatedResponse<Document>> {
    const response = await api.get(API_ENDPOINTS.documents, {
      params: { 
        project_id: projectId,
        page, 
        page_size: pageSize 
      }
    });
    return response.data;
  },

  // Get single document
  async getDocument(id: string): Promise<Document> {
    const response = await api.get(API_ENDPOINTS.document(id));
    return response.data;
  },

  // Upload document
  async uploadDocument(file: File, projectId: string, onProgress?: (progress: number) => void): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post(`${API_ENDPOINTS.uploadDocument}?project_id=${projectId}`, formData, {
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

  // Get document status
  async getDocumentStatus(id: string): Promise<Document> {
    const response = await api.get(API_ENDPOINTS.documentStatus(id));
    return response.data;
  },

  // Delete document
  async deleteDocument(id: string): Promise<void> {
    await api.delete(API_ENDPOINTS.document(id));
  }
};