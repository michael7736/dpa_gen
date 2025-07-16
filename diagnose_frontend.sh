#!/bin/bash

echo "🔍 诊断前端问题..."
echo ""

# 检查前端是否运行
echo "1. 检查前端服务："
if curl -s http://localhost:8031 > /dev/null; then
    echo "✅ 前端服务运行中 (端口 8031)"
else
    echo "❌ 前端服务未运行"
fi

# 检查API是否运行
echo ""
echo "2. 检查后端API："
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ 后端API运行中 (端口 8001)"
else
    echo "❌ 后端API未运行"
fi

# 检查认知API健康状态
echo ""
echo "3. 检查认知API健康状态："
HEALTH_RESPONSE=$(curl -s -H "X-USER-ID: u1" http://localhost:8001/api/v1/cognitive/health)
if [ $? -eq 0 ]; then
    echo "✅ 认知API响应正常"
    echo "   响应: $(echo $HEALTH_RESPONSE | head -c 100)..."
else
    echo "❌ 认知API无响应"
fi

echo ""
echo "📋 建议："
echo "1. 清除浏览器缓存并强制刷新 (Ctrl+Shift+R)"
echo "2. 直接访问: http://localhost:8031/cognitive"
echo "3. 检查浏览器控制台错误信息"
echo "4. 如果还有问题，查看前端日志: tail -f frontend/frontend.log"