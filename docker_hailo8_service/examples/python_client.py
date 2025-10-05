#!/usr/bin/env python3
"""
Hailo8服务Python客户端示例
演示如何从其他容器或应用程序调用Hailo8硬件加速服务
"""

import asyncio
import aiohttp
import base64
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Hailo8Client:
    """Hailo8服务客户端"""
    
    def __init__(self, base_url: str = "http://hailo8-service:8080"):
        """
        初始化客户端
        
        Args:
            base_url: Hailo8服务的基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """获取设备列表"""
        try:
            async with self.session.get(f"{self.base_url}/api/devices") as response:
                result = await response.json()
                return result.get("devices", [])
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return []
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        try:
            async with self.session.get(f"{self.base_url}/api/status") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"获取服务状态失败: {e}")
            return {}
    
    async def load_model(self, model_path: str, model_id: str, 
                        device_id: Optional[str] = None) -> Dict[str, Any]:
        """加载模型"""
        try:
            data = {
                "model_path": model_path,
                "model_id": model_id
            }
            if device_id:
                data["device_id"] = device_id
            
            async with self.session.post(
                f"{self.base_url}/api/models/load",
                json=data
            ) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """卸载模型"""
        try:
            async with self.session.delete(
                f"{self.base_url}/api/models/{model_id}"
            ) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"卸载模型失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """获取已加载模型列表"""
        try:
            async with self.session.get(f"{self.base_url}/api/models") as response:
                result = await response.json()
                return result.get("models", [])
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return []
    
    async def run_inference(self, model_id: str, input_data: str,
                          input_format: str = "base64", 
                          output_format: str = "json") -> Dict[str, Any]:
        """执行推理"""
        try:
            data = {
                "model_id": model_id,
                "input_data": input_data,
                "input_format": input_format,
                "output_format": output_format
            }
            
            async with self.session.post(
                f"{self.base_url}/api/inference",
                json=data
            ) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"推理失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def run_batch_inference(self, model_id: str, input_batch: List[str],
                                input_format: str = "base64",
                                output_format: str = "json",
                                batch_size: Optional[int] = None) -> Dict[str, Any]:
        """批量推理"""
        try:
            data = {
                "model_id": model_id,
                "input_batch": input_batch,
                "input_format": input_format,
                "output_format": output_format
            }
            if batch_size:
                data["batch_size"] = batch_size
            
            async with self.session.post(
                f"{self.base_url}/api/inference/batch",
                json=data
            ) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"批量推理失败: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计"""
        try:
            async with self.session.get(f"{self.base_url}/api/stats") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"获取服务统计失败: {e}")
            return {}


def image_to_base64(image_path: str) -> str:
    """将图片文件转换为base64字符串"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


async def main():
    """主函数 - 演示客户端使用"""
    
    # 创建客户端
    async with Hailo8Client("http://localhost:8080") as client:
        
        print("=== Hailo8服务客户端示例 ===\n")
        
        # 1. 健康检查
        print("1. 健康检查...")
        health = await client.health_check()
        print(f"健康状态: {health}")
        
        if not health.get("healthy", False):
            print("服务不健康，退出")
            return
        
        # 2. 获取设备列表
        print("\n2. 获取设备列表...")
        devices = await client.get_devices()
        print(f"发现设备数量: {len(devices)}")
        for device in devices:
            print(f"  - {device.get('device_id')}: {device.get('device_name')} "
                  f"({device.get('status')})")
        
        # 3. 获取服务状态
        print("\n3. 获取服务状态...")
        status = await client.get_service_status()
        print(f"服务版本: {status.get('version')}")
        print(f"运行时间: {status.get('uptime', 0):.2f}秒")
        print(f"总请求数: {status.get('total_requests', 0)}")
        
        # 4. 加载模型（示例）
        print("\n4. 加载模型...")
        model_result = await client.load_model(
            model_path="/app/models/yolov5s.hef",
            model_id="yolov5s_demo"
        )
        print(f"模型加载结果: {model_result}")
        
        if model_result.get("success"):
            # 5. 获取已加载模型列表
            print("\n5. 获取已加载模型...")
            models = await client.list_models()
            print(f"已加载模型数量: {len(models)}")
            for model in models:
                print(f"  - {model.get('model_id')}: {model.get('model_path')}")
            
            # 6. 执行推理（需要实际的图片文件）
            print("\n6. 执行推理...")
            
            # 创建示例图片数据（实际使用时应该是真实图片）
            # 这里使用随机数据作为示例
            import numpy as np
            from PIL import Image
            import io
            
            # 创建示例图片
            sample_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            pil_image = Image.fromarray(sample_image)
            
            # 转换为base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG')
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # 执行推理
            inference_result = await client.run_inference(
                model_id="yolov5s_demo",
                input_data=image_base64,
                input_format="base64",
                output_format="json"
            )
            print(f"推理结果: {inference_result}")
            
            # 7. 批量推理示例
            print("\n7. 批量推理...")
            batch_result = await client.run_batch_inference(
                model_id="yolov5s_demo",
                input_batch=[image_base64, image_base64],  # 两个相同的示例图片
                input_format="base64",
                output_format="json",
                batch_size=2
            )
            print(f"批量推理结果: {batch_result}")
            
            # 8. 卸载模型
            print("\n8. 卸载模型...")
            unload_result = await client.unload_model("yolov5s_demo")
            print(f"模型卸载结果: {unload_result}")
        
        # 9. 获取服务统计
        print("\n9. 获取服务统计...")
        stats = await client.get_service_stats()
        print(f"总请求数: {stats.get('total_requests', 0)}")
        print(f"成功请求数: {stats.get('successful_requests', 0)}")
        print(f"失败请求数: {stats.get('failed_requests', 0)}")
        print(f"平均响应时间: {stats.get('avg_response_time', 0):.2f}ms")
        
        print("\n=== 示例完成 ===")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())