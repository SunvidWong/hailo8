# Hailo8 + NVIDIA AI加速服务部署指南

## 🚀 快速部署

### 前置要求

**硬件要求：**
- Hailo8 PCIe加速卡 (可选)
- NVIDIA GPU (可选)
- 至少一种硬件可用

**系统要求：**
- Linux系统 (Ubuntu 20.04+, CentOS 8+, RHEL 8+)
- 内核版本: 4.15+
- Docker Engine: 20.10+
- NVIDIA Container Toolkit (如果使用NVIDIA GPU)

### 安装步骤

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
docker-compose -f docker-compose.hailo8-deploy.yml up -d

# 5. 验证部署
curl http://localhost:8000/health
curl http://localhost:8000/ai/hardware
```

## 📱 服务访问

| 服务 | 地址 | 用途 |
|------|------|------|
| AI推理API | http://localhost:8000 | 主要API服务 |
| Redis缓存 | localhost:6379 | 缓存服务 |
| API文档 | http://localhost:8000/docs | Swagger文档 |

## 🔧 API使用示例

```bash
# 检查硬件状态
curl http://localhost:8000/ai/hardware

# 自动推理
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image": [[[255,0,0]]],
    "engine": "auto"
  }' \
  http://localhost:8000/ai/infer
```

## 🔍 监控服务 (可选)

```bash
# 启动监控服务
docker-compose -f docker-compose.hailo8-deploy.yml --profile monitoring up -d

# 访问地址
# Grafana: http://localhost:3000 (admin/hailo8)
# Prometheus: http://localhost:9090
```

## 🛠️ 管理命令

```bash
# 查看服务状态
docker-compose -f docker-compose.hailo8-deploy.yml ps

# 查看日志
docker-compose -f docker-compose.hailo8-deploy.yml logs -f

# 重启服务
docker-compose -f docker-compose.hailo8-deploy.yml restart

# 停止服务
docker-compose -f docker-compose.hailo8-deploy.yml down
```