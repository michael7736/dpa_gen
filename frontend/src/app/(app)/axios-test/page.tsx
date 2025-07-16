"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import api from "@/services/api"
import axios from "axios"

export default function AxiosTestPage() {
  const [results, setResults] = useState<any[]>([])

  const addResult = (name: string, data: any) => {
    setResults(prev => [...prev, { name, data, timestamp: new Date().toISOString() }])
  }

  const testWithConfiguredAxios = async () => {
    try {
      addResult("配置的Axios - 开始", { url: "/api/v1/projects" })
      const response = await api.get("/api/v1/projects", {
        params: { page: 1, page_size: 10 }
      })
      addResult("配置的Axios - 成功", response.data)
    } catch (error: any) {
      addResult("配置的Axios - 错误", {
        message: error.message,
        code: error.code,
        response: error.response?.data,
        status: error.response?.status,
        isAxiosError: error.isAxiosError,
        stack: error.stack?.split('\n').slice(0, 5)
      })
    }
  }

  const testWithPlainAxios = async () => {
    try {
      addResult("原生Axios - 开始", { url: "http://localhost:8200/api/v1/projects" })
      const response = await axios.get("http://localhost:8200/api/v1/projects", {
        params: { page: 1, page_size: 10 },
        headers: {
          'X-USER-ID': 'u1',
          'Content-Type': 'application/json'
        }
      })
      addResult("原生Axios - 成功", response.data)
    } catch (error: any) {
      addResult("原生Axios - 错误", {
        message: error.message,
        code: error.code,
        response: error.response?.data,
        status: error.response?.status
      })
    }
  }

  const testDirectFetch = async () => {
    try {
      addResult("Direct Fetch - 开始", { url: "http://localhost:8200/api/v1/projects" })
      const response = await fetch("http://localhost:8200/api/v1/projects?page=1&page_size=10", {
        headers: {
          'X-USER-ID': 'u1',
          'Content-Type': 'application/json'
        }
      })
      const data = await response.json()
      addResult("Direct Fetch - 结果", {
        status: response.status,
        data: data
      })
    } catch (error: any) {
      addResult("Direct Fetch - 错误", {
        message: error.message
      })
    }
  }

  const clearResults = () => setResults([])

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Axios测试页面</h1>
      
      <div className="flex gap-4 mb-6 flex-wrap">
        <Button onClick={testWithConfiguredAxios}>测试配置的Axios</Button>
        <Button onClick={testWithPlainAxios}>测试原生Axios</Button>
        <Button onClick={testDirectFetch}>测试Direct Fetch</Button>
        <Button variant="outline" onClick={clearResults}>清空结果</Button>
      </div>

      <div className="space-y-4">
        {results.map((result, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle className="text-lg">
                {result.name}
                <span className="text-sm text-muted-foreground ml-2">
                  {new Date(result.timestamp).toLocaleTimeString()}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-muted p-4 rounded overflow-auto text-xs max-h-96">
                {JSON.stringify(result.data, null, 2)}
              </pre>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}