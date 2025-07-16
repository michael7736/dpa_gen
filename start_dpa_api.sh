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
echo "激活dpa_gen conda环境..."
eval "$(conda shell.bash hook)"
conda activate dpa_gen

# 验证环境
echo "当前Python路径: $(which python)"
echo "当前conda环境: $CONDA_DEFAULT_ENV"

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动服务
echo "在端口 8001 启动DPA服务..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload