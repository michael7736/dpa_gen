#!/bin/bash

echo "🔍 验证认知对话按钮是否存在..."
echo ""

# 检查侧边栏组件
echo "1. 检查sidebar.tsx组件："
if grep -q "认知对话" frontend/src/components/layout/sidebar.tsx; then
    echo "✅ sidebar.tsx包含'认知对话'菜单项"
    grep -A2 -B2 "认知对话" frontend/src/components/layout/sidebar.tsx
else
    echo "❌ sidebar.tsx未找到'认知对话'菜单项"
fi

echo ""

# 检查认知页面
echo "2. 检查cognitive页面："
if [ -f "frontend/src/app/(app)/cognitive/page.tsx" ]; then
    echo "✅ cognitive/page.tsx文件存在"
    head -10 frontend/src/app/(app)/cognitive/page.tsx | grep -E "(export|function|CognitivePage)"
else
    echo "❌ cognitive/page.tsx文件不存在"
fi

echo ""

# 检查认知服务
echo "3. 检查cognitive服务："
if [ -f "frontend/src/services/cognitive.ts" ]; then
    echo "✅ cognitive.ts服务文件存在"
else
    echo "❌ cognitive.ts服务文件不存在"
fi

echo ""

# 提示
echo "📌 如果仍然看不到认知对话按钮："
echo "   1. 强制刷新浏览器 (Ctrl+Shift+R 或 Cmd+Shift+R)"
echo "   2. 清除浏览器缓存"
echo "   3. 检查浏览器控制台是否有错误"
echo "   4. 确保前端正在运行: http://localhost:8031"
echo ""
echo "🔗 直接访问认知对话页面: http://localhost:8031/cognitive"