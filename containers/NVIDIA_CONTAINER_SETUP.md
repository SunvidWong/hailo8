# NVIDIA容器支持配置指南

## 🎯 问题说明

您指出的问题非常正确！之前的配置缺少了NVIDIA容器在Docker中运行的关键配置。要让NVIDIA显卡在容器中正常工作，需要正确配置NVIDIA Container Toolkit。

## 🔧 前置要求

### 1. 系统要求
- **Linux系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **内核版本**: 4.15+
- **NVIDIA驱动**: 470.xx+ (推荐 515.xx+)
- **Docker Engine**: 20.10+
- **NVIDIA Container Toolkit**: 最新版本

### 2. 硬件要求
- **NVIDIA GPU**: Pascal架构或更新
- **Hailo8 PCIe卡**: 可选，用于双硬件加速

## 🚀 NVIDIA容器支持安装步骤

### 步骤1: 安装NVIDIA驱动
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nvidia-driver-515 nvidia-cuda-toolkit

# 验证驱动安装
nvidia-smi
```

### 步骤2: 安装NVIDIA Container Toolkit
```bash
# 添加NVIDIA仓库
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 安装toolkit
sudo apt update
sudo apt install -y nvidia-container-toolkit

# 配置Docker运行时
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 步骤3: 验证NVIDIA容器支持
```bash
# 测试NVIDIA容器
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 应该显示GPU信息，而不是错误
```

## 📋 正确的Docker Compose配置

### 关键配置要素

1. **GPU设备分配**:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

2. **环境变量**:
```yaml
environment:
  - NVIDIA_VISIBLE_DEVICES=all
  - NVIDIA_DRIVER_CAPABILITIES=compute,utility
  - CUDA_VISIBLE_DEVICES=all
  - CUDA_MODULE_LOADING=LAZY
```

3. **基础镜像选择**:
```dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
```

## 🔍 验证配置

### 检查NVIDIA支持
```bash
# 启动服务
docker-compose -f docker-compose.nvidia-fixed.yml up -d

# 进入容器检查GPU
docker exec -it hailo8-ai nvidia-smi

# 检查CUDA
docker exec -it hailo8-ai python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### API测试
```bash
# 检查硬件状态
curl http://localhost:8000/ai/hardware

# 应该看到类似输出:
{
  "available_engines": ["hailo", "nvidia"],
  "nvidia_devices": [
    {
      "id": 0,
      "name": "NVIDIA GeForce RTX 4090",
      "memory_total": 24576,
      "memory_allocated": 0
    }
  ]
}
```

## ⚠️ 常见问题

### 1. "Could not select device driver"
**原因**: NVIDIA Container Toolkit未正确安装
**解决**: 重新安装NVIDIA Container Toolkit

### 2. "CUDA runtime error"
**原因**: CUDA版本不匹配或驱动版本过低
**解决**: 更新NVIDIA驱动到最新版本

### 3. "GPU内存不足"
**原因**: GPU内存被其他进程占用
**解决**: 检查GPU使用情况并释放内存

### 4. "权限被拒绝"
**原因**: 用户不在docker组中
**解决**:
```bash
sudo usermod -aG docker $USER
# 重新登录或执行 newgrp docker
```

## 🎯 完整部署流程

```bash
# 1. 检查系统要求
nvidia-smi
docker --version

# 2. 安装NVIDIA Container Toolkit (如果未安装)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update && sudo apt install -y nvidia-docker2
sudo systemctl restart docker

# 3. 验证容器支持
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi

# 4. 启动AI加速服务
docker-compose -f docker-compose.nvidia-fixed.yml up -d

# 5. 验证服务
curl http://localhost:8000/ai/hardware
```

## 📊 性能优化

### GPU内存管理
```yaml
environment:
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
  - CUDA_LAUNCH_BLOCKING=1  # 调试时使用
```

### 批处理优化
```yaml
environment:
  - TORCH_CUDA_ARCH_LIST="8.6"  # 根据GPU架构调整
  - CUDA_VISIBLE_DEVICES=0      # 指定使用哪块GPU
```

## 🎉 总结

现在配置已经正确支持NVIDIA容器：

✅ **正确安装NVIDIA Container Toolkit**
✅ **使用deploy.resources.reservations配置GPU**
✅ **设置正确的NVIDIA环境变量**
✅ **使用NVIDIA CUDA基础镜像**
✅ **完整的健康检查和验证流程**

这样NVIDIA显卡就能在容器中正常工作，与Hailo8一起提供双硬件AI加速服务！