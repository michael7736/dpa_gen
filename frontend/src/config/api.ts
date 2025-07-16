// API配置
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8200',
  ENDPOINTS: {
    DOCUMENTS: '/api/v1/documents',
    PROJECTS: '/api/v1/projects',
    QA: '/api/v1/qa',
    AAG: '/api/v1/aag',
    ANALYSIS: '/api/v1/analysis'
  },
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'X-USER-ID': 'u1'
  }
}

// 导出单独的API_BASE_URL供兼容性使用
export const API_BASE_URL = API_CONFIG.BASE_URL

export const getApiUrl = (endpoint: string) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}