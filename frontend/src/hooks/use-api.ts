import { useState } from 'react';
import api from '@/services/api';

interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  status?: number;
}

interface UseApiReturn {
  loading: boolean;
  error: string | null;
  get: <T = any>(url: string) => Promise<T>;
  post: <T = any>(url: string, data?: any) => Promise<T>;
  put: <T = any>(url: string, data?: any) => Promise<T>;
  delete: <T = any>(url: string) => Promise<T>;
  uploadFile: <T = any>(url: string, formData: FormData) => Promise<T>;
}

export function useApi(): UseApiReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const makeRequest = async <T = any>(
    method: 'get' | 'post' | 'put' | 'delete',
    url: string,
    data?: any
  ): Promise<T> => {
    try {
      setLoading(true);
      setError(null);
      
      let response;
      if (method === 'get' || method === 'delete') {
        response = await api[method](url);
      } else {
        response = await api[method](url, data);
      }
      
      return response.data;
    } catch (err: any) {
      const errorMessage = err.message || '请求失败';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = async <T = any>(url: string, formData: FormData): Promise<T> => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.post(url, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (err: any) {
      const errorMessage = err.message || '文件上传失败';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    get: <T = any>(url: string) => makeRequest<T>('get', url),
    post: <T = any>(url: string, data?: any) => makeRequest<T>('post', url, data),
    put: <T = any>(url: string, data?: any) => makeRequest<T>('put', url, data),
    delete: <T = any>(url: string) => makeRequest<T>('delete', url),
    uploadFile,
  };
}