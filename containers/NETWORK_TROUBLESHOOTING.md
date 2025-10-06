# 网络连接问题解决方案

## 🔍 常见网络问题

### 1. Docker Hub连接问题
```
Error response from daemon: Get "https://registry-1.docker.io/v2/":
read tcp xx.xx.xx.xx:xx -> xx.xx.xx.xx:443: read: connection reset by peer
```

### 2. GitHub Container Registry访问问题
```
Error Head "https://ghcr.io/v2/sunvidwong/hailo8-nvidia-hailo/manifests/latest": denied
```

## 🔧 解决方案

### 方案一：本地构建镜像（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers

# 2. 使用本地构建配置
docker-compose -f docker-compose.hailo8-local.yml up -d

# 3. 验证部署
curl http://localhost:8000/health
```

### 方案二：配置国内镜像源

```bash
# 1. 配置Docker镜像加速器
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
EOF

# 2. 重启Docker服务
sudo systemctl daemon-reload
sudo systemctl restart docker

# 3. 重新拉取镜像
docker-compose -f docker-compose.hailo8-deploy.yml up -d
```

### 方案三：使用阿里云镜像

修改 `docker-compose.hailo8-deploy.yml` 中的镜像地址：

```yaml
services:
  hailo8-ai:
    image: registry.cn-hangzhou.aliyuncs.com/sunvidwong/hailo8-nvidia-hailo:latest
    # ... 其他配置
```

## 📋 可用配置文件

| 配置文件 | 适用场景 | 特点 |
|----------|----------|------|
| `docker-compose.hailo8-local.yml` | 网络问题 | 本地构建，无需网络 |
| `docker-compose.hailo8-deploy.yml` | 正常网络 | 远程镜像 |
| `docker-compose.official.yml` | 开发环境 | 完整功能 |

## 🚀 快速部署命令

### 针对网络问题的部署

```bash
# 方法1：本地构建
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers
docker-compose -f docker-compose.hailo8-local.yml up -d

# 方法2：使用国内镜像源
wget https://raw.githubusercontent.com/SunvidWong/hailo8/main/containers/docker-compose.hailo8-deploy.yml
# 修改镜像地址为国内源
docker-compose -f docker-compose.hailo8-deploy.yml up -d
```

## 🔍 网络诊断

### 检查网络连接
```bash
# 测试Docker Hub连接
curl -v https://registry-1.docker.io/v2/

# 测试GitHub Container Registry
curl -v https://ghcr.io/v2/

# 检查DNS解析
nslookup registry-1.docker.io
nslookup ghcr.io
```

### 检查Docker配置
```bash
docker info | grep "Registry Mirrors"
docker system info
```

## 🛠️ 故障排除步骤

1. **检查网络连接**
   ```bash
   ping 8.8.8.8
   curl -I https://www.google.com
   ```

2. **检查Docker服务**
   ```bash
   sudo systemctl status docker
   sudo docker info
   ```

3. **配置镜像加速器**
   ```bash
   # 使用阿里云镜像加速器
   sudo tee /etc/docker/daemon.json <<EOF
   {
     "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"]
   }
   EOF
   sudo systemctl restart docker
   ```

4. **使用本地构建**
   ```bash
   # 克隆完整项目
   git clone https://github.com/SunvidWong/hailo8.git
   cd hailo8/containers

   # 本地构建
   docker-compose -f docker-compose.hailo8-local.yml up -d --build
   ```

## 📞 联系支持

如果问题仍然存在：

1. 检查防火墙设置
2. 确认网络代理配置
3. 联系网络管理员
4. 提交Issue到GitHub仓库

---

**推荐**: 在网络不稳定的环境中，优先使用 `docker-compose.hailo8-local.yml` 进行本地构建。