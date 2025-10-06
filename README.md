# Hailo8 + NVIDIA AI加速服务

🚀 **双硬件AI推理加速解决方案 - Docker Compose容器化部署**

## 📖 项目概述

本项目提供了一套完整的Hailo8 PCIe + NVIDIA GPU双硬件AI推理加速解决方案，通过Docker Compose容器化部署，为其他容器提供统一的AI推理API服务。

![架构图](https://maas-log-prod.cn-wlcb.ufileos.com/anthropic/37cb952e-bf22-45fb-ab90-1bf74ce56b5c/19bca8642cc000fb1b8dec3a39b7f842.jpg?UCloudPublicKey=TOKEN_e15ba47a-d098-4fbd-9afc-a0dcf0e4e621&Expires=1759715004&Signature=sJPoOSljpc0B+A04yf9aqWNhXug=)

## 🎯 部署方案

### 方案一：容器化AI推理服务（推荐）⭐

**使用Docker Compose部署容器，为其他容器提供AI推理加速API**

#### 📋 前置要求

**硬件要求：**
- **Hailo8 PCIe加速卡** (可选)
- **NVIDIA GPU** (可选)
- **至少一种硬件可用**

**系统要求：**
- **Linux系统** (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- **内核版本**: 4.15+
- **Docker Engine**: 20.10+
- **NVIDIA Container Toolkit** (如果使用NVIDIA GPU)

#### 🚀 5分钟快速部署

```bash
# 1. 克隆项目
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers

# 2. 安装NVIDIA Container Toolkit (仅NVIDIA用户)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update && sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# 3. 验证NVIDIA支持 (仅NVIDIA用户)
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi

# 4. 启动AI加速服务
docker-compose -f docker-compose.official.yml up -d

# 5. 验证部署
curl http://localhost:8000/health
curl http://localhost:8000/ai/hardware
```

#### 📱 服务访问

| 服务 | 地址 | 用途 |
|------|------|------|
| **AI推理API** | http://localhost:8000 | 主要API服务 |
| **API文档** | http://localhost:8000/docs | Swagger文档 |
| **Redis缓存** | localhost:6379 | 缓存服务 |

#### 🔧 API调用示例

```bash
# 检查硬件状态
curl http://localhost:8000/ai/hardware

# 自动推理 (智能选择硬件)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0], [255,255,255], [255,0,0]]],
    "engine": "auto",
    "threshold": 0.4
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

# 强制使用Hailo8
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "hailo"
  }' \
  http://localhost:8000/ai/infer
```

#### 🎛️ 高级推理模式

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
  http://localhost:8000/ai/inver

# 负载均衡 (自动优化)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "load_balance"
  }' \
  http://localhost:8000/ai/infer
```

#### 🐳 其他容器调用示例

```python
# 其他容器中调用AI服务
import requests

def ai_inference(image_data, engine="auto"):
    response = requests.post(
        'http://hailo8-ai:8000/ai/infer',
        json={
            'image': image_data,
            'engine': engine,
            'threshold': 0.5
        }
    )

    if response.status_code == 200:
        result = response.json()
        print(f"检测到 {len(result['detections'])} 个对象")
        print(f"使用引擎: {result['engines_used']}")
        print(f"推理时间: {result['inference_time']:.3f}s")
        return result
    else:
        print(f"推理失败: {response.text}")
        return None

# 使用示例
result = ai_inference(your_image_data)
```

#### 📊 Docker Compose配置详解

```yaml
# docker-compose.official.yml
services:
  hailo8-ai:
    build:
      context: ./hailo-runtime
      args:
        SUPPORT_NVIDIA: "true"
        SUPPORT_HAILO: "true"

    # NVIDIA GPU支持
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

    ports:
      - "8000:8000"

    volumes:
      - ./models:/app/models
      - /dev/hailo0:/dev/hailo0
      - /dev/dri:/dev/dri

    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=all
      - DEFAULT_ENGINE=auto
```

#### 🔍 验证和测试

```bash
# 运行完整测试套件
./test_ai_acceleration.sh

# 手动测试硬件检测
curl http://localhost:8000/ai/hardware | jq

# 测试各引擎性能
curl -X POST -H "Content-Type: application/json" \
  -d '{"image":[[[255,0,0]]],"engine":"auto"}' \
  http://localhost:8000/ai/infer
```

---

### 方案二：Hailo8 PCIe卡驱动安装

**直接在宿主机安装Hailo8驱动，适用于非容器化部署**

#### 系统要求
- Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+, RHEL 7+)
- 内核版本 4.0+
- root权限
- 至少 2GB 可用空间

#### 安装步骤
```bash
# 1. 准备环境
sudo su
cd hailo8/installer

# 2. 执行安装
python3 hailo8_installer.py

# 3. 验证安装
ls -la /dev/hailo*
```

---

### 方案三：NVIDIA Docker环境

**配置NVIDIA Container Toolkit，为容器提供GPU支持**

#### 安装配置
```bash
# 安装NVIDIA Container Toolkit
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add
sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# 验证GPU容器支持
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

## 📁 项目结构

```
hailo8/
├── 📦 containers/                    # 方案一：容器化服务
│   ├── docker-compose.official.yml  # Docker官方规范配置
│   ├── docker-compose.nvidia-fixed.yml # NVIDIA修正版
│   ├── README_STANDARD.md           # 标准配置说明
│   ├── NVIDIA_CONTAINER_SETUP.md    # NVIDIA容器配置指南
│   ├── DOCKER_COMPOSE_SPEC.md       # Docker规范说明
│   ├── AI_ACCELERATION_GUIDE.md     # 完整使用指南
│   ├── ENGINE_SELECTION_GUIDE.md     # 引擎选择指南
│   ├── ZERO_CONFIG_GUIDE.md         # 零配置部署指南
│   ├── test_ai_acceleration.sh      # 完整测试脚本
│   └── 📁 hailo-runtime/            # AI服务源码
│       ├── Dockerfile              # 容器镜像构建
│       ├── api/                    # API服务代码
│       │   ├── enhanced_ai_acceleration_adapter.py
│       │   ├── frigate_auto_discovery.py
│       │   └── main.py
│       └── scripts/                # 部署脚本
├── 🔧 installer/                    # 方案二：驱动安装
│   ├── hailo8_installer.py         # 智能安装管理器
│   ├── install_hailo8_onekey.sh    # 一键安装脚本
│   └── README_INSTALLER.md         # 安装器说明
└── 📚 docs/                        # 文档目录
    ├── INSTALL_GUIDE.md             # 安装指南
    ├── TROUBLESHOOTING.md          # 故障排除
    └── API_REFERENCE.md            # API参考
```

## 🔧 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SUPPORT_HAILO` | `true` | 启用Hailo8支持 |
| `SUPPORT_NVIDIA` | `true` | 启用NVIDIA支持 |
| `DEFAULT_ENGINE` | `auto` | 默认推理引擎 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 推理引擎选择

| 引擎 | 适用场景 | 优势 |
|------|----------|------|
| `auto` | 通用场景 | 自动选择最佳硬件 |
| `hailo` | 边缘推理 | 低功耗、低延迟 |
| `nvidia` | 高精度推理 | 高算力、复杂模型 |
| `both` | 高精度需求 | 双引擎融合 |
| `parallel` | 高吞吐量 | 并行处理 |
| `load_balance` | 生产环境 | 负载均衡 |

## 📊 监控和运维

### 服务状态检查
```bash
# 检查容器状态
docker-compose -f docker-compose.official.yml ps

# 查看实时日志
docker-compose -f docker-compose.official.yml logs -f hailo8-ai

# 检查硬件状态
curl http://localhost:8000/ai/hardware
```

### 性能监控
```bash
# 查看GPU使用情况 (NVIDIA)
nvidia-smi

# 查看服务资源使用
docker stats hailo8-ai

# API性能测试
curl -X POST -H "Content-Type: application/json" \
  -d '{"image":[[[255,0,0]]],"engine":"auto"}' \
  http://localhost:8000/ai/infer
```

## 🔍 故障排除

### 常见问题

#### 1. NVIDIA容器问题
```bash
# 检查NVIDIA驱动
nvidia-smi

# 验证容器支持
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi

# 重新安装NVIDIA Container Toolkit
sudo apt purge nvidia-docker2
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add
sudo apt install -y nvidia-docker2
sudo systemctl restart docker
```

#### 2. Hailo8设备问题
```bash
# 检查PCIe设备
lspci | grep hailo

# 检查设备节点
ls -la /dev/hailo*

# 检查驱动加载
lsmod | grep hailo

# 查看内核日志
dmesg | grep hailo
```

#### 3. 容器启动问题
```bash
# 查看详细错误日志
docker-compose -f docker-compose.official.yml logs hailo8-ai

# 重新构建镜像
docker-compose -f docker-compose.official.yml build --no-cache

# 检查权限问题
sudo usermod -aG docker $USER
newgrp docker
```

## 🎯 使用场景

### 1. 智能摄像头系统
```python
# 摄像头容器调用AI服务
def process_camera_frame(frame_data):
    result = requests.post(
        'http://hailo8-ai:8000/ai/infer',
        json={
            'image': frame_data,
            'engine': 'auto',
            'threshold': 0.5
        }
    )
    return result.json()
```

### 2. 实时视频分析
```python
# 视频流处理容器
import cv2
import requests

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if ret:
        # 发送帧到AI服务
        result = ai_inference(frame.tolist())
        # 处理检测结果...
```

### 3. 批量图像处理
```python
# 批量处理服务容器
def batch_process_images(image_paths):
    for path in image_paths:
        with open(path, 'rb') as f:
            image_data = f.read()
        result = ai_inference(image_data)
        # 保存结果...
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起Pull Request

## 📄 许可证

本项目遵循 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 技术支持

- 🐛 问题反馈: [GitHub Issues](https://github.com/SunvidWong/hailo8/issues)
- 📖 完整文档: [containers/README_STANDARD.md](containers/README_STANDARD.md)
- 🔧 详细配置: [containers/AI_ACCELERATION_GUIDE.md](containers/AI_ACCELERATION_GUIDE.md)

---

🎉 **感谢使用Hailo8 + NVIDIA AI加速服务！**

🌟 如果这个项目对您有帮助，请给它一个⭐️