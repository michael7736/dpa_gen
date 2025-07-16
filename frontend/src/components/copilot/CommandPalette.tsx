'use client'

import { useState, useEffect } from 'react'
import { FiSearch, FiFile, FiBarChart, FiEdit3, FiDownload, FiActivity } from 'react-icons/fi'

interface Command {
  id: string
  title: string
  description: string
  category: string
  icon: React.ReactNode
  shortcut?: string
  action: () => void
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  const commands: Command[] = [
    {
      id: 'analyze',
      title: '分析这篇文档的核心论点',
      description: '执行深度分析，识别主要观点和论证结构',
      category: '最近使用',
      icon: <FiBarChart size={16} />,
      action: () => console.log('分析核心论点')
    },
    {
      id: 'compare',
      title: '对比最近上传的两篇论文',
      description: '比较不同文档的观点和数据',
      category: '最近使用',
      icon: <FiFile size={16} />,
      action: () => console.log('对比论文')
    },
    {
      id: 'cmd-analyze',
      title: '/analyze - 执行深度分析',
      description: '对当前文档进行全面的深度分析',
      category: '可用命令',
      icon: <FiBarChart size={16} />,
      shortcut: '/analyze',
      action: () => console.log('执行深度分析')
    },
    {
      id: 'cmd-search',
      title: '/search - 搜索相关内容',
      description: '在文档库中搜索相关内容和概念',
      category: '可用命令',
      icon: <FiSearch size={16} />,
      shortcut: '/search',
      action: () => console.log('搜索内容')
    },
    {
      id: 'cmd-summary',
      title: '/summary - 生成摘要',
      description: '为当前文档生成不同级别的摘要',
      category: '可用命令',
      icon: <FiEdit3 size={16} />,
      shortcut: '/summary',
      action: () => console.log('生成摘要')
    },
    {
      id: 'cmd-graph',
      title: '/graph - 构建知识图谱',
      description: '从文档中提取实体和关系，构建知识图谱',
      category: '可用命令',
      icon: <FiActivity size={16} />,
      shortcut: '/graph',
      action: () => console.log('构建知识图谱')
    },
    {
      id: 'cmd-think',
      title: '/think - 批判性思维分析',
      description: '评估论证质量，识别逻辑漏洞和偏见',
      category: '可用命令',
      icon: <FiActivity size={16} />,
      shortcut: '/think',
      action: () => console.log('批判性思维分析')
    },
    {
      id: 'cmd-export',
      title: '/export - 导出分析结果',
      description: '将分析结果导出为PDF或Word格式',
      category: '可用命令',
      icon: <FiDownload size={16} />,
      shortcut: '/export',
      action: () => console.log('导出结果')
    }
  ]

  const filteredCommands = commands.filter(cmd =>
    cmd.title.toLowerCase().includes(search.toLowerCase()) ||
    cmd.description.toLowerCase().includes(search.toLowerCase())
  )

  const groupedCommands = filteredCommands.reduce((groups, cmd) => {
    const category = cmd.category
    if (!groups[category]) {
      groups[category] = []
    }
    groups[category].push(cmd)
    return groups
  }, {} as Record<string, Command[]>)

  useEffect(() => {
    if (!isOpen) {
      setSearch('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  useEffect(() => {
    setSelectedIndex(0)
  }, [search])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (filteredCommands[selectedIndex]) {
        filteredCommands[selectedIndex].action()
        onClose()
      }
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-20 z-50">
      <div className="bg-gray-800 rounded-lg border border-gray-700 w-full max-w-2xl shadow-2xl">
        {/* 搜索输入 */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <FiSearch className="text-gray-400" size={20} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入命令或问题..."
              className="flex-1 bg-transparent text-gray-200 text-lg outline-none placeholder-gray-400"
              autoFocus
            />
          </div>
        </div>

        {/* 命令列表 */}
        <div className="max-h-96 overflow-y-auto">
          {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
            <div key={category}>
              {/* 分类标题 */}
              <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide bg-gray-750">
                {category}
              </div>
              
              {/* 命令项 */}
              {categoryCommands.map((command, index) => {
                const globalIndex = filteredCommands.indexOf(command)
                const isSelected = globalIndex === selectedIndex
                
                return (
                  <div
                    key={command.id}
                    onClick={() => {
                      command.action()
                      onClose()
                    }}
                    className={`px-4 py-3 cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-600' : 'hover:bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`${isSelected ? 'text-white' : 'text-gray-400'}`}>
                          {command.icon}
                        </div>
                        <div>
                          <div className={`text-sm font-medium ${
                            isSelected ? 'text-white' : 'text-gray-200'
                          }`}>
                            {command.title}
                          </div>
                          <div className={`text-xs ${
                            isSelected ? 'text-blue-100' : 'text-gray-400'
                          }`}>
                            {command.description}
                          </div>
                        </div>
                      </div>
                      {command.shortcut && (
                        <div className={`text-xs px-2 py-1 rounded ${
                          isSelected 
                            ? 'bg-blue-700 text-blue-100' 
                            : 'bg-gray-700 text-gray-300'
                        }`}>
                          {command.shortcut}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ))}
        </div>

        {filteredCommands.length === 0 && (
          <div className="p-8 text-center text-gray-400">
            <div className="text-lg mb-2">没有找到相关命令</div>
            <div className="text-sm">尝试使用不同的关键词搜索</div>
          </div>
        )}

        {/* 底部提示 */}
        <div className="px-4 py-3 border-t border-gray-700 bg-gray-750">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <div className="flex items-center space-x-4">
              <span>↑↓ 导航</span>
              <span>⏎ 选择</span>
              <span>esc 关闭</span>
            </div>
            <span>快速命令面板</span>
          </div>
        </div>
      </div>
    </div>
  )
}