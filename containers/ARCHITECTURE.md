# Hailo8 容器化服务架构设计

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host / 飞牛OS                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Hailo8 PCIe 硬件设备                      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (PCIe + /dev/hailo0)
┌─────────────────────────────────────────────────────────────┐
│                Hailo8 Runtime Container                     │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │   Linux 内核     │  │       HailoRT Python API        │  │
│  │   驱动模块       │  │      (hailo_platform)          │  │
│  │ hailo1x_pci.ko  │  │                                 │  │
│  └─────────────────┘  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              HTTP API 服务层                        │    │
│  │         (FastAPI + gRPC)                           │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              模型管理服务                            │    │
│  │        (模型加载、推理、结果缓存)                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (HTTP/gRPC)
┌─────────────────────────────────────────────────────────────┐
│                  Application Containers                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Web App   │  │  AI Service │  │   Data Processing   │  │
│  │   (前端)     │  │  (AI服务)   │  │     (数据处理)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 设计原则

1. **单一职责**: 每个容器专注特定功能
2. **松耦合**: 通过API接口通信
3. **可扩展**: 支持水平扩展
4. **高可用**: 支持多实例部署
5. **安全性**: 设备权限和网络隔离

## 📦 容器组件

### 1. hailo-runtime (核心运行时容器)
- **功能**: 提供Hailo8硬件访问和AI推理服务
- **组件**:
  - Linux内核驱动模块 (hailo1x_pci.ko)
  - HailoRT Python API
  - HTTP API服务 (FastAPI)
  - gRPC服务接口
  - 模型管理器
- **端口**: 8000 (HTTP), 50051 (gRPC)
- **设备**: /dev/hailo0, /dev/hailo1

### 2. hailo-web-app (Web应用示例)
- **功能**: 展示如何使用Hailo8推理的Web界面
- **技术**: React/Vue + Node.js
- **端口**: 3000

### 3. hailo-ai-service (AI服务示例)
- **功能**: 图像处理、视频分析等AI应用
- **技术**: Python + OpenCV + Hailo8 API
- **端口**: 8080

### 4. hailo-model-manager (模型管理)
- **功能**: 模型上传、版本管理、热加载
- **存储**: /models (挂载卷)
- **端口**: 9000

## 🔗 通信方式

### API接口
```yaml
# REST API (端口 8000)
POST /api/v1/inference          # 执行推理
GET  /api/v1/models             # 获取模型列表
POST /api/v1/models/load        # 加载模型
GET  /api/v1/device/info        # 设备信息

# gRPC (端口 50051)
service HailoInference {
  rpc Inference(Request) returns (Response);
  rpc StreamInference(stream Request) returns (stream Response);
}
```

### 数据流
```
输入数据 → 应用容器 → HTTP/gRPC → 运行时容器 → Hailo8硬件 → 推理结果 → 应用容器
```

## 🛠️ 部署方式

### Docker Compose (推荐)
```bash
docker-compose up -d
```

### Kubernetes (生产环境)
```yaml
# 支持 HPA, VPA, 自动扩缩容
# 使用 Device Plugin 访问硬件
```

## 📁 目录结构

```
containers/
├── architecture.md              # 架构文档
├── docker-compose.yml          # 完整服务编排
├── docker-compose.dev.yml      # 开发环境配置
├── hailo-runtime/              # 核心运行时容器
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/
│   │   ├── main.py            # FastAPI 服务
│   │   ├── inference.py       # 推理逻辑
│   │   └── models.py          # 数据模型
│   ├── models/                # 示例模型文件
│   └── scripts/
│       ├── install_driver.sh  # 驱动安装脚本
│       └── health_check.sh    # 健康检查
├── hailo-web-app/              # Web应用示例
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── hailo-ai-service/           # AI服务示例
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── nginx/                      # 反向代理配置
│   ├── Dockerfile
│   └── nginx.conf
├── models/                     # 模型文件目录
├── config/                     # 配置文件
└── docs/                       # 使用文档
```

## 🔒 安全考虑

1. **设备权限**: 限制容器对硬件设备的访问
2. **网络隔离**: 使用Docker网络隔离各服务
3. **资源限制**: CPU、内存使用限制
4. **API认证**: JWT token认证
5. **数据加密**: HTTPS/TLS通信

## 📊 监控和日志

- **Prometheus**: 指标收集
- **Grafana**: 可视化监控
- **ELK Stack**: 日志聚合分析
- **健康检查**: 容器健康状态监控

## 🚀 扩展能力

1. **水平扩展**: 支持多个运行时容器实例
2. **模型热加载**: 运行时更新模型
3. **批处理**: 支持批量推理
4. **流处理**: 实时视频流处理
5. **多云部署**: 支持私有云和公有云部署