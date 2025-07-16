#!/bin/bash
# MVP快速启动脚本

echo "🚀 启动DPA MVP系统..."
echo "================================"

# 检查conda环境
if ! conda info --envs | grep -q "dpa_gen"; then
    echo "❌ 未找到dpa_gen环境，请先运行: conda env create -f environment.yml"
    exit 1
fi

# 激活环境
echo "📦 激活conda环境..."
eval "$(conda shell.bash hook)"
conda activate dpa_gen

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，复制模板..."
    cp env.template .env
    echo "📝 请编辑.env文件配置数据库连接和API密钥"
    exit 1
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p data/{uploads,processed,cache,logs}
mkdir -p memory-bank

# 检查数据库连接
echo "🔍 检查数据库连接..."
python scripts/test_config.py
if [ $? -ne 0 ]; then
    echo "❌ 数据库连接失败，请检查配置"
    exit 1
fi

# 初始化数据库（如果需要）
echo "🗄️  初始化数据库..."
python scripts/setup_databases.py

# 启动API服务
echo "🌐 启动API服务..."
echo "================================"
echo "📍 API文档: http://localhost:8000/docs"
echo "📍 健康检查: http://localhost:8000/health"
echo "================================"

# 使用uvicorn启动
uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info