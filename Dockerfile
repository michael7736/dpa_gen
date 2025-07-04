# 多阶段构建 - 优化的Docker镜像
# 阶段1：Python依赖构建
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY pyproject.toml .
COPY setup.py .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 升级pip并安装依赖
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 阶段2：运行时镜像
FROM python:3.11-slim

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 -s /bin/bash dpa

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 设置环境变量
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    # 应用配置
    ENVIRONMENT=production \
    LOG_LEVEL=INFO

# 复制应用代码
COPY --chown=dpa:dpa . .

# 创建必要的目录
RUN mkdir -p data/logs data/uploads data/processed data/cache && \
    chown -R dpa:dpa data

# 切换到非root用户
USER dpa

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]