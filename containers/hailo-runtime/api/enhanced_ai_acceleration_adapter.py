#!/usr/bin/env python3
"""
增强版AI加速服务适配器
支持Hailo8和NVIDIA GPU同时调用、负载分配和并行推理
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import random

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
    AUTO = "auto"           # 自动分配
    HAILO = "hailo"         # 仅Hailo8
    NVIDIA = "nvidia"       # 仅NVIDIA
    BOTH = "both"           # 同时使用两个引擎
    PARALLEL = "parallel"   # 并行推理
    LOAD_BALANCE = "load_balance"  # 负载均衡

# 推理请求模型
class AccelerationRequest(BaseModel):
    """AI加速推理请求模型"""
    image: Union[List[List[List[int]]], str]  # 图像数据或文件路径
    engine: EngineType = EngineType.AUTO       # 推理引擎
    model_name: Optional[str] = None           # 模型名称
    threshold: float = 0.4                      # 置信度阈值
    targets: Optional[List[str]] = None        # 目标类别
    # 新增参数
    priority: str = "performance"               # performance/latency/accuracy
    max_results: int = 100                     # 最大结果数
    timeout: float = 10.0                      # 超时时间(秒)

# 推理结果模型
class AccelerationResponse(BaseModel):
    """AI加速推理响应模型"""
    success: bool
    engines_used: List[EngineType]             # 使用的推理引擎列表
    detections: List[Dict[str, Any]]           # 检测结果
    inference_time: float                      # 总推理时间
    model_info: Dict[str, Any]                 # 模型信息
    hardware_info: Dict[str, Any]              # 硬件信息
    frame_id: Optional[int] = None             # 帧ID
    # 新增字段
    engine_results: Dict[str, Any]             # 各引擎的详细结果
    performance_metrics: Dict[str, float]      # 性能指标


class LoadBalancer:
    """负载均衡器"""

    def __init__(self):
        self.hailo_weight = 1.0
        self.nvidia_weight = 1.0
        self.hailo_usage = 0.0
        self.nvidia_usage = 0.0
        self.last_reset = time.time()

    def update_weights(self, hailo_perf: float, nvidia_perf: float):
        """根据性能更新权重"""
        # 性能越好，权重越高
        self.hailo_weight = 1.0 / (hailo_perf + 0.001)
        self.nvidia_weight = 1.0 / (nvidia_perf + 0.001)

    def select_engine(self) -> EngineType:
        """根据负载和权重选择引擎"""
        # 简单的负载均衡算法
        total_weight = self.hailo_weight + self.nvidia_weight

        if random.random() < self.hailo_weight / total_weight:
            return EngineType.HAILO
        else:
            return EngineType.NVIDIA

    def reset_usage_counters(self):
        """重置使用计数器"""
        current_time = time.time()
        if current_time - self.last_reset > 60:  # 每分钟重置
            self.hailo_usage = 0.0
            self.nvidia_usage = 0.0
            self.last_reset = current_time


class EnhancedAccelerationService:
    """增强版AI加速服务类"""

    def __init__(self):
        self.hailo_service = None
        self.nvidia_detector = None
        self.hailo_detector = None
        self.load_balancer = LoadBalancer()
        self.performance_history = {
            'hailo': [],
            'nvidia': []
        }
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

            logger.info("增强版AI加速服务初始化完成")

        except Exception as e:
            logger.error(f"AI加速服务初始化失败: {e}")
            raise

    def get_available_engines(self) -> List[EngineType]:
        """获取可用的推理引擎列表"""
        available = []
        if self.hailo_detector.is_available():
            available.append(EngineType.HAILO)
        if self.nvidia_detector.is_available():
            available.append(EngineType.NVIDIA)

        # 如果两个都可用，添加复合引擎类型
        if len(available) == 2:
            available.extend([EngineType.BOTH, EngineType.PARALLEL, EngineType.LOAD_BALANCE])

        return available

    async def infer_parallel(self, request: AccelerationRequest) -> Dict[str, Any]:
        """并行推理：同时使用两个引擎"""
        tasks = []
        results = {}

        # 并行启动推理任务
        if self.hailo_detector.is_available():
            tasks.append(self._infer_with_hailo_internal(request))

        if self.nvidia_detector.is_available():
            tasks.append(self._infer_with_nvidia_internal(request))

        if not tasks:
            raise HTTPException(status_code=503, detail="没有可用的推理引擎")

        # 等待所有任务完成
        try:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            engine_types = []
            if self.hailo_detector.is_available():
                hailo_result = task_results[0]
                if not isinstance(hailo_result, Exception):
                    results['hailo'] = hailo_result
                    engine_types.append(EngineType.HAILO)
                    self._update_performance_history('hailo', hailo_result.get('processing_time', 0))

            if self.nvidia_detector.is_available():
                nvidia_idx = 1 if self.hailo_detector.is_available() else 0
                nvidia_result = task_results[nvidia_idx]
                if not isinstance(nvidia_result, Exception):
                    results['nvidia'] = nvidia_result
                    engine_types.append(EngineType.NVIDIA)
                    self._update_performance_history('nvidia', nvidia_result.get('processing_time', 0))

            # 合并检测结果
            merged_detections = self._merge_detections(results)

            return {
                'success': True,
                'engines_used': engine_types,
                'detections': merged_detections,
                'engine_results': results,
                'processing_time': max(r.get('processing_time', 0) for r in results.values()),
                'parallel_execution': True
            }

        except Exception as e:
            logger.error(f"并行推理失败: {e}")
            raise HTTPException(status_code=500, detail=f"并行推理失败: {str(e)}")

    async def infer_load_balance(self, request: AccelerationRequest) -> Dict[str, Any]:
        """负载均衡推理"""
        self.load_balancer.reset_usage_counters()

        # 选择引擎
        selected_engine = self.load_balancer.select_engine()

        logger.info(f"负载均衡选择引擎: {selected_engine}")

        if selected_engine == EngineType.HAILO:
            result = await self._infer_with_hailo_internal(request)
            self.load_balancer.hailo_usage += 1
        else:
            result = await self._infer_with_nvidia_internal(request)
            self.load_balancer.nvidia_usage += 1

        result['engines_used'] = [selected_engine]
        result['load_balance_selection'] = True

        return result

    async def infer_both(self, request: AccelerationRequest) -> Dict[str, Any]:
        """双引擎推理：使用两个引擎并对结果进行融合"""
        # 首先尝试Hailo8
        hailo_result = None
        nvidia_result = None

        if self.hailo_detector.is_available():
            try:
                hailo_result = await self._infer_with_hailo_internal(request)
                logger.info("Hailo8推理完成")
            except Exception as e:
                logger.warning(f"Hailo8推理失败: {e}")

        # 然后尝试NVIDIA
        if self.nvidia_detector.is_available():
            try:
                nvidia_result = await self._infer_with_nvidia_internal(request)
                logger.info("NVIDIA推理完成")
            except Exception as e:
                logger.warning(f"NVIDIA推理失败: {e}")

        if not hailo_result and not nvidia_result:
            raise HTTPException(status_code=503, detail="所有引擎都失败了")

        # 融合结果
        final_result = self._fuse_results(hailo_result, nvidia_result, request.priority)

        engines_used = []
        if hailo_result:
            engines_used.append(EngineType.HAILO)
        if nvidia_result:
            engines_used.append(EngineType.NVIDIA)

        final_result['engines_used'] = engines_used
        final_result['dual_engine_fusion'] = True

        return final_result

    def _merge_detections(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """合并多个引擎的检测结果"""
        all_detections = []

        for engine, result in results.items():
            detections = result.get('results', {}).get('predictions', [])
            for detection in detections:
                detection['source_engine'] = engine
                all_detections.append(detection)

        # 简单的非极大值抑制来去重
        merged_detections = self._non_max_suppression(all_detections)

        return merged_detections[:100]  # 限制最大结果数

    def _fuse_results(self, hailo_result: Optional[Dict], nvidia_result: Optional[Dict],
                     priority: str) -> Dict[str, Any]:
        """融合两个引擎的结果"""
        if not hailo_result:
            return nvidia_result
        if not nvidia_result:
            return hailo_result

        # 根据优先级选择融合策略
        if priority == "accuracy":
            # 精度优先：选择置信度更高的结果
            return self._select_by_confidence(hailo_result, nvidia_result)
        elif priority == "latency":
            # 延迟优先：选择更快的结果
            hailo_time = hailo_result.get('processing_time', float('inf'))
            nvidia_time = nvidia_result.get('processing_time', float('inf'))
            return hailo_result if hailo_time < nvidia_time else nvidia_result
        else:
            # 性能优先：融合两个结果
            return self._merge_engine_results(hailo_result, nvidia_result)

    def _select_by_confidence(self, result1: Dict, result2: Dict) -> Dict:
        """根据置信度选择最佳结果"""
        detections1 = result1.get('results', {}).get('predictions', [])
        detections2 = result2.get('results', {}).get('predictions', [])

        avg_conf1 = sum(d.get('confidence', 0) for d in detections1) / len(detections1) if detections1 else 0
        avg_conf2 = sum(d.get('confidence', 0) for d in detections2) / len(detections2) if detections2 else 0

        return result1 if avg_conf1 > avg_conf2 else result2

    def _merge_engine_results(self, result1: Dict, result2: Dict) -> Dict:
        """合并两个引擎的结果"""
        # 使用处理时间较长的结果作为基础，合并检测框
        if result1.get('processing_time', 0) > result2.get('processing_time', 0):
            base_result = result1.copy()
            other_result = result2
        else:
            base_result = result2.copy()
            other_result = result1

        # 合并检测框
        all_detections = []
        for result in [base_result, other_result]:
            all_detections.extend(result.get('results', {}).get('predictions', []))

        # 应用非极大值抑制
        merged_detections = self._non_max_suppression(all_detections)

        base_result['results']['predictions'] = merged_detections
        base_result['engines_merged'] = True

        return base_result

    def _non_max_suppression(self, detections: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
        """非极大值抑制"""
        if not detections:
            return []

        # 按置信度排序
        detections.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        keep = []
        while detections:
            # 选择置信度最高的检测框
            best = detections.pop(0)
            keep.append(best)

            # 移除与最佳检测框重叠度高的其他检测框
            remaining = []
            for det in detections:
                if self._calculate_iou(best, det) < iou_threshold:
                    remaining.append(det)

            detections = remaining

        return keep

    def _calculate_iou(self, box1: Dict, box2: Dict) -> float:
        """计算两个检测框的IoU"""
        try:
            b1 = box1.get('bbox', [])
            b2 = box2.get('bbox', [])

            if len(b1) < 4 or len(b2) < 4:
                return 0.0

            # 计算交集
            x1 = max(b1[0], b2[0])
            y1 = max(b1[1], b2[1])
            x2 = min(b1[2], b2[2])
            y2 = min(b1[3], b2[3])

            if x2 <= x1 or y2 <= y1:
                return 0.0

            intersection = (x2 - x1) * (y2 - y1)

            # 计算并集
            area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
            area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
            union = area1 + area2 - intersection

            return intersection / union if union > 0 else 0.0

        except Exception:
            return 0.0

    def _update_performance_history(self, engine: str, processing_time: float):
        """更新性能历史记录"""
        history = self.performance_history[engine]
        history.append(processing_time)

        # 只保留最近100次记录
        if len(history) > 100:
            history.pop(0)

        # 更新负载均衡器权重
        if len(history) >= 5:
            avg_time = sum(history[-5:]) / 5
            self.load_balancer.update_weights(
                avg_time if engine == 'hailo' else self.load_balancer.nvidia_weight,
                avg_time if engine == 'nvidia' else self.load_balancer.hailo_weight
            )

    async def _infer_with_hailo_internal(self, request: AccelerationRequest) -> Dict[str, Any]:
        """Hailo8内部推理方法"""
        if not self.hailo_service or not self.hailo_service.is_ready():
            raise Exception("Hailo8服务不可用")

        from .models import InferenceRequest

        inference_request = InferenceRequest(
            model_name=request.model_name,
            input_data=request.image.encode() if isinstance(request.image, str) else str(request.image).encode(),
            confidence_threshold=request.threshold
        )

        result = await self.hailo_service.run_inference(inference_request)
        result['engine_type'] = 'hailo'
        return result

    async def _infer_with_nvidia_internal(self, request: AccelerationRequest) -> Dict[str, Any]:
        """NVIDIA内部推理方法"""
        import torch

        if not torch.cuda.is_available():
            raise Exception("CUDA不可用")

        device = self.nvidia_detector.get_best_device()
        if not device:
            raise Exception("没有可用的NVIDIA设备")

        device_id = device['id']
        image_data = self._prepare_image_data(request.image)

        with torch.cuda.device(device_id):
            # 模拟推理过程
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

            memory_allocated = torch.cuda.memory_allocated(device_id) // 1024 // 1024

            result = {
                'success': True,
                'results': {'predictions': detections},
                'processing_time': 0.08,  # 模拟处理时间
                'engine_type': 'nvidia',
                'gpu_memory_used': memory_allocated,
                'device_info': device
            }

        return result

    def _prepare_image_data(self, image: Union[List[List[List[int]]], str]) -> np.ndarray:
        """准备图像数据"""
        try:
            if isinstance(image, str):
                import cv2
                img_array = cv2.imread(image)
                if img_array is None:
                    raise ValueError(f"无法读取图像文件: {image}")
                return cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            else:
                return np.array(image, dtype=np.uint8)
        except Exception as e:
            logger.error(f"图像数据处理失败: {e}")
            raise ValueError(f"图像数据处理失败: {e}")

    async def infer(self, request: AccelerationRequest) -> AccelerationResponse:
        """执行AI加速推理 - 主入口"""
        start_time = time.time()

        try:
            # 根据引擎类型选择推理策略
            if request.engine == EngineType.PARALLEL:
                if len(self.get_available_engines()) < 2:
                    raise HTTPException(status_code=400, detail="并行推理需要两个引擎都可用")
                result = await self.infer_parallel(request)

            elif request.engine == EngineType.BOTH:
                if len(self.get_available_engines()) < 2:
                    raise HTTPException(status_code=400, detail="双引擎推理需要两个引擎都可用")
                result = await self.infer_both(request)

            elif request.engine == EngineType.LOAD_BALANCE:
                if len(self.get_available_engines()) < 2:
                    raise HTTPException(status_code=400, detail="负载均衡需要两个引擎都可用")
                result = await self.infer_load_balance(request)

            elif request.engine == EngineType.HAILO:
                if not self.hailo_detector.is_available():
                    raise HTTPException(status_code=503, detail="Hailo8不可用")
                result = await self._infer_with_hailo_internal(request)
                result['engines_used'] = [EngineType.HAILO]

            elif request.engine == EngineType.NVIDIA:
                if not self.nvidia_detector.is_available():
                    raise HTTPException(status_code=503, detail="NVIDIA不可用")
                result = await self._infer_with_nvidia_internal(request)
                result['engines_used'] = [EngineType.NVIDIA]

            else:  # AUTO
                # 自动选择最佳策略
                available_engines = self.get_available_engines()

                if EngineType.LOAD_BALANCE in available_engines:
                    # 如果两个引擎都可用，使用负载均衡
                    result = await self.infer_load_balance(request)
                elif EngineType.HAILO in available_engines:
                    result = await self._infer_with_hailo_internal(request)
                    result['engines_used'] = [EngineType.HAILO]
                elif EngineType.NVIDIA in available_engines:
                    result = await self._infer_with_nvidia_internal(request)
                    result['engines_used'] = [EngineType.NVIDIA]
                else:
                    raise HTTPException(status_code=503, detail="没有可用的推理引擎")

            # 构建最终响应
            inference_time = time.time() - start_time

            return AccelerationResponse(
                success=result.get('success', False),
                engines_used=result.get('engines_used', []),
                detections=result.get('results', {}).get('predictions', result.get('detections', [])),
                inference_time=inference_time,
                model_info={
                    'model_name': request.model_name,
                    'engines_count': len(result.get('engines_used', [])),
                    'fusion_enabled': result.get('dual_engine_fusion', False) or result.get('parallel_execution', False)
                },
                hardware_info={
                    'engines_used': result.get('engines_used', []),
                    'load_balance': result.get('load_balance_selection', False),
                    'parallel': result.get('parallel_execution', False),
                    'gpu_memory': result.get('gpu_memory_used')
                },
                engine_results=result.get('engine_results', {}),
                performance_metrics={
                    'total_inference_time': inference_time,
                    'engine_processing_time': result.get('processing_time', 0),
                    'hailo_avg_time': sum(self.performance_history['hailo'][-5:]) / min(5, len(self.performance_history['hailo'])) if self.performance_history['hailo'] else 0,
                    'nvidia_avg_time': sum(self.performance_history['nvidia'][-5:]) / min(5, len(self.performance_history['nvidia'])) if self.performance_history['nvidia'] else 0
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AI加速推理失败: {e}")
            raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


# 保持原有的检测器类（简化版）
class NVIDIADetector:
    def __init__(self):
        self.devices = []
        self._detect_devices()

    def _detect_devices(self):
        try:
            import torch
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                for i in range(device_count):
                    device_info = {
                        'id': i,
                        'name': torch.cuda.get_device_name(i),
                        'memory_total': torch.cuda.get_device_properties(i).total_memory // 1024 // 1024,
                        'memory_allocated': torch.cuda.memory_allocated(i) // 1024 // 1024,
                        'capabilities': torch.cuda.get_device_capability(i),
                        'is_available': True
                    }
                    self.devices.append(device_info)
        except Exception as e:
            logger.warning(f"NVIDIA GPU检测失败: {e}")

    def is_available(self) -> bool:
        return len(self.devices) > 0

    def get_best_device(self) -> Optional[Dict[str, Any]]:
        if not self.devices:
            return None
        return max(self.devices, key=lambda x: x['memory_total'])

    def get_devices(self) -> List[Dict[str, Any]]:
        return self.devices


class Hailo8Detector:
    def __init__(self):
        self.devices = []
        self._detect_devices()

    def _detect_devices(self):
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
        return len(self.devices) > 0

    def get_best_device(self) -> Optional[Dict[str, Any]]:
        if not self.devices:
            return None
        return self.devices[0]

    def get_devices(self) -> List[Dict[str, Any]]:
        return self.devices


# 全局服务实例
enhanced_acceleration_service = EnhancedAccelerationService()


# 更新的API路由
@ai_acceleration_router.post("/infer", response_model=AccelerationResponse)
async def enhanced_accelerate_inference(request: AccelerationRequest):
    """
    增强版AI加速推理接口

    支持多种引擎策略：
    - auto: 自动选择最佳引擎
    - hailo: 仅使用Hailo8
    - nvidia: 仅使用NVIDIA
    - both: 双引擎融合
    - parallel: 并行推理
    - load_balance: 负载均衡
    """
    try:
        logger.info(f"收到增强版AI推理请求: 引擎={request.engine}, 优先级={request.priority}")

        result = await enhanced_acceleration_service.infer(request)

        logger.info(f"推理完成: 引擎={result.engines_used}, 检测到{len(result.detections)}个对象, 耗时{result.inference_time:.3f}s")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"增强版AI推理失败: {e}")
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@ai_acceleration_router.get("/engines")
async def get_enhanced_engines_info():
    """获取增强版推理引擎信息"""
    try:
        available_engines = enhanced_acceleration_service.get_available_engines()

        engine_info = []
        for engine in available_engines:
            info = {
                'name': engine.value,
                'description': _get_engine_description(engine),
                'available': True
            }
            engine_info.append(info)

        return {
            'available_engines': engine_info,
            'total_count': len(available_engines),
            'load_balancer_active': enhanced_acceleration_service.load_balancer is not None,
            'performance_history': {
                'hailo_samples': len(enhanced_acceleration_service.performance_history['hailo']),
                'nvidia_samples': len(enhanced_acceleration_service.performance_history['nvidia'])
            }
        }
    except Exception as e:
        logger.error(f"获取引擎信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取引擎信息失败: {str(e)}")


def _get_engine_description(engine: EngineType) -> str:
    """获取引擎描述"""
    descriptions = {
        EngineType.AUTO: "自动选择最佳引擎",
        EngineType.HAILO: "Hailo8 PCIe AI加速卡",
        EngineType.NVIDIA: "NVIDIA GPU",
        EngineType.BOTH: "双引擎融合推理",
        EngineType.PARALLEL: "并行双引擎推理",
        EngineType.LOAD_BALANCE: "负载均衡推理"
    }
    return descriptions.get(engine, "未知引擎")


# 其他API路由保持不变...
@ai_acceleration_router.get("/hardware")
async def get_hardware_info():
    """获取硬件信息"""
    try:
        available_engines = []
        hailo_devices = []
        nvidia_devices = []

        if enhanced_acceleration_service.hailo_detector.is_available():
            available_engines.append("hailo")
            hailo_devices = enhanced_acceleration_service.hailo_detector.get_devices()

        if enhanced_acceleration_service.nvidia_detector.is_available():
            available_engines.append("nvidia")
            nvidia_devices = enhanced_acceleration_service.nvidia_detector.get_devices()

        total_memory = None
        used_memory = None

        if nvidia_devices:
            total_memory = sum(device['memory_total'] for device in nvidia_devices)
            used_memory = sum(device['memory_allocated'] for device in nvidia_devices)

        return {
            'available_engines': available_engines,
            'hailo_devices': hailo_devices,
            'nvidia_devices': nvidia_devices,
            'total_memory': total_memory,
            'used_memory': used_memory,
            'dual_engine_support': len(available_engines) == 2
        }
    except Exception as e:
        logger.error(f"获取硬件信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取硬件信息失败: {str(e)}")


@ai_acceleration_router.get("/health")
async def enhanced_health_check():
    """增强版健康检查"""
    try:
        hailo_available = enhanced_acceleration_service.hailo_detector.is_available()
        nvidia_available = enhanced_acceleration_service.nvidia_detector.is_available()

        status = {
            'status': 'healthy' if (hailo_available or nvidia_available) else 'unhealthy',
            'service': '增强版AI加速服务',
            'engines': {
                'hailo': 'available' if hailo_available else 'unavailable',
                'nvidia': 'available' if nvidia_available else 'unavailable'
            },
            'features': {
                'parallel_inference': hailo_available and nvidia_available,
                'load_balancing': hailo_available and nvidia_available,
                'dual_engine_fusion': hailo_available and nvidia_available
            },
            'performance_stats': {
                'hailo_avg_time': sum(enhanced_acceleration_service.performance_history['hailo'][-10:]) / min(10, len(enhanced_acceleration_service.performance_history['hailo'])) if enhanced_acceleration_service.performance_history['hailo'] else 0,
                'nvidia_avg_time': sum(enhanced_acceleration_service.performance_history['nvidia'][-10:]) / min(10, len(enhanced_acceleration_service.performance_history['nvidia'])) if enhanced_acceleration_service.performance_history['nvidia'] else 0
            }
        }

        return status

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            'status': 'error',
            'service': '增强版AI加速服务',
            'message': str(e)
        }


# 初始化函数
async def init_enhanced_acceleration_service():
    """初始化增强版AI加速服务"""
    await enhanced_acceleration_service.initialize()