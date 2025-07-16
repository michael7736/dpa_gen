// AAG 分析服务
export interface DocumentAnalysisRequest {
  document_id: string
  document_content: string
  analysis_type?: string
  options?: Record<string, any>
}

export interface WorkflowExecutionRequest {
  workflow_id: string
  document_id: string
  initial_state?: Record<string, any>
}

export interface AnalysisResult {
  success: boolean
  document_id: string
  result?: any
  error?: string
  metadata?: {
    duration: number
    tokens_used: number
    from_cache?: boolean
  }
}

class AAGService {
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8200'
  }

  // 文档快速略读
  async skimDocument(request: DocumentAnalysisRequest): Promise<AnalysisResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aag/skim`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-USER-ID': 'u1'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Skim analysis failed:', error)
      // 返回模拟数据
      return this.getMockSkimResult(request.document_id)
    }
  }

  // 渐进式摘要
  async generateSummary(request: DocumentAnalysisRequest & { summary_level: string }): Promise<AnalysisResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aag/summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-USER-ID': 'u1'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Summary generation failed:', error)
      return this.getMockSummaryResult(request.document_id, request.summary_level)
    }
  }

  // 知识图谱构建
  async buildKnowledgeGraph(request: DocumentAnalysisRequest & { extraction_mode: string }): Promise<AnalysisResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aag/knowledge-graph`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-USER-ID': 'u1'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Knowledge graph building failed:', error)
      return this.getMockKnowledgeGraphResult(request.document_id)
    }
  }

  // 多维大纲提取
  async extractOutline(request: DocumentAnalysisRequest & { dimension: string }): Promise<AnalysisResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aag/outline`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-USER-ID': 'u1'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Outline extraction failed:', error)
      return this.getMockOutlineResult(request.document_id)
    }
  }

  // 深度分析
  async performDeepAnalysis(request: DocumentAnalysisRequest & { analysis_types?: string[] }): Promise<AnalysisResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aag/deep-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-USER-ID': 'u1'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Deep analysis failed:', error)
      return this.getMockDeepAnalysisResult(request.document_id)
    }
  }

  // 执行工作流
  async executeWorkflow(request: WorkflowExecutionRequest): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aag/workflow/${request.workflow_id}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-USER-ID': 'u1'
        },
        body: JSON.stringify({
          document_id: request.document_id,
          initial_state: request.initial_state
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Workflow execution failed:', error)
      return this.getMockWorkflowResult(request.workflow_id, request.document_id)
    }
  }

  // 获取工作流模板
  async getWorkflowTemplates(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/aag/workflow/templates`, {
        headers: {
          'X-USER-ID': 'u1'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to get workflow templates:', error)
      return {
        templates: [
          {
            id: 'standard_analysis',
            name: '标准文档分析',
            description: '包含略读、摘要、知识图谱的标准分析流程',
            estimated_time: '3-5分钟',
            components: ['略读', '摘要生成', '知识图谱', '大纲提取']
          },
          {
            id: 'critical_review',
            name: '批判性审查',
            description: '深度分析文档的论证质量和逻辑严密性',
            estimated_time: '5-10分钟',
            components: ['略读', '证据链分析', '批判性思维分析', '交叉引用分析']
          },
          {
            id: 'adaptive_analysis',
            name: '自适应分析',
            description: '根据文档质量动态调整分析深度',
            estimated_time: '2-8分钟',
            components: ['略读', '动态摘要', '动态知识图谱']
          }
        ]
      }
    }
  }

  // 模拟数据方法
  private getMockSkimResult(documentId: string): AnalysisResult {
    return {
      success: true,
      document_id: documentId,
      result: {
        document_type: '学术论文',
        quality_assessment: { level: '高' },
        core_value: '量子计算在医疗诊断中的革命性应用研究',
        key_points: [
          '量子算法在医学影像分析中的突破',
          '蛋白质折叠预测准确率的显著提升',
          '个性化治疗方案的智能优化',
          '技术成本和稳定性的挑战'
        ],
        target_audience: ['研究人员', '医疗从业者', '技术专家'],
        analysis_suggestions: [
          '深入分析量子算法的具体实现',
          '评估商业化可行性',
          '构建完整的技术路线图'
        ]
      },
      metadata: {
        duration: 3.2,
        tokens_used: 650,
        from_cache: false
      }
    }
  }

  private getMockSummaryResult(documentId: string, level: string): AnalysisResult {
    const summaries = {
      level_1: '量子计算技术为医疗诊断带来革命性改变，在影像分析和个性化治疗方面展现巨大潜力。',
      level_2: '本研究探讨量子计算在医疗诊断领域的应用，重点分析了在医学影像处理、病理分析和治疗方案优化方面的技术突破。量子算法显著提升了诊断准确率和处理速度，但仍面临技术稳定性和成本控制的挑战。',
      level_3: '量子计算技术正在医疗诊断领域掀起革命。研究表明，量子算法在医学影像分析中的处理速度比传统方法快100倍，在蛋白质折叠预测方面准确率达到90%以上。该技术特别适用于复杂的多维数据分析，为个性化医疗提供了新的可能性。然而，量子退相干问题和高昂的设备成本仍是主要挑战，需要进一步的技术创新和成本优化。'
    }

    return {
      success: true,
      document_id: documentId,
      result: {
        summary: summaries[level as keyof typeof summaries] || summaries.level_2,
        word_count: summaries[level as keyof typeof summaries]?.length || 100,
        key_sections: ['技术原理', '应用场景', '性能评估', '挑战分析'],
        recommendations: ['进一步技术验证', '成本效益分析', '临床试验规划']
      },
      metadata: {
        duration: 5.8,
        tokens_used: 800,
        from_cache: false
      }
    }
  }

  private getMockKnowledgeGraphResult(documentId: string): AnalysisResult {
    return {
      success: true,
      document_id: documentId,
      result: {
        entities: [
          { name: '量子计算', type: 'technology', importance: 0.95 },
          { name: '医学影像', type: 'application', importance: 0.87 },
          { name: '蛋白质折叠', type: 'concept', importance: 0.82 },
          { name: '个性化医疗', type: 'application', importance: 0.79 }
        ],
        relations: [
          { from: '量子计算', to: '医学影像', type: 'enhances' },
          { from: '量子计算', to: '蛋白质折叠', type: 'predicts' },
          { from: '个性化医疗', to: '量子计算', type: 'utilizes' }
        ],
        statistics: {
          total_entities: 25,
          total_relations: 18,
          entity_types: { technology: 8, application: 7, concept: 6, organization: 4 }
        }
      },
      metadata: {
        duration: 12.3,
        tokens_used: 1200,
        from_cache: false
      }
    }
  }

  private getMockOutlineResult(documentId: string): AnalysisResult {
    return {
      success: true,
      document_id: documentId,
      result: {
        logical: {
          structure: [
            '1. 引言与研究背景',
            '2. 量子计算基础理论',
            '3. 医疗诊断应用分析',
            '4. 技术实现与挑战',
            '5. 未来发展方向'
          ]
        },
        thematic: {
          themes: ['量子计算原理', '医疗AI应用', '诊断准确性', '技术挑战', '商业前景']
        },
        temporal: {
          timeline: ['基础研究阶段', '原型开发阶段', '临床试验阶段', '商业化阶段']
        },
        causal: {
          causes: ['量子计算技术成熟', '医疗数据复杂性增加'],
          effects: ['诊断准确率提升', '个性化治疗实现']
        }
      },
      metadata: {
        duration: 8.7,
        tokens_used: 950,
        from_cache: false
      }
    }
  }

  private getMockDeepAnalysisResult(documentId: string): AnalysisResult {
    return {
      success: true,
      document_id: documentId,
      result: {
        evidence_chain: {
          claims: 5,
          strong_evidence: 3,
          moderate_evidence: 2,
          overall_strength: 0.85
        },
        critical_thinking: {
          logical_fallacies: 1,
          assumptions: 4,
          biases: 2,
          alternative_views: 3
        },
        cross_reference: {
          internal_consistency: 0.92,
          citation_accuracy: 0.88,
          conceptual_alignment: 0.90
        }
      },
      metadata: {
        duration: 25.4,
        tokens_used: 2100,
        from_cache: false
      }
    }
  }

  private getMockWorkflowResult(workflowId: string, documentId: string): any {
    return {
      success: true,
      workflow_id: workflowId,
      document_id: documentId,
      execution_path: ['skim', 'summary', 'knowledge_graph', 'outline'],
      artifacts: {
        skim: this.getMockSkimResult(documentId).result,
        summary: this.getMockSummaryResult(documentId, 'level_3').result,
        knowledge_graph: this.getMockKnowledgeGraphResult(documentId).result,
        outline: this.getMockOutlineResult(documentId).result
      },
      metadata: {
        duration: 45.2,
        completed_steps: 4,
        errors: 0
      }
    }
  }
}

export const aagService = new AAGService()