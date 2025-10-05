# Hailo8 Runtime Container
FROM ubuntu:22.04

# 设置非交互模式
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    build-essential \
    curl \
    wget \
    git \
    # Python环境
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3.10-venv \
    # 内核编译工具 (用于驱动编译)
    linux-headers-generic \
    make \
    gcc \
    dkms \
    kmod \
    # 系统工具
    kmod \
    pciutils \
    usbutils \
    # 网络工具
    netcat-openbsd \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/*

# 创建Python虚拟环境
RUN python3.10 -m venv /opt/hailo_venv
ENV PATH="/opt/hailo_venv/bin:$PATH"

# 升级pip并安装Python依赖
RUN pip install --upgrade pip setuptools wheel

# 复制requirements文件并安装Python包
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制API代码
COPY api/ ./api/
COPY scripts/ ./scripts/

# 设置脚本权限
RUN chmod +x scripts/*.sh

# 创建必要的目录
RUN mkdir -p /app/models /app/logs /app/temp

# 设置环境变量
ENV HAILO_MODEL_PATH=/app/models
ENV HAILO_LOG_PATH=/app/logs
ENV HAILO_API_HOST=0.0.0.0
ENV HAILO_API_PORT=8000
ENV HAILO_GRPC_PORT=50051

# 创建非root用户
RUN groupadd -r hailo && useradd -r -g hailo hailo
RUN chown -R hailo:hailo /app /opt/hailo_venv
USER hailo

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD scripts/health_check.sh

# 暴露端口
EXPOSE 8000 50051

# 启动命令
CMD ["/opt/hailo_venv/bin/python", "api/main.py"]