"use client"

import { useStore } from "@/store/useStore"
import { 
  FileText, 
  FolderOpen, 
  MessageSquare, 
  Plus,
  Settings,
  Network,
  Brain,
  History,
  Upload
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

interface NavigationItem {
  name: string;
  href: string;
  icon: any;
  badge?: string;
}

const navigation = [
  { name: '项目管理', href: '/projects', icon: FolderOpen },
  { name: '文档管理', href: '/documents', icon: FileText },
  { name: '智能上传 V2', href: '/documents-v2', icon: Upload, badge: 'NEW' },
  { name: '智能问答', href: '/chat', icon: MessageSquare },
  { name: '对话问答', href: '/qa-history', icon: History },
  { name: '认知对话', href: '/cognitive', icon: Brain },
  { name: '知识图谱', href: '/knowledge-graph', icon: Network },
  { name: '设置', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { isSidebarOpen, currentProject } = useStore()

  return (
    <>
      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div 
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 40
          }}
          className="lg:hidden"
          onClick={() => useStore.getState().toggleSidebar()}
        />
      )}
      
      {/* Sidebar */}
      <aside 
        style={{
          position: 'fixed',
          left: 0,
          top: '64px',
          zIndex: 50,
          height: 'calc(100vh - 64px)',
          width: '256px',
          backgroundColor: '#ffffff',
          borderRight: '1px solid #e5e7eb',
          transform: isSidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 200ms'
        }}
      >
        <div style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          padding: '16px',
          gap: '16px'
        }}>
          {/* Current Project */}
          {currentProject && (
            <div style={{
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <h3 style={{
                fontSize: '14px',
                fontWeight: '600',
                color: '#6b7280',
                marginBottom: '4px'
              }}>
                当前项目
              </h3>
              <p style={{ fontWeight: '500' }}>{currentProject.name}</p>
            </div>
          )}

          {/* New Project Button */}
          <Link 
            href="/projects/new"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              borderRadius: '6px',
              backgroundColor: '#6366f1',
              color: 'white',
              padding: '8px 16px',
              fontSize: '14px',
              fontWeight: '500',
              textDecoration: 'none',
              transition: 'background-color 150ms'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#5558e3'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#6366f1'
            }}
          >
            <Plus style={{ width: '16px', height: '16px' }} />
            新建项目
          </Link>

          {/* Navigation */}
          <nav style={{ flex: 1 }}>
            {navigation.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    marginBottom: '4px',
                    fontSize: '14px',
                    fontWeight: isActive ? '500' : '400',
                    textDecoration: 'none',
                    color: isActive ? '#111827' : '#6b7280',
                    backgroundColor: isActive ? '#f3f4f6' : 'transparent',
                    transition: 'all 150ms'
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
                  <Icon style={{ width: '16px', height: '16px', flexShrink: 0 }} />
                  <span style={{ display: 'block', flex: 1 }}>{item.name}</span>
                  {item.badge && (
                    <span style={{
                      fontSize: '10px',
                      fontWeight: '600',
                      backgroundColor: '#ef4444',
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '999px',
                      lineHeight: 1
                    }}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>
        </div>
      </aside>
    </>
  )
}