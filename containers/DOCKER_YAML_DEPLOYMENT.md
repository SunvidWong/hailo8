# Docker Compose YAML部署指南

🐳 **使用YAML配置文件部署Hailo8 AI推理服务**

## 📖 什么是Docker Compose YAML？

Docker Compose使用YAML格式（通常命名为`docker-compose.yml`）来定义和配置多容器Docker应用程序。通过一个YAML文件，您可以：

- 定义所有相关的服务（容器）
- 配置网络和数据卷
- 设置环境变量
- 管理服务依赖关系
- 一键启动/停止整个应用栈

## 🎯 为什么选择YAML部署？

✅ **声明式配置**: 清晰描述期望的状态
✅ **版本控制**: 配置文件可以纳入Git管理
✅ **环境一致性**: 开发、测试、生产环境统一配置
✅ **简单部署**: 一条命令启动整个服务栈
✅ **易于维护**: 配置集中管理，修改方便

## 📁 项目中的YAML文件

```
hailo8/containers/
├── 📄 docker-compose.yml           # 主配置文件 (完整功能)
├── 📄 docker-compose.dev.yml       # 开发环境配置
├── 📄 docker-compose.remote.yml    # 生产环境配置
├── 📄 docker-compose.quick.yml     # 快速部署配置
├── 📄 .env                         # 环境变量文件
└── 📄 .env.remote                  # 生产环境变量
```

## 🚀 基本部署流程

### 第1步: 选择YAML配置文件

根据您的需求选择合适的YAML文件：

```bash
# 选项1: 完整功能部署 (推荐生产使用)
docker-compose -f docker-compose.yml up -d

# 选项2: 开发环境部署
docker-compose -f docker-compose.dev.yml up -d

# 选项3: 生产环境部署
docker-compose -f docker-compose.remote.yml up -d

# 选项4: 快速测试部署
docker-compose -f docker-compose.quick.yml up -d
```

### 第2步: 配置环境变量

```bash
# 复制环境变量模板
cp .env.remote .env

# 编辑配置文件
vim .env
```

**关键配置项:**
```bash
DOMAIN=your-domain.com
JWT_SECRET_KEY=your-secret-key
GRAFANA_PASSWORD=your-password
```

### 第3步: 启动服务

```bash
# 使用指定YAML文件启动
docker-compose -f docker-compose.yml up -d

# 查看启动状态
docker-compose ps
```

## 📋 YAML文件详解

### 完整功能配置 - `docker-compose.yml`

```yaml
version: '3.8'  # Docker Compose版本

services:      # 服务定义
  # Hailo8 核心API服务
  hailo-runtime:
    build:                          # 构建配置
      context: ./hailo-runtime      # 构建上下文
      dockerfile: Dockerfile        # Dockerfile名称
    image: hailo8/runtime:latest    # 镜像名称
    container_name: hailo-runtime   # 容器名称
    restart: unless-stopped         # 重启策略
    privileged: true                # 需要加载内核模块

    ports:                          # 端口映射
      - "8000:8000"                 # HTTP API
      - "50051:50051"               # gRPC服务
      - "9090:9090"                 # Prometheus指标

    volumes:                        # 数据卷挂载
      - /dev/hailo0:/dev/hailo0      # Hailo设备
      - ./models:/app/models:ro      # 模型文件(只读)
      - hailo_logs:/app/logs         # 日志存储
      - hailo_temp:/app/temp         # 临时文件

    environment:                    # 环境变量
      - HAILO_API_HOST=0.0.0.0
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379

    depends_on:                     # 服务依赖
      - redis

    healthcheck:                    # 健康检查
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Redis缓存服务
  redis:
    image: redis:7-alpine
    container_name: hailo-redis
    restart: unless-stopped

    ports:
      - "6379:6379"

    volumes:
      - redis_data:/data

    command: redis-server --appendonly yes

    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Web前端服务
  hailo-web-app:
    build:
      context: ./hailo-web-app
      dockerfile: Dockerfile
    image: hailo8/web-app:latest
    container_name: hailo-web-app
    restart: unless-stopped

    ports:
      - "3000:3000"

    environment:
      - REACT_APP_API_URL=http://localhost:8000

    depends_on:
      - hailo-runtime

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # AI服务
  hailo-ai-service:
    build:
      context: ./hailo-ai-service
      dockerfile: Dockerfile
    image: hailo8/ai-service:latest
    container_name: hailo-ai-service
    restart: unless-stopped

    ports:
      - "8080:8080"

    environment:
      - HAILO_API_URL=http://hailo-runtime:8000
      - SERVICE_PORT=8080

    volumes:
      - hailo_data:/app/data

    depends_on:
      - hailo-runtime
      - redis

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    container_name: hailo-nginx
    restart: unless-stopped

    ports:
      - "80:80"
      - "443:443"

    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro

    depends_on:
      - hailo-runtime
      - hailo-web-app

    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 5s
      retries: 3

# 数据卷定义
volumes:
  hailo_models:
    driver: local
  hailo_logs:
    driver: local
  hailo_temp:
    driver: local
  hailo_data:
    driver: local
  redis_data:
    driver: local

# 网络定义
networks:
  default:
    name: hailo8-network
    driver: bridge
```

### 快速部署配置 - `docker-compose.quick.yml`

```yaml
version: '3.8'

services:
  # 简化版Hailo Runtime服务
  hailo-runtime:
    build: ./hailo-runtime
    image: hailo8/runtime:latest
    container_name: hailo-runtime
    restart: unless-stopped
    privileged: true

    ports:
      - "8000:8000"

    volumes:
      - /dev/hailo0:/dev/hailo0
      - ./models:/app/models:ro

    environment:
      - LOG_LEVEL=INFO

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: hailo-redis
    restart: unless-stopped

    ports:
      - "6379:6379"

    volumes:
      - redis_data:/data

    command: redis-server --appendonly yes

  # 简单Web界面
  hailo-web-app:
    build: ./hailo-web-app
    image: hailo8/web-app:latest
    container_name: hailo-web-app
    restart: unless-stopped

    ports:
      - "3000:3000"

    environment:
      - REACT_APP_API_URL=http://localhost:8000

    depends_on:
      - hailo-runtime

volumes:
  redis_data:
    driver: local

networks:
  default:
    name: hailo8-quick-network
    driver: bridge
```

### 开发环境配置 - `docker-compose.dev.yml`

```yaml
version: '3.8'

services:
  # 开发版Hailo Runtime (支持热重载)
  hailo-runtime:
    build:
      context: ./hailo-runtime
      dockerfile: Dockerfile
    image: hailo8/runtime:dev
    container_name: hailo-runtime-dev
    restart: unless-stopped
    privileged: true

    ports:
      - "8000:8000"

    volumes:
      - /dev/hailo0:/dev/hailo0
      - ./hailo-runtime:/app               # 源码挂载
      - ./models:/app/models:ro

    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - RELOAD=true

    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

    depends_on:
      - redis

  # 开发版Web应用 (支持热重载)
  hailo-web-app:
    build:
      context: ./hailo-web-app
      dockerfile: Dockerfile.dev
    image: hailo8/web-app:dev
    container_name: hailo-web-app-dev
    restart: unless-stopped

    ports:
      - "3000:3000"

    volumes:
      - ./hailo-web-app:/app               # 源码挂载
      - /app/node_modules                   # 防止node_modules被覆盖

    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - CHOKIDAR_USEPOLLING=true           # 文件监控

    command: npm start

    depends_on:
      - hailo-runtime

  # Redis开发服务
  redis:
    image: redis:7-alpine
    container_name: hailo-redis-dev
    restart: unless-stopped

    ports:
      - "6379:6379"

    command: redis-server --appendonly yes --save ""

volumes:
  redis_data_dev:
    driver: local

networks:
  default:
    name: hailo8-dev-network
    driver: bridge
```

## 🔧 YAML配置语法详解

### 服务配置语法

```yaml
services:
  service_name:                    # 服务名称
    image: image:tag              # 使用的镜像

    # 构建配置 (如果不使用预构建镜像)
    build:
      context: ./directory       # 构建上下文路径
      dockerfile: Dockerfile     # Dockerfile名称
      args:                      # 构建参数
        - VAR=value

    # 容器配置
    container_name: container_name  # 容器名称
    hostname: hostname               # 主机名
    restart: policy                  # 重启策略 (no/always/on-failure/unless-stopped)

    # 端口映射
    ports:
      - "host_port:container_port"  # 主机端口:容器端口
      - "8080:80"                   # 也可以省略协议
      - "9090:9090/udp"             # UDP端口

    # 数据卷
    volumes:
      - /host/path:/container/path          # 主机路径:容器路径
      - volume_name:/container/path          # 命名卷
      - ./relative/path:/container/path     # 相对路径
      - /host/path:/container/path:ro        # 只读挂载

    # 环境变量
    environment:
      - VAR=value                           # 简单格式
      - VAR2: "complex value"               # 复杂值
    env_file:
      - .env                                # 从文件读取环境变量

    # 网络配置
    networks:
      - network_name                        # 加入网络
    dns:
      - 8.8.8.8                            # DNS服务器

    # 依赖关系
    depends_on:
      - service_name1                       # 依赖的服务
      - service_name2

    # 健康检查
    healthcheck:
      test: ["CMD", "command"]              # 健康检查命令
      interval: 30s                         # 检查间隔
      timeout: 10s                          # 超时时间
      retries: 3                            # 重试次数
      start_period: 60s                     # 启动等待时间

    # 资源限制
    deploy:
      resources:
        limits:                              # 资源上限
          cpus: '2.0'
          memory: 4G
        reservations:                        # 资源预留
          cpus: '1.0'
          memory: 2G
```

### 数据卷语法

```yaml
volumes:
  volume_name:                    # 数据卷名称
    driver: local                  # 驱动类型
    driver_opts:                   # 驱动选项
      type: none
      o: bind
      device: /path/on/host
    external: true                 # 外部数据卷
    labels:                        # 标签
      - "label=value"
```

### 网络语法

```yaml
networks:
  network_name:                   # 网络名称
    driver: bridge                 # 网络驱动 (bridge/overlay/host/none)
    driver_opts:                   # 驱动选项
      com.docker.network.bridge.name: mybridge
    ipam:                          # IP地址管理
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
    external: true                 # 外部网络
    internal: true                 # 内部网络
    labels:                        # 标签
      - "label=value"
```

## 🚀 常用部署命令

### 基本命令

```bash
# 使用指定YAML文件启动服务
docker-compose -f docker-compose.yml up -d

# 启动并显示日志
docker-compose -f docker-compose.yml up

# 停止服务
docker-compose -f docker-compose.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.yml down -v

# 重新构建并启动
docker-compose -f docker-compose.yml up --build -d
```

### 服务管理命令

```bash
# 查看服务状态
docker-compose -f docker-compose.yml ps

# 查看服务日志
docker-compose -f docker-compose.yml logs

# 查看特定服务日志
docker-compose -f docker-compose.yml logs hailo-runtime

# 实时跟踪日志
docker-compose -f docker-compose.yml logs -f

# 重启特定服务
docker-compose -f docker-compose.yml restart hailo-runtime

# 停止特定服务
docker-compose -f docker-compose.yml stop hailo-runtime

# 启动特定服务
docker-compose -f docker-compose.yml start hailo-runtime
```

### 维护命令

```bash
# 拉取最新镜像
docker-compose -f docker-compose.yml pull

# 更新服务
docker-compose -f docker-compose.yml pull
docker-compose -f docker-compose.yml up -d

# 查看资源使用
docker-compose -f docker-compose.yml top

# 执行命令进入容器
docker-compose -f docker-compose.yml exec hailo-runtime bash

# 查看配置
docker-compose -f docker-compose.yml config

# 验证YAML文件
docker-compose -f docker-compose.yml config --quiet
```

## 🔍 环境变量配置

### .env 文件格式

```bash
# 基本配置
DOMAIN=localhost
VERSION=2.0.0
LOG_LEVEL=INFO
DEBUG=false
TZ=Asia/Shanghai

# API配置
HAILO_API_HOST=0.0.0.0
HAILO_API_PORT=8000
HAILO_GRPC_PORT=50051

# 数据库配置
REDIS_URL=redis://redis:6379

# 安全配置
JWT_SECRET_KEY=your-secret-key
GRAFANA_PASSWORD=admin123

# 存储配置
DATA_PATH=./data
MODEL_PATH=./models
```

### 在YAML中使用环境变量

```yaml
services:
  hailo-runtime:
    environment:
      - HAILO_API_HOST=${HAILO_API_HOST}
      - HAILO_API_PORT=${HAILO_API_PORT}
      - LOG_LEVEL=${LOG_LEVEL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - TZ=${TZ}

    volumes:
      - ${DATA_PATH}/models:/app/models:ro
      - ${DATA_PATH}/logs:/app/logs

    ports:
      - "${HAILO_API_PORT}:8000"
      - "${HAILO_GRPC_PORT}:50051"
```

### 变量替换语法

```yaml
# 直接替换
image: hailo8/runtime:${VERSION}

# 带默认值
image: hailo8/runtime:${VERSION:-latest}

# 多个变量组合
environment:
  - API_URL=${DOMAIN}:${HAILO_API_PORT}
```

## 📊 实际部署示例

### 示例1: 开发环境快速部署

```bash
# 1. 选择开发配置
docker-compose -f docker-compose.dev.yml up -d

# 2. 查看启动状态
docker-compose -f docker-compose.dev.yml ps

# 3. 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 4. 访问服务
curl http://localhost:8000/health
```

### 示例2: 生产环境部署

```bash
# 1. 配置环境变量
cp .env.remote .env
vim .env  # 修改域名、密码等

# 2. 启动生产服务
docker-compose -f docker-compose.remote.yml up -d

# 3. 验证部署
docker-compose -f docker-compose.remote.yml ps
curl http://localhost/health

# 4. 检查所有服务
docker-compose -f docker-compose.remote.yml logs
```

### 示例3: 服务扩展部署

```bash
# 1. 扩展AI服务副本
docker-compose -f docker-compose.yml up -d --scale hailo-ai-service=3

# 2. 查看扩展后的状态
docker-compose -f docker-compose.yml ps

# 3. 调整扩展规模
docker-compose -f docker-compose.yml up -d --scale hailo-ai-service=1
```

## 🛠️ 故障排除

### YAML文件语法错误

```bash
# 验证YAML文件语法
docker-compose -f docker-compose.yml config

# 检查详细错误信息
docker-compose -f docker-compose.yml config --verbose
```

### 服务启动失败

```bash
# 查看详细错误日志
docker-compose -f docker-compose.yml logs service-name

# 重新构建镜像
docker-compose -f docker-compose.yml build --no-cache

# 强制重新创建容器
docker-compose -f docker-compose.yml up -d --force-recreate
```

### 端口冲突

```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 修改YAML文件中的端口映射
vim docker-compose.yml

# 重启服务
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml up -d
```

### 资源不足

```bash
# 检查系统资源
free -h
df -h

# 调整资源限制
vim docker-compose.yml

# 重启服务
docker-compose -f docker-compose.yml restart
```

## 📈 高级配置

### 多文件配置

```bash
# 使用多个YAML文件
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# 文件覆盖优先级
# docker-compose.yml (基础) -> docker-compose.override.yml (覆盖)
```

### 配置继承

```yaml
# docker-compose.yml (基础配置)
version: '3.8'
services:
  hailo-runtime:
    build: ./hailo-runtime
    environment:
      - LOG_LEVEL=INFO

# docker-compose.dev.yml (开发配置)
version: '3.8'
services:
  hailo-runtime:
    environment:
      - LOG_LEVEL=DEBUG
    volumes:
      - ./hailo-runtime:/app
    command: uvicorn main:app --reload
```

### 条件部署

```yaml
services:
  hailo-runtime:
    build: ./hailo-runtime
    environment:
      - DEBUG=${DEBUG:-false}

    # 仅在DEBUG=true时挂载源码
    volumes:
      - /dev/hailo0:/dev/hailo0
      - ${DEBUG:+./hailo-runtime:/app}  # 条件挂载
```

---

🎉 **现在您完全掌握了使用Docker Compose YAML文件部署Hailo8的所有知识！**

从简单的快速部署到复杂的生产环境，YAML配置文件提供了强大而灵活的部署能力。选择合适的YAML配置，开始您的Hailo8 AI推理服务部署吧！