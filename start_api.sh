#!/bin/bash
# 启动DPA API服务

echo "启动DPA智能知识引擎API服务..."

# 检查端口是否被占用
if lsof -Pi :8200 -sTCP:LISTEN -t >/dev/null ; then
    echo "端口8200已被占用，检查端口8201..."
    if lsof -Pi :8201 -sTCP:LISTEN -t >/dev/null ; then
        echo "端口8201也被占用，使用端口8202..."
        PORT=8202
    else
        PORT=8201
    fi
else
    PORT=8200
fi

# 激活conda环境
echo "激活conda环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate dpa_gen

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动服务
echo "在端口 $PORT 启动服务..."
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --reload

# 如果需要后台运行，使用以下命令：
# nohup uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --reload > api.log 2>&1 &
# echo "API服务已在后台启动，PID: $!"
# echo "查看日志: tail -f api.log"