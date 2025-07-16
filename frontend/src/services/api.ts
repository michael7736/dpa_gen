import axios, { AxiosInstance, AxiosError } from 'axios';
import { API_BASE_URL } from '@/lib/config';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-USER-ID': 'u1', // 单用户阶段固定值
  },
  withCredentials: false, // 暂时禁用以避免CORS问题
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if exists
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    
    // Enhanced error handling
    const responseData = error.response?.data as any;
    const errorMessage = responseData?.detail || 
                        responseData?.message || 
                        error.message || 
                        '网络错误，请稍后重试';
    
    // Create a more informative error object
    const enhancedError = {
      ...error,
      message: errorMessage,
      status: error.response?.status,
      data: error.response?.data
    };
    
    return Promise.reject(enhancedError);
  }
);

export default api;