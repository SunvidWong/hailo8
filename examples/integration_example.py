#!/usr/bin/env python3
"""
Hailo8 项目集成示例

本示例展示如何将 Hailo8 TPU 支持集成到现有项目中
"""

import os
import sys
from pathlib import Path

# 添加 hailo8_installer 到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import (
    create_integration,
    integrate_with_existing_project,
    quick_integrate,
    IntegrationConfig
)
from hailo8_installer import setup_logging

def example_quick_integration():
    """快速集成示例"""
    print("=== 快速集成示例 ===")
    
    # 创建示例项目目录
    example_project = "/tmp/example_project"
    os.makedirs(example_project, exist_ok=True)
    
    # 创建一个简单的项目文件
    with open(f"{example_project}/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
# 示例项目主文件
print("Hello from example project!")
""")
    
    print(f"创建示例项目: {example_project}")
    
    # 快速集成
    success = quick_integrate(
        project_path=example_project,
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=False
    )
    
    if success:
        print("✓ 快速集成成功！")
        print(f"集成文件已创建在: {example_project}/hailo8/")
    else:
        print("✗ 快速集成失败")
    
    return success

def example_detailed_integration():
    """详细集成示例"""
    print("\n=== 详细集成示例 ===")
    
    # 创建示例项目目录
    example_project = "/tmp/detailed_project"
    os.makedirs(example_project, exist_ok=True)
    
    # 创建项目文件
    with open(f"{example_project}/app.py", "w") as f:
        f.write("""#!/usr/bin/env python3
# 详细示例项目
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent / "hailo8"))

def main():
    try:
        from hailo8_installer import test_hailo8, install_hailo8
        
        # 检查 Hailo8 状态
        if test_hailo8():
            print("Hailo8 已就绪")
        else:
            print("Hailo8 未安装，开始安装...")
            if install_hailo8():
                print("Hailo8 安装成功")
            else:
                print("Hailo8 安装失败")
                return 1
        
        # 你的业务逻辑
        print("运行主要业务逻辑...")
        
    except ImportError:
        print("Hailo8 支持未集成")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
    
    print(f"创建详细示例项目: {example_project}")
    
    # 创建集成配置
    integrator = create_integration(
        project_name="DetailedProject",
        project_path=example_project,
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=False,
        log_level="INFO",
        custom_settings={
            "install_timeout": 600,
            "retry_count": 3,
            "enable_monitoring": True
        }
    )
    
    # 执行集成
    success = integrator.integrate_with_project()
    
    if success:
        print("✓ 详细集成成功！")
        
        # 获取集成状态
        status = integrator.get_integration_status()
        print(f"集成状态: {status['project_name']}")
        
        # 导出配置
        config_file = f"{example_project}/integration_config.yaml"
        integrator.export_integration_config(config_file)
        print(f"配置已导出到: {config_file}")
        
    else:
        print("✗ 详细集成失败")
    
    return success

def example_custom_integration():
    """自定义集成示例"""
    print("\n=== 自定义集成示例 ===")
    
    # 创建示例项目目录
    example_project = "/tmp/custom_project"
    os.makedirs(example_project, exist_ok=True)
    
    # 创建自定义配置
    config = IntegrationConfig(
        project_name="CustomProject",
        project_path=example_project,
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=False,
        config_file=None,
        log_level="DEBUG",
        custom_settings={
            "custom_install_dir": "/opt/custom_hailo8",
            "custom_docker_image": "custom-hailo8:latest",
            "enable_advanced_features": True,
            "monitoring_enabled": True,
            "backup_enabled": True
        }
    )
    
    print(f"创建自定义示例项目: {example_project}")
    print(f"自定义配置: {config.custom_settings}")
    
    # 使用自定义配置创建集成器
    from hailo8_installer.integration import ProjectIntegrator
    integrator = ProjectIntegrator(config)
    
    # 执行集成
    success = integrator.integrate_with_project()
    
    if success:
        print("✓ 自定义集成成功！")
        
        # 显示集成状态
        status = integrator.get_integration_status()
        print("集成状态:")
        for key, value in status.items():
            if key != 'system_info':  # 跳过详细系统信息
                print(f"  {key}: {value}")
        
    else:
        print("✗ 自定义集成失败")
    
    return success

def example_batch_integration():
    """批量集成示例"""
    print("\n=== 批量集成示例 ===")
    
    # 创建多个示例项目
    projects = []
    for i in range(3):
        project_path = f"/tmp/batch_project_{i+1}"
        os.makedirs(project_path, exist_ok=True)
        
        # 创建项目文件
        with open(f"{project_path}/main.py", "w") as f:
            f.write(f"""#!/usr/bin/env python3
# 批量示例项目 {i+1}
print("Hello from batch project {i+1}!")
""")
        
        projects.append(project_path)
    
    print(f"创建 {len(projects)} 个批量示例项目")
    
    # 批量集成
    success_count = 0
    for i, project_path in enumerate(projects):
        print(f"\n集成项目 {i+1}: {project_path}")
        
        success = quick_integrate(
            project_path=project_path,
            hailo8_enabled=True,
            docker_enabled=True,
            auto_install=False
        )
        
        if success:
            print(f"✓ 项目 {i+1} 集成成功")
            success_count += 1
        else:
            print(f"✗ 项目 {i+1} 集成失败")
    
    print(f"\n批量集成完成: {success_count}/{len(projects)} 成功")
    return success_count == len(projects)

def example_conditional_integration():
    """条件集成示例"""
    print("\n=== 条件集成示例 ===")
    
    from hailo8_installer.utils import get_system_info
    
    # 获取系统信息
    system_info = get_system_info()
    print(f"系统信息: {system_info['distro_name']} {system_info['distro_version']}")
    
    # 创建示例项目
    example_project = "/tmp/conditional_project"
    os.makedirs(example_project, exist_ok=True)
    
    # 根据系统条件决定集成参数
    if system_info['distro_name'] in ['ubuntu', 'debian']:
        print("检测到 Ubuntu/Debian 系统，启用完整集成")
        docker_enabled = True
        auto_install = True
    else:
        print("检测到其他系统，使用基础集成")
        docker_enabled = False
        auto_install = False
    
    # 执行条件集成
    success = integrate_with_existing_project(
        project_path=example_project,
        project_name="ConditionalProject",
        hailo8_enabled=True,
        docker_enabled=docker_enabled,
        auto_install=auto_install,
        log_level="INFO"
    )
    
    if success:
        print("✓ 条件集成成功")
    else:
        print("✗ 条件集成失败")
    
    return success

def example_integration_with_existing_code():
    """与现有代码集成示例"""
    print("\n=== 与现有代码集成示例 ===")
    
    # 创建模拟现有项目
    existing_project = "/tmp/existing_project"
    os.makedirs(existing_project, exist_ok=True)
    
    # 创建现有项目结构
    os.makedirs(f"{existing_project}/src", exist_ok=True)
    os.makedirs(f"{existing_project}/tests", exist_ok=True)
    os.makedirs(f"{existing_project}/docs", exist_ok=True)
    
    # 创建现有代码文件
    with open(f"{existing_project}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
# 现有项目主文件
import sys
import logging

logger = logging.getLogger(__name__)

class ExistingApplication:
    def __init__(self):
        self.name = "ExistingApp"
        self.version = "1.0.0"
        self.hailo8_enabled = False
    
    def initialize(self):
        \"\"\"初始化应用\"\"\"
        logger.info(f"初始化 {self.name} v{self.version}")
        
        # 尝试初始化 Hailo8
        self._setup_hailo8()
    
    def _setup_hailo8(self):
        \"\"\"设置 Hailo8 支持\"\"\"
        try:
            # 这里会在集成后自动添加 Hailo8 支持
            from hailo8_installer import test_hailo8, install_hailo8
            
            if test_hailo8():
                logger.info("Hailo8 已就绪")
                self.hailo8_enabled = True
            else:
                logger.warning("Hailo8 未安装")
                
        except ImportError:
            logger.info("Hailo8 支持未集成")
    
    def run(self):
        \"\"\"运行应用\"\"\"
        logger.info("运行应用...")
        
        if self.hailo8_enabled:
            logger.info("使用 Hailo8 加速")
        else:
            logger.info("使用 CPU 模式")

def main():
    logging.basicConfig(level=logging.INFO)
    
    app = ExistingApplication()
    app.initialize()
    app.run()

if __name__ == "__main__":
    main()
""")
    
    # 创建配置文件
    with open(f"{existing_project}/config.yaml", "w") as f:
        f.write("""# 现有项目配置
app:
  name: "ExistingApp"
  version: "1.0.0"
  debug: false

features:
  hailo8_support: true
  docker_support: true
""")
    
    # 创建 requirements.txt
    with open(f"{existing_project}/requirements.txt", "w") as f:
        f.write("""# 现有项目依赖
pyyaml>=5.4.0
requests>=2.25.0
numpy>=1.20.0
""")
    
    print(f"创建现有项目结构: {existing_project}")
    
    # 集成 Hailo8 支持
    success = integrate_with_existing_project(
        project_path=existing_project,
        project_name="ExistingApp",
        hailo8_enabled=True,
        docker_enabled=True,
        auto_install=False,
        log_level="INFO",
        custom_settings={
            "preserve_existing_structure": True,
            "add_to_requirements": True,
            "update_config": True
        }
    )
    
    if success:
        print("✓ 现有项目集成成功")
        print("集成后的项目结构:")
        
        # 显示集成后的结构
        for root, dirs, files in os.walk(existing_project):
            level = root.replace(existing_project, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print("✗ 现有项目集成失败")
    
    return success

def main():
    """主函数"""
    print("Hailo8 项目集成示例")
    print("=" * 50)
    
    # 设置日志
    logger = setup_logging(level="INFO")
    
    # 运行所有示例
    examples = [
        ("快速集成", example_quick_integration),
        ("详细集成", example_detailed_integration),
        ("自定义集成", example_custom_integration),
        ("批量集成", example_batch_integration),
        ("条件集成", example_conditional_integration),
        ("现有代码集成", example_integration_with_existing_code),
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            success = example_func()
            results[name] = success
            
            if success:
                print(f"✓ {name} 示例执行成功")
            else:
                print(f"✗ {name} 示例执行失败")
                
        except Exception as e:
            print(f"✗ {name} 示例执行异常: {e}")
            results[name] = False
    
    # 显示总结
    print(f"\n{'='*50}")
    print("示例执行总结:")
    
    success_count = 0
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
        if success:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(examples)} 个示例成功")
    
    # 清理提示
    print(f"\n注意: 示例文件创建在 /tmp/ 目录下")
    print("如需清理，请手动删除 /tmp/example_project* 和 /tmp/*_project* 目录")
    
    return success_count == len(examples)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)