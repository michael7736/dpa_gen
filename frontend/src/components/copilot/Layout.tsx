'use client'

import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-900">
      {/* 顶部导航栏 */}
      <header className="border-b border-gray-700 bg-gray-800 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="text-xl font-bold text-blue-400">DPA</div>
              <div className="text-sm text-gray-400">智能知识引擎</div>
            </div>
            <div className="text-sm text-gray-300">
              [AI医疗研究项目]
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* 搜索快捷键提示 */}
            <div className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded">
              ⌘K 打开命令面板
            </div>
            
            {/* 用户菜单 */}
            <div className="flex items-center space-x-2">
              <div className="text-sm text-gray-300">mdwong</div>
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                M
              </div>
            </div>
          </div>
        </div>
      </header>
      
      {children}
    </div>
  )
}