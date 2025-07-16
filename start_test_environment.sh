#!/bin/bash

# DPA测试环境启动脚本

echo "🚀 启动DPA测试环境..."

# 检查conda环境
if ! command -v conda &> /dev/null; then
    echo "❌ Conda未安装或未配置"
    exit 1
fi

# 激活conda环境
echo "🐍 激活conda环境..."
eval "$(/Users/mdwong001/miniconda3/condabin/conda shell.bash hook)"
conda activate dpa_gen

if [ $? -ne 0 ]; then
    echo "❌ 无法激活conda环境dpa_gen"
    exit 1
fi

echo "✅ Conda环境已激活"

# 检查必要文件
if [ ! -f "src/api/main.py" ]; then
    echo "❌ 未找到API主文件"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo "❌ 未找到前端目录"
    exit 1
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd /Users/mdwong001/Desktop/code/rag/DPA

# 检查端口8200是否被占用
if lsof -i :8200 > /dev/null 2>&1; then
    echo "⚠️ 端口8200已被占用，尝试停止现有服务..."
    pkill -f "uvicorn.*8200" || true
    sleep 2
fi

# 启动后端服务（后台运行）
nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload > backend.log 2>&1 &
BACKEND_PID=$!

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

# 等待后端服务启动
echo "⏳ 等待后端服务启动..."
for i in {1..30}; do
    if curl -s http://localhost:8200/api/v1/health > /dev/null 2>&1; then
        echo "✅ 后端服务已就绪"
        break
    fi
    sleep 1
done

# 检查后端是否启动成功
if ! curl -s http://localhost:8200/api/v1/health > /dev/null 2>&1; then
    echo "❌ 后端服务启动失败"
    cat backend.log
    exit 1
fi

# 启动前端服务
echo "🎨 启动前端服务..."
cd frontend

# 检查端口8230是否被占用
if lsof -i :8230 > /dev/null 2>&1; then
    echo "⚠️ 端口8230已被占用，尝试停止现有服务..."
    pkill -f "next.*8230" || true
    sleep 2
fi

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端服务（后台运行）
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

# 等待前端服务启动
echo "⏳ 等待前端服务启动..."
for i in {1..60}; do
    if curl -s http://localhost:8230 > /dev/null 2>&1; then
        echo "✅ 前端服务已就绪"
        break
    fi
    sleep 1
done

# 检查前端是否启动成功
if ! curl -s http://localhost:8230 > /dev/null 2>&1; then
    echo "❌ 前端服务启动失败"
    cat ../frontend.log
    exit 1
fi

# 创建停止脚本
cat > stop_test_environment.sh << 'EOF'
#!/bin/bash
echo "🛑 停止DPA测试环境..."

# 停止后端服务
if pgrep -f "uvicorn.*8200" > /dev/null; then
    echo "🔧 停止后端服务..."
    pkill -f "uvicorn.*8200"
fi

# 停止前端服务
if pgrep -f "next.*8230" > /dev/null; then
    echo "🎨 停止前端服务..."
    pkill -f "next.*8230"
fi

echo "✅ 测试环境已停止"
EOF

chmod +x stop_test_environment.sh

# 保存PID到文件
echo "$BACKEND_PID" > backend.pid
echo "$FRONTEND_PID" > frontend.pid

echo ""
echo "🎉 DPA测试环境已启动！"
echo "📊 服务状态:"
echo "   后端服务: http://localhost:8200"
echo "   前端服务: http://localhost:8230"
echo "   AAG页面: http://localhost:8230/aag"
echo ""
echo "🔍 测试工具:"
echo "   自动化测试: open test_browser_simple.html"
echo "   WebSocket诊断: open websocket_diagnostic.html"
echo ""
echo "🛑 停止服务: ./stop_test_environment.sh"
echo ""
echo "📋 日志文件:"
echo "   后端日志: backend.log"
echo "   前端日志: frontend.log"
echo ""

# 显示当前状态
echo "🔧 当前服务状态："
echo "后端服务: $(curl -s http://localhost:8200/api/v1/health > /dev/null 2>&1 && echo '✅ 正常' || echo '❌ 异常')"
echo "前端服务: $(curl -s http://localhost:8230 > /dev/null 2>&1 && echo '✅ 正常' || echo '❌ 异常')"

echo ""
echo "🎯 现在可以运行浏览器自动化测试了！"