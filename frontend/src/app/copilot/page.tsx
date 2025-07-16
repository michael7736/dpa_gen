'use client'

import { useState, useEffect } from 'react'
import Layout from '@/components/copilot/Layout'
import Sidebar from '@/components/copilot/Sidebar'
import WorkSpace from '@/components/copilot/WorkSpace'
import AICopilot from '@/components/copilot/AICopilot'
import CommandPalette from '@/components/copilot/CommandPalette'

export default function CopilotPage() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [copilotOpen, setCopilotOpen] = useState(true)

  // 监听快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setCommandPaletteOpen(true)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <Layout>
      <div className="flex h-screen bg-gray-900 text-gray-100">
        {/* 侧边栏 */}
        <Sidebar />
        
        {/* 主工作区 */}
        <WorkSpace />
        
        {/* AI副驾驶面板 */}
        <AICopilot 
          isOpen={copilotOpen}
          onToggle={() => setCopilotOpen(!copilotOpen)}
        />
        
        {/* 命令面板 */}
        <CommandPalette 
          isOpen={commandPaletteOpen}
          onClose={() => setCommandPaletteOpen(false)}
        />
      </div>
    </Layout>
  )
}