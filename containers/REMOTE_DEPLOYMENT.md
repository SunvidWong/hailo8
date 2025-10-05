# Hailo8 远程部署指南

🚀 **完整的生产环境远程部署解决方案**

## 📋 部署概述

本指南提供了在生产环境远程服务器上部署Hailo8容器化AI推理服务的完整解决方案，包含自动化部署脚本、配置管理和监控体系。

## 🎯 部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                    远程生产服务器                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Hailo8 PCIe Hardware                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                              │                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Docker Compose Services                  │    │
│  │  ┌─────────────┐  ┌─────────────────────────────┐   │    │
│  │  │ Hailo Runtime│  │    Nginx (SSL + 负载均衡)   │   │    │
│  │  │   + gRPC     │  │                             │   │    │
│  │  └─────────────┘  └─────────────────────────────┘   │    │
│  │  ┌─────────────┐  ┌─────────────────────────────┐   │    │
│  │  │AI Services  │  │     Monitoring Stack       │   │    │
│  │  │ (多副本)    │  │ Prometheus + Grafana + ELK │   │    │
│  │  └─────────────┘  └─────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 环境要求

### 服务器配置
- **CPU**: 4核心以上，推荐8核心
- **内存**: 16GB以上，推荐32GB
- **存储**: 100GB以上SSD存储
- **网络**: 千兆网络连接
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

### 软件要求
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **SSH**: 开放22端口或其他指定端口
- **域名**: 配置域名解析（可选，HTTPS需要）

### 硬件要求
- **Hailo8 PCIe加速卡**: 已正确安装并识别
- **权限**: root权限或sudo权限

## 🚀 快速部署

### 1. 准备本地环境

```bash
# 克隆项目
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers

# 配置环境变量
cp .env.remote .env
vim .env  # 修改配置
```

### 2. 配置环境变量

编辑 `.env` 文件，配置以下关键参数：

```bash
# 服务器配置
DOMAIN=hailo-api.yourdomain.com          # 您的域名
API_URL=https://hailo-api.yourdomain.com
TZ=Asia/Shanghai                         # 时区

# 安全配置
JWT_SECRET_KEY=your-super-secret-key     # JWT密钥
GRAFANA_PASSWORD=your-secure-password    # Grafana密码

# 数据存储
DATA_PATH=/opt/hailo8/data               # 数据存储路径
```

### 3. 一键部署

```bash
# 基本部署
./deploy-remote.sh 192.168.1.100

# 指定用户和端口
./deploy-remote.sh -u deploy -p 2222 192.168.1.100

# 带备份的部署
./deploy-remote.sh -b 192.168.1.100
```

## 📝 部署脚本详解

### 基本用法

```bash
./deploy-remote.sh [选项] <服务器地址>

选项:
  -p, --port PORT        SSH端口 (默认: 22)
  -u, --user USER        SSH用户 (默认: root)
  -d, --path PATH        部署路径 (默认: /opt/hailo8)
  -f, --file FILE        Compose文件 (默认: docker-compose.remote.yml)
  -e, --env ENV          环境文件 (默认: .env.remote)
  -b, --backup           部署前备份现有服务
  -r, --rollback         回滚到上一个版本
  -s, --skip-ssl         跳过SSL证书检查
  -h, --help             显示帮助信息
```

### 部署示例

```bash
# 1. 标准部署到生产服务器
./deploy-remote.sh 192.168.1.100

# 2. 部署到特定用户的云服务器
./deploy-remote.sh -u ubuntu -p 2222 203.0.113.10

# 3. 自定义部署路径
./deploy-remote.sh -d /data/hailo8 192.168.1.100

# 4. 带备份的安全部署
./deploy-remote.sh -b 192.168.1.100

# 5. 回滚到上一个版本
./deploy-remote.sh -r 192.168.1.100
```

## 🔒 安全配置

### SSL证书配置

#### 方案1: 使用Let's Encrypt免费证书

```bash
# 在服务器上安装Certbot
ssh root@your-server
apt install certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d hailo-api.yourdomain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

#### 方案2: 使用自签名证书（测试用）

```bash
# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=CN/ST=State/L=City/O=Organization/CN=hailo-api.local"
```

### 防火墙配置

```bash
# Ubuntu/Debian
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw enable

# CentOS/RHEL
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

## 📊 监控配置

### Prometheus指标收集

系统自动收集以下指标：
- **服务指标**: API响应时间、请求量、错误率
- **系统指标**: CPU、内存、磁盘、网络使用率
- **容器指标**: Docker容器状态、资源使用
- **硬件指标**: Hailo8设备温度、功耗（如果支持）

### Grafana仪表板

访问地址：`http://your-server:3001`

默认账号：`admin` / `your-password`

主要仪表板：
- **系统总览**: 整体服务状态
- **API性能**: 接口响应时间和错误率
- **硬件监控**: Hailo8设备状态
- **容器监控**: Docker容器资源使用

### 日志收集

使用ELK Stack收集和分析日志：
- **Elasticsearch**: 日志存储和搜索
- **Logstash**: 日志处理和转换
- **Kibana**: 日志可视化界面

访问地址：`http://your-server:5601`

## 🔧 运维管理

### 服务管理

```bash
# SSH连接到服务器
ssh root@your-server

# 进入部署目录
cd /opt/hailo8

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 重启特定服务
docker-compose restart hailo-runtime

# 更新服务
docker-compose pull
docker-compose up -d

# 停止所有服务
docker-compose down

# 完全清理（包括数据）
docker-compose down -v
```

### 备份恢复

```bash
# 手动备份
cd /opt/hailo8
docker-compose exec hailo-runtime tar -czf /tmp/backup-$(date +%Y%m%d).tar.gz /app/data

# 自动备份（每天凌晨2点）
# 已在docker-compose中配置db-backup服务

# 恢复备份
./deploy-remote.sh -r your-server
```

### 性能优化

```bash
# 调整Docker资源限制
vim docker-compose.remote.yml

# 修改服务副本数
# 在AI服务中增加 replicas: 3

# 调整系统参数
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
sysctl -p
```

## 🔍 故障排除

### 常见问题

#### 1. SSH连接失败
```bash
# 检查SSH服务
systemctl status ssh

# 检查防火墙
ufw status

# 检查SSH密钥
ssh-keygen -l -f ~/.ssh/id_rsa.pub
```

#### 2. Docker服务启动失败
```bash
# 查看详细错误日志
docker-compose logs hailo-runtime

# 检查磁盘空间
df -h

# 检查内存使用
free -h

# 重启Docker服务
systemctl restart docker
```

#### 3. Hailo设备访问失败
```bash
# 检查设备权限
ls -la /dev/hailo*

# 检查驱动模块
lsmod | grep hailo

# 查看内核日志
dmesg | grep hailo

# 重新配置设备权限
./setup_device_permissions.sh
```

#### 4. 域名访问问题
```bash
# 检查DNS解析
nslookup hailo-api.yourdomain.com

# 检查Nginx配置
nginx -t

# 查看Nginx日志
tail -f /var/log/nginx/error.log
```

### 健康检查脚本

```bash
#!/bin/bash
# health-check.sh

# 检查API服务
if curl -f http://localhost:8000/health; then
    echo "✅ API服务正常"
else
    echo "❌ API服务异常"
fi

# 检查数据库连接
if docker exec hailo-redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis连接正常"
else
    echo "❌ Redis连接异常"
fi

# 检查硬件设备
if ls /dev/hailo* 2>/dev/null; then
    echo "✅ Hailo设备正常"
else
    echo "❌ Hailo设备未检测到"
fi
```

## 📈 扩展部署

### 多节点部署

```yaml
# docker-compose.cluster.yml
version: '3.8'

services:
  hailo-runtime:
    image: hailo8/runtime:2.0.0
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.hostname == worker-1

  hailo-ai-service:
    image: hailo8/ai-service:2.0.0
    deploy:
      replicas: 2
```

### Kubernetes部署

```yaml
# k8s/deployment.yaml
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
        image: hailo8/runtime:2.0.0
        resources:
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: hailo-device
          mountPath: /dev/hailo0
      volumes:
      - name: hailo-device
        hostPath:
          path: /dev/hailo0
```

## 📞 技术支持

### 联系方式
- 📧 邮箱: support@example.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/SunvidWong/hailo8/issues)
- 📖 文档: [项目文档](https://github.com/SunvidWong/hailo8)

### 支持信息
如需技术支持，请提供以下信息：
1. 服务器配置和操作系统版本
2. 错误日志和问题描述
3. 部署配置文件（敏感信息可删除）
4. 网络环境和防火墙配置

---

🎉 **感谢使用Hailo8远程部署方案！**

如有问题，请查阅文档或提交Issue获取支持。