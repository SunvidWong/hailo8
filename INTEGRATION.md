# Hailo8 TPU 项目集成指南

本文档详细说明如何将 Hailo8 TPU 智能安装管理器集成到其他项目中。

## 概述

Hailo8 安装管理器提供了完整的项目集成功能，可以轻松地将 Hailo8 TPU 支持添加到现有项目中，包括：

- **自动化集成**: 一键集成到现有项目
- **配置管理**: 灵活的配置选项
- **脚本生成**: 自动生成集成脚本
- **文档生成**: 自动生成项目文档
- **Docker 支持**: 完整的容器化支持

## 集成方式

### 1. 作为 Python 包集成

#### 安装包

```bash
# 从源码安装
cd Linux-debain-intall-hailo8
pip install -e .

# 或者直接安装
pip install hailo8-installer
```

#### 在项目中使用

```python
from hailo8_installer import install_hailo8, test_hailo8, setup_docker

# 基本使用
success = install_hailo8()
if success:
    print("Hailo8 安装成功")

# 测试安装
test_result = test_hailo8()
if test_result:
    print("Hailo8 测试通过")

# 设置 Docker
docker_success = setup_docker()
if docker_success:
    print("Docker 环境设置成功")
```

### 2. 项目集成模式

#### 快速集成

```python
from hailo8_installer.integration import quick_integrate

# 快速集成到现有项目
success = quick_integrate(
    project_path="/path/to/your/project",
    hailo8_enabled=True,
    docker_enabled=True,
    auto_install=False
)
```

#### 详细集成

```python
from hailo8_installer.integration import create_integration

# 创建集成配置
integrator = create_integration(
    project_name="MyProject",
    project_path="/path/to/project",
    hailo8_enabled=True,
    docker_enabled=True,
    auto_install=True,
    log_level="INFO",
    custom_settings={
        "install_timeout": 600,
        "retry_count": 5
    }
)

# 执行集成
success = integrator.integrate_with_project()
```

### 3. 命令行集成

```bash
# 使用安装脚本
cd Linux-debain-intall-hailo8
./install.sh --integrate-project /path/to/project

# 或者使用 Python 模块
python -m hailo8_installer.integration --project-path /path/to/project
```

## 集成后的项目结构

集成完成后，你的项目将包含以下结构：

```
your_project/
├── hailo8/                     # Hailo8 集成目录
│   ├── config/                 # 配置文件
│   │   ├── hailo8_integration.yaml
│   │   └── hailo8.env
│   ├── scripts/                # 集成脚本
│   │   ├── install_hailo8.py
│   │   ├── test_hailo8.py
│   │   ├── docker_hailo8.py
│   │   └── startup.sh
│   ├── logs/                   # 日志文件
│   ├── docker/                 # Docker 相关文件
│   ├── tests/                  # 测试文件
│   ├── README.md              # 集成说明
│   └── API.md                 # API 文档
└── [你的原有项目文件]
```

## 配置选项

### 基本配置

```yaml
# hailo8/config/hailo8_integration.yaml
project:
  name: "MyProject"
  hailo8_enabled: true
  docker_enabled: true

hailo8:
  install_dir: "./hailo8"
  auto_install: false
  log_level: "INFO"

docker:
  enabled: true
  image_name: "myproject-hailo8"
  container_name: "myproject-hailo8-container"

custom:
  install_timeout: 600
  retry_count: 3
```

### 环境变量

```bash
# hailo8/config/hailo8.env
PROJECT_NAME=MyProject
HAILO8_ENABLED=True
DOCKER_ENABLED=True
HAILO8_INSTALL_DIR=./hailo8
LOG_LEVEL=INFO
```

## 使用集成后的功能

### 1. 安装 Hailo8

```bash
cd hailo8/scripts
python3 install_hailo8.py
```

### 2. 测试安装

```bash
python3 test_hailo8.py
```

### 3. 设置 Docker

```bash
python3 docker_hailo8.py
```

### 4. 使用启动脚本

```bash
./startup.sh
```

### 5. 在代码中使用

```python
# 在你的项目代码中
import sys
import os
from pathlib import Path

# 添加 hailo8_installer 到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from hailo8_installer import install_hailo8, test_hailo8

# 使用 Hailo8 功能
if not test_hailo8():
    print("Hailo8 未安装，开始安装...")
    install_hailo8()

# 你的业务逻辑
def main():
    # 使用 Hailo8 进行推理
    pass
```

## 高级集成选项

### 1. 自定义集成配置

```python
from hailo8_installer.integration import IntegrationConfig, ProjectIntegrator

# 创建自定义配置
config = IntegrationConfig(
    project_name="AdvancedProject",
    project_path="/path/to/project",
    hailo8_enabled=True,
    docker_enabled=True,
    auto_install=True,
    config_file="/custom/config.yaml",
    log_level="DEBUG",
    custom_settings={
        "advanced_features": True,
        "custom_docker_image": "my-custom-hailo8:latest",
        "install_location": "/opt/hailo8"
    }
)

# 创建集成器
integrator = ProjectIntegrator(config)

# 执行集成
success = integrator.integrate_with_project()

# 获取集成状态
status = integrator.get_integration_status()
print(f"集成状态: {status}")

# 导出配置
integrator.export_integration_config("integration_config.yaml")
```

### 2. 条件集成

```python
from hailo8_installer.integration import integrate_with_existing_project
from hailo8_installer.utils import get_system_info

# 根据系统信息决定是否集成
system_info = get_system_info()

if system_info['distro_name'] in ['ubuntu', 'debian']:
    success = integrate_with_existing_project(
        project_path="/path/to/project",
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=True
    )
else:
    print("不支持的系统，跳过 Hailo8 集成")
```

### 3. 批量集成

```python
import os
from hailo8_installer.integration import quick_integrate

# 批量集成多个项目
projects = [
    "/path/to/project1",
    "/path/to/project2", 
    "/path/to/project3"
]

for project_path in projects:
    if os.path.exists(project_path):
        print(f"集成项目: {project_path}")
        success = quick_integrate(
            project_path=project_path,
            hailo8_enabled=True,
            docker_enabled=True
        )
        if success:
            print(f"✓ {project_path} 集成成功")
        else:
            print(f"✗ {project_path} 集成失败")
```

## Docker 集成

### 1. 基本 Docker 集成

集成后会自动生成 Docker 相关文件：

```dockerfile
# hailo8/docker/Dockerfile
FROM ubuntu:20.04

# 安装 Hailo8 依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    build-essential

# 复制 Hailo8 安装器
COPY hailo8_installer/ /opt/hailo8_installer/

# 安装 Hailo8
RUN cd /opt/hailo8_installer && python3 -m pip install -e .

# 运行安装
RUN python3 -c "from hailo8_installer import install_hailo8; install_hailo8()"

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

CMD ["python3", "main.py"]
```

### 2. Docker Compose 集成

```yaml
# hailo8/docker/docker-compose.yml
version: '3.8'

services:
  myproject-hailo8:
    build:
      context: ../..
      dockerfile: hailo8/docker/Dockerfile
    container_name: myproject-hailo8-container
    devices:
      - /dev/hailo0:/dev/hailo0
    volumes:
      - ../logs:/app/logs
      - ../config:/app/config
    environment:
      - HAILO8_ENABLED=true
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

## CI/CD 集成

### GitHub Actions

```yaml
# .github/workflows/hailo8-test.yml
name: Hailo8 Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    
    - name: Install Hailo8 Installer
      run: |
        cd hailo8
        pip install -e ../
    
    - name: Test Hailo8 Installation
      run: |
        cd hailo8/scripts
        python3 test_hailo8.py
```

### Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'cd hailo8 && pip install -e ../'
            }
        }
        
        stage('Test Hailo8') {
            steps {
                sh 'cd hailo8/scripts && python3 test_hailo8.py'
            }
        }
        
        stage('Build Docker') {
            steps {
                sh 'cd hailo8/docker && docker build -t myproject-hailo8 .'
            }
        }
    }
}
```

## 故障排除

### 常见问题

1. **集成失败**
   ```bash
   # 检查权限
   ls -la /path/to/project
   
   # 检查 Python 路径
   python3 -c "import sys; print(sys.path)"
   ```

2. **配置文件错误**
   ```bash
   # 验证 YAML 格式
   python3 -c "import yaml; yaml.safe_load(open('hailo8/config/hailo8_integration.yaml'))"
   ```

3. **Docker 问题**
   ```bash
   # 检查 Docker 状态
   systemctl status docker
   
   # 检查设备权限
   ls -la /dev/hailo*
   ```

### 调试模式

```python
from hailo8_installer.integration import create_integration

# 启用调试模式
integrator = create_integration(
    project_name="DebugProject",
    project_path="/path/to/project",
    log_level="DEBUG",
    custom_settings={
        "debug_mode": True,
        "keep_temp_files": True
    }
)

# 查看详细日志
integrator.integrate_with_project()
```

## 最佳实践

### 1. 版本管理

```python
# 在项目中固定版本
from hailo8_installer import __version__
print(f"使用 Hailo8 安装器版本: {__version__}")

# 检查兼容性
if __version__ < "1.0.0":
    raise RuntimeError("需要 Hailo8 安装器 1.0.0 或更高版本")
```

### 2. 错误处理

```python
from hailo8_installer import install_hailo8, test_hailo8
import logging

logger = logging.getLogger(__name__)

def setup_hailo8():
    """设置 Hailo8 环境"""
    try:
        # 测试现有安装
        if test_hailo8():
            logger.info("Hailo8 已安装并正常工作")
            return True
        
        # 尝试安装
        logger.info("开始安装 Hailo8...")
        if install_hailo8():
            logger.info("Hailo8 安装成功")
            return True
        else:
            logger.error("Hailo8 安装失败")
            return False
            
    except Exception as e:
        logger.error(f"Hailo8 设置异常: {e}")
        return False
```

### 3. 配置管理

```python
import os
from pathlib import Path

def get_hailo8_config():
    """获取 Hailo8 配置"""
    config_file = Path(__file__).parent / "hailo8" / "config" / "hailo8_integration.yaml"
    
    if config_file.exists():
        import yaml
        with open(config_file) as f:
            return yaml.safe_load(f)
    else:
        # 返回默认配置
        return {
            'hailo8': {
                'enabled': True,
                'auto_install': False
            }
        }
```

## 支持和帮助

如果在集成过程中遇到问题：

1. 查看日志文件：`hailo8/logs/`
2. 检查配置文件：`hailo8/config/`
3. 运行诊断脚本：`hailo8/scripts/test_hailo8.py`
4. 查看 API 文档：`hailo8/API.md`

## 更新和维护

### 更新集成

```bash
# 更新 Hailo8 安装器
pip install --upgrade hailo8-installer

# 重新生成集成文件
cd hailo8/scripts
python3 -c "
from hailo8_installer.integration import quick_integrate
quick_integrate('../../', force_update=True)
"
```

### 清理集成

```bash
# 移除集成文件
rm -rf hailo8/

# 或者使用清理脚本
python3 -c "
from hailo8_installer.integration import cleanup_integration
cleanup_integration('/path/to/project')
"
```

这个集成指南提供了完整的项目集成方案，让你可以轻松地将 Hailo8 TPU 支持添加到任何现有项目中。