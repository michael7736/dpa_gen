"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function TestApiPage() {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const testApi = async () => {
    setLoading(true)
    setResult(null)
    
    try {
      // 直接使用fetch API，绕过axios
      const response = await fetch('http://localhost:8200/api/v1/projects?page=1&page_size=10', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-USER-ID': 'u1'
        }
      })
      
      const data = await response.json()
      
      setResult({
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        data: data
      })
    } catch (error: any) {
      setResult({
        error: true,
        message: error.message,
        stack: error.stack
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">API测试页面（原生Fetch）</h1>
      
      <Button onClick={testApi} disabled={loading}>
        {loading ? '测试中...' : '测试项目API'}
      </Button>
      
      {result && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>测试结果</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded overflow-auto text-xs">
              {JSON.stringify(result, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}