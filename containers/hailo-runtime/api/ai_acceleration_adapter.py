#!/usr/bin/env python3
"""
AI加速服务适配器
统一管理Hailo8和NVIDIA GPU推理服务
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
from enum import Enum

import numpy as np
import torch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .inference import HailoInferenceService
from .config import settings

logger = logging.getLogger(__name__)

# 创建AI加速服务路由器
ai_acceleration_router = APIRouter(prefix="/ai", tags=["AI加速"])

# 推理引擎类型
class EngineType(str, Enum):
    AUTO = "auto"      # 自动选择
    HAILO = "hailo"    # 强制使用Hailo8
    NVIDIA = "nvidia"  # 强制使用NVIDIA GPU

# 推理请求模型
class AccelerationRequest(BaseModel):
    """AI加速推理请求模型"""
    image: Union[List[List[List[int]]], str]  # 图像数据或文件路径
    engine: EngineType = EngineType.AUTO     # 推理引擎
    model_name: Optional[str] = None         # 模型名称
    threshold: float = 0.4                    # 置信度阈值
    targets: Optional[List[str]] = None      # 目标类别

# 推理结果模型
class AccelerationResponse(BaseModel):
    """AI加速推理响应模型"""
    success: bool
    engine_used: EngineType                 # 使用的推理引擎
    detections: List[Dict[str, Any]]         # 检测结果
    inference_time: float                     # 推理时间
    model_info: Dict[str, Any]                # 模型信息
    hardware_info: Dict[str, Any]             # 硬件信息
    frame_id: Optional[int] = None            # 帧ID

# 硬件信息模型
class HardwareInfo(BaseModel):
    """硬件信息模型"""
    available_engines: List[str]          # 可用的推理引擎
    hailo_devices: List[Dict[str, Any]]    # Hailo设备信息
    nvidia_devices: List[Dict[str, Any]]  # NVIDIA设备信息
    total_memory: Optional[int] = None     # 总内存(MB)
    used_memory: Optional[int] = None      # 已用内存(MB)


class NVIDIADetector:
    """NVIDIA GPU检测器"""

    def __init__(self):
        self.devices = []
        self._detect_devices()

    def _detect_devices(self):
        """检测NVIDIA设备"""
        try:
            import torch
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                for i in range(device_count):
                    device_info = {
                        'id': i,
                        'name': torch.cuda.get_device_name(i),
                        'memory_total': torch.cuda.get_device_properties(i).total_memory // 1024 // 1024,  # MB
                        'memory_allocated': torch.cuda.memory_allocated(i) // 1024 // 1024,  # MB
                        'capabilities': torch.cuda.get_device_capability(i),
                        'is_available': True
                    }
                    self.devices.append(device_info)
        except Exception as e:
            logger.warning(f"NVIDIA GPU检测失败: {e}")

    def is_available(self) -> bool:
        """检查NVIDIA是否可用"""
        return len(self.devices) > 0

    def get_best_device(self) -> Optional[Dict[str, Any]]:
        """获取最佳NVIDIA设备"""
        if not self.devices:
            return None
        # 返回内存最大的设备
        return max(self.devices, key=lambda x: x['memory_total'])

    def get_devices(self) -> List[Dict[str, Any]]:
        """获取所有设备信息"""
        return self.devices


class Hailo8Detector:
    """Hailo8设备检测器"""

    def __init__(self):
        self.devices = []
        self._detect_devices()

    def _detect_devices(self):
        """检测Hailo8设备"""
        try:
            import hailo_platform as hpf
            device = hpf.Device()
            if device:
                device_info = {
                    'id': 0,
                    'name': 'Hailo8 PCIe Device',
                    'is_available': True,
                    'device_id': getattr(device, 'device_id', 'unknown'),
                    'fw_version': getattr(device, 'fw_version', 'unknown'),
                    'arch': getattr(device, 'arch', 'hailo')
                }
                self.devices.append(device_info)
        except Exception as e:
            logger.warning(f"Hailo8设备检测失败: {e}")

    def is_available(self) -> bool:
        """检查Hailo8是否可用"""
        return len(self.devices) > 0

    def get_best_device(self) -> Optional[Dict[str, Any]]:
        """获取最佳Hailo8设备"""
        if not self.devices:
            return None
        return self.devices[0]  # 通常只有一个设备

    def get_devices(self) -> List[Dict[str, Any]]:
        """获取所有设备信息"""
        return self.devices


class AccelerationService:
    """AI加速服务类"""

    def __init__(self):
        self.hailo_service = None
        self.nvidia_detector = None
        self.hailo_detector = None
        self.default_engine = EngineType.AUTO
        self._initialize_detectors()

    def _initialize_detectors(self):
        """初始化硬件检测器"""
        self.hailo_detector = Hailo8Detector()
        self.nvidia_detector = NVIDIADetector()

    async def initialize(self):
        """初始化服务"""
        try:
            # 初始化Hailo服务
            if self.hailo_detector.is_available():
                self.hailo_service = HailoInferenceService()
                await self.hailo_service.initialize()
                logger.info("Hailo8推理服务初始化完成")
            else:
                logger.warning("Hailo8设备不可用")

            # 检查NVIDIA支持
            if self.nvidia_detector.is_available():
                logger.info(f"NVIDIA GPU可用: {len(self.nvidia_detector.get_devices())} 个设备")
            else:
                logger.warning("NVIDIA GPU不可用")

            # 确定默认推理引擎
            self.default_engine = self._determine_default_engine()
            logger.info(f"默认推理引擎: {self.default_engine}")

        except Exception as e:
            logger.error(f"AI加速服务初始化失败: {e}")
            raise

    def _determine_default_engine(self) -> EngineType:
        """确定默认推理引擎"""
        hailo_available = self.hailo_detector.is_available()
        nvidia_available = self.nvidia_detector.is_available()

        if hailo_available and nvidia_available:
            return EngineType.AUTO
        elif hailo_available:
            return EngineType.HAILO
        elif nvidia_available:
            return EngineType.NVIDIA
        else:
            return EngineType.AUTO

    async def get_hardware_info(self) -> HardwareInfo:
        """获取硬件信息"""
        available_engines = []
        hailo_devices = []
        nvidia_devices = []

        # 检查可用引擎
        if self.hailo_detector.is_available():
            available_engines.append("hailo")
            hailo_devices = self.hailo_detector.get_devices()

        if self.nvidia_detector.is_available():
            available_engines.append("nvidia")
            nvidia_devices = self.nvidia_detector.get_devices()

        # 获取内存信息
        total_memory = None
        used_memory = None

        if nvidia_devices:
            total_memory = sum(device['memory_total'] for device in nvidia_devices)
            used_memory = sum(device['memory_allocated'] for device in nvidia_devices)

        return HardwareInfo(
            available_engines=available_engines,
            hailo_devices=hailo_devices,
            nvidia_devices=nvidia_devices,
            total_memory=total_memory,
            used_memory=used_memory
        )

    def _select_engine(self, preferred_engine: EngineType) -> EngineType:
        """选择推理引擎"""
        # 如果指定了特定引擎
        if preferred_engine != EngineType.AUTO:
            if preferred_engine == EngineType.HAILO and self.hailo_detector.is_available():
                return EngineType.HAILO
            elif preferred_engine == EngineType.NVIDIA and self.nvidia_detector.is_available():
                return EngineType.NVIDIA
            else:
                logger.warning(f"指定的引擎 {preferred_engine} 不可用，使用默认引擎")
                return self.default_engine

        # 自动选择引擎
        if self.default_engine == EngineType.AUTO:
            # 优先使用NVIDIA GPU（性能更好）
            if self.nvidia_detector.is_available():
                return EngineType.NVIDIA
            elif self.hailo_detector.is_available():
                return EngineType.HAILO

        # 回退到默认引擎
        return self.default_engine

    async def infer_with_hailo(self, request: AccelerationRequest) -> Dict[str, Any]:
        """使用Hailo8进行推理"""
        try:
            if not self.hailo_service or not self.hailo_service.is_ready():
                raise HTTPException(status_code=503, detail="Hailo8服务不可用")

            from .models import InferenceRequest

            # 准备推理请求
            inference_request = InferenceRequest(
                model_name=request.model_name,
                input_data=request.image.encode() if isinstance(request.image, str) else request.image.tobytes(),
                confidence_threshold=request.threshold
            )

            # 执行推理
            result = await self.hailo_service.run_inference(inference_request)

            # 标记使用的引擎
            result['engine_used'] = EngineType.HAILO
            result['hardware_device'] = self.hailo_detector.get_best_device()

            return result

        except Exception as e:
            logger.error(f"Hailo8推理失败: {e}")
            raise HTTPException(status_code=500, detail=f"Hailo8推理失败: {str(e)}")

    async def infer_with_nvidia(self, request: AccelerationRequest) -> Dict[str, Any]:
        """使用NVIDIA GPU进行推理"""
        try:
            import torch

            # 检查CUDA可用性
            if not torch.cuda.is_available():
                raise HTTPException(status_code=503, detail="CUDA不可用")

            # 获取最佳设备
            device = self.nvidia_detector.get_best_device()
            if not device:
                raise HTTPException(status_code=503, detail="没有可用的NVIDIA设备")

            device_id = device['id']

            # 处理图像数据
            image_data = self._prepare_image_data(request.image)

            # 使用PyTorch进行推理（这里应该加载实际的模型）
            with torch.cuda.device(device_id):
                # 模拟推理过程
                # 实际应用中，这里应该加载并运行实际的PyTorch模型

                # 创建假的检测结果用于演示
                detections = [
                    {
                        'confidence': 0.85,
                        'class': 'person',
                        'bbox': [100, 100, 300, 300],
                        'track_id': 1
                    },
                    {
                        'confidence': 0.75,
                        'class': 'car',
                        'bbox': [400, 200, 600, 400],
                        'track_id': 2
                    }
                ]

                # 获取GPU内存使用情况
                memory_allocated = torch.cuda.memory_allocated(device_id) // 1024 // 1024

                result = {
                    'success': True,
                    'results': {
                        'predictions': detections
                    },
                    'processing_time': 0.1,  # 模拟处理时间
                    'engine_used': EngineType.NVIDIA,
                    'hardware_device': device,
                    'gpu_memory_used': memory_allocated
                }

            return result

        except Exception as e:
            logger.error(f"NVIDIA推理失败: {e}")
            raise HTTPException(status_code=500, detail=f"NVIDIA推理失败: {str(e)}")

    def _prepare_image_data(self, image: Union[List[List[List[int]]], str]) -> np.ndarray:
        """准备图像数据"""
        try:
            if isinstance(image, str):
                # 如果是文件路径，读取文件
                import cv2
                img_array = cv2.imread(image)
                if img_array is None:
                    raise ValueError(f"无法读取图像文件: {image}")
                return cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            else:
                # 如果是图像数据数组，转换为numpy数组
                return np.array(image, dtype=np.uint8)
        except Exception as e:
            logger.error(f"图像数据处理失败: {e}")
            raise ValueError(f"图像数据处理失败: {e}")

    async def infer(self, request: AccelerationRequest) -> AccelerationResponse:
        """执行AI加速推理"""
        start_time = time.time()

        try:
            # 选择推理引擎
            engine = self._select_engine(request.engine)
            logger.info(f"使用推理引擎: {engine}")

            # 执行推理
            if engine == EngineType.HAILO:
                result = await self.infer_with_hailo(request)
            elif engine == EngineType.NVIDIA:
                result = await self.infer_with_nvidia(request)
            else:
                # 自动选择
                if self.nvidia_detector.is_available():
                    result = await self.infer_with_nvidia(request)
                elif self.hailo_detector.is_available():
                    result = await self.infer_with_hailo(request)
                else:
                    raise HTTPException(status_code=503, detail="没有可用的推理引擎")

            # 构建响应
            inference_time = time.time() - start_time

            return AccelerationResponse(
                success=result.get('success', False),
                engine_used=result.get('engine_used', engine),
                detections=result.get('results', {}).get('predictions', []),
                inference_time=inference_time,
                model_info={
                    'engine': result.get('engine_used', engine),
                    'device': result.get('hardware_device', {}),
                    'model_name': request.model_name
                },
                hardware_info={
                    'engine': result.get('engine_used', engine),
                    'device': result.get('hardware_device', {}),
                    'gpu_memory': result.get('gpu_memory_used') if 'gpu_memory_used' in result else None
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AI加速推理失败: {e}")
            raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            status = {
                'status': 'healthy',
                'service': 'AI加速服务',
                'hardware_info': await self.get_hailo8_device_info() if self.hailo_detector else None
            }

            # 检查Hailo8状态
            if self.hailo_service and self.hailo_service.is_ready():
                status['hailo8'] = 'ready'
            elif self.hailo_detector.is_available():
                status['hailo8'] = 'available'
            else:
                status['hailo8'] = 'unavailable'

            # 检查NVIDIA状态
            if self.nvidia_detector.is_available():
                status['nvidia'] = 'available'
                devices = self.nvidia_detector.get_devices()
                status['nvidia_devices'] = len(devices)
            else:
                status['nvidia'] = 'unavailable'
                status['nvidia_devices'] = 0

            # 确定整体状态
            if status['hailo8'] == 'unavailable' and status['nvidia'] == 'unavailable':
                status['status'] = 'unhealthy'
                status['message'] = '没有可用的AI加速硬件'

            return status

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'status': 'error',
                'service': 'AI加速服务',
                'message': str(e)
            }

    async def get_hailo8_device_info(self) -> Dict[str, Any]:
        """获取Hailo8设备信息"""
        if not self.hailo_service:
            return {'status': 'not_initialized'}

        try:
            return await self.hailo_service.get_device_status()
        except Exception as e:
            logger.error(f"获取Hailo8设备信息失败: {e}")
            return {'status': 'error', 'message': str(e)}


# 全局服务实例
acceleration_service = AccelerationService()


# AI加速API路由
@ai_acceleration_router.post("/infer", response_model=AccelerationResponse)
async def accelerate_inference(request: AccelerationRequest):
    """
    AI加速推理接口

    根据可用硬件自动选择Hailo8或NVIDIA GPU进行推理
    """
    try:
        logger.info(f"收到AI加速推理请求: 引擎={request.engine}, 阈值={request.threshold}")

        result = await acceleration_service.infer(request)

        logger.info(f"AI加速推理完成: 引擎={result.engine_used}, 检测到{len(result.detections)}个对象, 耗时{result.inference_time:.3f}s")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI加速推理失败: {e}")
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@ai_acceleration_router.get("/hardware", response_model=HardwareInfo)
async def get_hardware_info():
    """获取硬件信息"""
    try:
        hardware_info = await acceleration_service.get_hardware_info()
        return hardware_info
    except Exception as e:
        logger.error(f"获取硬件信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取硬件信息失败: {str(e)}")


@ai_acceleration_router.get("/health")
async def acceleration_health_check():
    """AI加速服务健康检查"""
    try:
        health_status = await acceleration_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@ai_acceleration_router.get("/engines")
async def get_available_engines():
    """获取可用的推理引擎"""
    try:
        available_engines = []

        if acceleration_service.hailo_detector.is_available():
            available_engines.append({
                'name': 'hailo8',
                'type': 'edge',
                'description': 'Hailo8 PCIe AI加速卡',
                'devices': acceleration_service.hailo_detector.get_devices()
            })

        if acceleration_service.nvidia_detector.is_available():
            available_engines.append({
                'name': 'nvidia',
                'type': 'gpu',
                'description': 'NVIDIA GPU',
                'devices': acceleration_service.nvidia_detector.get_devices()
            })

        return {
            'available_engines': available_engines,
            'total_count': len(available_engines),
            'default_engine': acceleration_service.default_engine
        }
    except Exception as e:
        logger.error(f"获取推理引擎信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取推理引擎信息失败: {str(e)}")


@ai_acceleration_router.post("/validate")
async def validate_hardware():
    """验证硬件配置"""
    try:
        results = {
            'hailo8': acceleration_service.hailo_detector.is_available(),
            'nvidia': acceleration_service.nvidia_detector.is_available(),
            'total_engines': 0
        }

        if results['hailo8']:
            results['hailo8_devices'] = acceleration_service.hailo_detector.get_devices()
            results['total_engines'] += len(results['hailo8_devices'])

        if results['nvidia']:
            results['nvidia_devices'] = acceleration_service.nvidia_detector.get_devices()
            results['total_engines'] += len(results['nvidia_devices'])

        results['validation_time'] = time.time()

        return {
            'success': results['total_engines'] > 0,
            'results': results,
            'message': f"检测到 {results['total_engines']} 个可用推理引擎"
        }

    except Exception as e:
        logger.error(f"硬件验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"硬件验证失败: {str(e)}")


# 初始化函数
async def init_acceleration_service():
    """初始化AI加速服务"""
    await acceleration_service.initialize()