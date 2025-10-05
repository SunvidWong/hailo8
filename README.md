# Hailo8 TPU 智能安装管理器 & 容器化服务

🚀 **完整的Hailo8 TPU解决方案 - 包含智能安装管理和容器化AI推理服务**

## 📖 项目概述

本项目提供了一套完整的Hailo8 TPU解决方案，包含：

1. **智能安装管理器** - 具有完整容错、纠错和回滚能力的安装管理软件
2. **容器化AI推理服务** - 将Hailo8硬件能力封装为标准化API服务

## ✨ 主要特性

### 🔧 智能安装管理器
- **智能容错**: 自动检测和处理安装过程中的各种错误
- **自动纠错**: 内置多种修复策略，自动解决常见问题
- **完整回滚**: 支持完整的安装回滚，确保系统安全
- **状态管理**: 实时保存安装状态，支持断点续装
- **Docker 集成**: 自动配置 Docker 以支持 Hailo8 设备访问
- **多平台支持**: 支持 Ubuntu、Debian、CentOS、RHEL、Fedora

### 🐳 容器化AI推理服务
- **微服务架构**: 支持水平扩展和负载均衡
- **标准化API**: RESTful API (FastAPI) + gRPC 双协议支持
- **Web界面**: React前端应用 + Python AI服务示例
- **监控体系**: Prometheus + Grafana 完整监控
- **日志收集**: ELK栈日志收集和分析
- **生产就绪**: 健康检查、自动恢复、负载均衡

## 🚀 快速开始

### 方案一：容器化AI推理服务（推荐）

#### 前置要求
- Hailo8 PCIe加速卡已安装
- Docker Engine 20.10+
- Linux系统，内核版本4.15+

#### 5分钟部署
```bash
# 克隆项目
git clone https://github.com/SunvidWong/hailo8.git
cd hailo8/containers

# 配置设备权限
sudo ./setup_device_permissions.sh

# 启动服务
docker-compose up -d

# 验证部署
curl http://localhost:8000/health
```

#### 服务访问
- 🌐 Web界面: http://localhost:3000
- 📡 API文档: http://localhost:8000/docs
- 📊 监控面板: http://localhost:3001

### 方案二：智能安装管理器

#### 系统要求
- Linux (Ubuntu 18.04+, Debian 9+, CentOS 7+, RHEL 7+, Fedora 30+)
- 内核版本 4.0+
- root权限
- 至少 2GB 可用空间

#### 安装步骤
```bash
# 准备环境
sudo su
pip3 install -r requirements.txt
chmod +x hailo8_installer.py

# 执行安装
python3 hailo8_installer.py

# 查看状态
python3 hailo8_installer.py --status
```

## 📁 项目结构

```
hailo8/
├── 📦 容器化服务
│   └── containers/
│       ├── 📋 README.md           # 容器化服务文档
│       ├── 📋 QUICK_START.md      # 5分钟快速开始
│       ├── 📋 ARCHITECTURE.md     # 架构设计文档
│       ├── 🐳 docker-compose.yml  # 生产环境编排
│       ├── 🐳 docker-compose.dev.yml # 开发环境
│       ├── ⚙️ setup_device_permissions.sh # 设备权限配置
│       ├── 🧪 test_services.sh    # 功能测试脚本
│       └── 📁 服务组件
│           ├── hailo-runtime/     # 核心运行时容器
│           ├── hailo-web-app/     # React前端应用
│           ├── hailo-ai-service/  # Python AI服务
│           └── nginx/             # 反向代理配置
├── 🔧 安装工具
│   ├── 🐧 docker_compile.sh       # Docker编译脚本
│   ├── 🐧 compile_hailo8_driver.sh # Linux编译脚本
│   ├── 📦 install_hailo8_onekey.sh # 一键安装脚本
│   └── 📚 文档和指南
│       ├── README.md              # 项目主文档
│       ├── INSTALL_GUIDE.md       # 安装指南
│       ├── PYTHON_ENV_GUIDE.md    # Python环境指南
│       └── MACOS_SOLUTION.md      # macOS解决方案
├── 📦 官方驱动源码
│   └── hailort-drivers-master/    # Hailo官方驱动源码
└── ⚙️ 配置文件
    ├── .gitignore                 # Git忽略文件
    └── .env.example              # 环境变量模板
```

## 🔧 使用指南

### 容器化服务使用

#### API调用示例
```bash
# 健康检查
curl http://localhost:8000/health

# 图像推理
curl -X POST \
  http://localhost:8000/api/v1/inference/image \
  -F "file=@image.jpg" \
  -F "confidence_threshold=0.5"

# 设备状态
curl http://localhost:8000/api/v1/device/status
```

#### Python客户端
```python
import requests

# 客户端类
class HailoClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def inference(self, image_path, confidence=0.5):
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'confidence_threshold': confidence}
            response = requests.post(
                f"{self.base_url}/api/v1/inference/image",
                files=files,
                data=data
            )
        return response.json()

# 使用示例
client = HailoClient()
result = client.inference("test.jpg")
print(result)
```

### 安装管理器使用

#### 基本命令
```bash
# 完整安装
python3 hailo8_installer.py

# 查看安装状态
python3 hailo8_installer.py --status

# 回滚安装
python3 hailo8_installer.py --rollback

# 修复安装
python3 hailo8_installer.py --repair
```

#### Docker集成使用
```bash
# 运行测试容器
docker run --rm --device=/dev/hailo0 hailo8:latest

# 在容器中使用Hailo8
docker run -it --device=/dev/hailo0 hailo8:latest python3 -c "
import hailo_platform
print('Hailo8 在 Docker 中运行正常')
"
```

## 📊 监控和运维

### 服务监控
- **Grafana仪表板**: http://localhost:3001 (admin/admin123)
- **Prometheus指标**: http://localhost:9091
- **服务日志**: `docker-compose logs -f`

### 健康检查
```bash
# 运行完整测试
./test_services.sh

# 快速测试
./test_services.sh --quick

# API测试
curl http://localhost:8000/health
```

## 🔍 故障排除

### 容器化服务问题
```bash
# 检查容器状态
docker-compose ps

# 查看详细日志
docker-compose logs hailo-runtime

# 重新构建容器
docker-compose build --no-cache

# 设备权限问题
sudo ./setup_device_permissions.sh
```

### 安装管理器问题
```bash
# 查看安装日志
tail -f /opt/hailo8/logs/hailo8_install_*.log

# 检查系统状态
python3 hailo8_installer.py --status

# 修复安装
python3 hailo8_installer.py --repair

# 完全回滚
python3 hailo8_installer.py --rollback
```

### 常见问题
1. **权限不足**: 使用sudo运行安装脚本
2. **包依赖问题**: 运行 `apt --fix-broken install -y`
3. **驱动加载失败**: 检查 `dmesg | grep hailo`
4. **设备节点不存在**: 检查 `ls -la /dev/hailo*`

## 🏗️ 架构设计

### 容器化架构
```
┌─────────────────────────────────────────┐
│           Hailo8 PCIe 硬件              │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Hailo8 Runtime Container        │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   驱动模块   │  │   HTTP/gRPC API │   │
│  │ hailo1x_pci │  │   (FastAPI)     │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Application Containers          │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   Web App   │  │   AI Services   │   │
│  │   (React)   │  │   (Python)      │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

### 安装管理器架构
```
┌─────────────────────────────────────────┐
│         智能安装管理器                   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  容错引擎   │  │   状态管理器     │   │
│  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  自动修复   │  │   回滚管理器     │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 发起Pull Request

## 📄 许可证

本项目遵循 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔄 更新日志

### v2.0.0 - 容器化服务版本
- ✨ 添加完整的容器化AI推理服务
- ✨ 微服务架构，支持水平扩展
- ✨ FastAPI + gRPC双协议支持
- ✨ Prometheus + Grafana监控体系
- ✨ React前端应用示例
- ✨ 完整的测试和文档

### v1.0.0 - 智能安装管理器
- ✨ 初始版本发布
- ✨ 支持完整的Hailo8安装流程
- ✨ 实现容错和回滚机制
- ✨ 添加Docker集成支持

## 📞 技术支持

- 📧 邮箱: support@example.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/SunvidWong/hailo8/issues)
- 📖 文档: [完整文档](./containers/README.md)

---

🎉 **感谢使用Hailo8 TPU解决方案！**

如果您觉得这个项目有用，请给它一个 ⭐️