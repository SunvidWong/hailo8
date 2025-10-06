# Docker Compose官方规范说明

## 📖 规范概述

本项目遵循最新的 **Docker Compose Specification** 规范，这是Docker官方推荐的Compose文件格式标准。

## 🔗 官方文档

- **Docker Compose Specification**: https://docs.docker.com/compose/compose-file/
- **Compose文件参考**: https://docs.docker.com/compose/compose-file/compose-file-v3/
- **最佳实践指南**: https://docs.docker.com/compose/

## 📋 规范要点

### 1. 版本声明
```yaml
# 新规范中不再需要显式声明version
# 但为了兼容性，我们使用 version: '3.9'
version: '3.9'
```

### 2. 服务配置规范
```yaml
services:
  service_name:
    # 镜像配置
    image: username/image:tag

    # 构建配置
    build:
      context: ./path
      dockerfile: Dockerfile
      args:
        KEY: "value"

    # 部署配置 (包括GPU)
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

    # 端口配置 - 详细格式
    ports:
      - target: 8000           # 容器内端口
        published: 8000        # 主机端口
        protocol: tcp          # 协议类型
        mode: host            # 发布模式

    # 卷挂载 - 类型化格式
    volumes:
      - type: bind           # 卷类型
        source: ./local      # 源路径
        target: /container   # 目标路径
        read_only: true      # 只读选项

    # 环境变量 - 映射格式
    environment:
      KEY: "value"
      ANOTHER_KEY: "value"
```

### 3. NVIDIA GPU支持规范
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### 4. 健康检查规范
```yaml
healthcheck:
  test: ["CMD", "command", "args"]
  interval: 30s          # 检查间隔
  timeout: 10s           # 超时时间
  retries: 3            # 重试次数
  start_period: 60s     # 启动等待时间
```

### 5. 服务依赖规范
```yaml
depends_on:
  service_name:
    condition: service_healthy  # 等待服务健康
```

## 🎯 本项目的规范遵循

### ✅ 正确的配置示例

```yaml
# docker-compose.official.yml
services:
  hailo8-ai:
    build:
      context: ./hailo-runtime
      dockerfile: Dockerfile
      args:
        SUPPORT_NVIDIA: "true"    # 构建参数使用字符串

    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia      # NVIDIA GPU支持
              count: all
              capabilities: [gpu]

    ports:
      - target: 8000
        published: 8000
        protocol: tcp
        mode: host

    volumes:
      - type: bind
        source: ./models
        target: /app/models
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000

    environment:
      HAILO_API_HOST: "0.0.0.0"   # 环境变量映射格式
      NVIDIA_VISIBLE_DEVICES: "all"

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### ❌ 需要避免的旧格式

```yaml
# 旧格式 - 不推荐
ports:
  - "8000:8000"    # 简化格式，缺少详细信息

volumes:
  - ./models:/app/models  # 简化格式

environment:
  - KEY=value            # 列表格式，不是映射格式
```

## 📊 规范对比

| 配置项 | 旧格式 | 新规范格式 | 优势 |
|--------|--------|------------|------|
| 端口 | `"8000:8000"` | 详细配置 | 更明确的控制 |
| 卷 | `./src:/dst` | 类型化配置 | 支持更多选项 |
| 环境 | `- KEY=value` | 映射格式 | 更清晰的表示 |
| GPU | 设备挂载 | deploy配置 | 官方标准支持 |

## 🔧 验证工具

### 1. Docker Compose验证
```bash
# 验证Compose文件语法
docker-compose -f docker-compose.official.yml config

# 检查服务配置
docker-compose -f docker-compose.official.yml ps
```

### 2. 规范检查
```bash
# 检查配置是否符合规范
docker-compose -f docker-compose.official.yml config --quiet
```

## 🚀 使用规范配置的优势

1. **标准化**: 遵循Docker官方标准
2. **可维护性**: 清晰的配置结构
3. **兼容性**: 跨平台兼容
4. **扩展性**: 支持最新Docker特性
5. **调试友好**: 详细的错误信息

## 📚 学习资源

- **官方规范文档**: https://github.com/compose-spec/compose-spec
- **Docker Compose教程**: https://docs.docker.com/compose/gettingstarted/
- **最佳实践**: https://docs.docker.com/compose/production/

## 🎯 项目中的规范文件

- `docker-compose.official.yml` - 完全符合官方规范
- `docker-compose.nvidia-fixed.yml` - 修正NVIDIA支持
- `DOCKER_COMPOSE_SPEC.md` - 本规范说明文档

通过遵循这些规范，确保配置文件的标准性、可维护性和兼容性。