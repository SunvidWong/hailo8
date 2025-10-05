#!/usr/bin/env python3
"""
Hailo8 安装器项目集成模块
提供与其他项目整合的接口和工具
"""

import os
import sys
import json
import yaml
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

from .installer import Hailo8Installer, InstallStatus
from .docker_manager import DockerHailo8Manager
from .tester import Hailo8Tester
from .utils import setup_logging, get_system_info

@dataclass
class IntegrationConfig:
    """集成配置类"""
    project_name: str
    project_path: str
    hailo8_enabled: bool = True
    docker_enabled: bool = True
    auto_install: bool = False
    config_file: Optional[str] = None
    log_level: str = "INFO"
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}

class ProjectIntegrator:
    """项目集成器"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.logger = setup_logging(level=config.log_level)
        self.installer = None
        self.docker_manager = None
        self.tester = None
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 创建安装器
            install_dir = os.path.join(self.config.project_path, 'hailo8')
            self.installer = Hailo8Installer(install_dir=install_dir)
            
            # 创建Docker管理器
            if self.config.docker_enabled:
                self.docker_manager = DockerHailo8Manager()
            
            # 创建测试器
            self.tester = Hailo8Tester()
            
            self.logger.info(f"项目集成器初始化完成: {self.config.project_name}")
            
        except Exception as e:
            self.logger.error(f"项目集成器初始化失败: {e}")
            raise
    
    def integrate_with_project(self) -> bool:
        """与项目集成"""
        self.logger.info(f"开始与项目集成: {self.config.project_name}")
        
        try:
            # 1. 创建项目目录结构
            if not self._setup_project_structure():
                return False
            
            # 2. 生成配置文件
            if not self._generate_config_files():
                return False
            
            # 3. 创建集成脚本
            if not self._create_integration_scripts():
                return False
            
            # 4. 生成文档
            if not self._generate_documentation():
                return False
            
            # 5. 自动安装（如果启用）
            if self.config.auto_install:
                if not self._auto_install_hailo8():
                    self.logger.warning("自动安装失败，但集成继续")
            
            self.logger.info("项目集成完成")
            return True
            
        except Exception as e:
            self.logger.error(f"项目集成失败: {e}")
            return False
    
    def _setup_project_structure(self) -> bool:
        """设置项目目录结构"""
        try:
            base_path = Path(self.config.project_path)
            
            # 创建必要目录
            directories = [
                'hailo8',
                'hailo8/config',
                'hailo8/scripts',
                'hailo8/logs',
                'hailo8/docker',
                'hailo8/tests'
            ]
            
            for directory in directories:
                dir_path = base_path / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"创建目录: {dir_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置项目结构失败: {e}")
            return False
    
    def _generate_config_files(self) -> bool:
        """生成配置文件"""
        try:
            config_dir = Path(self.config.project_path) / 'hailo8' / 'config'
            
            # 生成主配置文件
            main_config = {
                'project': {
                    'name': self.config.project_name,
                    'hailo8_enabled': self.config.hailo8_enabled,
                    'docker_enabled': self.config.docker_enabled
                },
                'hailo8': {
                    'install_dir': str(Path(self.config.project_path) / 'hailo8'),
                    'auto_install': self.config.auto_install,
                    'log_level': self.config.log_level
                },
                'docker': {
                    'enabled': self.config.docker_enabled,
                    'image_name': f"{self.config.project_name.lower()}-hailo8",
                    'container_name': f"{self.config.project_name.lower()}-hailo8-container"
                },
                'custom': self.config.custom_settings
            }
            
            # 保存为YAML格式
            config_file = config_dir / 'hailo8_integration.yaml'
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(main_config, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"配置文件已生成: {config_file}")
            
            # 生成环境变量文件
            env_file = config_dir / 'hailo8.env'
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"# Hailo8 环境变量配置\n")
                f.write(f"PROJECT_NAME={self.config.project_name}\n")
                f.write(f"HAILO8_ENABLED={self.config.hailo8_enabled}\n")
                f.write(f"DOCKER_ENABLED={self.config.docker_enabled}\n")
                f.write(f"HAILO8_INSTALL_DIR={Path(self.config.project_path) / 'hailo8'}\n")
                f.write(f"LOG_LEVEL={self.config.log_level}\n")
            
            return True
            
        except Exception as e:
            self.logger.error(f"生成配置文件失败: {e}")
            return False
    
    def _create_integration_scripts(self) -> bool:
        """创建集成脚本"""
        try:
            scripts_dir = Path(self.config.project_path) / 'hailo8' / 'scripts'
            
            # 创建安装脚本
            install_script = scripts_dir / 'install_hailo8.py'
            with open(install_script, 'w', encoding='utf-8') as f:
                f.write(self._generate_install_script())
            
            # 创建测试脚本
            test_script = scripts_dir / 'test_hailo8.py'
            with open(test_script, 'w', encoding='utf-8') as f:
                f.write(self._generate_test_script())
            
            # 创建Docker脚本
            if self.config.docker_enabled:
                docker_script = scripts_dir / 'docker_hailo8.py'
                with open(docker_script, 'w', encoding='utf-8') as f:
                    f.write(self._generate_docker_script())
            
            # 创建启动脚本
            startup_script = scripts_dir / 'startup.sh'
            with open(startup_script, 'w', encoding='utf-8') as f:
                f.write(self._generate_startup_script())
            
            # 设置执行权限
            os.chmod(startup_script, 0o755)
            
            self.logger.info("集成脚本已创建")
            return True
            
        except Exception as e:
            self.logger.error(f"创建集成脚本失败: {e}")
            return False
    
    def _generate_install_script(self) -> str:
        """生成安装脚本内容"""
        return f'''#!/usr/bin/env python3
"""
{self.config.project_name} - Hailo8 安装脚本
自动生成的集成脚本
"""

import sys
import os
from pathlib import Path

# 添加hailo8_installer到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hailo8_installer import install_hailo8, setup_logging

def main():
    """主函数"""
    # 设置日志
    logger = setup_logging(level="{self.config.log_level}")
    
    # 配置安装参数
    install_dir = Path(__file__).parent.parent
    config_file = install_dir / "config" / "hailo8_integration.yaml"
    
    logger.info("开始安装Hailo8...")
    
    # 执行安装
    success = install_hailo8(
        install_dir=str(install_dir),
        config_file=str(config_file) if config_file.exists() else None
    )
    
    if success:
        logger.info("Hailo8安装成功！")
        return 0
    else:
        logger.error("Hailo8安装失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    def _generate_test_script(self) -> str:
        """生成测试脚本内容"""
        return f'''#!/usr/bin/env python3
"""
{self.config.project_name} - Hailo8 测试脚本
自动生成的集成脚本
"""

import sys
import os
from pathlib import Path

# 添加hailo8_installer到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hailo8_installer import test_hailo8, setup_logging

def main():
    """主函数"""
    # 设置日志
    logger = setup_logging(level="{self.config.log_level}")
    
    logger.info("开始测试Hailo8...")
    
    # 执行测试
    success = test_hailo8()
    
    if success:
        logger.info("Hailo8测试通过！")
        return 0
    else:
        logger.error("Hailo8测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    def _generate_docker_script(self) -> str:
        """生成Docker脚本内容"""
        return f'''#!/usr/bin/env python3
"""
{self.config.project_name} - Hailo8 Docker脚本
自动生成的集成脚本
"""

import sys
import os
from pathlib import Path

# 添加hailo8_installer到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hailo8_installer import setup_docker, setup_logging

def main():
    """主函数"""
    # 设置日志
    logger = setup_logging(level="{self.config.log_level}")
    
    logger.info("开始设置Hailo8 Docker环境...")
    
    # 执行Docker设置
    success = setup_docker(
        image_name="{self.config.project_name.lower()}-hailo8",
        container_name="{self.config.project_name.lower()}-hailo8-container"
    )
    
    if success:
        logger.info("Hailo8 Docker环境设置成功！")
        return 0
    else:
        logger.error("Hailo8 Docker环境设置失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    def _generate_startup_script(self) -> str:
        """生成启动脚本内容"""
        return f'''#!/bin/bash
# {self.config.project_name} - Hailo8 启动脚本
# 自动生成的集成脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== {self.config.project_name} Hailo8 启动脚本 ==="

# 加载环境变量
if [ -f "$PROJECT_DIR/config/hailo8.env" ]; then
    source "$PROJECT_DIR/config/hailo8.env"
    echo "已加载环境变量"
fi

# 检查Hailo8状态
echo "检查Hailo8状态..."
python3 "$SCRIPT_DIR/test_hailo8.py"

if [ $? -eq 0 ]; then
    echo "Hailo8状态正常"
else
    echo "Hailo8状态异常，尝试重新安装..."
    python3 "$SCRIPT_DIR/install_hailo8.py"
fi

# 启动Docker（如果启用）
if [ "$DOCKER_ENABLED" = "True" ]; then
    echo "启动Hailo8 Docker环境..."
    python3 "$SCRIPT_DIR/docker_hailo8.py"
fi

echo "=== 启动完成 ==="
'''
    
    def _generate_documentation(self) -> bool:
        """生成文档"""
        try:
            project_dir = Path(self.config.project_path)
            
            # 生成集成说明文档
            readme_content = self._generate_integration_readme()
            readme_file = project_dir / 'hailo8' / 'README.md'
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # 生成API文档
            api_doc_content = self._generate_api_documentation()
            api_doc_file = project_dir / 'hailo8' / 'API.md'
            with open(api_doc_file, 'w', encoding='utf-8') as f:
                f.write(api_doc_content)
            
            self.logger.info("文档已生成")
            return True
            
        except Exception as e:
            self.logger.error(f"生成文档失败: {e}")
            return False
    
    def _generate_integration_readme(self) -> str:
        """生成集成说明文档"""
        return f'''# {self.config.project_name} - Hailo8 集成

本文档说明如何在 {self.config.project_name} 项目中使用 Hailo8 TPU。

## 概述

本集成提供了完整的 Hailo8 TPU 支持，包括：
- 自动安装和配置
- Docker 容器支持
- 完整的测试套件
- 故障恢复机制

## 目录结构

```
hailo8/
├── config/                 # 配置文件
│   ├── hailo8_integration.yaml
│   └── hailo8.env
├── scripts/                # 集成脚本
│   ├── install_hailo8.py
│   ├── test_hailo8.py
│   ├── docker_hailo8.py
│   └── startup.sh
├── logs/                   # 日志文件
├── docker/                 # Docker相关文件
├── tests/                  # 测试文件
├── README.md              # 本文档
└── API.md                 # API文档
```

## 快速开始

### 1. 安装 Hailo8

```bash
cd hailo8/scripts
python3 install_hailo8.py
```

### 2. 测试安装

```bash
python3 test_hailo8.py
```

### 3. 设置 Docker（可选）

```bash
python3 docker_hailo8.py
```

### 4. 使用启动脚本

```bash
./startup.sh
```

## 配置

主要配置文件位于 `config/hailo8_integration.yaml`：

```yaml
project:
  name: {self.config.project_name}
  hailo8_enabled: {self.config.hailo8_enabled}
  docker_enabled: {self.config.docker_enabled}

hailo8:
  install_dir: ./hailo8
  auto_install: {self.config.auto_install}
  log_level: {self.config.log_level}

docker:
  enabled: {self.config.docker_enabled}
  image_name: {self.config.project_name.lower()}-hailo8
  container_name: {self.config.project_name.lower()}-hailo8-container
```

## Python API

在你的 Python 代码中使用 Hailo8：

```python
from hailo8_installer import install_hailo8, test_hailo8, setup_docker

# 安装 Hailo8
success = install_hailo8()

# 测试 Hailo8
test_result = test_hailo8()

# 设置 Docker
docker_success = setup_docker()
```

## 故障排除

### 常见问题

1. **权限错误**: 确保以 root 权限运行安装脚本
2. **依赖缺失**: 运行 `install_hailo8.py` 会自动安装依赖
3. **Docker 问题**: 检查 Docker 服务是否运行

### 日志查看

日志文件位于 `logs/` 目录：
- `hailo8_installer.log`: 主要日志
- `docker.log`: Docker 相关日志
- `test.log`: 测试日志

### 重新安装

如果遇到问题，可以重新安装：

```bash
cd scripts
python3 install_hailo8.py --force-reinstall
```

## 支持

如有问题，请查看：
1. 日志文件
2. API 文档 (API.md)
3. 原始 Hailo8 安装器文档

## 更新

要更新 Hailo8 集成：

```bash
cd scripts
python3 install_hailo8.py --update
```
'''
    
    def _generate_api_documentation(self) -> str:
        """生成API文档"""
        return f'''# {self.config.project_name} - Hailo8 API 文档

本文档描述了 Hailo8 集成提供的 Python API。

## 主要函数

### install_hailo8()

安装 Hailo8 TPU 驱动和运行时。

```python
from hailo8_installer import install_hailo8

success = install_hailo8(
    install_dir="/path/to/install",  # 可选，安装目录
    config_file="/path/to/config.yaml",  # 可选，配置文件
    force_reinstall=False,  # 可选，强制重新安装
    skip_docker=False  # 可选，跳过Docker设置
)
```

**参数:**
- `install_dir` (str, 可选): 安装目录路径
- `config_file` (str, 可选): 配置文件路径
- `force_reinstall` (bool, 可选): 是否强制重新安装
- `skip_docker` (bool, 可选): 是否跳过Docker设置

**返回值:**
- `bool`: 安装是否成功

### test_hailo8()

测试 Hailo8 安装和功能。

```python
from hailo8_installer import test_hailo8

result = test_hailo8(
    full_test=True,  # 可选，是否执行完整测试
    generate_report=True  # 可选，是否生成测试报告
)
```

**参数:**
- `full_test` (bool, 可选): 是否执行完整测试套件
- `generate_report` (bool, 可选): 是否生成详细测试报告

**返回值:**
- `bool`: 测试是否通过

### setup_docker()

设置 Hailo8 Docker 环境。

```python
from hailo8_installer import setup_docker

success = setup_docker(
    image_name="my-hailo8",  # 可选，Docker镜像名称
    container_name="my-hailo8-container",  # 可选，容器名称
    build_image=True,  # 可选，是否构建镜像
    start_container=False  # 可选，是否启动容器
)
```

**参数:**
- `image_name` (str, 可选): Docker镜像名称
- `container_name` (str, 可选): 容器名称
- `build_image` (bool, 可选): 是否构建镜像
- `start_container` (bool, 可选): 是否启动容器

**返回值:**
- `bool`: Docker设置是否成功

## 类和对象

### Hailo8Installer

主要的安装器类。

```python
from hailo8_installer.installer import Hailo8Installer

installer = Hailo8Installer(
    install_dir="/path/to/install",
    config_file="/path/to/config.yaml"
)

# 执行安装
success = installer.install()

# 获取状态
status = installer.get_status()

# 执行修复
installer.repair()
```

### DockerHailo8Manager

Docker管理器类。

```python
from hailo8_installer.docker_manager import DockerHailo8Manager

docker_manager = DockerHailo8Manager()

# 设置Docker
docker_manager.setup_docker()

# 构建镜像
docker_manager.build_hailo8_image("my-image")

# 运行容器
docker_manager.run_hailo8_container("my-container")
```

### Hailo8Tester

测试器类。

```python
from hailo8_installer.tester import Hailo8Tester

tester = Hailo8Tester()

# 运行所有测试
results = tester.run_all_tests()

# 运行特定测试
driver_test = tester.test_driver_installation()
runtime_test = tester.test_hailort_installation()
```

## 配置

### 配置文件格式

配置文件使用 YAML 格式：

```yaml
# 基本配置
basic:
  install_dir: "/opt/hailo8"
  package_dir: "./packages"
  max_retries: 3
  command_timeout: 300

# 系统检查
system_check:
  skip_check: false
  supported_distros: ["ubuntu", "debian"]
  min_kernel_version: "4.14"
  min_disk_space_gb: 2

# Docker配置
docker:
  enabled: true
  auto_install: true
  image_name: "hailo8-runtime"
  daemon_config:
    runtimes:
      hailo8:
        path: "/usr/bin/hailo8-runtime"
```

### 环境变量

支持的环境变量：

- `HAILO8_INSTALL_DIR`: 安装目录
- `HAILO8_CONFIG_FILE`: 配置文件路径
- `HAILO8_LOG_LEVEL`: 日志级别
- `HAILO8_SKIP_DOCKER`: 跳过Docker设置

## 错误处理

所有函数都包含完整的错误处理：

```python
try:
    success = install_hailo8()
    if not success:
        print("安装失败")
except Exception as e:
    print(f"安装出错: {{e}}")
```

## 日志

使用内置日志系统：

```python
from hailo8_installer.utils import setup_logging

logger = setup_logging(level="DEBUG")
logger.info("开始安装")
```

## 示例

### 完整安装示例

```python
from hailo8_installer import install_hailo8, test_hailo8, setup_docker

def main():
    # 1. 安装Hailo8
    print("安装Hailo8...")
    if not install_hailo8():
        print("安装失败")
        return False
    
    # 2. 测试安装
    print("测试安装...")
    if not test_hailo8():
        print("测试失败")
        return False
    
    # 3. 设置Docker
    print("设置Docker...")
    if not setup_docker():
        print("Docker设置失败")
        return False
    
    print("所有步骤完成！")
    return True

if __name__ == "__main__":
    main()
```

### 自定义配置示例

```python
from hailo8_installer.installer import Hailo8Installer

# 创建自定义配置
config = {{
    'basic': {{
        'install_dir': '/custom/path',
        'max_retries': 5
    }},
    'docker': {{
        'enabled': True,
        'image_name': 'my-hailo8'
    }}
}}

# 使用自定义配置
installer = Hailo8Installer(config=config)
success = installer.install()
```
'''
    
    def _auto_install_hailo8(self) -> bool:
        """自动安装Hailo8"""
        try:
            self.logger.info("开始自动安装Hailo8...")
            
            if self.installer:
                success = self.installer.install()
                if success:
                    self.logger.info("Hailo8自动安装成功")
                else:
                    self.logger.error("Hailo8自动安装失败")
                return success
            else:
                self.logger.error("安装器未初始化")
                return False
                
        except Exception as e:
            self.logger.error(f"自动安装异常: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        status = {
            'project_name': self.config.project_name,
            'project_path': self.config.project_path,
            'hailo8_enabled': self.config.hailo8_enabled,
            'docker_enabled': self.config.docker_enabled,
            'system_info': get_system_info(),
            'components': {}
        }
        
        # 检查安装器状态
        if self.installer:
            try:
                status['components']['installer'] = self.installer.get_status()
            except Exception as e:
                status['components']['installer'] = {'error': str(e)}
        
        # 检查Docker状态
        if self.docker_manager:
            try:
                status['components']['docker'] = {
                    'docker_installed': self.docker_manager.check_docker_installation(),
                    'hailo8_configured': self.docker_manager.check_hailo8_docker_config()
                }
            except Exception as e:
                status['components']['docker'] = {'error': str(e)}
        
        # 检查测试状态
        if self.tester:
            try:
                status['components']['tester'] = {
                    'available': True,
                    'last_test_result': 'unknown'
                }
            except Exception as e:
                status['components']['tester'] = {'error': str(e)}
        
        return status
    
    def export_integration_config(self, output_file: str) -> bool:
        """导出集成配置"""
        try:
            config_data = {
                'integration_config': asdict(self.config),
                'system_info': get_system_info(),
                'status': self.get_integration_status()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_file.endswith('.json'):
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            self.logger.info(f"集成配置已导出: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出集成配置失败: {e}")
            return False

def create_integration(
    project_name: str,
    project_path: str,
    hailo8_enabled: bool = True,
    docker_enabled: bool = True,
    auto_install: bool = False,
    config_file: Optional[str] = None,
    log_level: str = "INFO",
    custom_settings: Optional[Dict[str, Any]] = None
) -> ProjectIntegrator:
    """
    创建项目集成器
    
    Args:
        project_name: 项目名称
        project_path: 项目路径
        hailo8_enabled: 是否启用Hailo8
        docker_enabled: 是否启用Docker
        auto_install: 是否自动安装
        config_file: 配置文件路径
        log_level: 日志级别
        custom_settings: 自定义设置
    
    Returns:
        项目集成器实例
    """
    
    config = IntegrationConfig(
        project_name=project_name,
        project_path=project_path,
        hailo8_enabled=hailo8_enabled,
        docker_enabled=docker_enabled,
        auto_install=auto_install,
        config_file=config_file,
        log_level=log_level,
        custom_settings=custom_settings or {}
    )
    
    return ProjectIntegrator(config)

def integrate_with_existing_project(
    project_path: str,
    project_name: Optional[str] = None,
    **kwargs
) -> bool:
    """
    与现有项目集成
    
    Args:
        project_path: 项目路径
        project_name: 项目名称（自动检测如果为None）
        **kwargs: 其他配置参数
    
    Returns:
        是否成功
    """
    
    # 自动检测项目名称
    if project_name is None:
        project_name = os.path.basename(os.path.abspath(project_path))
    
    # 创建集成器
    integrator = create_integration(
        project_name=project_name,
        project_path=project_path,
        **kwargs
    )
    
    # 执行集成
    return integrator.integrate_with_project()

# 便捷函数
def quick_integrate(project_path: str, **kwargs) -> bool:
    """快速集成到项目"""
    return integrate_with_existing_project(project_path, **kwargs)