"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import api from "@/services/api"
import { API_BASE_URL, API_ENDPOINTS } from "@/lib/config"

export default function DebugPage() {
  const [results, setResults] = useState<any[]>([])

  const addResult = (name: string, status: string, data: any) => {
    setResults(prev => [...prev, { name, status, data, timestamp: new Date().toISOString() }])
  }

  const testHealthCheck = async () => {
    try {
      addResult("Health Check", "开始", { url: `${API_BASE_URL}${API_ENDPOINTS.health}` })
      const response = await api.get(API_ENDPOINTS.health)
      addResult("Health Check", "成功", response.data)
    } catch (error: any) {
      addResult("Health Check", "失败", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        config: {
          url: error.config?.url,
          headers: error.config?.headers,
          baseURL: error.config?.baseURL
        }
      })
    }
  }

  const testProjectsAPI = async () => {
    try {
      addResult("Projects API", "开始", { url: `${API_BASE_URL}${API_ENDPOINTS.projects}` })
      const response = await api.get(API_ENDPOINTS.projects, {
        params: { page: 1, page_size: 10 }
      })
      addResult("Projects API", "成功", response.data)
    } catch (error: any) {
      addResult("Projects API", "失败", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        config: {
          url: error.config?.url,
          headers: error.config?.headers,
          baseURL: error.config?.baseURL
        }
      })
    }
  }

  const testDirectFetch = async () => {
    try {
      addResult("Direct Fetch", "开始", { url: `${API_BASE_URL}/api/v1/health` })
      const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
        headers: {
          'X-USER-ID': 'u1',
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()
      addResult("Direct Fetch", response.ok ? "成功" : "失败", {
        status: response.status,
        data: data
      })
    } catch (error: any) {
      addResult("Direct Fetch", "失败", {
        message: error.message
      })
    }
  }

  const clearResults = () => {
    setResults([])
  }

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">API调试页面</h1>
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>配置信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 font-mono text-sm">
            <p>API_BASE_URL: {API_BASE_URL}</p>
            <p>API_VERSION: v1</p>
            <p>环境: {process.env.NODE_ENV}</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-4 mb-6">
        <Button onClick={testHealthCheck}>测试健康检查</Button>
        <Button onClick={testProjectsAPI}>测试项目API</Button>
        <Button onClick={testDirectFetch}>测试直接Fetch</Button>
        <Button variant="outline" onClick={clearResults}>清空结果</Button>
      </div>

      <div className="space-y-4">
        {results.map((result, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle className="text-lg">
                {result.name} - {result.status}
                <span className="text-sm text-muted-foreground ml-2">
                  {new Date(result.timestamp).toLocaleTimeString()}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted p-4 rounded overflow-auto text-xs">
                {JSON.stringify(result.data, null, 2)}
              </pre>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}