export default function SimpleTestPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">简单测试页面</h1>
      <p>这是一个静态页面，用于测试基本渲染。</p>
      
      <div className="mt-6 p-4 bg-gray-100 rounded">
        <h2 className="text-xl font-semibold mb-2">API配置信息：</h2>
        <ul className="space-y-1">
          <li>API URL: {process.env.NEXT_PUBLIC_API_URL || '未设置'}</li>
          <li>环境: {process.env.NODE_ENV}</li>
        </ul>
      </div>
    </div>
  )
}