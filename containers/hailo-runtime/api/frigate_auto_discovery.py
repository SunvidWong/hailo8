#!/usr/bin/env python3
"""
Frigate自动发现和无缝集成服务
零配置即可让Frigate调用Hailo8和NVIDIA硬件
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

import aiohttp
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Frigate自动发现路由器
frigate_router = APIRouter(prefix="/frigate", tags=["Frigate集成"])

class FrigateConfigGenerator:
    """Frigate配置自动生成器"""

    def __init__(self, ai_service_url: str = "http://localhost:8000"):
        self.ai_service_url = ai_service_url
        self.frigate_config_dir = "/config/frigate"
        self.config_file = "/config/frigate.yml"
        self.detectors_config = {}
        self.model_configs = {}

    async def detect_hardware(self) -> Dict[str, Any]:
        """检测可用硬件"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ai_service_url}/ai/hardware", timeout=5) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.warning(f"无法连接AI服务: {e}")

        return {"available_engines": [], "hailo_devices": [], "nvidia_devices": []}

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ai_service_url}/ai/engines", timeout=5) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            logger.warning(f"获取引擎信息失败: {e}")

        return {"available_engines": []}

    def generate_frigate_config(self, hardware_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成Frigate配置"""
        config = {
            "version": "0.14",
            "detectors": {},
            "model": {
                "width": 640,
                "height": 480
            },
            "objects": {
                "track": ["person", "car", "bicycle", "motorcycle", "bus", "truck"]
            }
        }

        # 根据可用硬件生成检测器配置
        available_engines = hardware_info.get("available_engines", [])

        if "hailo" in available_engines:
            config["detectors"]["hailo8"] = {
                "type": "remote",
                "api": {
                    "url": f"{self.ai_service_url}/frigate/infer/hailo",
                    "timeout": 10,
                    "max_retries": 3
                },
                "model": {
                    "width": 640,
                    "height": 640,
                    "input_tensor": "nhwc",
                    "input_pixel_format": "rgb"
                }
            }
            logger.info("✓ 已配置Hailo8检测器")

        if "nvidia" in available_engines:
            config["detectors"]["nvidia"] = {
                "type": "remote",
                "api": {
                    "url": f"{self.ai_service_url}/frigate/infer/nvidia",
                    "timeout": 15,
                    "max_retries": 3
                },
                "model": {
                    "width": 640,
                    "height": 640,
                    "input_tensor": "nhwc",
                    "input_pixel_format": "rgb"
                }
            }
            logger.info("✓ 已配置NVIDIA检测器")

        # 如果两个都可用，创建一个智能检测器
        if len(available_engines) >= 2:
            config["detectors"]["auto"] = {
                "type": "remote",
                "api": {
                    "url": f"{self.ai_service_url}/frigate/infer/auto",
                    "timeout": 20,
                    "max_retries": 3
                },
                "model": {
                    "width": 640,
                    "height": 640,
                    "input_tensor": "nhwc",
                    "input_pixel_format": "rgb"
                }
            }
            logger.info("✓ 已配置智能双引擎检测器")

        return config

    async def save_frigate_config(self, config: Dict[str, Any]) -> bool:
        """保存Frigate配置"""
        try:
            # 确保配置目录存在
            os.makedirs(self.frigate_config_dir, exist_ok=True)

            # 备份现有配置
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup.{int(time.time())}"
                os.rename(self.config_file, backup_file)
                logger.info(f"已备份现有配置到: {backup_file}")

            # 保存新配置
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)

            logger.info(f"✓ Frigate配置已保存到: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"保存Frigate配置失败: {e}")
            return False

    def generate_docker_compose_override(self) -> Dict[str, Any]:
        """生成Docker Compose覆盖配置"""
        return {
            "version": "3.8",
            "services": {
                "frigate": {
                    "networks": ["ai-acceleration-network"],
                    "depends_on": ["ai-acceleration-service"],
                    "environment": [
                        "DETECTOR_NAME=auto",  # 使用智能检测器
                        "AI_SERVICE_URL=http://ai-acceleration-service:8000",
                        "FRS_AUTO_DETECT=true"
                    ]
                }
            }
        }


class FrigateIntegrationService:
    """Frigate集成服务"""

    def __init__(self):
        self.config_generator = FrigateConfigGenerator()
        self.auto_discovery_enabled = True
        self.config_refresh_interval = 300  # 5分钟

    async def initialize(self):
        """初始化服务"""
        logger.info("🔗 初始化Frigate自动集成服务...")

        # 检测硬件并生成配置
        await self.auto_configure_frigate()

        # 启动定期配置刷新
        if self.auto_discovery_enabled:
            asyncio.create_task(self.periodic_config_refresh())

    async def auto_configure_frigate(self):
        """自动配置Frigate"""
        try:
            # 检测硬件
            hardware_info = await self.config_generator.detect_hardware()

            if not hardware_info.get("available_engines"):
                logger.warning("⚠ 未检测到可用的AI加速硬件")
                return False

            logger.info(f"🔍 检测到硬件: {hardware_info['available_engines']}")

            # 生成配置
            config = self.config_generator.generate_frigate_config(hardware_info)

            # 保存配置
            success = await self.config_generator.save_frigate_config(config)

            if success:
                logger.info("✅ Frigate自动配置完成")
                return True
            else:
                logger.error("❌ Frigate自动配置失败")
                return False

        except Exception as e:
            logger.error(f"Frigate自动配置异常: {e}")
            return False

    async def periodic_config_refresh(self):
        """定期刷新配置"""
        while True:
            try:
                await asyncio.sleep(self.config_refresh_interval)
                logger.info("🔄 定期刷新Frigate配置...")
                await self.auto_configure_frigate()
            except Exception as e:
                logger.error(f"配置刷新失败: {e}")


# 全局服务实例
frigate_integration = FrigateIntegrationService()


# Frigate API端点
@frigate_router.get("/status")
async def frigate_status():
    """获取Frigate集成状态"""
    try:
        hardware_info = await frigate_integration.config_generator.detect_hardware()

        return {
            "status": "active",
            "auto_discovery": frigate_integration.auto_discovery_enabled,
            "hardware_detected": hardware_info,
            "config_file": frigate_integration.config_generator.config_file,
            "endpoints": {
                "hailo_infer": f"{frigate_integration.config_generator.ai_service_url}/frigate/infer/hailo",
                "nvidia_infer": f"{frigate_integration.config_generator.ai_service_url}/frigate/infer/nvidia",
                "auto_infer": f"{frigate_integration.config_generator.ai_service_url}/frigate/infer/auto"
            }
        }
    except Exception as e:
        logger.error(f"获取Frigate状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@frigate_router.post("/configure")
async def configure_frigate():
    """手动配置Frigate"""
    try:
        success = await frigate_integration.auto_configure_frigate()

        if success:
            return {
                "success": True,
                "message": "Frigate配置已更新",
                "config_file": frigate_integration.config_generator.config_file
            }
        else:
            return {
                "success": False,
                "message": "Frigate配置更新失败"
            }
    except Exception as e:
        logger.error(f"配置Frigate失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@frigate_router.get("/config")
async def get_frigate_config():
    """获取生成的Frigate配置"""
    try:
        hardware_info = await frigate_integration.config_generator.detect_hardware()
        config = frigate_integration.config_generator.generate_frigate_config(hardware_info)

        return {
            "config": config,
            "hardware_info": hardware_info,
            "yaml_content": yaml.dump(config, default_flow_style=False, indent=2)
        }
    except Exception as e:
        logger.error(f"获取Frigate配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Frigate推理端点 - 兼容Frigate API格式
class FrigateInferenceRequest(BaseModel):
    """Frigate推理请求格式"""
    input_image: List[List[List[int]]]  # 图像数据
    model_config: Optional[Dict[str, Any]] = None


class FrigateInferenceResponse(BaseModel):
    """Frigate推理响应格式"""
    detections: List[Dict[str, Any]]
    processing_time: float
    detector: str
    success: bool


@frigate_router.post("/infer/{engine}", response_model=FrigateInferenceResponse)
async def frigate_infer(engine: str, request: FrigateInferenceRequest):
    """
    Frigate推理接口
    兼容Frigate的API调用格式
    """
    try:
        from .enhanced_ai_acceleration_adapter import AccelerationRequest, enhanced_acceleration_service
        from .ai_acceleration_adapter import EngineType

        # 转换请求格式
        if engine == "hailo":
            engine_type = EngineType.HAILO
        elif engine == "nvidia":
            engine_type = EngineType.NVIDIA
        elif engine == "auto":
            engine_type = EngineType.AUTO
        else:
            raise HTTPException(status_code=400, detail=f"不支持的引擎类型: {engine}")

        # 构建AI加速请求
        ai_request = AccelerationRequest(
            image=request.input_image,
            engine=engine_type,
            threshold=0.4,
            priority="performance"
        )

        # 执行推理
        result = await enhanced_acceleration_service.infer(ai_request)

        # 转换为Frigate格式
        frigate_detections = []
        for detection in result.detections:
            frigate_detection = {
                "label": detection.get("class", "unknown"),
                "confidence": detection.get("confidence", 0),
                "box": {
                    "x_min": detection.get("bbox", [0, 0, 0, 0])[0],
                    "y_min": detection.get("bbox", [0, 0, 0, 0])[1],
                    "x_max": detection.get("bbox", [0, 0, 0, 0])[2],
                    "y_max": detection.get("bbox", [0, 0, 0, 0])[3]
                }
            }
            frigate_detections.append(frigate_detection)

        return FrigateInferenceResponse(
            detections=frigate_detections,
            processing_time=result.inference_time,
            detector=engine,
            success=result.success
        )

    except Exception as e:
        logger.error(f"Frigate推理失败: {e}")
        return FrigateInferenceResponse(
            detections=[],
            processing_time=0,
            detector=engine,
            success=False
        )


# Docker Compose自动生成
@frigate_router.get("/docker-compose")
async def generate_docker_compose():
    """生成Docker Compose配置"""
    try:
        # 生成Frigate Docker Compose配置
        frigate_config = {
            "version": "3.8",
            "services": {
                "frigate": {
                    "image": "ghcr.io/blakeblackshear/frigate:stable",
                    "container_name": "frigate",
                    "restart": "unless-stopped",
                    "volumes": [
                        "/etc/localtime:/etc/localtime:ro",
                        "./config/frigate.yml:/config/config.yml:ro",
                        "/media/frigate:/media/frigate"
                    ],
                    "ports": [
                        "5000:5000",  # Web界面
                        "1935:1935",   # RTMP流
                        "8554:8554",   # RTSP流
                        "8555:8555"    # WebRTC
                    ],
                    "environment": [
                        "DETECTOR_NAME=auto",
                        "AI_SERVICE_URL=http://ai-acceleration-service:8000"
                    ],
                    "networks": ["ai-acceleration-network"],
                    "depends_on": ["ai-acceleration-service"]
                }
            },
            "networks": {
                "ai-acceleration-network": {
                    "external": True
                }
            }
        }

        return {
            "docker_compose": frigate_config,
            "yaml_content": yaml.dump(frigate_config, default_flow_style=False, indent=2),
            "setup_commands": [
                "# 创建网络",
                "docker network create ai-acceleration-network",
                "",
                "# 启动AI加速服务",
                "docker-compose -f docker-compose.ai-acceleration.yml up -d",
                "",
                "# 启动Frigate",
                "docker-compose -f frigate-docker-compose.yml up -d",
                "",
                "# 访问Frigate Web界面",
                "http://localhost:5000"
            ]
        }

    except Exception as e:
        logger.error(f"生成Docker Compose配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 初始化函数
async def init_frigate_integration():
    """初始化Frigate集成服务"""
    await frigate_integration.initialize()
    logger.info("✅ Frigate自动集成服务初始化完成")