# 🚀 Hailo8容器化服务 - 快速开始指南

## 📋 前置检查清单

在开始之前，请确认以下条件：

- [ ] **硬件**: Hailo8 PCIe加速卡已安装
- [ ] **系统**: Linux系统，内核版本4.15+
- [ ] **Docker**: Docker Engine 20.10+ 已安装
- [ ] **权限**: 具有sudo权限的用户账户

## ⚡ 5分钟快速部署

### 1️⃣ 克隆项目
```bash
git clone <repository-url>
cd hailo8/containers
```

### 2️⃣ 配置设备权限
```bash
sudo ./setup_device_permissions.sh
# 重新登录使权限生效
```

### 3️⃣ 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 等待服务启动（约1-2分钟）
```

### 4️⃣ 验证部署
```bash
# 检查服务状态
docker-compose ps

# 应该看到所有服务都是 "Up" 状态
```

### 5️⃣ 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 Web界面 | http://localhost:3000 | 用户界面 |
| 📡 API文档 | http://localhost:8000/docs | API文档 |
| 📊 监控面板 | http://localhost:3001 | Grafana监控 |
| 🔍 服务状态 | http://localhost:8000/health | 健康检查 |

## 🧪 测试推理功能

### 使用curl测试
```bash
# 下载测试图片
wget https://example.com/test-image.jpg -O test.jpg

# 执行推理
curl -X POST \
  http://localhost:8000/api/v1/inference/image \
  -F "file=@test.jpg" \
  -F "confidence_threshold=0.5"
```

### 使用Python客户端
```python
import requests

# 上传图片进行推理
with open('test.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/v1/inference/image',
        files=files
    )

print(response.json())
```

## 🔧 开发模式

如果需要修改代码或进行开发：

```bash
# 启动开发环境（支持代码热重载）
docker-compose -f docker-compose.dev.yml up -d

# 进入开发容器
docker exec -it hailo-runtime-dev bash

# 查看实时日志
docker-compose -f docker-compose.dev.yml logs -f hailo-runtime
```

## 📊 查看监控

1. **访问Grafana**: http://localhost:3001
   - 用户名: `admin`
   - 密码: `admin123`

2. **访问Prometheus**: http://localhost:9091

3. **查看服务指标**:
```bash
curl http://localhost:8000/metrics
```

## 🆘 常见问题解决

### 问题1: 容器启动失败
```bash
# 查看错误日志
docker-compose logs hailo-runtime

# 重新构建
docker-compose build --no-cache
```

### 问题2: 设备权限错误
```bash
# 重新设置权限
sudo ./setup_device_permissions.sh

# 检查设备状态
ls -la /dev/hailo*
```

### 问题3: API调用失败
```bash
# 检查服务健康状态
curl http://localhost:8000/health

# 检查网络连接
docker network ls
```

## 📚 下一步

- 📖 阅读完整文档: [README.md](./README.md)
- 🏗️ 了解架构设计: [ARCHITECTURE.md](./ARCHITECTURE.md)
- 🔧 自定义配置: 编辑 `.env` 文件
- 🚀 部署到生产环境: 使用 `docker-compose.yml`

## 💡 提示

- 首次启动可能需要较长时间来下载镜像
- 建议使用SSD存储以提高性能
- 生产环境请修改默认密码和密钥
- 定期检查系统资源使用情况

---

🎉 **恭喜！您已成功部署Hailo8容器化服务！**

如有问题，请查看 [完整文档](./README.md) 或提交Issue。