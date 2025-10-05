# Frigate Setup Wizard with Hailo8 Integration

一个现代化的Web界面，用于简化Frigate NVR系统的安装和配置，集成了Hailo8 TPU加速支持。

## 项目特性

### 🚀 核心功能
- **一键安装Frigate** - 自动化Docker环境配置
- **Hailo8 TPU集成** - 智能检测和安装Hailo8加速器
- **可视化配置** - 直观的Web界面配置摄像头和检测器
- **硬件检测** - 自动识别系统硬件和兼容性
- **实时监控** - 安装过程实时反馈

### 🎯 支持的安装模式
1. **标准安装** - Frigate + CPU检测
2. **Coral加速** - Frigate + Google Coral TPU
3. **Hailo8加速** - Frigate + Hailo8 TPU (新功能)
4. **混合模式** - 多种加速器组合

### 🛠 技术栈
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **后端**: Python Flask
- **容器化**: Docker & Docker Compose
- **硬件集成**: Hailo8 TPU, Google Coral
- **系统支持**: Ubuntu, Debian, Raspberry Pi OS

## 快速开始

### 系统要求
- Ubuntu 20.04+ 或 Debian 11+
- Docker 20.10+
- Python 3.8+
- 至少4GB RAM
- 20GB可用存储空间

### 一键安装
```bash
# 下载并运行安装向导
curl -fsSL https://raw.githubusercontent.com/your-repo/frigate-wizard/main/install.sh | bash

# 或者手动安装
git clone https://github.com/your-repo/frigate-wizard.git
cd frigate-wizard
./setup.sh
```

### 访问Web界面
安装完成后，访问: `http://your-server-ip:8080`

## 项目结构

```
frigate_wizard/
├── app/                    # Flask应用
│   ├── __init__.py
│   ├── routes/            # 路由模块
│   ├── templates/         # HTML模板
│   ├── static/           # 静态资源
│   └── services/         # 业务逻辑
├── hailo8_integration/    # Hailo8集成模块
├── docker/               # Docker配置
├── scripts/              # 安装脚本
├── config/               # 配置文件
└── tests/                # 测试用例
```

## 安装流程

### 1. 系统检测
- 操作系统兼容性检查
- Docker环境验证
- 硬件设备扫描
- 网络连接测试

### 2. 硬件配置
- 自动检测Hailo8 TPU
- 配置设备权限
- 安装必要驱动
- 性能基准测试

### 3. Frigate部署
- 生成Docker Compose配置
- 创建存储目录
- 配置网络端口
- 启动服务容器

### 4. 摄像头配置
- 网络摄像头发现
- RTSP流配置
- 检测区域设置
- 录制参数调整

## Hailo8集成特性

### 🔧 自动安装
- 智能检测Hailo8硬件
- 自动下载和安装驱动
- 配置HailoRT运行时
- 优化性能参数

### ⚡ 性能优化
- 自动模型量化
- 推理加速配置
- 内存使用优化
- 多流并行处理

### 📊 监控面板
- 实时性能指标
- TPU使用率监控
- 温度和功耗显示
- 错误日志追踪

## 使用指南

### Web界面操作

1. **欢迎页面** - 选择安装模式
2. **系统检测** - 查看兼容性报告
3. **硬件配置** - 配置Hailo8设置
4. **Frigate设置** - 基础参数配置
5. **摄像头添加** - 配置视频源
6. **完成安装** - 启动服务

### 命令行工具

```bash
# 检查安装状态
frigate-wizard status

# 重新配置Hailo8
frigate-wizard configure-hailo8

# 更新Frigate版本
frigate-wizard update

# 备份配置
frigate-wizard backup

# 卸载服务
frigate-wizard uninstall
```

## 配置示例

### Hailo8配置
```yaml
hailo8:
  enabled: true
  device_id: 0
  model_path: "/opt/hailo8/models"
  optimization_level: "high"
  batch_size: 1
  threads: 4
```

### Frigate配置
```yaml
detectors:
  hailo8:
    type: hailo8
    device: 0
    
cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://camera-ip/stream
          roles: [detect, record]
    detect:
      width: 1280
      height: 720
      fps: 10
```

## 故障排除

### 常见问题

**Q: Hailo8设备未检测到**
```bash
# 检查设备连接
lspci | grep Hailo
# 重新安装驱动
sudo frigate-wizard reinstall-hailo8
```

**Q: Docker权限错误**
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER
# 重新登录生效
```

**Q: 摄像头连接失败**
```bash
# 测试RTSP流
ffmpeg -i rtsp://camera-ip/stream -t 10 -f null -
```

## 开发指南

### 本地开发环境

```bash
# 克隆项目
git clone https://github.com/your-repo/frigate-wizard.git
cd frigate-wizard

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py --debug
```

### 添加新功能

1. 在`app/routes/`中添加新路由
2. 在`app/templates/`中创建模板
3. 在`app/static/`中添加静态资源
4. 更新`tests/`中的测试用例

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

### 代码规范
- 遵循PEP 8
- 添加适当的注释
- 编写单元测试
- 更新文档

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

- [Frigate NVR](https://github.com/blakeblackshear/frigate) - 优秀的开源NVR系统
- [Hailo](https://hailo.ai/) - 高性能AI加速器
- 社区贡献者们的支持和反馈

## 联系方式

- 项目主页: https://github.com/your-repo/frigate-wizard
- 问题反馈: https://github.com/your-repo/frigate-wizard/issues
- 讨论区: https://github.com/your-repo/frigate-wizard/discussions

---

**让Frigate安装变得简单，让AI加速触手可及！** 🚀