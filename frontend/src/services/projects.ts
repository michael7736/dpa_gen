import api from './api';
import { API_ENDPOINTS } from '@/lib/config';
import { Project, ApiResponse, PaginatedResponse } from '@/types';

export const projectService = {
  // Get all projects
  async getProjects(page = 1, pageSize = 10): Promise<PaginatedResponse<Project>> {
    const response = await api.get(API_ENDPOINTS.projects, {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  // Get single project
  async getProject(id: string): Promise<Project> {
    const response = await api.get(API_ENDPOINTS.project(id));
    return response.data;
  },

  // Create project
  async createProject(data: {
    name: string;
    description?: string;
  }): Promise<Project> {
    const response = await api.post(API_ENDPOINTS.projects, data);
    return response.data;
  },

  // Update project
  async updateProject(id: string, data: {
    name?: string;
    description?: string;
  }): Promise<Project> {
    const response = await api.put(API_ENDPOINTS.project(id), data);
    return response.data;
  },

  // Delete project
  async deleteProject(id: string): Promise<void> {
    await api.delete(API_ENDPOINTS.project(id));
  }
};