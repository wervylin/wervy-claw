FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY src/ ./src/
COPY config/ ./config/
COPY .env .

# 设置环境变量
ENV COZE_WORKSPACE_PATH=/app
ENV COZE_PROJECT_TYPE=agent
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 创建日志目录
RUN mkdir -p /tmp/work/logs/bypass

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# 启动命令
CMD ["python", "src/main.py", "-m", "http", "-p", "5000"]
