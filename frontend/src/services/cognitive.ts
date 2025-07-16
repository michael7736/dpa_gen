import api from './api'

export interface CognitiveChatRequest {
  message: string
  project_id: string
  conversation_id?: string | null
  use_memory?: boolean
  strategy?: string
  max_results?: number
}

export interface CognitiveChatResponse {
  conversation_id: string
  response: string
  strategy_used: string
  confidence_score: number
  sources: Array<{
    id: string
    content: string
    score: number
    source: string
  }>
  metacognitive_state: {
    current_strategy: string
    confidence_level: string
    attention_focus: Record<string, number>
  }
  processing_time: number
}

export interface CognitiveHealthResponse {
  status: string
  timestamp: string
  components: {
    storage: string
    memory_bank: string
    workflow: string
    s2_chunker: string
    retrieval_system: string
    metacognitive_engine: string
  }
}

export interface CognitiveAnalysisRequest {
  document_id?: string
  document_text?: string
  project_id: string
  analysis_type?: string
  analysis_goal?: string
  use_memory?: boolean
  enable_metacognition?: boolean
}

export interface CognitiveAnalysisResponse {
  analysis_id: string
  processing_report: Record<string, any>
  chunks_created: number
  retrieval_results: number
  metacognitive_strategy: string
  performance_score: number
  confidence_level: string
  working_memory_usage: number
  cognitive_state_id: string
  insights: Array<{
    type: string
    content: string
    confidence: number
  }>
}

export const cognitiveService = {
  // 认知对话
  chat: async (data: CognitiveChatRequest): Promise<CognitiveChatResponse> => {
    const response = await api.post('/api/v1/cognitive/chat', {
      request: data  // FastAPI期望请求体包装在request字段中
    })
    return response.data
  },

  // 获取系统健康状态
  getHealth: async (): Promise<CognitiveHealthResponse> => {
    const response = await api.get('/api/v1/cognitive/health')
    return response.data
  },

  // 执行认知分析
  analyze: async (data: CognitiveAnalysisRequest): Promise<CognitiveAnalysisResponse> => {
    const response = await api.post('/api/v1/cognitive/analyze', {
      request: data
    })
    return response.data
  },

  // 查询记忆库
  queryMemory: async (query: string, project_id: string, memory_types: string[] = ['all']) => {
    const response = await api.post('/api/v1/cognitive/memory/query', {
      request: {
        query,
        project_id,
        memory_types,
        limit: 20
      }
    })
    return response.data
  },

  // 获取认知状态
  getCognitiveState: async (thread_id: string) => {
    const response = await api.get(`/api/v1/cognitive/state/${thread_id}`)
    return response.data
  }
}