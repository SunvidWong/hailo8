"""
Hailo8服务客户端库
提供简单易用的API来与Hailo8服务进行交互
"""

import aiohttp
import asyncio
import json
import base64
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class Hailo8ClientError(Exception):
    """Hailo8客户端异常"""
    pass


class Hailo8Client:
    """Hailo8服务异步客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            base_url: Hailo8服务的基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数
            
        Returns:
            响应数据
            
        Raises:
            Hailo8ClientError: 请求失败时抛出
        """
        if not self.session:
            raise Hailo8ClientError("客户端未初始化，请使用async with语句")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.content_type == 'application/json':
                    data = await response.json()
                else:
                    text = await response.text()
                    data = {"message": text}
                
                if response.status >= 400:
                    error_msg = data.get('detail', data.get('message', f'HTTP {response.status}'))
                    raise Hailo8ClientError(f"请求失败: {error_msg}")
                
                return data
        
        except aiohttp.ClientError as e:
            raise Hailo8ClientError(f"网络请求错误: {e}")
        except asyncio.TimeoutError:
            raise Hailo8ClientError("请求超时")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return await self._request('GET', '/health')
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """获取设备列表"""
        response = await self._request('GET', '/devices')
        return response.get('devices', [])
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return await self._request('GET', '/status')
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return await self._request('GET', '/stats')
    
    async def load_model(self, model_path: str, model_id: str, 
                        config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        加载模型
        
        Args:
            model_path: 模型文件路径
            model_id: 模型ID
            config: 模型配置
            
        Returns:
            加载结果
        """
        data = {
            "model_path": model_path,
            "model_id": model_id
        }
        if config:
            data["config"] = config
        
        return await self._request('POST', '/models/load', json=data)
    
    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """卸载模型"""
        return await self._request('POST', f'/models/{model_id}/unload')
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """列出已加载的模型"""
        response = await self._request('GET', '/models')
        return response.get('models', [])
    
    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息"""
        return await self._request('GET', f'/models/{model_id}')
    
    async def run_inference(self, model_id: str, input_data: Union[str, bytes, Dict],
                           input_format: str = "base64", output_format: str = "json",
                           config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行单次推理
        
        Args:
            model_id: 模型ID
            input_data: 输入数据
            input_format: 输入格式 (base64, binary, json)
            output_format: 输出格式 (json, base64, binary)
            config: 推理配置
            
        Returns:
            推理结果
        """
        data = {
            "model_id": model_id,
            "input_data": input_data,
            "input_format": input_format,
            "output_format": output_format
        }
        if config:
            data["config"] = config
        
        return await self._request('POST', '/inference', json=data)
    
    async def run_batch_inference(self, model_id: str, input_batch: List[Union[str, bytes, Dict]],
                                 input_format: str = "base64", output_format: str = "json",
                                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行批量推理
        
        Args:
            model_id: 模型ID
            input_batch: 输入数据批次
            input_format: 输入格式
            output_format: 输出格式
            config: 推理配置
            
        Returns:
            批量推理结果
        """
        data = {
            "model_id": model_id,
            "input_batch": input_batch,
            "input_format": input_format,
            "output_format": output_format
        }
        if config:
            data["config"] = config
        
        return await self._request('POST', '/inference/batch', json=data)
    
    async def submit_async_inference(self, model_id: str, input_data: Union[str, bytes, Dict],
                                   input_format: str = "base64", output_format: str = "json",
                                   config: Optional[Dict[str, Any]] = None) -> str:
        """
        提交异步推理任务
        
        Args:
            model_id: 模型ID
            input_data: 输入数据
            input_format: 输入格式
            output_format: 输出格式
            config: 推理配置
            
        Returns:
            任务ID
        """
        data = {
            "model_id": model_id,
            "input_data": input_data,
            "input_format": input_format,
            "output_format": output_format
        }
        if config:
            data["config"] = config
        
        response = await self._request('POST', '/inference/async', json=data)
        return response.get('task_id')
    
    async def get_async_result(self, task_id: str) -> Dict[str, Any]:
        """获取异步推理结果"""
        return await self._request('GET', f'/inference/async/{task_id}')
    
    async def wait_for_async_result(self, task_id: str, timeout: int = 60, 
                                  poll_interval: float = 1.0) -> Dict[str, Any]:
        """
        等待异步推理完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            推理结果
            
        Raises:
            Hailo8ClientError: 超时或任务失败时抛出
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            result = await self.get_async_result(task_id)
            status = result.get('status')
            
            if status == 'completed':
                return result
            elif status == 'failed':
                error = result.get('error', '未知错误')
                raise Hailo8ClientError(f"异步推理失败: {error}")
            elif status in ['pending', 'running']:
                # 检查超时
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    raise Hailo8ClientError(f"异步推理超时: {timeout}秒")
                
                # 等待下次轮询
                await asyncio.sleep(poll_interval)
            else:
                raise Hailo8ClientError(f"未知任务状态: {status}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标"""
        return await self._request('GET', '/metrics')


# 便利函数
async def load_image_as_base64(image_path: Union[str, Path]) -> str:
    """
    加载图片并转换为base64格式
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        base64编码的图片数据
    """
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


async def save_base64_image(base64_data: str, output_path: Union[str, Path]):
    """
    保存base64格式的图片数据到文件
    
    Args:
        base64_data: base64编码的图片数据
        output_path: 输出文件路径
    """
    image_data = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)


# 示例使用
async def example_usage():
    """使用示例"""
    async with Hailo8Client('http://localhost:8080') as client:
        # 健康检查
        health = await client.health_check()
        print(f"服务健康状态: {health}")
        
        # 获取设备信息
        devices = await client.get_devices()
        print(f"可用设备: {len(devices)}")
        
        # 加载模型
        load_result = await client.load_model(
            model_path="/path/to/model.hef",
            model_id="my_model"
        )
        print(f"模型加载结果: {load_result}")
        
        # 加载图片并执行推理
        image_base64 = await load_image_as_base64("/path/to/image.jpg")
        inference_result = await client.run_inference(
            model_id="my_model",
            input_data=image_base64
        )
        print(f"推理结果: {inference_result}")
        
        # 卸载模型
        await client.unload_model("my_model")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())