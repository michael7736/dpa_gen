'use client'

import { useState } from 'react'
import { FiFolder, FiFile, FiSearch, FiTag, FiBarChart, FiPlus } from 'react-icons/fi'

const documents = [
  { id: '1', name: '量子计算医疗应用.pdf', type: 'pdf', active: true },
  { id: '2', name: 'AI药物发现研究.pdf', type: 'pdf', active: false },
  { id: '3', name: '医疗AI伦理报告.docx', type: 'docx', active: false },
]

const tags = [
  { name: '医疗', count: 12, color: 'bg-green-500' },
  { name: 'AI', count: 8, color: 'bg-blue-500' },
  { name: '量子计算', count: 5, color: 'bg-purple-500' },
  { name: '药物发现', count: 3, color: 'bg-yellow-500' },
]

const insights = [
  { name: '技术趋势', description: '7个新兴技术方向' },
  { name: '关联分析', description: '15个跨文档关联' },
  { name: '知识图谱', description: '245个实体关系' },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  if (collapsed) {
    return (
      <div className="w-12 bg-gray-800 border-r border-gray-700 flex flex-col items-center py-4 space-y-4">
        <button 
          onClick={() => setCollapsed(false)}
          className="text-gray-400 hover:text-gray-200"
        >
          <FiFolder size={20} />
        </button>
        <FiSearch className="text-gray-400" size={16} />
        <FiTag className="text-gray-400" size={16} />
        <FiBarChart className="text-gray-400" size={16} />
      </div>
    )
  }

  return (
    <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* 文件树区域 */}
      <div className="flex-1 p-4">
        {/* 项目文档 */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300 flex items-center">
              <FiFolder className="mr-2" size={16} />
              项目文档
            </h3>
            <button className="text-gray-400 hover:text-gray-200">
              <FiPlus size={14} />
            </button>
          </div>
          <div className="space-y-1">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className={`flex items-center p-2 rounded cursor-pointer transition-colors ${
                  doc.active 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <FiFile className="mr-2 flex-shrink-0" size={14} />
                <span className="text-sm truncate">{doc.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 搜索 */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center mb-3">
            <FiSearch className="mr-2" size={16} />
            智能搜索
          </h3>
          <div className="relative">
            <input
              type="text"
              placeholder="搜索文档内容..."
              className="w-full bg-gray-700 text-gray-200 text-sm px-3 py-2 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>

        {/* 标签 */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-300 flex items-center mb-3">
            <FiTag className="mr-2" size={16} />
            主题标签
          </h3>
          <div className="space-y-2">
            {tags.map((tag) => (
              <div
                key={tag.name}
                className="flex items-center justify-between p-2 rounded hover:bg-gray-700 cursor-pointer transition-colors"
              >
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full ${tag.color} mr-2`} />
                  <span className="text-sm text-gray-300">{tag.name}</span>
                </div>
                <span className="text-xs text-gray-400">{tag.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 洞察 */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 flex items-center mb-3">
            <FiBarChart className="mr-2" size={16} />
            智能洞察
          </h3>
          <div className="space-y-2">
            {insights.map((insight) => (
              <div
                key={insight.name}
                className="p-2 rounded hover:bg-gray-700 cursor-pointer transition-colors"
              >
                <div className="text-sm text-gray-300 font-medium">{insight.name}</div>
                <div className="text-xs text-gray-400">{insight.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 折叠按钮 */}
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={() => setCollapsed(true)}
          className="text-xs text-gray-400 hover:text-gray-200 flex items-center"
        >
          ← 收起侧边栏
        </button>
      </div>
    </div>
  )
}