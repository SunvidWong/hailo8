# Hailo8 TPU 集成示例

本目录包含了将 Hailo8 TPU 智能安装管理器集成到不同类型项目中的完整示例。

## 📁 示例列表

### 1. 基础集成示例
- **文件**: `integration_example.py`
- **描述**: 展示各种集成方式的基础示例
- **特性**:
  - 快速集成
  - 详细集成
  - 自定义集成
  - 批量集成
  - 条件集成

### 2. Flask Web 应用集成
- **文件**: `flask_integration.py`
- **描述**: 将 Hailo8 支持集成到 Flask Web 应用
- **特性**:
  - Web API 接口
  - 实时状态监控
  - 推理服务
  - Docker 部署

### 3. Django Web 应用集成
- **文件**: `django_integration.py`
- **描述**: 将 Hailo8 支持集成到 Django Web 应用
- **特性**:
  - 完整的 Django 项目结构
  - 管理后台集成
  - REST API
  - 前端界面

### 4. FastAPI 应用集成
- **文件**: `fastapi_integration.py`
- **描述**: 将 Hailo8 支持集成到 FastAPI 应用
- **特性**:
  - 高性能异步 API
  - 自动 API 文档
  - 性能监控
  - 现代化前端

### 5. 微服务架构集成
- **文件**: `microservice_integration.py`
- **描述**: 在微服务架构中集成 Hailo8 支持
- **特性**:
  - API 网关
  - 推理服务
  - 模型服务
  - 监控服务
  - Kubernetes 部署

### 6. 完整 AI 平台集成
- **文件**: `ai_platform_complete.py`
- **描述**: 构建完整的 AI 平台，集成 Hailo8 TPU 支持
- **特性**:
  - 前端 React 应用
  - 后端 FastAPI 服务
  - ML 流水线
  - 模型注册中心
  - 监控系统
  - 完整部署配置

## 🚀 使用方法

### 运行示例

```bash
# 进入项目根目录
cd /path/to/Linux-debain-intall-hailo8

# 运行基础集成示例
python examples/integration_example.py

# 运行 Flask 集成示例
python examples/flask_integration.py

# 运行 Django 集成示例
python examples/django_integration.py

# 运行 FastAPI 集成示例
python examples/fastapi_integration.py

# 运行微服务集成示例
python examples/microservice_integration.py

# 运行完整 AI 平台示例
python examples/ai_platform_complete.py
```

### 生成的项目位置

所有示例都会在 `/tmp/` 目录下生成相应的项目：

- `/tmp/hailo8_integration_example/` - 基础集成示例
- `/tmp/flask_hailo8_app/` - Flask 应用
- `/tmp/django_hailo8_app/` - Django 应用
- `/tmp/fastapi_hailo8_app/` - FastAPI 应用
- `/tmp/hailo8_microservices/` - 微服务架构
- `/tmp/complete_ai_platform/` - 完整 AI 平台

## 📋 集成特性

### 🔧 核心功能
- **自动安装**: 自动检测和安装 Hailo8 驱动
- **设备管理**: Hailo8 设备状态监控
- **推理加速**: 高性能推理服务
- **模型优化**: 模型量化和编译
- **性能监控**: 实时性能指标

### 🌐 Web 集成
- **REST API**: 标准化 API 接口
- **实时监控**: WebSocket 实时数据
- **前端界面**: 现代化 Web 界面
- **用户认证**: 安全访问控制

### 🐳 部署支持
- **Docker**: 容器化部署
- **Docker Compose**: 多服务编排
- **Kubernetes**: 云原生部署
- **CI/CD**: 自动化部署流水线

### 📊 监控和日志
- **系统监控**: CPU、内存、磁盘使用率
- **设备监控**: Hailo8 温度、利用率
- **性能指标**: 推理延迟、吞吐量
- **日志管理**: 结构化日志记录

## 🛠️ 自定义集成

### 创建自定义集成

```python
from hailo8_installer.integration import integrate_with_existing_project

# 自定义集成配置
config = {
    "hailo8_features": [
        "inference_acceleration",
        "model_optimization",
        "performance_monitoring"
    ],
    "target_platforms": ["linux", "docker"],
    "api_integration": True,
    "monitoring": True,
    "custom_endpoints": [
        "/api/v1/hailo8/status",
        "/api/v1/hailo8/inference",
        "/api/v1/hailo8/metrics"
    ]
}

# 执行集成
integrate_with_existing_project(
    project_path="/path/to/your/project",
    project_name="Your Project",
    integration_type="detailed",
    config=config
)
```

### 集成配置选项

```yaml
# hailo8_config.yaml
hailo8:
  enabled: true
  device_id: 0
  optimization_level: 3
  
features:
  - inference_acceleration
  - model_optimization
  - performance_monitoring
  - auto_scaling

api:
  enabled: true
  prefix: "/api/v1/hailo8"
  authentication: true

monitoring:
  enabled: true
  metrics_interval: 5
  alert_thresholds:
    temperature: 70
    utilization: 90
```

## 📚 文档和支持

### 相关文档
- [集成指南](../INTEGRATION.md) - 详细集成说明
- [API 文档](../docs/API.md) - API 接口文档
- [配置参考](../docs/CONFIG.md) - 配置选项说明

### 获取帮助
- 查看示例代码中的注释
- 阅读生成项目中的 README.md
- 检查集成后的配置文件
- 运行测试脚本验证集成

## 🔍 故障排除

### 常见问题

1. **权限问题**
   ```bash
   sudo python examples/integration_example.py
   ```

2. **依赖缺失**
   ```bash
   pip install -r requirements.txt
   ```

3. **Hailo8 设备未检测到**
   ```bash
   # 检查设备状态
   lspci | grep Hailo
   
   # 重新安装驱动
   python -m hailo8_installer.installer --reinstall
   ```

4. **Docker 权限问题**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### 调试模式

```bash
# 启用详细日志
export HAILO8_LOG_LEVEL=DEBUG

# 运行示例
python examples/integration_example.py
```

## 🤝 贡献

欢迎提交新的集成示例！请确保：

1. 代码清晰易懂
2. 包含完整的文档
3. 提供使用说明
4. 添加错误处理
5. 包含测试用例

## 📄 许可证

这些示例遵循项目的 MIT 许可证。