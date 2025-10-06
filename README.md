# Hailo8 + NVIDIA AI加速服务

🚀 **双硬件AI推理加速解决方案 - Docker容器化部署**

## 📖 项目概述

本项目提供Hailo8 PCIe + NVIDIA GPU双硬件AI推理加速服务，通过Docker容器化部署，为其他容器提供统一的AI推理API服务。

## 🚀 快速开始

### 远程部署（推荐）

```bash
# 1. 准备部署目录
mkdir hailo8-deploy
cd hailo8-deploy

# 2. 下载部署配置文件
wget https://raw.githubusercontent.com/SunvidWong/hailo8/main/containers/docker-compose.hailo8-deploy.yml

# 3. 创建必要目录
mkdir -p models logs monitoring/{grafana/{dashboards,datasources}}

# 4. 安装NVIDIA Container Toolkit (仅NVIDIA用户)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update && sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# 5. 启动AI加速服务
docker-compose -f docker-compose.hailo8-deploy.yml up -d

# 6. 验证部署
curl http://localhost:8000/health
curl http://localhost:8000/ai/hardware
```

## 📱 服务访问

| 服务 | 地址 | 用途 |
|------|------|------|
| **AI推理API** | http://localhost:8000 | 主要API服务 |
| **API文档** | http://localhost:8000/docs | Swagger文档 |
| **Redis缓存** | localhost:6379 | 缓存服务 |

## 🔧 API使用示例

```bash
# 检查硬件状态
curl http://localhost:8000/ai/hardware

# 自动推理 (智能选择硬件)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
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

## 🐳 其他容器调用示例

```python
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
        return result
    else:
        print(f"推理失败: {response.text}")
        return None

# 使用示例
result = ai_inference(your_image_data)
```

## 🎛️ 高级推理模式

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

## 📊 监控服务 (可选)

```bash
# 启动监控服务
docker-compose -f docker-compose.hailo8-deploy.yml --profile monitoring up -d

# 访问地址
# Grafana: http://localhost:3000 (admin/hailo8)
# Prometheus: http://localhost:9090
```

## 📁 项目结构

```
hailo8/
├── 📦 containers/
│   ├── docker-compose.hailo8-deploy.yml  # 远程部署配置 ⭐
│   ├── docker-compose.official.yml       # Docker官方规范
│   ├── docker-compose.nvidia-fixed.yml   # NVIDIA修正版
│   ├── DEPLOY_GUIDE.md                   # 部署指南
│   ├── AI_ACCELERATION_GUIDE.md           # 完整使用指南
│   ├── ENGINE_SELECTION_GUIDE.md           # 引擎选择指南
│   ├── NVIDIA_CONTAINER_SETUP.md          # NVIDIA容器配置
│   ├── test_ai_acceleration.sh            # 测试脚本
│   └── 📁 hailo-runtime/                 # AI服务源码
└── 📚 docs/                              # 文档目录
```

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SUPPORT_HAILO` | `true` | 启用Hailo8支持 |
| `SUPPORT_NVIDIA` | `true` | 启用NVIDIA支持 |
| `DEFAULT_ENGINE` | `auto` | 默认推理引擎 |

### 推理引擎

| 引擎 | 适用场景 | 优势 |
|------|----------|------|
| `auto` | 通用场景 | 自动选择最佳硬件 |
| `hailo` | 边缘推理 | 低功耗、低延迟 |
| `nvidia` | 高精度推理 | 高算力、复杂模型 |
| `both` | 高精度需求 | 双引擎融合 |
| `parallel` | 高吞吐量 | 并行处理 |
| `load_balance` | 生产环境 | 负载均衡 |

## 📊 监控和运维

```bash
# 检查服务状态
docker-compose -f docker-compose.hailo8-deploy.yml ps

# 查看日志
docker-compose -f docker-compose.hailo8-deploy.yml logs -f hailo8-ai

# 重启服务
docker-compose -f docker-compose.hailo8-deploy.yml restart

# 停止服务
docker-compose -f docker-compose.hailo8-deploy.yml down
```

## 🔍 故障排除

### NVIDIA容器问题
```bash
# 检查NVIDIA驱动
nvidia-smi

# 验证容器支持
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi

# 重新安装NVIDIA Container Toolkit
sudo apt purge nvidia-docker2
# 重新执行安装步骤...
```

### Hailo8设备问题
```bash
# 检查PCIe设备
lspci | grep hailo

# 检查设备节点
ls -la /dev/hailo*

# 检查驱动加载
lsmod | grep hailo
```

## 🎯 使用场景

### 智能摄像头系统
```python
def process_camera_frame(frame_data):
    result = requests.post(
        'http://hailo8-ai:8000/ai/infer',
        json={'image': frame_data, 'engine': 'auto', 'threshold': 0.5}
    )
    return result.json()
```

### 实时视频分析
```python
import cv2
cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if ret:
        result = ai_inference(frame.tolist())
        # 处理检测结果...
```

### 批量图像处理
```python
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