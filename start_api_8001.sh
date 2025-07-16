#!/bin/bash
# 启动DPA API服务在8001端口

echo "DPA智能知识引擎API服务 - 端口8001"
echo "================================"

# 检查并停止占用8001端口的进程
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null ; then
    echo "发现端口8001被占用，正在停止占用进程..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null
    sleep 2
fi

# 激活conda环境
echo "激活conda环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate dpa_gen

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动服务
echo "在端口 8001 启动DPA服务..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload