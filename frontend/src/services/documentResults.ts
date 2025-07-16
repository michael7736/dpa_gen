/**
 * 文档结果查看服务
 * 用于获取文档摘要、索引、分析结果
 */

import api from './api'

export interface DocumentSummary {
  document_id: string
  filename: string
  summary: string
  generated_at: string
}

export interface DocumentAnalysis {
  analysis_id: string
  document_id: string
  analysis_depth: string
  status: string
  created_at: string
  result: {
    executive_summary: string
    key_insights: string[]
    action_items: string[]
    detailed_report: string
    visualization_data: any
  }
}

export interface DocumentOperationStatus {
  document_id: string
  document_status: string
  operations_summary: {
    summary_completed: boolean
    index_completed: boolean
    analysis_completed: boolean
  }
  pipelines: Array<{
    pipeline_id: string
    overall_progress: number
    completed: boolean
    stages: Array<{
      type: string
      name: string
      status: string
      progress: number
      message?: string
    }>
  }>
}

class DocumentResultsService {
  
  /**
   * 获取文档摘要
   */
  async getSummary(documentId: string): Promise<DocumentSummary> {
    const response = await api.get(`/api/v1/documents/${documentId}/summary`)
    return response.data
  }

  /**
   * 获取文档分析结果
   */
  async getAnalysis(documentId: string): Promise<DocumentAnalysis> {
    const response = await api.get(`/api/v1/documents/${documentId}/analysis`)
    return response.data
  }

  /**
   * 获取文档操作状态
   */
  async getOperationStatus(documentId: string): Promise<DocumentOperationStatus> {
    const response = await api.get(`/api/v1/documents/${documentId}/operations/status`)
    return response.data
  }

  /**
   * 检查操作是否完成
   */
  async isOperationCompleted(documentId: string, operation: 'summary' | 'index' | 'analysis'): Promise<boolean> {
    try {
      const status = await this.getOperationStatus(documentId)
      switch (operation) {
        case 'summary':
          return status.operations_summary.summary_completed
        case 'index':
          return status.operations_summary.index_completed
        case 'analysis':
          return status.operations_summary.analysis_completed
        default:
          return false
      }
    } catch (error) {
      console.error(`检查操作状态失败:`, error)
      return false
    }
  }

  /**
   * 获取索引统计信息
   */
  async getIndexStats(documentId: string): Promise<any> {
    try {
      // 通过操作状态获取索引相关信息
      const status = await this.getOperationStatus(documentId)
      const indexPipeline = status.pipelines.find(p => 
        p.stages.some(s => s.type === 'index')
      )
      
      if (indexPipeline) {
        const indexStage = indexPipeline.stages.find(s => s.type === 'index')
        return {
          completed: indexStage?.status === 'completed',
          progress: indexStage?.progress || 0,
          message: indexStage?.message,
          pipeline_id: indexPipeline.pipeline_id
        }
      }
      
      return {
        completed: false,
        progress: 0,
        message: '未开始索引创建'
      }
    } catch (error) {
      console.error('获取索引统计失败:', error)
      throw error
    }
  }
}

export const documentResultsService = new DocumentResultsService()
export default documentResultsService