"""Hailo8 TPU 智能安装管理器

一个功能完整的 Hailo8 TPU 安装、配置和管理工具包，
提供故障容错、自动修复、Docker 集成和项目集成功能。

主要功能:
- 智能系统检测和环境配置
- 故障容错的安装流程
- 自动依赖管理和修复
- 完整的 Docker 集成支持
- 全面的测试和验证套件
- 状态管理和回滚机制
- 项目集成和整合工具

使用示例:
    from hailo8_installer import install_hailo8, test_hailo8, setup_docker
    
    # 安装 Hailo8
    success = install_hailo8()
    
    # 测试安装
    test_result = test_hailo8()
    
    # 设置 Docker
    docker_success = setup_docker()
    
    # 项目集成
    from hailo8_installer.integration import integrate_with_existing_project
    integrate_with_existing_project("/path/to/project")
"""

import sys
import logging
from typing import Optional, Dict, Any

# 版本信息
__version__ = "1.0.0"
__author__ = "Hailo8 Installer Team"
__email__ = "support@hailo8-installer.com"
__description__ = "Hailo8 TPU 智能安装管理器"

# 导入核心类
from .installer import Hailo8Installer, InstallStatus, ComponentType, InstallComponent
from .docker_manager import DockerHailo8Manager
from .tester import Hailo8Tester
from .utils import setup_logging, get_system_info, SystemInfo

# 导入集成功能
from .integration import (
    ProjectIntegrator, 
    IntegrationConfig, 
    create_integration,
    integrate_with_existing_project,
    quick_integrate
)

# 设置默认日志
_default_logger = setup_logging(level="INFO")

def install_hailo8(
    install_dir: Optional[str] = None,
    config_file: Optional[str] = None,
    force_reinstall: bool = False,
    skip_docker: bool = False
) -> bool:
    """
    安装 Hailo8 TPU 驱动和运行时
    
    Args:
        install_dir: 安装目录路径
        config_file: 配置文件路径
        force_reinstall: 是否强制重新安装
        skip_docker: 是否跳过Docker设置
    
    Returns:
        安装是否成功
    """
    try:
        installer = Hailo8Installer(
            install_dir=install_dir,
            config_file=config_file
        )
        
        if force_reinstall:
            installer.uninstall()
        
        success = installer.install()
        
        if success and not skip_docker:
            docker_manager = DockerHailo8Manager()
            docker_manager.setup_docker()
        
        return success
        
    except Exception as e:
        _default_logger.error(f"安装失败: {e}")
        return False

def test_hailo8(
    full_test: bool = True,
    generate_report: bool = True
) -> bool:
    """
    测试 Hailo8 安装和功能
    
    Args:
        full_test: 是否执行完整测试套件
        generate_report: 是否生成详细测试报告
    
    Returns:
        测试是否通过
    """
    try:
        tester = Hailo8Tester()
        
        if full_test:
            results = tester.run_all_tests()
        else:
            results = tester.run_basic_tests()
        
        if generate_report:
            tester.generate_report()
        
        return all(results.values())
        
    except Exception as e:
        _default_logger.error(f"测试失败: {e}")
        return False

def setup_docker(
    image_name: Optional[str] = None,
    container_name: Optional[str] = None,
    build_image: bool = True,
    start_container: bool = False
) -> bool:
    """
    设置 Hailo8 Docker 环境
    
    Args:
        image_name: Docker镜像名称
        container_name: 容器名称
        build_image: 是否构建镜像
        start_container: 是否启动容器
    
    Returns:
        Docker设置是否成功
    """
    try:
        docker_manager = DockerHailo8Manager()
        
        # 设置Docker基础环境
        if not docker_manager.setup_docker():
            return False
        
        # 构建镜像
        if build_image:
            if not docker_manager.build_hailo8_image(image_name or "hailo8-runtime"):
                return False
        
        # 启动容器
        if start_container:
            if not docker_manager.run_hailo8_container(
                container_name or "hailo8-container",
                image_name or "hailo8-runtime"
            ):
                return False
        
        return True
        
    except Exception as e:
        _default_logger.error(f"Docker设置失败: {e}")
        return False

def get_status() -> Dict[str, Any]:
    """
    获取 Hailo8 系统状态
    
    Returns:
        系统状态信息
    """
    try:
        installer = Hailo8Installer()
        docker_manager = DockerHailo8Manager()
        tester = Hailo8Tester()
        
        status = {
            'system_info': get_system_info(),
            'installer_status': installer.get_status(),
            'docker_status': {
                'docker_installed': docker_manager.check_docker_installation(),
                'hailo8_configured': docker_manager.check_hailo8_docker_config()
            },
            'test_status': {
                'driver_ok': tester.test_driver_installation(),
                'runtime_ok': tester.test_hailort_installation()
            }
        }
        
        return status
        
    except Exception as e:
        _default_logger.error(f"获取状态失败: {e}")
        return {'error': str(e)}

def integrate_project(
    project_path: str,
    project_name: Optional[str] = None,
    **kwargs
) -> bool:
    """
    将 Hailo8 集成到现有项目
    
    Args:
        project_path: 项目路径
        project_name: 项目名称（自动检测如果为None）
        **kwargs: 其他集成配置参数
    
    Returns:
        集成是否成功
    """
    try:
        return integrate_with_existing_project(
            project_path=project_path,
            project_name=project_name,
            **kwargs
        )
    except Exception as e:
        _default_logger.error(f"项目集成失败: {e}")
        return False

# 兼容性检查
def _check_compatibility():
    """检查系统兼容性"""
    if sys.version_info < (3, 7):
        raise RuntimeError("需要 Python 3.7 或更高版本")
    
    import platform
    if platform.system() != 'Linux':
        _default_logger.warning("Hailo8 主要支持 Linux 系统")

# 执行兼容性检查
try:
    _check_compatibility()
except Exception as e:
    _default_logger.error(f"兼容性检查失败: {e}")

# 导出的公共接口
__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    '__email__',
    '__description__',
    
    # 核心类
    'Hailo8Installer',
    'DockerHailo8Manager', 
    'Hailo8Tester',
    'InstallStatus',
    'ComponentType',
    'InstallComponent',
    'SystemInfo',
    
    # 集成类
    'ProjectIntegrator',
    'IntegrationConfig',
    
    # 便捷函数
    'install_hailo8',
    'test_hailo8',
    'setup_docker',
    'get_status',
    'setup_logging',
    'get_system_info',
    
    # 集成函数
    'create_integration',
    'integrate_with_existing_project',
    'integrate_project',
    'quick_integrate',
]