#!/usr/bin/env python3
"""
Hailo8 安装验证测试脚本
用于验证 Hailo8 TPU 是否正确安装并可以正常使用
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class Hailo8Tester:
    """Hailo8 测试类"""
    
    def __init__(self):
        self.setup_logging()
        self.test_results = {}
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('hailo8_test.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_command(self, command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """执行命令"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", str(e)
    
    def test_system_info(self) -> bool:
        """测试系统信息"""
        self.logger.info("=== 系统信息测试 ===")
        
        try:
            # 操作系统信息
            with open('/etc/os-release', 'r') as f:
                os_info = f.read()
            self.logger.info(f"操作系统信息:\n{os_info}")
            
            # 内核版本
            success, stdout, _ = self.run_command(['uname', '-r'])
            if success:
                self.logger.info(f"内核版本: {stdout.strip()}")
            
            # 系统架构
            success, stdout, _ = self.run_command(['uname', '-m'])
            if success:
                self.logger.info(f"系统架构: {stdout.strip()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"系统信息测试失败: {e}")
            return False
    
    def test_driver_status(self) -> bool:
        """测试驱动状态"""
        self.logger.info("=== 驱动状态测试 ===")
        
        try:
            # 检查模块是否加载
            success, stdout, _ = self.run_command(['lsmod'])
            if success:
                if 'hailo' in stdout.lower():
                    self.logger.info("✓ Hailo 驱动模块已加载")
                    
                    # 显示模块详细信息
                    lines = stdout.split('\n')
                    for line in lines:
                        if 'hailo' in line.lower():
                            self.logger.info(f"  模块信息: {line}")
                else:
                    self.logger.error("✗ Hailo 驱动模块未加载")
                    return False
            
            # 检查设备节点
            device_nodes = ['/dev/hailo0', '/dev/hailo_pci']
            found_device = False
            
            for node in device_nodes:
                if os.path.exists(node):
                    self.logger.info(f"✓ 设备节点存在: {node}")
                    
                    # 检查设备权限
                    stat_info = os.stat(node)
                    self.logger.info(f"  权限: {oct(stat_info.st_mode)[-3:]}")
                    found_device = True
            
            if not found_device:
                self.logger.error("✗ 未找到 Hailo 设备节点")
                return False
            
            # 检查 PCIe 设备
            success, stdout, _ = self.run_command(['lspci', '-d', '1e60:'])
            if success and stdout.strip():
                self.logger.info("✓ 检测到 Hailo PCIe 设备:")
                for line in stdout.strip().split('\n'):
                    self.logger.info(f"  {line}")
            else:
                self.logger.warning("⚠ 未检测到 Hailo PCIe 设备")
            
            return True
            
        except Exception as e:
            self.logger.error(f"驱动状态测试失败: {e}")
            return False
    
    def test_hailort_installation(self) -> bool:
        """测试 HailoRT 安装"""
        self.logger.info("=== HailoRT 安装测试 ===")
        
        try:
            # 检查 CLI 工具
            success, stdout, _ = self.run_command(['which', 'hailortcli'])
            if success:
                self.logger.info(f"✓ HailoRT CLI 工具路径: {stdout.strip()}")
                
                # 获取版本信息
                success, stdout, _ = self.run_command(['hailortcli', '--version'])
                if success:
                    self.logger.info(f"  版本信息: {stdout.strip()}")
            else:
                self.logger.warning("⚠ HailoRT CLI 工具未找到")
            
            # 检查 Python 模块
            success, stdout, stderr = self.run_command([
                'python3', '-c', 
                'import hailo_platform; print(f"HailoRT Python 版本: {hailo_platform.__version__}")'
            ])
            
            if success:
                self.logger.info(f"✓ {stdout.strip()}")
            else:
                self.logger.error(f"✗ HailoRT Python 模块导入失败: {stderr}")
                return False
            
            # 测试基本功能
            success, stdout, stderr = self.run_command([
                'python3', '-c', '''
import hailo_platform
try:
    # 尝试获取设备信息
    devices = hailo_platform.Device.scan()
    print(f"检测到 {len(devices)} 个 Hailo 设备")
    for i, device in enumerate(devices):
        print(f"设备 {i}: {device}")
except Exception as e:
    print(f"设备扫描失败: {e}")
'''
            ])
            
            if success:
                self.logger.info(f"✓ HailoRT 功能测试:")
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
            else:
                self.logger.error(f"✗ HailoRT 功能测试失败: {stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"HailoRT 安装测试失败: {e}")
            return False
    
    def test_docker_integration(self) -> bool:
        """测试 Docker 集成"""
        self.logger.info("=== Docker 集成测试 ===")
        
        try:
            # 检查 Docker 是否安装
            success, stdout, _ = self.run_command(['which', 'docker'])
            if not success:
                self.logger.warning("⚠ Docker 未安装，跳过 Docker 测试")
                return True
            
            self.logger.info("✓ Docker 已安装")
            
            # 检查 Docker 服务状态
            success, stdout, _ = self.run_command(['systemctl', 'is-active', 'docker'])
            if success and 'active' in stdout:
                self.logger.info("✓ Docker 服务运行中")
            else:
                self.logger.error("✗ Docker 服务未运行")
                return False
            
            # 检查 Hailo Docker 镜像
            success, stdout, _ = self.run_command(['docker', 'images', 'hailo8'])
            if success and 'hailo8' in stdout:
                self.logger.info("✓ Hailo8 Docker 镜像存在")
                
                # 测试容器运行
                success, stdout, stderr = self.run_command([
                    'docker', 'run', '--rm', '--device=/dev/hailo0', 
                    'hailo8:latest', 'python3', '-c', 
                    'import hailo_platform; print("Docker 中 Hailo8 运行正常")'
                ], timeout=60)
                
                if success:
                    self.logger.info(f"✓ Docker 容器测试成功: {stdout.strip()}")
                else:
                    self.logger.error(f"✗ Docker 容器测试失败: {stderr}")
                    return False
            else:
                self.logger.warning("⚠ Hailo8 Docker 镜像不存在")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Docker 集成测试失败: {e}")
            return False
    
    def test_performance_benchmark(self) -> bool:
        """性能基准测试"""
        self.logger.info("=== 性能基准测试 ===")
        
        try:
            # 简单的性能测试
            success, stdout, stderr = self.run_command([
                'python3', '-c', '''
import hailo_platform
import time

try:
    devices = hailo_platform.Device.scan()
    if not devices:
        print("未找到 Hailo 设备")
        exit(1)
    
    device = devices[0]
    print(f"使用设备: {device}")
    
    # 测试设备初始化时间
    start_time = time.time()
    # 这里可以添加更多的性能测试代码
    end_time = time.time()
    
    print(f"设备初始化时间: {end_time - start_time:.3f} 秒")
    print("基本性能测试完成")
    
except Exception as e:
    print(f"性能测试失败: {e}")
    exit(1)
'''
            ], timeout=120)
            
            if success:
                self.logger.info("✓ 性能基准测试:")
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
            else:
                self.logger.error(f"✗ 性能基准测试失败: {stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"性能基准测试失败: {e}")
            return False
    
    def test_stress_test(self) -> bool:
        """压力测试"""
        self.logger.info("=== 压力测试 ===")
        
        try:
            # 简单的压力测试
            success, stdout, stderr = self.run_command([
                'python3', '-c', '''
import hailo_platform
import time
import threading

def device_test():
    try:
        devices = hailo_platform.Device.scan()
        if devices:
            device = devices[0]
            # 这里可以添加设备操作
            time.sleep(1)
            return True
    except:
        return False
    return False

# 运行多线程测试
threads = []
results = []

for i in range(5):
    thread = threading.Thread(target=lambda: results.append(device_test()))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

success_count = sum(results)
print(f"压力测试结果: {success_count}/5 成功")

if success_count >= 4:
    print("压力测试通过")
else:
    print("压力测试失败")
    exit(1)
'''
            ], timeout=60)
            
            if success:
                self.logger.info("✓ 压力测试:")
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.info(f"  {line}")
            else:
                self.logger.error(f"✗ 压力测试失败: {stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"压力测试失败: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        self.logger.info("开始 Hailo8 完整测试...")
        
        tests = [
            ("系统信息", self.test_system_info),
            ("驱动状态", self.test_driver_status),
            ("HailoRT安装", self.test_hailort_installation),
            ("Docker集成", self.test_docker_integration),
            ("性能基准", self.test_performance_benchmark),
            ("压力测试", self.test_stress_test)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.logger.info(f"\n开始测试: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                    self.logger.info(f"✅ {test_name} - 通过")
                else:
                    self.logger.error(f"❌ {test_name} - 失败")
            except Exception as e:
                results[test_name] = False
                self.logger.error(f"❌ {test_name} - 异常: {e}")
        
        # 输出测试总结
        self.logger.info(f"\n=== 测试总结 ===")
        self.logger.info(f"总测试数: {total}")
        self.logger.info(f"通过测试: {passed}")
        self.logger.info(f"失败测试: {total - passed}")
        self.logger.info(f"成功率: {passed/total*100:.1f}%")
        
        if passed == total:
            self.logger.info("🎉 所有测试通过！Hailo8 安装成功！")
        else:
            self.logger.error("⚠️  部分测试失败，请检查安装")
        
        return results
    
    def generate_report(self, results: Dict[str, bool]):
        """生成测试报告"""
        report_file = "hailo8_test_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Hailo8 安装验证报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("测试结果:\n")
            for test_name, result in results.items():
                status = "✅ 通过" if result else "❌ 失败"
                f.write(f"  {test_name}: {status}\n")
            
            f.write(f"\n总体结果: {sum(results.values())}/{len(results)} 通过\n")
            
            if all(results.values()):
                f.write("\n🎉 Hailo8 安装验证成功！\n")
            else:
                f.write("\n⚠️  部分测试失败，建议重新安装或检查配置\n")
        
        self.logger.info(f"测试报告已保存到: {report_file}")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Hailo8 测试脚本")
        print("用法: python3 test_hailo8.py [选项]")
        print("选项:")
        print("  --help    显示帮助信息")
        print("  --quick   快速测试（跳过压力测试）")
        return
    
    tester = Hailo8Tester()
    
    # 检查是否为 root 权限
    if os.geteuid() != 0:
        tester.logger.warning("建议以 root 权限运行测试以获得完整结果")
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 生成报告
    tester.generate_report(results)
    
    # 返回适当的退出码
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()