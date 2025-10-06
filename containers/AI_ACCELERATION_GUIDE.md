# Hailo8 + NVIDIA AI加速服务指南

🚀 **双硬件AI推理加速解决方案**

## 📖 概述

本指南提供了使用Hailo8和NVIDIA GPU进行AI推理加速的完整解决方案。容器内的AI加速服务可以同时支持Hailo8 PCIe加速卡和NVIDIA GPU，为其他容器提供统一的推理API服务。

## 🎯 解决方案特点

✅ **双硬件支持**: 同时支持Hailo8和NVIDIA GPU
✅ **自动选择**: 根据可用性自动选择最佳推理引擎
✅ **统一接口**: 提供统一的API接口供其他容器调用
✅ **硬件透明**: 上层应用无需关心底层硬件细节
✅ **性能监控**: 实时监控硬件使用情况和推理性能
✅ **负载均衡**: 支持在多个硬件间进行负载均衡

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                  AI加速服务容器                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            统一AI推理API                           │    │
│  │        ┌─────────────┐  ┌─────────────────────┐      │    │
│  │        │  引擎选择器  │  │   智能调度器      │      │    │
│  │        └─────────────┘  └─────────────────────┘      │    │
│  │              │                    │                 │    │
│  │  ┌─────────▼─────────┐  ┌──────────▼─────────┐  │    │
│  │  │  Hailo8 推理器  │  │ NVIDIA推理管理器  │  │    │
│  │  └─────────┬─────────┘  └──────────┬─────────┘  │    │
│  │            │                    │                 │    │
│  │  ┌─────────▼─────────┐  ┌──────────▼─────────┐  │    │
│  │  │    Hailo8硬件    │  │   NVIDIA GPU      │  │    │
│  │  │    (PCIe卡)      │  │    (显卡)        │  │    │
│  │  └─────────────────┘  └─────────────────────┘�  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/gRPC API
┌─────────────────────────────────────────────────────────────┐
│                  其他应用容器                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Frigate   │  │  Home      │  │   AI应用容器     │  │
│  │  (NVR)     │  │  Assistant│  │                 │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 硬件要求

### 基本要求
- **Docker Engine**: 20.10+
- **Docker Compose**: 2.0+
- **Linux系统**: 支持PCIe的Linux发行版

### 硬件要求（至少一种）
- **Hailo8 PCIe加速卡**:
  - Hailo8 PCIe x4或更高
  - 支持的Linux内核
  - 足够的PCIe带宽和电源供应

- **NVIDIA GPU**:
  - NVIDIA GPU (Pascal架构或更新)
  - NVIDIA驱动版本 >= 470.xx
  - CUDA Toolkit >= 12.0
  - 足够的GPU内存（建议8GB+）

### 推荐配置
- **双硬件环境**: 同时配置Hailo8和NVIDIA GPU
- **内存**: 16GB+ (用于模型加载和推理缓存)
- **存储**: 100GB+ SSD
- **网络**: 千兆网络连接

## 🚀 快速部署

### 1. 基本部署

```bash
# 克隆项目
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers

# 启动AI加速服务
docker-compose -f docker-compose.ai-acceleration.yml up -d

# 检查服务状态
docker-compose -f docker-compose.ai-acceleration.yml ps
```

### 2. 验证硬件

```bash
# 检查可用硬件
curl http://localhost:8000/ai/hardware

# 验证硬件配置
curl -X POST http://localhost:8000/ai/validate
```

### 3. 测试推理

```bash
# 推理引擎选择 (自动)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [ [[255,0,0,255], [255,255,255], [255,0,0]]],
    "engine": "auto"
  }' \
  http://localhost:8000/ai/infer

# 强制使用Hailo8
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [255,0,0,255,255,255,255,255,0,0]],
    "engine": "hailo",
    "threshold": 0.5
  }' \
  http://localhost:8000/ai/infer

# 强制使用NVIDIA
curl -X -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [255,0,0,255,255,255,255,255,0,0]],
    "engine": "nvidia",
    "threshold": 0.5
  }' \
  http://localhost:8000/ai/infer
```

## 📋 API接口说明

### 核心接口

#### 1. 推理接口
```http
POST /ai/infer
Content-Type: application/json

{
  "image": [
    [[255,0,0], [255,255,255], [255,0,0]]
  ],
  "engine": "auto",
  "model_name": "yolov8n",
  "threshold": 0.4,
  "targets": ["person", "car"]
}
```

#### 2. 硬件信息接口
```http
GET /ai/hardware
```

响应示例:
```json
{
  "available_engines": ["hailo", "nvidia"],
  "hailo_devices": [
    {
      "id": 0,
      "name": "Hailo8 PCIe Device",
      "is_available": true,
      "device_id": "0000:00:01.0"
    }
  ],
  "nvidia_devices": [
    {
      "id": 0,
      "name": "NVIDIA GeForce RTX 4090",
      "memory_total": 24576,
      "memory_allocated": 2048,
      "is_available": true
    }
  ]
}
```

#### 3. 引擎信息接口
```http
GET /ai/engines
```

#### 4. 健康检查接口
```http
GET /ai/health
```

## 🔧 配置选项

### 环境变量配置

```bash
# AI加速服务配置
SUPPORT_HAILO=true              # 启用Hailo8支持
SUPPORT_NVIDIA=true            # 启用NVIDIA支持
DEFAULT_ENGINE=auto             # 默认推理引擎
FALLBACK_ENGINE=hailo           # 回退引擎
CACHE_ENABLED=true              # 启用缓存
REDIS_URL=redis://redis:6379   # Redis连接字符串
```

### 推理引擎配置

#### 自动选择模式 (推荐)
```yaml
environment:
  - DEFAULT_ENGINE=auto
  - FALLBACK_ENGINE=hailo
```

- 自动选择最佳可用引擎
- 优先使用NVIDIA GPU (性能更好)
- 回退到Hailo8 (边缘推理)

#### 手动指定模式
```yaml
environment:
  - DEFAULT_ENGINE=nvidia  # 强制使用NVIDIA
  # 或
  - DEFAULT_ENGINE=hailo   # 强制使用Hailo8
```

### 性能调优

#### Hailo8优化
```yaml
environment:
  - HAILO_BATCH_SIZE=1          # 批处理大小
  - HAILO_THREADS=2              # 线程数
  - HAILO_MEMORY_LIMIT=1024      # 内存限制(MB)
```

#### NVIDIA优化
```yaml
environment:
  - CUDA_VISIBLE_DEVICES=all    # 可见GPU设备
  - NVIDIA_VISIBLE_DEVICES=all   # NVIDIA驱动支持
  - TORCH_CUDA_ARCH_LIST=8.6       # CUDA架构支持
```

## 🎯 使用场景

### 1. 与Frigate集成

在Frigate配置中设置推理检测器：

```yaml
# frigate config.yml
detectors:
  hailo8_detector:
    type: remote
    api:
      url: http://ai-acceleration-service:8000/ai/infer
      timeout: 5
      max_retries: 3
    threshold: 0.4
```

### 2. 与Home Assistant集成

在Home Assistant中添加API调用：

```yaml
# configuration.yaml
sensor:
  - platform: rest
    name: AI Inference Status
    resource: http://ai-acceleration-service:8000/ai/health
    value_template: "{{ value_json.status }}"
```

### 3. 自定义AI应用

在您的应用中调用API：

```python
import requests

# 发送推理请求
response = requests.post(
    'http://ai-acceleration-service:8000/ai/infer',
    json={
        'image': image_data,
        'engine': 'auto',
        'threshold': 0.5
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"检测到 {len(result['detections'])} 个对象")
    print(f"使用引擎: {result['engine_used']}")
```

## 📊 监控和管理

### 1. 服务监控

访问地址：
- **Grafana监控**: http://localhost:3000
- **Prometheus指标**: http://localhost:9090
- **服务状态**: http://localhost:8000/ai/health

### 2. 监控指标

- 推理请求总数和响应时间
- 各引擎使用情况
- 硬件利用率
- 错误率和故障统计

### 3. 日志管理

```bash
# 查看服务日志
docker-compose -f docker-compose.ai-acceleration.yml logs -f ai-acceleration-service

# 查看推理日志
tail -f logs/hailo/ai_service.log
```

### 4. 性能优化

```bash
# 调整资源配置
vim docker-compose.ai-acceleration.yml

# 重启服务
docker-compose -f docker-compose.ai-acceleration.yml restart
```

## 🔍 故障排除

### 常见问题

#### 1. 硬件检测失败

**问题**: 服务启动时无法检测到硬件

**解决方案**:
```bash
# 检查Hailo8设备
lspci | grep -i hailo
ls -la /dev/hailo*

# 检查NVIDIA设备
nvidia-smi
lspci | grep -i nvidia

# 检查内核模块
lsmod | grep hailo
lsmod | grep nvidia
```

#### 2. 推理引擎选择问题

**问题**: 推理引擎选择不符合预期

**解决方案**:
```bash
# 检查可用引擎
curl http://localhost:8000/ai/engines

# 手动指定引擎
curl -X POST http://localhost:8000/ai/infer \
  -H "Content-Type: application/json" \
  -d '{"image": [[[255,0,0]]], "engine": "hailo"}'
```

#### 3. 内存不足

**问题**: 推理失败，提示内存不足

**解决方案**:
```bash
# 检查内存使用
docker stats ai-acceleration-service

# 释放GPU内存
nvidia-smi --gpu-reset

# 调整容器内存限制
vim docker-compose.ai-acceleration.yml
```

#### 4. 网络连接问题

**问题**: 其他容器无法访问AI服务

**解决方案**:
```bash
# 检查网络连接
docker network ls

# 检查容器网络
docker exec ai-aceration-service ping frigate

# 验证端口映射
netstat -tlnp | grep 8000
```

### 调试技巧

#### 1. 启用调试模式
```yaml
environment:
  - DEBUG=true
  - LOG_LEVEL=DEBUG
```

#### 2. 进入容器调试
```bash
docker exec -it ai-acceleration-service bash
```

#### 3. 查看详细日志
```bash
docker-compose -f docker-compose.ai-acceleration.yml logs ai-acceleration-service
```

## 📚 扩展功能

### 1. 多实例部署

```yaml
services:
  ai-acceleration-service-1:
    # 配置...

  ai-acceleration-service-2:
    # 配置...
```

### 2. 负载均衡

```yaml
environment:
  - LOAD_BALANCING=true
  - ROUND_ROBIN=true
```

### 3. 缓存优化

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

## 🎉 总结

使用Hailo8 + NVIDIA双硬件加速服务，您可以：

✅ **提高推理性能**: 根据工作负载自动选择最佳硬件
✅ **简化应用开发**: 上层应用无需关心底层硬件
✅ **提高硬件利用率**: 同时利用两种加速器
✅ **增强系统可靠性**: 硬件故障时自动切换
✅ **降低部署复杂度**: 统一的API接口管理

开始使用双硬件AI加速服务，体验更强大的AI推理能力！

---

🚀 **现在您可以开始部署双硬件AI加速服务了！**

如有问题，请参考故障排除部分或查看完整文档。