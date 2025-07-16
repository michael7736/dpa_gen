#!/bin/bash

echo "🚀 启动 DPA AI副驾驶 Demo"
echo "================================"

# 检查前端依赖
echo "📦 检查前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端开发服务器
echo "🎨 启动前端服务器 (端口 8230)..."
npm run dev -- --port 8230 &
FRONTEND_PID=$!

# 等待前端服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 打开浏览器
echo "🌐 打开浏览器..."
if command -v open >/dev/null 2>&1; then
    # macOS
    open "http://localhost:8230/copilot"
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open "http://localhost:8230/copilot"
elif command -v start >/dev/null 2>&1; then
    # Windows
    start "http://localhost:8230/copilot"
fi

echo ""
echo "🎉 Demo 已启动!"
echo "📍 访问地址: http://localhost:8230/copilot"
echo ""
echo "✨ 特色功能:"
echo "  • AI副驾驶对话界面"
echo "  • 智能文档分析展示"
echo "  • 命令面板 (Cmd+K)"
echo "  • 可扩展的AI助手面板"
echo ""
echo "💡 快捷键:"
echo "  • Cmd+K / Ctrl+K: 打开命令面板"
echo "  • 回车: 发送消息"
echo "  • Shift+回车: 换行"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
wait $FRONTEND_PID