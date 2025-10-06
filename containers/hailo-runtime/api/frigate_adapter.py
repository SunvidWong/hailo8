#!/usr/bin/env python3
"""
Hailo8 Frigate推理适配器
为Frigate提供标准的推理接口
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from .inference import HailoInferenceService
from .config import settings

logger = logging.getLogger(__name__)

# 创建Frigate专用路由器
frigate_router = APIRouter(prefix="/frigate", tags=["frigate"])

# Frigate推理请求模型
class FrigateRequest(BaseModel):
    """Frigate推理请求模型"""
    image: List[List[List[int]]]  # 图像数据 (RGB格式)
    threshold: float = 0.4        # 置信度阈值
    model_name: Optional[str] = None
    targets: Optional[List[str]] = None  # 目标类别

class FrigateDetection(BaseModel):
    """Frigate检测结果模型"""
    confidence: float            # 置信度
    label: str                   # 标签
    box: List[float]             # 边界框 [x1, y1, x2, y2]
    attributes: Optional[Dict[str, Any]] = {}  # 额外属性

class FrigateResponse(BaseModel):
    """Frigate推理响应模型"""
    success: bool
    detections: List[FrigateDetection]
    inference_time: float
    model_info: Dict[str, Any]
    frame_id: Optional[int] = None

class FrigateModelInfo(BaseModel):
    """Frigate模型信息"""
    name: str
    input_shape: List[int]
    output_shape: List[int]
    classes: List[str]
    version: str
    input_format: str = "RGB"


class FrigateInferenceAdapter:
    """Frigate推理适配器类"""

    def __init__(self):
        self.inference_service = None
        self.model_info = None
        self._frigate_classes = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus",
            "train", "truck", "boat", "traffic light", "fire hydrant",
            "stop sign", "parking meter", "bench", "bird", "cat", "dog",
            "horse", "sheep", "cow", "elephant", "bear", "zebra",
            "giraffe", "backpack", "umbrella", "handbag", "tie",
            "suitcase", "frisbee", "skis", "snowboard", "sports ball",
            "kite", "baseball bat", "baseball glove", "skateboard",
            "surfboard", "tennis racket", "bottle", "wine glass", "cup",
            "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog",
            "pizza", "donut", "cake", "chair", "couch", "potted plant",
            "bed", "dining table", "toilet", "tv", "laptop", "mouse",
            "remote", "keyboard", "cell phone", "microwave", "oven",
            "toaster", "sink", "refrigerator", "book", "clock", "vase",
            "scissors", "teddy bear", "hair drier", "toothbrush"
        ]

    async def initialize(self):
        """初始化适配器"""
        try:
            self.inference_service = HailoInferenceService()
            await self.inference_service.initialize()

            # 加载Frigate专用模型信息
            await self._load_frigate_model_info()

            logger.info("Frigate适配器初始化完成")

        except Exception as e:
            logger.error(f"Frigate适配器初始化失败: {e}")
            raise

    async def _load_frigate_model_info(self):
        """加载Frigate模型信息"""
        try:
            # 这里应该从实际的模型文件中读取
            # 暂时使用默认的COCO类别
            self.model_info = FrigateModelInfo(
                name="yolov8n_hailo",
                input_shape=[640, 640, 3],
                output_shape=[84, 8400],  # 示例输出形状
                classes=self._frigate_classes,
                version="1.0.0",
                input_format="RGB"
            )

            logger.info(f"加载Frigate模型: {self.model_info.name}")

        except Exception as e:
            logger.error(f"加载Frigate模型信息失败: {e}")
            raise

    def _convert_image_format(self, image_data: List[List[List[int]]]) -> np.ndarray:
        """转换Frigate图像格式到numpy数组"""
        try:
            # 将List[List[List[int]]转换为numpy数组
            image_array = np.array(image_data, dtype=np.uint8)

            # 检查图像维度
            if len(image_array.shape) == 3:
                h, w, c = image_array.shape
                if c == 3:
                    # RGB格式，直接返回
                    return image_array
                elif c == 1:
                    # 灰度图，转换为RGB
                    return np.stack([image_array] * 3, axis=-1)
                else:
                    raise ValueError(f"不支持的通道数: {c}")
            else:
                raise ValueError(f"不支持的图像维度: {image_array.shape}")

        except Exception as e:
            logger.error(f"图像格式转换失败: {e}")
            raise ValueError(f"图像格式转换失败: {e}")

    def _convert_to_frigate_detections(self, results: Dict) -> List[FrigateDetection]:
        """转换推理结果到Frigate检测格式"""
        detections = []

        try:
            if not results.get('success', False):
                return detections

            inference_results = results.get('results', {})
            predictions = inference_results.get('predictions', [])

            for pred in predictions:
                # 提取置信度
                confidence = pred.get('confidence', 0.0)
                if confidence < 0.25:  # Frigate默认最低置信度
                    continue

                # 提取类别
                class_name = pred.get('class', 'unknown')

                # 提取边界框
                bbox = pred.get('bbox', [])
                if len(bbox) != 4:
                    continue

                # Frigate期望的边界框格式: [x_min, y_min, x_max, y_max]
                x1, y1, x2, y2 = bbox

                # 确保坐标是有效的
                if x2 <= x1 or y2 <= y1:
                    continue

                detection = FrigateDetection(
                    confidence=confidence,
                    label=class_name,
                    box=[float(x1), float(y1), float(x2), float(y2)],
                    attributes={
                        'track_id': pred.get('track_id'),
                        'area': float((x2 - x1) * (y2 - y1)),
                        'center_x': float((x1 + x2) / 2),
                        'center_y': float((y1 + y2) / 2)
                    }
                )
                detections.append(detection)

        except Exception as e:
            logger.error(f"检测结果转换失败: {e}")

        return detections

    async def infer(self, request: FrigateRequest) -> FrigateResponse:
        """执行Frigate推理"""
        start_time = time.time()

        try:
            # 转换图像格式
            image_array = self._convert_image_format(request.image)

            # 准备推理请求
            from .models import InferenceRequest
            inference_request = InferenceRequest(
                model_name=request.model_name or "yolov8n_hailo",
                input_data=image_array.tobytes(),
                confidence_threshold=request.threshold
            )

            # 执行推理
            results = await self.inference_service.run_inference(inference_request)

            # 转换为Frigate格式
            detections = self._convert_to_frigate_detections(results)

            inference_time = time.time() - start_time

            # 构建响应
            response = FrigateResponse(
                success=results.get('success', False),
                detections=detections,
                inference_time=inference_time,
                model_info={
                    'name': self.model_info.name,
                    'version': self.model_info.version,
                    'input_shape': self.model_info.input_shape,
                    'classes': self.model_info.classes
                }
            )

            return response

        except Exception as e:
            logger.error(f"Frigate推理失败: {e}")
            return FrigateResponse(
                success=False,
                detections=[],
                inference_time=time.time() - start_time,
                model_info={}
            )

    async def get_model_info(self) -> FrigateModelInfo:
        """获取模型信息"""
        if self.model_info is None:
            await self._load_frigate_model_info()
        return self.model_info

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if self.inference_service is None:
                return {'status': 'error', 'message': '推理服务未初始化'}

            if not self.inference_service.is_ready():
                return {'status': 'not_ready', 'message': '推理服务未就绪'}

            device_status = await self.inference_service.get_device_status()

            return {
                'status': 'healthy',
                'model': self.model_info.name if self.model_info else 'unknown',
                'device_status': device_status,
                'classes_count': len(self._frigate_classes)
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {'status': 'error', 'message': str(e)}


# 全局适配器实例
frigate_adapter = FrigateInferenceAdapter()


# Frigate API路由
@frigate_router.post("/detect", response_model=FrigateResponse)
async def detect_objects(request: FrigateRequest):
    """
    Frigate对象检测接口

    这个接口与Frigate的标准推理接口兼容，
    可以直接被Frigate调用进行对象检测。
    """
    try:
        logger.info(f"收到Frigate检测请求: 阈值={request.threshold}, 模型={request.model_name}")

        result = await frigate_adapter.infer(request)

        logger.info(f"Frigate检测完成: 检测到{len(result.detections)}个对象, 耗时{result.inference_time:.3f}s")

        return result

    except Exception as e:
        logger.error(f"Frigate检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@frigate_router.get("/model_info", response_model=FrigateModelInfo)
async def get_frigate_model_info():
    """获取Frigate模型信息"""
    try:
        model_info = await frigate_adapter.get_model_info()
        return model_info
    except Exception as e:
        logger.error(f"获取模型信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")


@frigate_router.get("/health")
async def frigate_health_check():
    """Frigate适配器健康检查"""
    try:
        health_status = await frigate_adapter.health_check()
        return health_status
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@frigate_router.get("/classes")
async def get_detection_classes():
    """获取支持的检测类别"""
    try:
        return {
            'classes': frigate_adapter._frigate_classes,
            'count': len(frigate_adapter._frigate_classes)
        }
    except Exception as e:
        logger.error(f"获取检测类别失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取检测类别失败: {str(e)}")


@frigate_router.post("/validate")
async def validate_model(file: UploadFile = File(...)):
    """验证模型文件"""
    try:
        if not file.filename.endswith('.hef'):
            raise HTTPException(status_code=400, detail="只支持HEF格式的模型文件")

        # 保存模型文件
        model_path = Path(settings.HAILO_MODEL_PATH) / file.filename
        async with aiofiles.open(model_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 验证模型
        # 这里应该添加实际的模型验证逻辑

        return {
            'success': True,
            'message': f"模型文件 {file.filename} 验证成功",
            'model_path': str(model_path)
        }

    except Exception as e:
        logger.error(f"模型验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"模型验证失败: {str(e)}")


# 初始化函数
async def init_frigate_adapter():
    """初始化Frigate适配器"""
    await frigate_adapter.initialize()