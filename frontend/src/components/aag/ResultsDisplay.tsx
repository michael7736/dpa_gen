'use client'

import { useState } from 'react'
import { FiEye, FiDownload, FiShare, FiMaximize2, FiBarChart, FiGitBranch, FiList, FiSearch } from 'react-icons/fi'

interface ResultsDisplayProps {
  results: any
  documentId: string | null
}

export default function ResultsDisplay({ results, documentId }: ResultsDisplayProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const [fullscreen, setFullscreen] = useState(false)

  const tabs = [
    { id: 'overview', name: '概览', icon: <FiEye size={16} /> },
    { id: 'outline', name: '大纲', icon: <FiList size={16} /> },
    { id: 'knowledge', name: '知识图谱', icon: <FiGitBranch size={16} /> },
    { id: 'analysis', name: '深度分析', icon: <FiSearch size={16} /> },
    { id: 'insights', name: '洞察', icon: <FiBarChart size={16} /> }
  ]

  // 模拟数据
  const mockResults = {
    overview: {
      summary: '量子计算技术在医疗诊断领域展现出革命性的潜力，特别是在医学影像分析、病理诊断和个性化治疗方案制定方面。',
      keyPoints: [
        '量子算法可将医学影像处理速度提升100倍',
        '在蛋白质折叠预测方面准确率达到90%以上',
        '量子机器学习在药物分子设计中展现优势',
        '面临量子退相干和成本控制的技术挑战'
      ],
      metrics: {
        relevance: 0.92,
        novelty: 0.85,
        impact: 0.88,
        feasibility: 0.67
      }
    },
    outline: {
      dimensions: [
        {
          name: '逻辑结构',
          items: [
            '1. 引言与研究背景',
            '2. 量子计算基础理论',
            '3. 医疗诊断应用场景',
            '4. 技术实现与挑战',
            '5. 未来发展趋势'
          ]
        },
        {
          name: '主题脉络',
          items: [
            '量子计算原理',
            '医疗AI应用',
            '诊断准确性提升',
            '技术标准化',
            '商业化路径'
          ]
        },
        {
          name: '时间线',
          items: [
            '2018-2020: 基础理论研究',
            '2021-2023: 原型系统开发',
            '2024-2025: 临床试验阶段',
            '2026-2030: 商业化应用'
          ]
        }
      ]
    },
    knowledge: {
      stats: {
        entities: 45,
        relations: 38,
        concepts: 15,
        technologies: 8
      },
      topEntities: [
        { name: '量子计算', type: '技术', connections: 12, importance: 0.95 },
        { name: '医学影像', type: '应用', connections: 8, importance: 0.87 },
        { name: '机器学习', type: '方法', connections: 10, importance: 0.82 },
        { name: '蛋白质折叠', type: '问题', connections: 6, importance: 0.78 }
      ]
    },
    analysis: {
      evidenceChain: {
        claims: 5,
        strongEvidence: 3,
        moderateEvidence: 2,
        weakEvidence: 0,
        overallStrength: 0.85
      },
      criticalThinking: {
        logicalFallacies: 1,
        assumptions: 4,
        biases: 2,
        alternativeViews: 3
      },
      crossReference: {
        internalConsistency: 0.92,
        citationAccuracy: 0.88,
        conceptualAlignment: 0.90
      }
    }
  }

  const renderOverview = () => (
    <div className="space-y-6">
      {/* 核心摘要 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">核心摘要</h3>
        <p className="text-gray-300 leading-relaxed">{mockResults.overview.summary}</p>
      </div>

      {/* 关键要点 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">关键要点</h3>
        <ul className="space-y-2">
          {mockResults.overview.keyPoints.map((point, index) => (
            <li key={index} className="flex items-start space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
              <span className="text-gray-300">{point}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 质量指标 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">质量评估</h3>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(mockResults.overview.metrics).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-gray-400 capitalize">
                {key === 'relevance' ? '相关性' :
                 key === 'novelty' ? '新颖性' :
                 key === 'impact' ? '影响力' : '可行性'}
              </span>
              <div className="flex items-center space-x-2">
                <div className="w-20 bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-300">{(value * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderOutline = () => (
    <div className="space-y-4">
      {mockResults.outline.dimensions.map((dimension, index) => (
        <div key={index} className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-200 mb-3">{dimension.name}</h3>
          <div className="space-y-2">
            {dimension.items.map((item, itemIndex) => (
              <div key={itemIndex} className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                  {itemIndex + 1}
                </div>
                <span className="text-gray-300">{item}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )

  const renderKnowledgeGraph = () => (
    <div className="space-y-6">
      {/* 统计信息 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(mockResults.knowledge.stats).map(([key, value]) => (
          <div key={key} className="bg-gray-800 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-400">{value}</div>
            <div className="text-sm text-gray-400 capitalize">
              {key === 'entities' ? '实体' :
               key === 'relations' ? '关系' :
               key === 'concepts' ? '概念' : '技术'}
            </div>
          </div>
        ))}
      </div>

      {/* 知识图谱可视化占位 */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-200 mb-4">知识网络图</h3>
        <div className="bg-gray-700 rounded-lg h-64 flex items-center justify-center">
          <div className="text-center">
            <FiGitBranch className="mx-auto mb-2 text-gray-400" size={48} />
            <p className="text-gray-400">知识图谱可视化</p>
            <p className="text-sm text-gray-500 mt-1">
              {mockResults.knowledge.stats.entities} 个实体，{mockResults.knowledge.stats.relations} 个关系
            </p>
          </div>
        </div>
      </div>

      {/* 核心实体 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">核心实体</h3>
        <div className="space-y-3">
          {mockResults.knowledge.topEntities.map((entity, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                  {index + 1}
                </div>
                <div>
                  <div className="text-gray-200 font-medium">{entity.name}</div>
                  <div className="text-sm text-gray-400">{entity.type} • {entity.connections} 个连接</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-300">重要性</div>
                <div className="text-blue-400 font-semibold">{(entity.importance * 100).toFixed(0)}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderAnalysis = () => (
    <div className="space-y-6">
      {/* 证据链分析 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">证据链分析</h3>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-sm text-gray-400">声明总数</div>
            <div className="text-xl font-semibold text-gray-200">{mockResults.analysis.evidenceChain.claims}</div>
          </div>
          <div>
            <div className="text-sm text-gray-400">整体强度</div>
            <div className="text-xl font-semibold text-green-400">
              {(mockResults.analysis.evidenceChain.overallStrength * 100).toFixed(0)}%
            </div>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-green-400">强证据</span>
            <span>{mockResults.analysis.evidenceChain.strongEvidence}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-yellow-400">中等证据</span>
            <span>{mockResults.analysis.evidenceChain.moderateEvidence}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-red-400">弱证据</span>
            <span>{mockResults.analysis.evidenceChain.weakEvidence}</span>
          </div>
        </div>
      </div>

      {/* 批判性思维分析 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">批判性思维分析</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-400">逻辑谬误</div>
            <div className="text-lg font-semibold text-red-400">
              {mockResults.analysis.criticalThinking.logicalFallacies}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400">隐含假设</div>
            <div className="text-lg font-semibold text-yellow-400">
              {mockResults.analysis.criticalThinking.assumptions}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400">潜在偏见</div>
            <div className="text-lg font-semibold text-orange-400">
              {mockResults.analysis.criticalThinking.biases}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-400">替代观点</div>
            <div className="text-lg font-semibold text-blue-400">
              {mockResults.analysis.criticalThinking.alternativeViews}
            </div>
          </div>
        </div>
      </div>

      {/* 交叉引用分析 */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-200 mb-3">交叉引用分析</h3>
        <div className="space-y-3">
          {Object.entries(mockResults.analysis.crossReference).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-gray-400">
                {key === 'internalConsistency' ? '内部一致性' :
                 key === 'citationAccuracy' ? '引用准确性' : '概念对齐'}
              </span>
              <div className="flex items-center space-x-2">
                <div className="w-24 bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-300">{(value * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview()
      case 'outline':
        return renderOutline()
      case 'knowledge':
        return renderKnowledgeGraph()
      case 'analysis':
        return renderAnalysis()
      default:
        return <div className="text-center text-gray-400 py-12">选择一个标签页查看分析结果</div>
    }
  }

  if (!documentId) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <div className="text-center">
          <FiEye className="mx-auto mb-4 text-gray-600" size={48} />
          <h3 className="text-lg font-medium text-gray-400 mb-2">选择文档开始分析</h3>
          <p className="text-gray-500">从左侧选择一个文档来查看分析结果</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* 结果标签栏 */}
      <div className="border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
                }`}
              >
                {tab.icon}
                <span>{tab.name}</span>
              </button>
            ))}
          </div>
          
          <div className="flex items-center space-x-2">
            <button className="p-2 text-gray-400 hover:text-gray-200 rounded hover:bg-gray-700">
              <FiDownload size={16} />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-200 rounded hover:bg-gray-700">
              <FiShare size={16} />
            </button>
            <button 
              className="p-2 text-gray-400 hover:text-gray-200 rounded hover:bg-gray-700"
              onClick={() => setFullscreen(!fullscreen)}
            >
              <FiMaximize2 size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* 结果内容 */}
      <div className="flex-1 overflow-auto p-6">
        {renderContent()}
      </div>
    </div>
  )
}