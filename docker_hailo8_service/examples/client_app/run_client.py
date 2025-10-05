#!/usr/bin/env python3
"""
Hailo8客户端应用示例
演示如何在容器中使用Hailo8服务进行推理
"""

import os
import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import json

# 导入客户端库
import sys
sys.path.append('/app')
from hailo8_client import Hailo8Client

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClientApp:
    """客户端应用"""
    
    def __init__(self):
        self.hailo8_url = os.getenv('HAILO8_SERVICE_URL', 'http://hailo8-service:8080')
        self.input_dir = Path('/app/input')
        self.output_dir = Path('/app/output')
        self.client_name = os.getenv('CLIENT_NAME', 'Demo Client')
        
        # 确保目录存在
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"客户端应用初始化: {self.client_name}")
        logger.info(f"Hailo8服务URL: {self.hailo8_url}")
    
    async def wait_for_service(self, max_retries: int = 30, delay: int = 2):
        """等待Hailo8服务可用"""
        logger.info("等待Hailo8服务启动...")
        
        async with Hailo8Client(self.hailo8_url) as client:
            for attempt in range(max_retries):
                try:
                    health = await client.health_check()
                    if health.get('healthy', False):
                        logger.info("Hailo8服务已就绪")
                        return True
                except Exception as e:
                    logger.debug(f"服务检查失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                
                await asyncio.sleep(delay)
        
        logger.error("Hailo8服务启动超时")
        return False
    
    async def process_images(self):
        """处理输入目录中的图片"""
        if not self.input_dir.exists():
            logger.warning(f"输入目录不存在: {self.input_dir}")
            return
        
        # 查找图片文件
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            image_files.extend(self.input_dir.glob(ext))
        
        if not image_files:
            logger.info("输入目录中没有找到图片文件")
            return
        
        logger.info(f"找到 {len(image_files)} 个图片文件")
        
        async with Hailo8Client(self.hailo8_url) as client:
            # 加载模型
            model_id = "demo_model"
            load_result = await client.load_model(
                model_path="/app/models/demo_model.hef",
                model_id=model_id
            )
            
            if not load_result.get('success', False):
                logger.error(f"模型加载失败: {load_result}")
                return
            
            logger.info(f"模型加载成功: {model_id}")
            
            # 处理每个图片
            results = []
            for image_file in image_files:
                try:
                    logger.info(f"处理图片: {image_file.name}")
                    
                    # 读取图片并转换为base64
                    with open(image_file, 'rb') as f:
                        import base64
                        image_base64 = base64.b64encode(f.read()).decode('utf-8')
                    
                    # 执行推理
                    start_time = time.time()
                    inference_result = await client.run_inference(
                        model_id=model_id,
                        input_data=image_base64,
                        input_format="base64",
                        output_format="json"
                    )
                    inference_time = (time.time() - start_time) * 1000
                    
                    if inference_result.get('success', False):
                        logger.info(f"推理成功: {image_file.name}, 耗时: {inference_time:.2f}ms")
                        
                        # 保存结果
                        result_data = {
                            "image_file": image_file.name,
                            "inference_time_ms": inference_time,
                            "result": inference_result.get('output_data'),
                            "timestamp": time.time()
                        }
                        results.append(result_data)
                        
                        # 保存单个结果文件
                        result_file = self.output_dir / f"{image_file.stem}_result.json"
                        with open(result_file, 'w') as f:
                            json.dump(result_data, f, indent=2)
                    
                    else:
                        logger.error(f"推理失败: {image_file.name}, 错误: {inference_result}")
                
                except Exception as e:
                    logger.error(f"处理图片失败 {image_file.name}: {e}")
            
            # 保存汇总结果
            if results:
                summary_file = self.output_dir / "inference_summary.json"
                summary_data = {
                    "client_name": self.client_name,
                    "total_images": len(image_files),
                    "successful_inferences": len(results),
                    "results": results,
                    "timestamp": time.time()
                }
                
                with open(summary_file, 'w') as f:
                    json.dump(summary_data, f, indent=2)
                
                logger.info(f"处理完成，结果保存到: {summary_file}")
            
            # 卸载模型
            await client.unload_model(model_id)
    
    async def run_continuous_monitoring(self):
        """持续监控模式"""
        logger.info("启动持续监控模式...")
        
        async with Hailo8Client(self.hailo8_url) as client:
            while True:
                try:
                    # 获取服务状态
                    status = await client.get_service_status()
                    stats = await client.get_service_stats()
                    
                    logger.info(f"服务状态 - 运行时间: {status.get('uptime', 0):.2f}s, "
                              f"总请求: {stats.get('total_requests', 0)}, "
                              f"成功率: {stats.get('successful_requests', 0) / max(stats.get('total_requests', 1), 1) * 100:.1f}%")
                    
                    # 检查输入目录是否有新文件
                    if self.input_dir.exists():
                        new_files = list(self.input_dir.glob('*.jpg')) + list(self.input_dir.glob('*.png'))
                        if new_files:
                            logger.info(f"发现 {len(new_files)} 个新文件，开始处理...")
                            await self.process_images()
                    
                    # 等待下次检查
                    await asyncio.sleep(30)
                
                except Exception as e:
                    logger.error(f"监控循环错误: {e}")
                    await asyncio.sleep(10)
    
    async def run_demo_mode(self):
        """演示模式"""
        logger.info("运行演示模式...")
        
        async with Hailo8Client(self.hailo8_url) as client:
            # 1. 显示服务信息
            status = await client.get_service_status()
            devices = await client.get_devices()
            
            logger.info(f"服务版本: {status.get('version')}")
            logger.info(f"可用设备: {len(devices)}")
            
            # 2. 创建示例数据
            logger.info("创建示例数据...")
            import numpy as np
            from PIL import Image
            import io
            import base64
            
            # 创建示例图片
            sample_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            pil_image = Image.fromarray(sample_image)
            
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # 3. 加载模型并执行推理
            model_id = "demo_model"
            load_result = await client.load_model(
                model_path="/app/models/demo_model.hef",
                model_id=model_id
            )
            
            if load_result.get('success', False):
                logger.info("模型加载成功，执行推理...")
                
                # 单次推理
                inference_result = await client.run_inference(
                    model_id=model_id,
                    input_data=image_base64
                )
                logger.info(f"推理结果: {inference_result}")
                
                # 批量推理
                batch_result = await client.run_batch_inference(
                    model_id=model_id,
                    input_batch=[image_base64] * 3
                )
                logger.info(f"批量推理结果: {batch_result}")
                
                # 卸载模型
                await client.unload_model(model_id)
            
            # 4. 显示统计信息
            stats = await client.get_service_stats()
            logger.info(f"最终统计: {stats}")


async def main():
    """主函数"""
    app = ClientApp()
    
    # 等待服务可用
    if not await app.wait_for_service():
        logger.error("无法连接到Hailo8服务")
        return
    
    # 根据环境变量选择运行模式
    mode = os.getenv('RUN_MODE', 'demo')
    
    if mode == 'process':
        # 处理输入目录中的图片
        await app.process_images()
    elif mode == 'monitor':
        # 持续监控模式
        await app.run_continuous_monitoring()
    else:
        # 演示模式
        await app.run_demo_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("客户端应用停止")
    except Exception as e:
        logger.error(f"客户端应用错误: {e}")
        raise