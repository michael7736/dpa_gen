'use client'

import { useState } from 'react'

export default function AnalysisResults() {
  const [activeAnalysisTab, setActiveAnalysisTab] = useState('overview')

  const analysisData = {
    overview: {
      title: '核心洞察',
      insights: [
        {
          type: 'trend',
          title: '技术成熟度评估',
          content: '量子计算在医疗领域处于早期应用阶段，预计2025-2030年将迎来突破期',
          confidence: 85
        },
        {
          type: 'opportunity',
          title: '商业机会识别',
          content: '药物分子模拟和个性化医疗是最具潜力的应用方向',
          confidence: 92
        },
        {
          type: 'challenge',
          title: '主要技术挑战',
          content: '量子退相干、错误率控制和成本优化是三大核心挑战',
          confidence: 88
        }
      ]
    },
    outline: {
      dimensions: [
        {
          name: '逻辑结构',
          items: ['引言与背景', '技术原理', '应用案例', '挑战分析', '未来展望']
        },
        {
          name: '主题脉络',
          items: ['量子计算基础', '医疗AI应用', '诊断准确性提升', '商业化路径']
        },
        {
          name: '时间线',
          items: ['2018-2020基础研究', '2021-2023技术突破', '2024-2025应用探索', '2026-2030商业化']
        }
      ]
    },
    knowledge: {
      entities: [
        { name: '量子计算', type: '技术', connections: 12 },
        { name: 'Google', type: '组织', connections: 8 },
        { name: '医学影像诊断', type: '应用', connections: 15 },
        { name: '斯坦福大学', type: '组织', connections: 6 },
        { name: '糖尿病视网膜病变', type: '疾病', connections: 4 }
      ],
      relations: [
        { from: '量子计算', to: '医学影像诊断', type: '应用于' },
        { from: 'Google', to: '糖尿病视网膜病变', type: '研究' },
        { from: '斯坦福大学', to: '皮肤癌检测', type: '开发' }
      ]
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* 分析结果标签栏 */}
      <div className="border-b border-gray-700 bg-gray-800">
        <div className="flex items-center px-4">
          <button
            onClick={() => setActiveAnalysisTab('overview')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeAnalysisTab === 'overview'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            🎯 概览
          </button>
          <button
            onClick={() => setActiveAnalysisTab('outline')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeAnalysisTab === 'outline'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            📋 大纲
          </button>
          <button
            onClick={() => setActiveAnalysisTab('knowledge')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeAnalysisTab === 'knowledge'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            🧠 知识图谱
          </button>
          <button
            onClick={() => setActiveAnalysisTab('deep')}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeAnalysisTab === 'deep'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            🔍 深度分析
          </button>
        </div>
      </div>

      {/* 分析内容区域 */}
      <div className="flex-1 overflow-auto p-6">
        {activeAnalysisTab === 'overview' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-100 mb-4">核心洞察</h2>
            <div className="grid gap-4">
              {analysisData.overview.insights.map((insight, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-gray-200">{insight.title}</h3>
                    <div className="flex items-center text-sm text-gray-400">
                      <span>置信度: {insight.confidence}%</span>
                    </div>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed">{insight.content}</p>
                  <div className="mt-3 flex items-center">
                    <div className="flex-1 bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          insight.type === 'trend' ? 'bg-blue-500' :
                          insight.type === 'opportunity' ? 'bg-green-500' : 'bg-yellow-500'
                        }`}
                        style={{ width: `${insight.confidence}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeAnalysisTab === 'outline' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-100 mb-4">多维度大纲</h2>
            <div className="grid gap-6">
              {analysisData.outline.dimensions.map((dimension, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <h3 className="font-medium text-gray-200 mb-3">{dimension.name}</h3>
                  <div className="space-y-2">
                    {dimension.items.map((item, itemIndex) => (
                      <div key={itemIndex} className="flex items-center text-sm text-gray-300">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 flex-shrink-0" />
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeAnalysisTab === 'knowledge' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-100 mb-4">知识图谱</h2>
            
            {/* 简化的知识图谱可视化 */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="text-center mb-4">
                <div className="text-sm text-gray-400 mb-2">实体网络图</div>
                {/* 这里可以集成D3.js或其他图谱库 */}
                <div className="bg-gray-700 rounded-lg h-64 flex items-center justify-center">
                  <div className="text-gray-400">
                    🧠 知识图谱可视化
                    <div className="text-sm mt-2">
                      {analysisData.knowledge.entities.length} 个实体，
                      {analysisData.knowledge.relations.length} 个关系
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 实体列表 */}
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="font-medium text-gray-200 mb-3">核心实体</h3>
              <div className="grid grid-cols-2 gap-3">
                {analysisData.knowledge.entities.map((entity, index) => (
                  <div key={index} className="bg-gray-700 rounded p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-200 text-sm font-medium">{entity.name}</span>
                      <span className="text-xs text-gray-400">{entity.type}</span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {entity.connections} 个连接
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeAnalysisTab === 'deep' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-100 mb-4">深度分析</h2>
            
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="font-medium text-gray-200 mb-3">证据链分析</h3>
              <div className="space-y-3">
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-sm text-gray-200 font-medium">声明：量子计算可提升医疗诊断准确率</div>
                  <div className="text-xs text-gray-400 mt-1">证据强度: <span className="text-green-400">强</span></div>
                  <div className="text-xs text-gray-300 mt-2">
                    支持证据：Google研究(90.3%准确率)、斯坦福研究(91%准确率)
                  </div>
                </div>
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-sm text-gray-200 font-medium">声明：2025年将实现商业化应用</div>
                  <div className="text-xs text-gray-400 mt-1">证据强度: <span className="text-yellow-400">中</span></div>
                  <div className="text-xs text-gray-300 mt-2">
                    支持证据：技术发展趋势，但缺乏具体时间线证据
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="font-medium text-gray-200 mb-3">批判性思维分析</h3>
              <div className="space-y-3">
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-sm text-gray-200 font-medium">潜在偏见识别</div>
                  <div className="text-xs text-gray-300 mt-2">
                    • 过度依赖大型科技公司的研究结果<br/>
                    • 对技术挑战的严重性估计不足<br/>
                    • 缺乏失败案例的讨论
                  </div>
                </div>
                <div className="bg-gray-700 rounded p-3">
                  <div className="text-sm text-gray-200 font-medium">逻辑漏洞</div>
                  <div className="text-xs text-gray-300 mt-2">
                    从实验室成果直接推断商业化时间，忽略了监管和伦理因素
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}