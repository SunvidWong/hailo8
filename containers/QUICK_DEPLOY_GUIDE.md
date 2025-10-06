# 🚀 Hailo8 快速部署指南

5分钟内搭建Hailo8 AI推理服务

## 📋 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- Hailo8 PCIe硬件已安装
- Linux系统，内核4.15+

## ⚡ 一键部署

### 方式1: 使用快速配置

```bash
# 1. 克隆项目
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers

# 2. 快速部署
docker-compose -f docker-compose.quick.yml up -d

# 3. 等待服务启动 (约1-2分钟)
docker-compose -f docker-compose.quick.yml ps
```

### 方式2: 生产级部署

```bash
# 1. 配置环境变量
cp .env.remote .env
vim .env  # 修改域名和密码

# 2. 使用自动化脚本
./deploy-remote.sh 192.168.1.100
```

## 🌐 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| API文档 | http://localhost:8000/docs | Swagger UI |
| Web界面 | http://localhost:3000 | React前端 |
| AI服务 | http://localhost:8080 | Python AI应用 |
| 容器管理 | http://localhost:9000 | Portainer |
| Redis | localhost:6379 | 缓存服务 |

## 🧪 测试验证

```bash
# API健康检查
curl http://localhost:8000/health

# 图像推理测试
curl -X POST \
  http://localhost:8000/api/v1/inference/image \
  -F "file=@test.jpg" \
  -F "confidence_threshold=0.5"

# 查看服务状态
docker-compose -f docker-compose.quick.yml ps
```

## 🔧 常用命令

```bash
# 查看日志
docker-compose -f docker-compose.quick.yml logs -f

# 重启服务
docker-compose -f docker-compose.quick.yml restart

# 停止服务
docker-compose -f docker-compose.quick.yml down

# 更新服务
docker-compose -f docker-compose.quick.yml pull
docker-compose -f docker-compose.quick.yml up -d
```

## ❓ 故障排除

### 权限问题
```bash
# 设置设备权限
sudo chmod 666 /dev/hailo*
sudo usermod -a -G docker $USER
newgrp docker
```

### 端口冲突
```bash
# 检查端口占用
netstat -tlnp | grep :8000

# 修改端口
vim docker-compose.quick.yml
```

### 服务无法启动
```bash
# 查看详细错误
docker-compose -f docker-compose.quick.yml logs hailo-runtime

# 重新构建
docker-compose -f docker-compose.quick.yml build --no-cache
```

## 📚 完整文档

- [详细配置指南](./DOCKER_COMPOSE_REMOTE_GUIDE.md)
- [远程部署文档](./REMOTE_DEPLOYMENT.md)
- [架构设计文档](./ARCHITECTURE.md)

---

🎉 **开始使用Hailo8 AI推理服务！**