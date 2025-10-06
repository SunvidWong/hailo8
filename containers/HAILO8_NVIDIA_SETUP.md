# Hailo8 + NVIDIA AI加速服务部署指南

## 📋 部署配置文件

使用标准的Docker Compose格式，提供Hailo8和NVIDIA双硬件AI推理加速服务。

### 🚀 快速部署

```bash
# 启动AI加速服务
docker-compose -f docker-compose.hailo8-nvidia.yml up -d

# 查看服务状态
docker-compose -f docker-compose.hailo8-nvidia.yml ps

# 查看日志
docker-compose -f docker-compose.hailo8-nvidia.yml logs -f hailo8-ai
```

## 🔧 配置说明

### 服务组件

1. **hailo8-ai**: 主要AI推理服务
   - 端口: 8000 (HTTP API), 50051 (gRPC)
   - 硬件访问: Hailo8 PCIe + NVIDIA GPU
   - 自动引擎选择和负载均衡

2. **redis**: 缓存服务
   - 端口: 6379
   - 用于推理结果缓存和性能优化

### 硬件要求

- **Hailo8 PCIe加速卡** (可选)
- **NVIDIA GPU with CUDA** (可选)
- **至少一种硬件可用**

## 📱 API接口

### 基础端点

```bash
# 健康检查
curl http://localhost:8000/health

# 硬件状态
curl http://localhost:8000/ai/hardware

# 可用引擎
curl http://localhost:8000/ai/engines
```

### 推理接口

```bash
# 自动选择最佳引擎
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "auto",
    "threshold": 0.4
  }' \
  http://localhost:8000/ai/infer

# 强制使用Hailo8
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "hailo"
  }' \
  http://localhost:8000/ai/infer

# 强制使用NVIDIA
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "nvidia"
  }' \
  http://localhost:8000/ai/infer
```

### 高级推理模式

```bash
# 并行推理 (同时使用两个硬件)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "parallel",
    "priority": "performance"
  }' \
  http://localhost:8000/ai/infer

# 双引擎融合 (高精度)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "both",
    "priority": "accuracy"
  }' \
  http://localhost:8000/ai/infer

# 负载均衡 (自动优化)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "load_balance"
  }' \
  http://localhost:8000/ai/infer
```

## 🎯 使用场景

### 1. 其他容器调用AI服务

您的其他容器可以通过HTTP API调用AI推理服务：

```python
import requests

# 发送推理请求
response = requests.post(
    'http://hailo8-ai:8000/ai/infer',
    json={
        'image': image_data,
        'engine': 'auto',
        'threshold': 0.5
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"检测到 {len(result['detections'])} 个对象")
    print(f"使用引擎: {result['engines_used']}")
```

### 2. 环境变量配置

```yaml
# 在其他容器的docker-compose.yml中
services:
  your-app:
    environment:
      - AI_SERVICE_URL=http://hailo8-ai:8000
      - AI_ENGINE=auto
```

## 📊 性能监控

### 查看服务状态

```bash
# 检查容器状态
docker ps | grep hailo8

# 查看资源使用
docker stats hailo8-ai

# 查看硬件状态
curl http://localhost:8000/ai/hardware | jq
```

### 性能基准

```bash
# 运行性能测试
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"image":[[[255,0,0]]],"engine":"auto"}' \
  http://localhost:8000/ai/infer
```

## 🛠️ 故障排除

### 常见问题

1. **硬件未被检测到**
   ```bash
   # 检查Hailo8
   lspci | grep hailo
   ls -la /dev/hailo*

   # 检查NVIDIA
   nvidia-smi
   ```

2. **容器启动失败**
   ```bash
   # 查看详细日志
   docker-compose -f docker-compose.hailo8-nvidia.yml logs hailo8-ai

   # 检查权限
   ls -la /dev/hailo* /dev/nvidia*
   ```

3. **API调用失败**
   ```bash
   # 检查服务健康状态
   curl http://localhost:8000/health

   # 检查端口
   netstat -tlnp | grep 8000
   ```

## 🔄 维护操作

```bash
# 重启服务
docker-compose -f docker-compose.hailo8-nvidia.yml restart

# 更新镜像
docker-compose -f docker-compose.hailo8-nvidia.yml pull
docker-compose -f docker-compose.hailo8-nvidia.yml up -d

# 停止服务
docker-compose -f docker-compose.hailo8-nvidia.yml down

# 清理资源
docker-compose -f docker-compose.hailo8-nvidia.yml down -v
```

## 📂 目录结构

```
.
├── docker-compose.hailo8-nvidia.yml    # 主配置文件
├── models/                            # AI模型文件
├── logs/                              # 日志文件
└── hailo-runtime/                     # 服务源码
    ├── Dockerfile
    └── api/
        ├── enhanced_ai_acceleration_adapter.py
        ├── frigate_auto_discovery.py
        └── main.py
```

## 🎉 完成！

现在您有了一个标准的Docker Compose配置，可以为其他容器提供Hailo8和NVIDIA AI加速服务。其他容器只需通过HTTP API即可调用AI推理功能。