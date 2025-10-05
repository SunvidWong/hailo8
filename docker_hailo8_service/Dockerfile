# Hailo8 Docker 硬件加速服务
# 基于Ubuntu 20.04构建，包含完整的Hailo8运行环境

FROM ubuntu:20.04

# 设置环境变量，避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HAILO_LOG_LEVEL=INFO

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    # Python环境
    python3 \
    python3-pip \
    python3-dev \
    # 编译工具
    build-essential \
    cmake \
    pkg-config \
    # 系统库
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libopencv-dev \
    # PCIe和硬件支持
    pciutils \
    udev \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/*

# 创建Python软链接
RUN ln -s /usr/bin/python3 /usr/bin/python

# 升级pip
RUN python -m pip install --upgrade pip

# 复制Hailo8安装包
COPY De/hailort_4.23.0_amd64.deb /tmp/
COPY De/hailort-pcie-driver_4.23.0_all.deb /tmp/
COPY De/hailort-4.23.0-cp313-cp313-linux_x86_64.whl /tmp/

# 安装Hailo8运行时和驱动
RUN dpkg -i /tmp/hailort_4.23.0_amd64.deb || apt-get install -f -y && \
    dpkg -i /tmp/hailort-pcie-driver_4.23.0_all.deb || apt-get install -f -y && \
    rm -f /tmp/*.deb

# 安装Python依赖
COPY docker_hailo8_service/requirements.txt .
RUN pip install -r requirements.txt

# 安装Hailo8 Python包
RUN pip install /tmp/hailort-4.23.0-cp313-cp313-linux_x86_64.whl && \
    rm -f /tmp/*.whl

# 复制应用代码
COPY docker_hailo8_service/src/ ./src/
COPY docker_hailo8_service/models/ ./models/
COPY docker_hailo8_service/config/ ./config/

# 创建必要的目录
RUN mkdir -p /app/logs /app/temp /app/models

# 设置权限
RUN chmod +x src/main.py

# 创建非root用户（安全考虑）
RUN useradd -m -u 1000 hailo8user && \
    chown -R hailo8user:hailo8user /app

# 切换到非root用户
USER hailo8user

# 暴露API端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["python", "src/main.py"]