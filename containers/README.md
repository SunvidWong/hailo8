# Hailo8 容器化服务

🚀 **完整的Hailo8容器化AI推理解决方案**

## 📖 概述

本项目将Hailo8硬件AI加速能力封装为容器化服务，提供标准化的RESTful API和gRPC接口，支持多容器并发调用，实现真正的AI计算服务化。

### 🎯 核心特性

- ✅ **硬件抽象**: 通过API接口访问Hailo8硬件，无需关心底层驱动
- ✅ **容器化部署**: 支持Docker和Kubernetes，便于扩展和管理
- ✅ **多服务架构**: 包含推理服务、Web界面、监控、日志等完整服务
- ✅ **标准接口**: 提供RESTful API和gRPC，支持多种开发语言
- ✅ **实时推理**: 支持图像、视频流的实时AI推理
- ✅ **监控完善**: 集成Prometheus+Grafana监控体系
- ✅ **生产就绪**: 包含健康检查、负载均衡、日志收集等生产特性

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host System                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Hailo8 PCIe Hardware                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (PCIe + Device Access)
┌─────────────────────────────────────────────────────────────┐
│                Hailo8 Runtime Container                     │
│  ┌─────────────┐  ┌─────────────────────────────────────┐  │
│  │   Linux     │  │          HTTP/gRPC API             │  │
│  │   Driver    │  │        (FastAPI + gRPC)           │  │
│  │ hailo1x_pci │  │                                     │  │
│  └─────────────┘  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           HailoRT Python API                        │    │
│  │         (hailo_platform)                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (HTTP/gRPC)
┌─────────────────────────────────────────────────────────────┐
│                  Application Containers                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Web App   │  │  AI Service │  │   Monitoring        │  │
│  │  (React)    │  │ (Python)    │  │ (Prometheus)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 前置要求

1. **硬件要求**:
   - Hailo8 PCIe加速卡
   - 支持PCIe的Linux系统
   - 至少8GB内存，建议16GB

2. **软件要求**:
   - Docker Engine 20.10+
   - Docker Compose 2.0+
   - Linux内核版本 4.15+

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd hailo8/containers
```

#### 2. 配置设备权限
```bash
# 设置Hailo设备访问权限
sudo ./setup_device_permissions.sh

# 重新登录使权限生效
newgrp docker
newgrp hailo
```

#### 3. 准备模型文件
```bash
# 创建模型目录
mkdir -p models

# 将训练好的HEF模型文件复制到models目录
# cp your-model.hef models/
```

#### 4. 启动服务
```bash
# 生产环境启动
docker-compose up -d

# 开发环境启动
docker-compose -f docker-compose.dev.yml up -d
```

#### 5. 验证部署
```bash
# 检查服务状态
docker-compose ps

# 访问API文档
http://localhost:8000/docs

# 访问Web界面
http://localhost:3000

# 检查服务健康状态
curl http://localhost:8000/health
```

## 📁 目录结构

```
containers/
├── README.md                      # 本文档
├── docker-compose.yml             # 生产环境编排
├── docker-compose.dev.yml         # 开发环境编排
├── setup_device_permissions.sh    # 设备权限配置
├── ARCHITECTURE.md                # 架构设计文档
├── hailo-runtime/                 # 核心运行时容器
│   ├── Dockerfile                 # 容器构建文件
│   ├── requirements.txt           # Python依赖
│   ├── api/                       # API服务代码
│   │   ├── main.py               # 主服务入口
│   │   ├── inference.py          # 推理服务
│   │   ├── models.py             # 数据模型
│   │   └── config.py             # 配置管理
│   ├── models/                   # 模型文件目录
│   └── scripts/                  # 辅助脚本
│       ├── install_driver.sh     # 驱动安装
│       └── health_check.sh       # 健康检查
├── hailo-web-app/                # Web前端应用
│   ├── Dockerfile               # 前端容器
│   ├── package.json             # Node.js依赖
│   └── src/                     # React源码
├── hailo-ai-service/             # AI服务示例
│   ├── Dockerfile               # AI服务容器
│   ├── requirements.txt         # Python依赖
│   └── app.py                   # Flask应用
├── nginx/                        # 反向代理
│   ├── Dockerfile               # Nginx容器
│   └── nginx.conf               # 代理配置
├── models/                       # 模型文件存储
├── logs/                         # 日志文件存储
├── monitoring/                   # 监控配置
│   ├── prometheus.yml           # Prometheus配置
│   └── grafana/                 # Grafana仪表板
└── docs/                         # 详细文档
```

## 🔧 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HAILO_API_HOST` | 0.0.0.0 | API服务绑定地址 |
| `HAILO_API_PORT` | 8000 | API服务端口 |
| `HAILO_GRPC_PORT` | 50051 | gRPC服务端口 |
| `HAILO_MODEL_PATH` | /app/models | 模型文件路径 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `DEBUG` | false | 调试模式 |

### 设备访问配置

服务需要访问以下设备：
- `/dev/hailo0`, `/dev/hailo1` - Hailo设备节点
- `/dev/dri` - GPU设备（如果使用GPU）
- `/lib/modules` - 内核模块（只读）

### 网络配置

默认端口映射：
- `8000` - HTTP API服务
- `50051` - gRPC服务
- `3000` - Web界面
- `8080` - AI服务示例
- `9090` - Prometheus监控
- `3001` - Grafana可视化

## 📖 API使用指南

### RESTful API

#### 1. 健康检查
```bash
curl http://localhost:8000/health
```

#### 2. 设备状态
```bash
curl http://localhost:8000/api/v1/device/status
```

#### 3. 图像推理
```bash
curl -X POST \
  http://localhost:8000/api/v1/inference/image \
  -F "file=@image.jpg" \
  -F "model_name=yolov5" \
  -F "confidence_threshold=0.5"
```

#### 4. 流式推理
```bash
curl -X POST \
  http://localhost:8000/api/v1/inference/stream \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "yolov5",
    "max_frames": 100
  }'
```

### Python客户端示例

```python
import requests

# 客户端类
class HailoClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def inference(self, image_path, model_name=None, confidence=0.5):
        """执行图像推理"""
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'model_name': model_name,
                'confidence_threshold': confidence
            }
            response = requests.post(
                f"{self.base_url}/api/v1/inference/image",
                files=files,
                data=data
            )
        return response.json()

# 使用示例
client = HailoClient()
result = client.inference("test.jpg", model_name="yolov5")
print(result)
```

## 🔍 监控和日志

### Prometheus指标

访问 `http://localhost:9091` 查看Prometheus指标

主要指标：
- `hailo_inference_total` - 推理总次数
- `hailo_inference_duration_seconds` - 推理耗时
- `hailo_device_temperature` - 设备温度
- `hailo_device_power_usage` - 设备功耗

### Grafana仪表板

访问 `http://localhost:3001` 查看Grafana仪表板

默认账号：`admin` / `admin123`

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f hailo-runtime

# 查看API服务详细日志
docker exec hailo-runtime tail -f /app/logs/api.log
```

## 🛠️ 开发指南

### 开发环境设置

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 进入开发容器
docker exec -it hailo-runtime-dev bash

# 查看实时日志
docker-compose -f docker-compose.dev.yml logs -f
```

### 添加新的AI服务

1. 创建新的服务目录
2. 编写Dockerfile和应用代码
3. 在docker-compose.yml中添加服务定义
4. 配置网络和依赖关系

### 自定义模型

1. 将HEF模型文件放入 `models/` 目录
2. 更新模型配置
3. 重启服务
4. 通过API指定模型名称使用

## 🔧 故障排除

### 常见问题

#### 1. 设备访问权限问题
```bash
# 检查设备权限
ls -la /dev/hailo*

# 重新设置权限
sudo ./setup_device_permissions.sh
```

#### 2. 驱动加载失败
```bash
# 检查内核模块
lsmod | grep hailo

# 查看内核日志
dmesg | grep hailo

# 手动加载驱动
sudo modprobe hailo1x_pci
```

#### 3. 容器启动失败
```bash
# 查看容器状态
docker-compose ps

# 查看详细错误
docker-compose logs hailo-runtime

# 重新构建容器
docker-compose build --no-cache hailo-runtime
```

#### 4. API调用失败
```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 检查网络连接
docker network ls
docker network inspect hailo8_hailo-network
```

### 性能优化

1. **内存优化**: 调整容器内存限制
2. **并发优化**: 增加工作线程数
3. **缓存优化**: 启用Redis缓存
4. **GPU加速**: 配置GPU设备访问

## 📚 扩展功能

### Kubernetes部署

```yaml
# 示例Kubernetes配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hailo-runtime
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hailo-runtime
  template:
    spec:
      containers:
      - name: hailo-runtime
        image: hailo-runtime:latest
        ports:
        - containerPort: 8000
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: hailo-device
          mountPath: /dev/hailo0
      volumes:
      - name: hailo-device
        hostPath:
          path: /dev/hailo0
```

### 微服务架构

- 模型管理服务
- 任务调度服务
- 结果缓存服务
- 用户认证服务

### 云原生特性

- 自动扩缩容
- 服务发现
- 负载均衡
- 故障自愈

## 📄 许可证

本项目遵循Apache 2.0许可证

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 📞 技术支持

- 📧 邮箱: support@example.com
- 📖 文档: https://docs.example.com
- 🐛 问题反馈: https://github.com/example/issues

---

**注意**: 本项目需要Hailo8硬件支持，请确保硬件正确安装和配置。