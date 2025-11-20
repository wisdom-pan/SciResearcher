# SciResearcher Dockerfile
# 基于 smolagents + Qwen3 + MinerU2.5

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt \
    --extra-index-url https://wheels.myhloli.com

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data/pdfs \
    /app/data/processed \
    /app/data/vector_index \
    /app/data/cache \
    /app/logs

# 暴露端口 (如果需要Web服务)
EXPOSE 8000

# 设置入口点
ENTRYPOINT ["python", "sciresearcher_smolagents.py"]

# 默认命令 (交互模式)
CMD []
