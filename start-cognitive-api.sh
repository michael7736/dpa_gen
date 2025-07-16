#!/bin/bash

# DPA认知系统API启动脚本
# 启动集成了V3认知系统的完整API服务

set -e

echo "🚀 启动DPA认知系统API..."
echo "=================================="

# 检查当前目录
if [ ! -f "src/api/main.py" ]; then
    echo "❌ 错误: 请在DPA项目根目录下运行此脚本"
    exit 1
fi

# 检查环境文件
if [ ! -f ".env" ]; then
    echo "❌ 错误: .env文件不存在，请先配置环境变量"
    echo "   可以从env.template复制: cp env.template .env"
    exit 1
fi

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python &> /dev/null; then
    echo "❌ 错误: Python未找到"
    exit 1
fi

echo "✅ Python版本: $(python --version)"

# 检查依赖包
echo "🔍 检查关键依赖..."
required_packages=("fastapi" "uvicorn" "langchain" "langgraph" "qdrant-client" "neo4j")

for package in "${required_packages[@]}"; do
    if python -c "import $package" 2>/dev/null; then
        echo "✅ $package"
    else
        echo "❌ 缺少依赖: $package"
        echo "   请运行: pip install -r requirements.txt"
        exit 1
    fi
done

# 检查环境变量
echo "🔍 检查环境配置..."
source .env

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  警告: OPENAI_API_KEY未设置，认知系统将使用模拟模式"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ 错误: DATABASE_URL未配置"
    exit 1
fi

echo "✅ 环境配置检查完成"

# 启动API服务器
echo ""
echo "🧠 启动认知系统API服务器..."
echo "   - 后端地址: http://localhost:8001"
echo "   - 前端地址: http://localhost:8031"
echo "   - API文档: http://localhost:8001/docs"
echo "   - V3认知系统: http://localhost:8001/api/v1/cognitive/*"
echo "   - Conda环境: dpa_gen"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 检查conda环境
if [[ "$CONDA_DEFAULT_ENV" != "dpa_gen" ]]; then
    echo "⚠️  警告: 当前不在dpa_gen环境中"
    echo "   请先激活环境: conda activate dpa_gen"
fi

# 设置环境变量
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# 启动服务器在8001端口
python -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload \
    --log-level info \
    --access-log