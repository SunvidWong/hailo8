#!/usr/bin/env python3
"""
Hailo8 TPU 智能安装管理器 - 安装配置
支持作为 Python 包安装到其他项目中
"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取依赖文件
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# 读取版本信息
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "hailo8_installer", "__init__.py")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"

setup(
    name="hailo8-installer",
    version=get_version(),
    author="Hailo8 Installer Team",
    author_email="support@hailo8-installer.com",
    description="智能 Hailo8 TPU 安装管理器，具有容错能力和 Docker 集成",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/hailo8-installer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Hardware :: Hardware Drivers",
        "Topic :: System :: Installation/Setup",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docker": [
            "docker>=5.0.0",
        ],
        "all": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
            "docker>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "hailo8-install=hailo8_installer.cli:main",
            "hailo8-docker=hailo8_installer.docker_manager:main",
            "hailo8-test=hailo8_installer.tester:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hailo8_installer": [
            "config/*.yaml",
            "templates/*.j2",
            "scripts/*.sh",
            "packages/*.deb",
            "packages/*.whl",
        ],
    },
    data_files=[
        ("share/hailo8-installer/config", ["config.yaml"]),
        ("share/hailo8-installer/scripts", ["install.sh"]),
        ("share/hailo8-installer/docs", ["README.md", "BUILD.md"]),
    ],
    zip_safe=False,
    keywords="hailo8 tpu installer docker ai hardware driver",
    project_urls={
        "Bug Reports": "https://github.com/your-org/hailo8-installer/issues",
        "Source": "https://github.com/your-org/hailo8-installer",
        "Documentation": "https://hailo8-installer.readthedocs.io/",
    },
)