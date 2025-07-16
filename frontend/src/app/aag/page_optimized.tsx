'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { debounce } from 'lodash'

// 性能优化：动态导入大型组件
const AnalysisPanel = dynamic(
  () => import('@/components/aag/AnalysisPanel'),
  { 
    loading: () => <div className="animate-pulse bg-gray-200 h-96 rounded-lg" />,
    ssr: false 
  }
)

// 错误边界组件
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('AAG页面错误:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">出错了</h2>
            <p className="text-gray-600 mb-4">页面加载失败，请刷新重试</p>
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              刷新页面
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// 加载骨架屏组件
const LoadingSkeleton = () => (
  <div className="animate-pulse">
    <div className="h-16 bg-gray-200 rounded mb-4"></div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="h-64 bg-gray-200 rounded"></div>
      <div className="h-64 bg-gray-200 rounded"></div>
      <div className="h-64 bg-gray-200 rounded"></div>
    </div>
  </div>
)

export default function OptimizedAAGPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [analysisData, setAnalysisData] = useState(null)
  
  // 性能监控
  useEffect(() => {
    if (typeof window !== 'undefined' && window.performance) {
      const perfData = {
        navigation: performance.getEntriesByType('navigation')[0],
        paint: performance.getEntriesByType('paint'),
        memory: performance.memory ? {
          used: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
          total: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB'
        } : null
      }
      console.log('AAG页面性能数据:', perfData)
    }
  }, [])

  // 防抖搜索
  const debouncedSearch = useMemo(
    () => debounce((query: string) => {
      console.log('搜索:', query)
      // 搜索逻辑
    }, 300),
    []
  )

  // 优化的事件处理
  const handleAnalysisStart = useCallback(() => {
    setIsLoading(true)
    // 分析逻辑
    setTimeout(() => {
      setIsLoading(false)
      setAnalysisData({ status: 'completed' })
    }, 1000)
  }, [])

  // 模拟加载完成
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 500)
    return () => clearTimeout(timer)
  }, [])

  if (isLoading) {
    return <LoadingSkeleton />
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* 优化后的AAG内容 */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <h1 className="text-xl font-bold">AAG 智能分析引擎</h1>
              <div className="flex items-center space-x-4">
                <input
                  type="search"
                  placeholder="搜索..."
                  onChange={(e) => debouncedSearch(e.target.value)}
                  className="px-3 py-1 border rounded-md"
                />
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* 延迟加载的分析面板 */}
          <AnalysisPanel onStart={handleAnalysisStart} data={analysisData} />
        </main>
      </div>
    </ErrorBoundary>
  )
}