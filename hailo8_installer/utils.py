#!/usr/bin/env python3
"""
Hailo8 安装器通用工具函数
提供日志、系统检查、命令执行等通用功能
"""

import os
import sys
import subprocess
import logging
import platform
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

class SystemInfo:
    """系统信息类"""
    
    def __init__(self):
        self.os_name = platform.system()
        self.os_version = platform.release()
        self.architecture = platform.machine()
        self.python_version = platform.python_version()
        self.distro_info = self._get_distro_info()
    
    def _get_distro_info(self) -> Dict[str, str]:
        """获取Linux发行版信息"""
        info = {}
        
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            info[key] = value.strip('"')
        except Exception:
            pass
        
        return info
    
    def get_distro_name(self) -> str:
        """获取发行版名称"""
        return self.distro_info.get('ID', 'unknown').lower()
    
    def get_distro_version(self) -> str:
        """获取发行版版本"""
        return self.distro_info.get('VERSION_ID', 'unknown')
    
    def is_supported_distro(self) -> bool:
        """检查是否为支持的发行版"""
        supported = ['ubuntu', 'debian', 'centos', 'rhel', 'fedora']
        return self.get_distro_name() in supported

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    colored: bool = True,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    设置日志系统
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        colored: 是否使用彩色输出
        format_string: 自定义格式字符串
    
    Returns:
        配置好的logger对象
    """
    
    # 设置日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 设置格式
    if format_string is None:
        if colored:
            format_string = '\033[92m%(asctime)s\033[0m - \033[94m%(name)s\033[0m - \033[93m%(levelname)s\033[0m - %(message)s'
        else:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 创建logger
    logger = logging.getLogger('hailo8_installer')
    logger.setLevel(numeric_level)
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def run_command(
    command: List[str],
    timeout: int = 300,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    check: bool = False
) -> Tuple[bool, str, str]:
    """
    执行系统命令
    
    Args:
        command: 命令列表
        timeout: 超时时间（秒）
        cwd: 工作目录
        env: 环境变量
        capture_output: 是否捕获输出
        check: 是否检查返回码
    
    Returns:
        (成功标志, 标准输出, 标准错误)
    """
    
    logger = logging.getLogger('hailo8_installer.utils')
    logger.debug(f"执行命令: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            timeout=timeout,
            cwd=cwd,
            env=env,
            capture_output=capture_output,
            text=True,
            check=check
        )
        
        success = result.returncode == 0
        stdout = result.stdout if capture_output else ""
        stderr = result.stderr if capture_output else ""
        
        if success:
            logger.debug(f"命令执行成功: {command[0]}")
        else:
            logger.warning(f"命令执行失败: {command[0]}, 返回码: {result.returncode}")
        
        return success, stdout, stderr
        
    except subprocess.TimeoutExpired:
        logger.error(f"命令执行超时: {' '.join(command)}")
        return False, "", "命令执行超时"
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行错误: {e}")
        return False, e.stdout or "", e.stderr or ""
    except Exception as e:
        logger.error(f"命令执行异常: {e}")
        return False, "", str(e)

def check_system_requirements() -> Tuple[bool, List[str]]:
    """
    检查系统要求
    
    Returns:
        (是否满足要求, 错误信息列表)
    """
    
    logger = logging.getLogger('hailo8_installer.utils')
    errors = []
    
    # 检查操作系统
    if platform.system() != 'Linux':
        errors.append(f"不支持的操作系统: {platform.system()}")
    
    # 检查架构
    if platform.machine() not in ['x86_64', 'amd64']:
        errors.append(f"不支持的系统架构: {platform.machine()}")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        errors.append(f"Python版本过低: {sys.version}, 需要3.7+")
    
    # 检查权限
    if os.geteuid() != 0:
        errors.append("需要root权限运行")
    
    # 检查磁盘空间
    try:
        statvfs = os.statvfs('/')
        free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        if free_space_gb < 2:
            errors.append(f"磁盘空间不足: {free_space_gb:.1f}GB, 需要至少2GB")
    except Exception as e:
        logger.warning(f"无法检查磁盘空间: {e}")
    
    # 检查发行版
    system_info = SystemInfo()
    if not system_info.is_supported_distro():
        errors.append(f"不支持的Linux发行版: {system_info.get_distro_name()}")
    
    success = len(errors) == 0
    
    if success:
        logger.info("系统要求检查通过")
    else:
        logger.error("系统要求检查失败:")
        for error in errors:
            logger.error(f"  - {error}")
    
    return success, errors

def ensure_directory(path: str, mode: int = 0o755) -> bool:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        mode: 目录权限
    
    Returns:
        是否成功
    """
    
    try:
        os.makedirs(path, mode=mode, exist_ok=True)
        return True
    except Exception as e:
        logger = logging.getLogger('hailo8_installer.utils')
        logger.error(f"创建目录失败: {path} - {e}")
        return False

def backup_file(file_path: str, backup_suffix: str = ".backup") -> Optional[str]:
    """
    备份文件
    
    Args:
        file_path: 文件路径
        backup_suffix: 备份后缀
    
    Returns:
        备份文件路径，失败返回None
    """
    
    logger = logging.getLogger('hailo8_installer.utils')
    
    if not os.path.exists(file_path):
        return None
    
    try:
        backup_path = f"{file_path}{backup_suffix}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"文件已备份: {file_path} -> {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"文件备份失败: {file_path} - {e}")
        return None

def restore_file(backup_path: str) -> bool:
    """
    从备份恢复文件
    
    Args:
        backup_path: 备份文件路径
    
    Returns:
        是否成功
    """
    
    logger = logging.getLogger('hailo8_installer.utils')
    
    if not os.path.exists(backup_path):
        logger.error(f"备份文件不存在: {backup_path}")
        return False
    
    try:
        original_path = backup_path.replace(".backup", "")
        shutil.copy2(backup_path, original_path)
        logger.info(f"文件已恢复: {backup_path} -> {original_path}")
        return True
    except Exception as e:
        logger.error(f"文件恢复失败: {backup_path} - {e}")
        return False

def get_package_manager() -> Optional[str]:
    """
    检测系统包管理器
    
    Returns:
        包管理器名称，未找到返回None
    """
    
    managers = {
        'apt-get': ['ubuntu', 'debian'],
        'yum': ['centos', 'rhel'],
        'dnf': ['fedora'],
        'zypper': ['opensuse'],
        'pacman': ['arch']
    }
    
    system_info = SystemInfo()
    distro = system_info.get_distro_name()
    
    for manager, distros in managers.items():
        if distro in distros and shutil.which(manager):
            return manager
    
    # 备用检测
    for manager in managers.keys():
        if shutil.which(manager):
            return manager
    
    return None

def install_system_package(package: str, manager: Optional[str] = None) -> bool:
    """
    安装系统包
    
    Args:
        package: 包名
        manager: 包管理器（自动检测如果为None）
    
    Returns:
        是否成功
    """
    
    logger = logging.getLogger('hailo8_installer.utils')
    
    if manager is None:
        manager = get_package_manager()
    
    if manager is None:
        logger.error("未找到支持的包管理器")
        return False
    
    # 构建安装命令
    if manager == 'apt-get':
        cmd = ['apt-get', 'install', '-y', package]
    elif manager == 'yum':
        cmd = ['yum', 'install', '-y', package]
    elif manager == 'dnf':
        cmd = ['dnf', 'install', '-y', package]
    elif manager == 'zypper':
        cmd = ['zypper', 'install', '-y', package]
    elif manager == 'pacman':
        cmd = ['pacman', '-S', '--noconfirm', package]
    else:
        logger.error(f"不支持的包管理器: {manager}")
        return False
    
    logger.info(f"安装系统包: {package}")
    success, stdout, stderr = run_command(cmd)
    
    if not success:
        logger.error(f"包安装失败: {package}")
        logger.error(f"错误信息: {stderr}")
    
    return success

def check_service_status(service_name: str) -> bool:
    """
    检查系统服务状态
    
    Args:
        service_name: 服务名称
    
    Returns:
        服务是否运行
    """
    
    success, stdout, _ = run_command(['systemctl', 'is-active', service_name])
    return success and 'active' in stdout

def start_service(service_name: str) -> bool:
    """
    启动系统服务
    
    Args:
        service_name: 服务名称
    
    Returns:
        是否成功
    """
    
    logger = logging.getLogger('hailo8_installer.utils')
    
    success, _, stderr = run_command(['systemctl', 'start', service_name])
    
    if success:
        logger.info(f"服务启动成功: {service_name}")
    else:
        logger.error(f"服务启动失败: {service_name} - {stderr}")
    
    return success

def enable_service(service_name: str) -> bool:
    """
    启用系统服务（开机自启）
    
    Args:
        service_name: 服务名称
    
    Returns:
        是否成功
    """
    
    logger = logging.getLogger('hailo8_installer.utils')
    
    success, _, stderr = run_command(['systemctl', 'enable', service_name])
    
    if success:
        logger.info(f"服务已设置为开机自启: {service_name}")
    else:
        logger.error(f"服务自启设置失败: {service_name} - {stderr}")
    
    return success

def retry_operation(
    operation,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple = (Exception,)
):
    """
    重试装饰器
    
    Args:
        operation: 要重试的操作
        max_retries: 最大重试次数
        delay: 初始延迟时间
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
    
    Returns:
        装饰后的函数
    """
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('hailo8_installer.utils')
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"操作失败，已达到最大重试次数: {e}")
                        raise
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(f"操作失败，{wait_time:.1f}秒后重试 (第{attempt + 1}次): {e}")
                    time.sleep(wait_time)
            
        return wrapper
    return decorator

def get_system_info() -> Dict[str, Any]:
    """
    获取详细的系统信息
    
    Returns:
        系统信息字典
    """
    
    system_info = SystemInfo()
    
    info = {
        'os_name': system_info.os_name,
        'os_version': system_info.os_version,
        'architecture': system_info.architecture,
        'python_version': system_info.python_version,
        'distro_name': system_info.get_distro_name(),
        'distro_version': system_info.get_distro_version(),
        'kernel_version': platform.release(),
        'hostname': platform.node(),
        'processor': platform.processor(),
        'package_manager': get_package_manager(),
    }
    
    # 添加内存信息
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    info['memory_total'] = line.split()[1] + ' kB'
                elif line.startswith('MemAvailable:'):
                    info['memory_available'] = line.split()[1] + ' kB'
    except Exception:
        pass
    
    # 添加CPU信息
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            cpu_count = cpuinfo.count('processor')
            info['cpu_count'] = cpu_count
    except Exception:
        pass
    
    return info