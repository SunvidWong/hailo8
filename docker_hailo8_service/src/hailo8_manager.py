"""
Hailo8硬件管理器
负责设备管理、模型加载和推理执行
"""

import os
import sys
import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor
import threading

# 导入配置和模型
from config import settings, get_device_config, get_model_config
from models import DeviceInfo, DeviceStatus, ModelInfo, TaskStatus

# 设置日志
logger = logging.getLogger(__name__)


class Hailo8Manager:
    """Hailo8硬件管理器"""
    
    def __init__(self, mock_mode: bool = None):
        """初始化管理器"""
        self.mock_mode = mock_mode if mock_mode is not None else settings.HAILO_MOCK_MODE
        self.devices: Dict[str, DeviceInfo] = {}
        self.loaded_models: Dict[str, ModelInfo] = {}
        self.active_tasks: Dict[str, Dict] = {}
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_inference_time": 0.0,
            "total_inferences": 0,
            "start_time": time.time()
        }
        
        # 线程池用于执行推理任务
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_INFERENCES)
        self.lock = threading.RLock()
        
        # Hailo8相关对象（在实际环境中初始化）
        self.hailo_device = None
        self.hailo_network_groups = {}
        
        logger.info(f"Hailo8Manager初始化 - 模拟模式: {self.mock_mode}")
    
    async def initialize(self):
        """初始化管理器"""
        try:
            logger.info("正在初始化Hailo8管理器...")
            
            if self.mock_mode:
                await self._init_mock_devices()
            else:
                await self._init_real_devices()
            
            # 预加载模型
            if settings.MODEL_PRELOAD:
                await self._preload_models()
            
            logger.info(f"Hailo8管理器初始化完成 - 设备数: {len(self.devices)}")
            
        except Exception as e:
            logger.error(f"Hailo8管理器初始化失败: {e}")
            # 如果真实设备初始化失败，回退到模拟模式
            if not self.mock_mode:
                logger.warning("回退到模拟模式")
                self.mock_mode = True
                await self._init_mock_devices()
    
    async def _init_mock_devices(self):
        """初始化模拟设备"""
        logger.info("初始化模拟Hailo8设备...")
        
        for i in range(settings.HAILO_DEVICE_COUNT):
            device_id = f"hailo8_mock_{i}"
            device_info = DeviceInfo(
                device_id=device_id,
                device_name=f"Hailo8 Mock Device {i}",
                status=DeviceStatus.AVAILABLE,
                temperature=45.0 + i * 2,
                utilization=0.0,
                memory_used=0,
                memory_total=1024,
                firmware_version="4.23.0-mock",
                driver_version="4.23.0-mock"
            )
            self.devices[device_id] = device_info
            logger.info(f"模拟设备已创建: {device_id}")
    
    async def _init_real_devices(self):
        """初始化真实设备"""
        logger.info("初始化真实Hailo8设备...")
        
        try:
            # 尝试导入Hailo8库
            import hailo_platform
            
            # 检测设备
            device_infos = hailo_platform.Device.scan()
            
            if not device_infos:
                raise RuntimeError("未检测到Hailo8设备")
            
            for i, device_info in enumerate(device_infos):
                device_id = f"hailo8_{i}"
                
                # 创建设备对象
                device = hailo_platform.Device(device_info)
                
                # 获取设备信息
                device_data = DeviceInfo(
                    device_id=device_id,
                    device_name=f"Hailo8 Device {i}",
                    status=DeviceStatus.AVAILABLE,
                    temperature=device.get_temperature() if hasattr(device, 'get_temperature') else None,
                    utilization=0.0,
                    memory_used=0,
                    memory_total=device.get_memory_size() if hasattr(device, 'get_memory_size') else 1024,
                    firmware_version=device.get_firmware_version() if hasattr(device, 'get_firmware_version') else "unknown",
                    driver_version="4.23.0"
                )
                
                self.devices[device_id] = device_data
                logger.info(f"真实设备已初始化: {device_id}")
                
        except ImportError:
            logger.warning("Hailo8库未安装，使用模拟模式")
            raise RuntimeError("Hailo8库未安装")
        except Exception as e:
            logger.error(f"真实设备初始化失败: {e}")
            raise
    
    async def _preload_models(self):
        """预加载模型"""
        logger.info("预加载模型...")
        
        for model_path in settings.MODEL_PRELOAD:
            try:
                model_id = f"preload_{os.path.basename(model_path)}"
                await self.load_model(model_path, model_id)
                logger.info(f"预加载模型成功: {model_id}")
            except Exception as e:
                logger.error(f"预加载模型失败 {model_path}: {e}")
    
    async def cleanup(self):
        """清理资源"""
        logger.info("正在清理Hailo8管理器...")
        
        # 停止所有任务
        for task_id in list(self.active_tasks.keys()):
            await self._cancel_task(task_id)
        
        # 卸载所有模型
        for model_id in list(self.loaded_models.keys()):
            await self.unload_model(model_id)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("Hailo8管理器清理完成")
    
    # ==================== 设备管理 ====================
    
    async def get_devices(self) -> List[DeviceInfo]:
        """获取设备列表"""
        with self.lock:
            return list(self.devices.values())
    
    async def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """获取指定设备信息"""
        with self.lock:
            return self.devices.get(device_id)
    
    async def update_device_status(self, device_id: str, status: DeviceStatus):
        """更新设备状态"""
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id].status = status
                self.devices[device_id].last_update = datetime.now()
    
    def _get_available_device(self) -> Optional[str]:
        """获取可用设备"""
        with self.lock:
            for device_id, device in self.devices.items():
                if device.status == DeviceStatus.AVAILABLE:
                    return device_id
            return None
    
    # ==================== 模型管理 ====================
    
    async def load_model(self, model_path: str, model_id: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """加载模型"""
        try:
            logger.info(f"加载模型: {model_id} from {model_path}")
            
            # 检查模型是否已加载
            if model_id in self.loaded_models:
                return {
                    "success": False,
                    "model_id": model_id,
                    "message": "模型已加载"
                }
            
            # 检查模型文件
            if not self.mock_mode and not os.path.exists(model_path):
                return {
                    "success": False,
                    "model_id": model_id,
                    "message": f"模型文件不存在: {model_path}"
                }
            
            # 选择设备
            if device_id is None:
                device_id = self._get_available_device()
                if device_id is None:
                    return {
                        "success": False,
                        "model_id": model_id,
                        "message": "没有可用设备"
                    }
            
            # 更新设备状态
            await self.update_device_status(device_id, DeviceStatus.BUSY)
            
            try:
                if self.mock_mode:
                    # 模拟加载
                    await asyncio.sleep(0.5)  # 模拟加载时间
                    input_shape = [1, 3, 224, 224]
                    output_shape = [1, 1000]
                    model_size = 50 * 1024 * 1024  # 50MB
                else:
                    # 真实加载
                    input_shape, output_shape, model_size = await self._load_real_model(model_path, device_id)
                
                # 创建模型信息
                model_info = ModelInfo(
                    model_id=model_id,
                    model_path=model_path,
                    device_id=device_id,
                    load_time=datetime.now(),
                    input_shape=input_shape,
                    output_shape=output_shape,
                    model_size=model_size
                )
                
                with self.lock:
                    self.loaded_models[model_id] = model_info
                
                # 恢复设备状态
                await self.update_device_status(device_id, DeviceStatus.AVAILABLE)
                
                logger.info(f"模型加载成功: {model_id} on {device_id}")
                
                return {
                    "success": True,
                    "model_id": model_id,
                    "message": "模型加载成功",
                    "details": {
                        "device_id": device_id,
                        "input_shape": input_shape,
                        "output_shape": output_shape,
                        "model_size": model_size
                    }
                }
                
            except Exception as e:
                # 恢复设备状态
                await self.update_device_status(device_id, DeviceStatus.AVAILABLE)
                raise e
                
        except Exception as e:
            logger.error(f"模型加载失败 {model_id}: {e}")
            return {
                "success": False,
                "model_id": model_id,
                "message": f"模型加载失败: {str(e)}"
            }
    
    async def _load_real_model(self, model_path: str, device_id: str) -> tuple:
        """加载真实模型"""
        try:
            import hailo_platform
            
            # 这里应该实现真实的模型加载逻辑
            # 由于需要实际的Hailo8硬件和模型文件，这里提供框架
            
            # 示例代码（需要根据实际API调整）:
            # device = self.hailo_device
            # network_group = device.configure(model_path)
            # self.hailo_network_groups[model_id] = network_group
            
            # 返回模型信息
            return [1, 3, 224, 224], [1, 1000], os.path.getsize(model_path)
            
        except Exception as e:
            logger.error(f"真实模型加载失败: {e}")
            raise
    
    async def unload_model(self, model_id: str) -> Dict[str, Any]:
        """卸载模型"""
        try:
            logger.info(f"卸载模型: {model_id}")
            
            with self.lock:
                if model_id not in self.loaded_models:
                    return {
                        "success": False,
                        "message": "模型未加载"
                    }
                
                model_info = self.loaded_models[model_id]
                device_id = model_info.device_id
                
                # 清理模型资源
                if not self.mock_mode and model_id in self.hailo_network_groups:
                    # 清理真实模型资源
                    del self.hailo_network_groups[model_id]
                
                # 移除模型信息
                del self.loaded_models[model_id]
            
            logger.info(f"模型卸载成功: {model_id}")
            
            return {
                "success": True,
                "message": f"模型 {model_id} 卸载成功"
            }
            
        except Exception as e:
            logger.error(f"模型卸载失败 {model_id}: {e}")
            return {
                "success": False,
                "message": f"模型卸载失败: {str(e)}"
            }
    
    async def list_models(self) -> List[ModelInfo]:
        """获取已加载模型列表"""
        with self.lock:
            return list(self.loaded_models.values())
    
    # ==================== 推理服务 ====================
    
    async def run_inference(self, model_id: str, input_data: Any, 
                          input_format: str = "base64", output_format: str = "json") -> Dict[str, Any]:
        """执行推理"""
        try:
            start_time = time.time()
            
            # 检查模型
            if model_id not in self.loaded_models:
                return {
                    "success": False,
                    "message": f"模型未加载: {model_id}"
                }
            
            model_info = self.loaded_models[model_id]
            device_id = model_info.device_id
            
            # 更新统计
            with self.lock:
                self.stats["total_requests"] += 1
            
            # 执行推理
            if self.mock_mode:
                result = await self._run_mock_inference(model_id, input_data, input_format, output_format)
            else:
                result = await self._run_real_inference(model_id, input_data, input_format, output_format)
            
            # 计算推理时间
            inference_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 更新统计
            with self.lock:
                self.stats["successful_requests"] += 1
                self.stats["total_inference_time"] += inference_time
                self.stats["total_inferences"] += 1
                model_info.inference_count += 1
                
                # 更新平均推理时间
                if model_info.avg_inference_time is None:
                    model_info.avg_inference_time = inference_time
                else:
                    model_info.avg_inference_time = (
                        model_info.avg_inference_time * (model_info.inference_count - 1) + inference_time
                    ) / model_info.inference_count
            
            logger.info(f"推理完成: {model_id}, 耗时: {inference_time:.2f}ms")
            
            return {
                "success": True,
                "output_data": result,
                "inference_time": inference_time,
                "message": "推理成功"
            }
            
        except Exception as e:
            logger.error(f"推理失败 {model_id}: {e}")
            with self.lock:
                self.stats["failed_requests"] += 1
            
            return {
                "success": False,
                "message": f"推理失败: {str(e)}"
            }
    
    async def _run_mock_inference(self, model_id: str, input_data: Any, 
                                input_format: str, output_format: str) -> Any:
        """执行模拟推理"""
        # 模拟推理延迟
        await asyncio.sleep(settings.MOCK_INFERENCE_DELAY)
        
        # 返回模拟结果
        if output_format == "json":
            return {
                "predictions": [
                    {"class": "cat", "confidence": 0.95},
                    {"class": "dog", "confidence": 0.03},
                    {"class": "bird", "confidence": 0.02}
                ],
                "model_id": model_id,
                "mock": True
            }
        else:
            return "mock_result_data"
    
    async def _run_real_inference(self, model_id: str, input_data: Any,
                                input_format: str, output_format: str) -> Any:
        """执行真实推理"""
        try:
            # 这里应该实现真实的推理逻辑
            # 需要根据实际的Hailo8 API进行调整
            
            # 示例代码框架:
            # network_group = self.hailo_network_groups[model_id]
            # processed_input = self._preprocess_input(input_data, input_format)
            # raw_output = network_group.infer(processed_input)
            # result = self._postprocess_output(raw_output, output_format)
            
            # 暂时返回模拟结果
            return await self._run_mock_inference(model_id, input_data, input_format, output_format)
            
        except Exception as e:
            logger.error(f"真实推理失败: {e}")
            raise
    
    async def run_batch_inference(self, model_id: str, input_batch: List[Any],
                                input_format: str = "base64", output_format: str = "json",
                                batch_size: Optional[int] = None) -> Dict[str, Any]:
        """批量推理"""
        try:
            start_time = time.time()
            
            if batch_size is None:
                batch_size = min(len(input_batch), settings.HAILO_MAX_BATCH_SIZE)
            
            results = []
            
            # 分批处理
            for i in range(0, len(input_batch), batch_size):
                batch = input_batch[i:i + batch_size]
                batch_results = []
                
                # 并发执行批次内的推理
                tasks = []
                for input_data in batch:
                    task = self.run_inference(model_id, input_data, input_format, output_format)
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
            
            total_time = (time.time() - start_time) * 1000
            
            logger.info(f"批量推理完成: {model_id}, 数量: {len(input_batch)}, 耗时: {total_time:.2f}ms")
            
            return {
                "success": True,
                "batch_results": results,
                "total_time": total_time,
                "message": f"批量推理完成，处理 {len(input_batch)} 个样本"
            }
            
        except Exception as e:
            logger.error(f"批量推理失败 {model_id}: {e}")
            return {
                "success": False,
                "message": f"批量推理失败: {str(e)}"
            }
    
    # ==================== 任务管理 ====================
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        with self.lock:
            return self.active_tasks.get(task_id)
    
    async def _cancel_task(self, task_id: str):
        """取消任务"""
        with self.lock:
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = TaskStatus.CANCELLED
    
    # ==================== 状态和监控 ====================
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            healthy = True
            details = {
                "devices": len(self.devices),
                "loaded_models": len(self.loaded_models),
                "active_tasks": len(self.active_tasks),
                "mock_mode": self.mock_mode
            }
            
            # 检查设备状态
            for device_id, device in self.devices.items():
                if device.status == DeviceStatus.ERROR:
                    healthy = False
                    details[f"device_{device_id}_error"] = True
            
            return {
                "healthy": healthy,
                "timestamp": datetime.now(),
                "details": details
            }
            
        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {
                "healthy": False,
                "timestamp": datetime.now(),
                "details": {"error": str(e)}
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        uptime = time.time() - self.stats["start_time"]
        
        return {
            "service_name": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "uptime": uptime,
            "total_requests": self.stats["total_requests"],
            "active_tasks": len(self.active_tasks),
            "loaded_models": len(self.loaded_models),
            "available_devices": len([d for d in self.devices.values() if d.status == DeviceStatus.AVAILABLE]),
            "system_info": {
                "mock_mode": self.mock_mode,
                "python_version": sys.version,
                "platform": sys.platform
            }
        }
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计"""
        uptime = time.time() - self.stats["start_time"]
        
        avg_response_time = 0.0
        if self.stats["total_requests"] > 0:
            avg_response_time = self.stats["total_inference_time"] / self.stats["total_requests"]
        
        return {
            "total_requests": self.stats["total_requests"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "avg_response_time": avg_response_time,
            "total_inference_time": self.stats["total_inference_time"],
            "total_inferences": self.stats["total_inferences"],
            "active_models": len(self.loaded_models),
            "device_stats": [
                {
                    "device_id": device.device_id,
                    "status": device.status.value,
                    "temperature": device.temperature,
                    "utilization": device.utilization,
                    "memory_usage": device.memory_used / device.memory_total if device.memory_total else 0
                }
                for device in self.devices.values()
            ],
            "memory_usage": {"used": 0, "total": 0},  # 需要实现系统内存监控
            "cpu_usage": 0.0,  # 需要实现CPU监控
            "uptime": uptime
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """获取Prometheus格式的监控指标"""
        stats = await self.get_service_stats()
        
        # 转换为Prometheus格式
        metrics = {
            "hailo8_total_requests": stats["total_requests"],
            "hailo8_successful_requests": stats["successful_requests"],
            "hailo8_failed_requests": stats["failed_requests"],
            "hailo8_avg_response_time_ms": stats["avg_response_time"],
            "hailo8_active_models": stats["active_models"],
            "hailo8_uptime_seconds": stats["uptime"]
        }
        
        # 添加设备指标
        for i, device_stat in enumerate(stats["device_stats"]):
            metrics[f"hailo8_device_{i}_temperature"] = device_stat.get("temperature", 0)
            metrics[f"hailo8_device_{i}_utilization"] = device_stat.get("utilization", 0)
            metrics[f"hailo8_device_{i}_memory_usage"] = device_stat.get("memory_usage", 0)
        
        return metrics