"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useStore } from "@/store/useStore"

const menuItems = [
  { name: '项目管理', href: '/projects' },
  { name: '文档管理', href: '/documents' },
  { name: '智能问答', href: '/chat' },
  { name: '认知对话', href: '/cognitive' },
  { name: '知识图谱', href: '/knowledge-graph' },
  { name: '设置', href: '/settings' },
]

export function SimpleSidebar() {
  const pathname = usePathname()
  const { isSidebarOpen } = useStore()

  if (!isSidebarOpen) return null

  return (
    <div 
      style={{
        position: 'fixed',
        left: 0,
        top: '64px',
        width: '256px',
        height: 'calc(100vh - 64px)',
        backgroundColor: '#ffffff',
        borderRight: '1px solid #e5e7eb',
        padding: '16px',
        zIndex: 40
      }}
    >
      <div style={{ marginBottom: '16px' }}>
        <Link 
          href="/projects/new"
          style={{
            display: 'block',
            width: '100%',
            padding: '8px 16px',
            backgroundColor: '#4f46e5',
            color: 'white',
            textAlign: 'center',
            borderRadius: '6px',
            textDecoration: 'none',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          + 新建项目
        </Link>
      </div>

      <nav>
        {menuItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                display: 'block',
                padding: '8px 12px',
                marginBottom: '4px',
                borderRadius: '6px',
                textDecoration: 'none',
                fontSize: '14px',
                color: isActive ? '#111827' : '#6b7280',
                backgroundColor: isActive ? '#f3f4f6' : 'transparent',
                fontWeight: isActive ? '500' : '400'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = '#f9fafb'
                  e.currentTarget.style.color = '#111827'
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent'
                  e.currentTarget.style.color = '#6b7280'
                }
              }}
            >
              {item.name}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}