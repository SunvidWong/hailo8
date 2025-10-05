# Hailo8 Docker服务构建和部署指南

本文档详细说明如何构建、部署和配置Hailo8 Docker服务。

## 目录
- [系统要求](#系统要求)
- [构建步骤](#构建步骤)
- [部署配置](#部署配置)
- [环境变量](#环境变量)
- [存储配置](#存储配置)
- [网络配置](#网络配置)
- [故障排除](#故障排除)

## 系统要求

### 硬件要求
- **Hailo8设备**: 支持的Hailo8 AI加速卡
- **内存**: 最少2GB RAM，推荐4GB或更多
- **存储**: 最少10GB可用空间用于镜像和模型文件
- **CPU**: x86_64架构，支持Docker

### 软件要求
- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+, Debian 10+)
- **Docker**: 版本20.10+
- **Docker Compose**: 版本1.29+ (可选)
- **Hailo驱动**: 已安装Hailo8驱动程序

### 驱动安装验证
```bash
# 检查Hailo设备
ls -la /dev/hailo*

# 检查驱动状态
lsmod | grep hailo

# 验证设备信息
cat /proc/hailo/devices
```

## 构建步骤

### 1. 准备构建环境

```bash
# 克隆项目
git clone <repository-url>
cd docker_hailo8_service

# 确保Docker服务运行
sudo systemctl start docker
sudo systemctl enable docker

# 验证Docker安装
docker --version
docker-compose --version
```

### 2. 准备Hailo8运行时文件

将以下文件放置在项目根目录的 `hailo_runtime/` 文件夹中:

```
hailo_runtime/
├── libhailort.so.4.17.0      # Hailo运行时库
├── hailortcli                # Hailo命令行工具
├── hailo_platform.py         # Python平台接口
├── _pyhailort.so             # Python绑定库
└── pyhailort-4.17.0-py3-none-linux_x86_64.whl  # Python包
```

### 3. 构建Docker镜像

#### 基础构建
```bash
# 构建基础镜像
docker build -t hailo8-service:latest .

# 查看构建的镜像
docker images | grep hailo8-service
```

#### 多阶段构建（推荐）
```bash
# 构建优化镜像（更小的体积）
docker build -f Dockerfile.multi-stage -t hailo8-service:optimized .
```

#### 开发版本构建
```bash
# 构建开发版本（包含调试工具）
docker build -f Dockerfile.dev -t hailo8-service:dev .
```

### 4. 验证构建

```bash
# 运行基础健康检查
docker run --rm hailo8-service:latest python -c "import sys; print(f'Python {sys.version}')"

# 验证Hailo库
docker run --rm hailo8-service:latest python -c "import hailo_platform; print('Hailo platform imported successfully')"
```

## 部署配置

### 1. 单容器部署

#### 基础部署
```bash
docker run -d \
  --name hailo8-service \
  --restart unless-stopped \
  --device=/dev/hailo0 \
  -p 8080:8080 \
  -v $(pwd)/models:/app/models:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/temp:/app/temp \
  -e HAILO8_MOCK_MODE=false \
  -e HAILO8_DEVICE_COUNT=1 \
  -e SERVICE_LOG_LEVEL=INFO \
  hailo8-service:latest
```

#### 生产环境部署
```bash
docker run -d \
  --name hailo8-service \
  --restart unless-stopped \
  --device=/dev/hailo0 \
  -p 8080:8080 \
  --memory=2g \
  --cpus=1.0 \
  --security-opt no-new-privileges:true \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  -v $(pwd)/models:/app/models:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/config:/app/config:ro \
  -e HAILO8_MOCK_MODE=false \
  -e HAILO8_DEVICE_COUNT=1 \
  -e SERVICE_LOG_LEVEL=WARNING \
  -e API_RATE_LIMIT_ENABLED=true \
  -e API_RATE_LIMIT_REQUESTS=100 \
  -e API_RATE_LIMIT_WINDOW=60 \
  hailo8-service:latest
```

### 2. Docker Compose部署

#### 简单部署
```bash
# 使用简化配置
docker-compose -f docker-compose.simple.yml up -d

# 查看服务状态
docker-compose -f docker-compose.simple.yml ps
```

#### 完整部署（包含监控）
```bash
# 创建必要的目录
mkdir -p models logs temp config monitoring/data

# 启动所有服务
docker-compose up -d

# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f hailo8-service
```

#### 扩展部署
```bash
# 启动多个Hailo8服务实例
docker-compose up -d --scale hailo8-service=3

# 使用负载均衡
docker-compose -f docker-compose.lb.yml up -d
```

### 3. Kubernetes部署

#### 基础部署
```bash
# 应用Kubernetes配置
kubectl apply -f k8s/

# 查看部署状态
kubectl get pods -l app=hailo8-service

# 查看服务
kubectl get svc hailo8-service
```

#### Helm部署
```bash
# 安装Helm Chart
helm install hailo8-service ./helm/hailo8-service

# 升级部署
helm upgrade hailo8-service ./helm/hailo8-service

# 查看状态
helm status hailo8-service
```

## 环境变量

### 服务配置
```bash
# 基础服务配置
SERVICE_NAME=hailo8-service          # 服务名称
SERVICE_VERSION=1.0.0                # 服务版本
SERVICE_DEBUG=false                  # 调试模式
SERVICE_HOST=0.0.0.0                 # 监听地址
SERVICE_PORT=8080                    # 监听端口
SERVICE_LOG_LEVEL=INFO               # 日志级别

# 工作进程配置
SERVICE_WORKERS=1                    # 工作进程数
SERVICE_MAX_REQUESTS=1000            # 每个进程最大请求数
SERVICE_MAX_REQUESTS_JITTER=100      # 请求数抖动
```

### Hailo8硬件配置
```bash
# 设备配置
HAILO8_MOCK_MODE=false               # 模拟模式
HAILO8_DEVICE_COUNT=1                # 设备数量
HAILO8_DEVICE_IDS=hailo0             # 设备ID列表
HAILO8_DRIVER_PATH=/dev/hailo0       # 驱动路径

# 性能配置
HAILO8_BATCH_SIZE=1                  # 默认批次大小
HAILO8_TIMEOUT_SECONDS=30            # 操作超时
HAILO8_MAX_CONCURRENT_INFERENCES=4   # 最大并发推理数
```

### 模型管理配置
```bash
# 模型路径配置
MODEL_BASE_PATH=/app/models          # 模型基础路径
MODEL_CACHE_ENABLED=true             # 模型缓存
MODEL_CACHE_SIZE=5                   # 缓存模型数量
MODEL_SUPPORTED_FORMATS=hef,onnx     # 支持的模型格式
MODEL_MAX_SIZE_MB=500                # 最大模型文件大小
```

### API服务配置
```bash
# API限制配置
API_MAX_CONCURRENT_REQUESTS=10       # 最大并发请求
API_REQUEST_TIMEOUT=60               # 请求超时
API_MAX_REQUEST_SIZE=50MB            # 最大请求大小
API_RESPONSE_CACHE_TTL=300           # 响应缓存TTL

# 安全配置
API_KEY_REQUIRED=false               # 是否需要API密钥
API_KEY=your-secret-key              # API密钥
API_RATE_LIMIT_ENABLED=true          # 启用速率限制
API_RATE_LIMIT_REQUESTS=100          # 速率限制请求数
API_RATE_LIMIT_WINDOW=60             # 速率限制时间窗口

# CORS配置
API_CORS_ENABLED=true                # 启用CORS
API_CORS_ORIGINS=*                   # 允许的源
API_CORS_METHODS=GET,POST,PUT,DELETE # 允许的方法
```

### 监控配置
```bash
# 监控配置
MONITORING_ENABLED=true              # 启用监控
MONITORING_METRICS_ENABLED=true      # 启用指标收集
MONITORING_HEALTH_CHECK_INTERVAL=30  # 健康检查间隔
MONITORING_STATS_RETENTION_HOURS=24  # 统计数据保留时间
```

### 存储配置
```bash
# 存储路径配置
STORAGE_TEMP_PATH=/app/temp          # 临时文件路径
STORAGE_LOG_PATH=/app/logs           # 日志文件路径
STORAGE_CONFIG_PATH=/app/config      # 配置文件路径

# 日志配置
LOG_ROTATION_ENABLED=true            # 启用日志轮转
LOG_MAX_SIZE_MB=100                  # 日志文件最大大小
LOG_BACKUP_COUNT=5                   # 日志备份数量
LOG_FORMAT=json                      # 日志格式 (json/text)
```

## 存储配置

### 1. 目录结构
```
docker_hailo8_service/
├── models/                          # 模型文件目录
│   ├── yolov5s.hef
│   ├── resnet50.hef
│   └── custom_model.hef
├── logs/                            # 日志文件目录
│   ├── service.log
│   ├── access.log
│   └── error.log
├── temp/                            # 临时文件目录
│   ├── uploads/
│   └── cache/
├── config/                          # 配置文件目录
│   ├── service.yaml
│   └── models.yaml
└── monitoring/                      # 监控数据目录
    ├── prometheus/
    └── grafana/
```

### 2. 卷挂载配置

#### Docker运行时挂载
```bash
# 只读模型目录
-v $(pwd)/models:/app/models:ro

# 可写日志目录
-v $(pwd)/logs:/app/logs:rw

# 临时文件目录
-v $(pwd)/temp:/app/temp:rw

# 配置文件目录
-v $(pwd)/config:/app/config:ro
```

#### Docker Compose挂载
```yaml
volumes:
  - ./models:/app/models:ro
  - ./logs:/app/logs:rw
  - ./temp:/app/temp:rw
  - ./config:/app/config:ro
  - hailo8-data:/app/data
```

#### 命名卷配置
```yaml
volumes:
  hailo8-models:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/models
  
  hailo8-logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/logs
```

### 3. 存储优化

#### SSD存储配置
```bash
# 为模型文件使用SSD存储
-v /ssd/models:/app/models:ro

# 为临时文件使用内存文件系统
--tmpfs /app/temp:rw,noexec,nosuid,size=1g
```

#### 网络存储配置
```yaml
# NFS存储配置
volumes:
  nfs-models:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server,rw
      device: ":/path/to/models"
```

## 网络配置

### 1. 端口配置
```bash
# 默认端口映射
-p 8080:8080                         # API服务端口

# 自定义端口映射
-p 9000:8080                         # 映射到主机9000端口

# 多端口映射
-p 8080:8080 -p 8081:8081           # API和管理端口
```

### 2. 网络模式

#### 桥接网络（默认）
```yaml
networks:
  hailo8-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### 主机网络
```bash
# 使用主机网络模式
docker run --network host hailo8-service:latest
```

#### 自定义网络
```bash
# 创建自定义网络
docker network create --driver bridge hailo8-net

# 使用自定义网络
docker run --network hailo8-net hailo8-service:latest
```

### 3. 服务发现

#### Docker Compose服务发现
```yaml
services:
  hailo8-service:
    # 服务可通过 hailo8-service:8080 访问
    
  client-app:
    environment:
      - HAILO8_SERVICE_URL=http://hailo8-service:8080
```

#### 外部服务发现
```yaml
services:
  hailo8-service:
    external_links:
      - external-service:hailo8-backend
```

## 故障排除

### 1. 常见问题

#### 设备访问问题
```bash
# 检查设备权限
ls -la /dev/hailo*

# 检查用户组
groups $(whoami)

# 添加用户到设备组
sudo usermod -a -G hailo $(whoami)
```

#### 内存不足
```bash
# 检查容器内存使用
docker stats hailo8-service

# 增加内存限制
docker run --memory=4g hailo8-service:latest
```

#### 端口冲突
```bash
# 检查端口占用
netstat -tlnp | grep 8080

# 使用不同端口
docker run -p 9080:8080 hailo8-service:latest
```

### 2. 调试方法

#### 容器调试
```bash
# 进入运行中的容器
docker exec -it hailo8-service /bin/bash

# 查看容器日志
docker logs hailo8-service -f

# 检查容器进程
docker exec hailo8-service ps aux
```

#### 服务调试
```bash
# 检查服务健康状态
curl http://localhost:8080/health

# 查看服务状态
curl http://localhost:8080/status

# 获取详细错误信息
curl -v http://localhost:8080/devices
```

#### 性能调试
```bash
# 监控资源使用
docker stats hailo8-service

# 查看系统资源
htop

# 检查磁盘空间
df -h
```

### 3. 日志分析

#### 日志级别配置
```bash
# 设置详细日志
-e SERVICE_LOG_LEVEL=DEBUG

# 设置JSON格式日志
-e LOG_FORMAT=json
```

#### 日志查看命令
```bash
# 查看实时日志
docker logs hailo8-service -f

# 查看特定时间段日志
docker logs hailo8-service --since="1h"

# 搜索错误日志
docker logs hailo8-service 2>&1 | grep ERROR
```

### 4. 性能优化

#### 资源限制优化
```bash
# CPU限制
--cpus=2.0

# 内存限制
--memory=4g

# 交换限制
--memory-swap=4g
```

#### 并发优化
```bash
# 增加工作进程
-e SERVICE_WORKERS=4

# 增加并发推理数
-e HAILO8_MAX_CONCURRENT_INFERENCES=8
```

#### 缓存优化
```bash
# 启用模型缓存
-e MODEL_CACHE_ENABLED=true
-e MODEL_CACHE_SIZE=10

# 启用响应缓存
-e API_RESPONSE_CACHE_TTL=600
```

这个构建和部署指南提供了完整的配置选项和故障排除方法，可以帮助用户成功部署和运行Hailo8 Docker服务。