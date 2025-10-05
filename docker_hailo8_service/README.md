# Hailo8 Docker 硬件加速服务

## 项目概述

这是一个独立的Docker容器服务，提供Hailo8硬件加速能力。其他容器可以通过HTTP API调用来使用Hailo8的AI推理加速功能，无需直接安装Hailo8驱动。

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host                              │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Client App    │    │   Client App    │                │
│  │   Container     │    │   Container     │                │
│  │                 │    │                 │                │
│  └─────────┬───────┘    └─────────┬───────┘                │
│            │                      │                        │
│            │      HTTP API        │                        │
│            └──────────┬───────────┘                        │
│                       │                                    │
│  ┌─────────────────────▼─────────────────────┐             │
│  │        Hailo8 Service Container           │             │
│  │                                           │             │
│  │  ┌─────────────┐  ┌─────────────────────┐ │             │
│  │  │   FastAPI   │  │   Hailo8 Runtime    │ │             │
│  │  │   Server    │  │   + Drivers         │ │             │
│  │  └─────────────┘  └─────────────────────┘ │             │
│  │                                           │             │
│  └─────────────────────┬───────────────────────┘             │
│                        │                                    │
│  ┌─────────────────────▼─────────────────────┐             │
│  │           Hailo8 Hardware                 │             │
│  │         (PCIe/M.2 Card)                   │             │
│  └───────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## 核心功能

### 1. 硬件抽象层
- 自动检测Hailo8硬件设备
- 管理设备资源和状态
- 提供设备健康监控

### 2. API服务层
- RESTful HTTP API
- 模型管理（加载、卸载、列表）
- 推理请求处理
- 批处理支持

### 3. 容器化部署
- 包含完整的Hailo8运行环境
- 支持设备直通（device passthrough）
- 资源限制和监控

## API接口设计

### 基础信息
- `GET /health` - 服务健康检查
- `GET /devices` - 获取Hailo8设备信息
- `GET /status` - 获取服务状态

### 模型管理
- `POST /models/load` - 加载模型
- `DELETE /models/{model_id}` - 卸载模型
- `GET /models` - 获取已加载模型列表

### 推理服务
- `POST /inference` - 执行推理
- `POST /inference/batch` - 批量推理
- `GET /inference/{task_id}` - 获取异步推理结果

## 部署方式

### 1. 单容器部署
```bash
docker run -d \
  --name hailo8-service \
  --device=/dev/hailo0 \
  -p 8080:8080 \
  hailo8-service:latest
```

### 2. Docker Compose部署
```yaml
version: '3.8'
services:
  hailo8-service:
    image: hailo8-service:latest
    devices:
      - /dev/hailo0:/dev/hailo0
    ports:
      - "8080:8080"
    environment:
      - HAILO_LOG_LEVEL=INFO
```

## 客户端使用示例

### Python客户端
```python
import requests

# 检查服务状态
response = requests.get('http://hailo8-service:8080/health')

# 加载模型
model_data = {
    'model_path': '/models/yolov5.hef',
    'model_id': 'yolov5_detection'
}
requests.post('http://hailo8-service:8080/models/load', json=model_data)

# 执行推理
inference_data = {
    'model_id': 'yolov5_detection',
    'input_data': base64_encoded_image
}
result = requests.post('http://hailo8-service:8080/inference', json=inference_data)
```

## 优势特点

1. **即插即用** - 客户端无需安装Hailo8驱动
2. **资源共享** - 多个容器可共享同一个Hailo8设备
3. **版本管理** - 统一的运行时环境，避免版本冲突
4. **易于扩展** - 支持负载均衡和集群部署
5. **监控友好** - 提供详细的性能和状态监控

## 技术栈

- **基础镜像**: Ubuntu 20.04 LTS
- **API框架**: FastAPI + Uvicorn
- **Hailo运行时**: HailoRT 4.23.0
- **容器编排**: Docker Compose
- **监控**: Prometheus metrics (可选)