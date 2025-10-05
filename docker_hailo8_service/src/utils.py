"""
工具函数模块
包含数据处理、验证、转换等通用功能
"""

import os
import base64
import json
import hashlib
import mimetypes
import time
import io
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import logging
import asyncio
import aiofiles
from pathlib import Path

import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


# ==================== 数据格式转换 ====================

def encode_base64(data: bytes) -> str:
    """将字节数据编码为base64字符串"""
    return base64.b64encode(data).decode('utf-8')


def decode_base64(data: str) -> bytes:
    """将base64字符串解码为字节数据"""
    return base64.b64decode(data)


def image_to_base64(image_path: str) -> str:
    """将图片文件转换为base64字符串"""
    with open(image_path, 'rb') as f:
        return encode_base64(f.read())


def base64_to_image(base64_data: str, output_path: str):
    """将base64字符串保存为图片文件"""
    image_data = decode_base64(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)


def numpy_to_base64(array: np.ndarray) -> str:
    """将numpy数组转换为base64字符串"""
    # 将数组转换为字节
    array_bytes = array.tobytes()
    # 创建包含形状和数据类型信息的字典
    data_dict = {
        'data': encode_base64(array_bytes),
        'shape': array.shape,
        'dtype': str(array.dtype)
    }
    # 转换为JSON字符串再编码
    json_str = json.dumps(data_dict)
    return encode_base64(json_str.encode('utf-8'))


def base64_to_numpy(base64_data: str) -> np.ndarray:
    """将base64字符串转换为numpy数组"""
    # 解码JSON字符串
    json_str = decode_base64(base64_data).decode('utf-8')
    data_dict = json.loads(json_str)
    
    # 重建数组
    array_bytes = decode_base64(data_dict['data'])
    array = np.frombuffer(array_bytes, dtype=data_dict['dtype'])
    return array.reshape(data_dict['shape'])


# ==================== 图像处理 ====================

def preprocess_image(image_data: Union[str, bytes, np.ndarray], 
                    target_size: Tuple[int, int] = (224, 224),
                    normalize: bool = True) -> np.ndarray:
    """预处理图像数据"""
    try:
        # 处理不同输入格式
        if isinstance(image_data, str):
            # base64字符串
            if image_data.startswith('data:image'):
                # 移除data URL前缀
                image_data = image_data.split(',')[1]
            image_bytes = decode_base64(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        elif isinstance(image_data, bytes):
            # 字节数据
            image = Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, np.ndarray):
            # numpy数组
            if image_data.dtype != np.uint8:
                image_data = (image_data * 255).astype(np.uint8)
            image = Image.fromarray(image_data)
        else:
            raise ValueError(f"不支持的图像数据类型: {type(image_data)}")
        
        # 转换为RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 调整大小
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # 转换为numpy数组
        image_array = np.array(image)
        
        # 归一化
        if normalize:
            image_array = image_array.astype(np.float32) / 255.0
        
        # 添加批次维度并调整通道顺序 (HWC -> CHW)
        if len(image_array.shape) == 3:
            image_array = np.transpose(image_array, (2, 0, 1))  # CHW
            image_array = np.expand_dims(image_array, axis=0)   # NCHW
        
        return image_array
        
    except Exception as e:
        logger.error(f"图像预处理失败: {e}")
        raise ValueError(f"图像预处理失败: {str(e)}")


def postprocess_classification(output: np.ndarray, 
                             class_names: Optional[List[str]] = None,
                             top_k: int = 5) -> List[Dict[str, Any]]:
    """后处理分类结果"""
    try:
        # 确保输出是1D数组
        if len(output.shape) > 1:
            output = output.flatten()
        
        # 应用softmax
        exp_output = np.exp(output - np.max(output))
        probabilities = exp_output / np.sum(exp_output)
        
        # 获取top-k结果
        top_indices = np.argsort(probabilities)[-top_k:][::-1]
        
        results = []
        for i, idx in enumerate(top_indices):
            class_name = class_names[idx] if class_names and idx < len(class_names) else f"class_{idx}"
            results.append({
                "class": class_name,
                "confidence": float(probabilities[idx]),
                "index": int(idx)
            })
        
        return results
        
    except Exception as e:
        logger.error(f"分类结果后处理失败: {e}")
        raise ValueError(f"分类结果后处理失败: {str(e)}")


def postprocess_detection(output: np.ndarray,
                         confidence_threshold: float = 0.5,
                         nms_threshold: float = 0.4,
                         class_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """后处理目标检测结果"""
    try:
        # 这里应该根据具体的检测模型输出格式进行调整
        # 示例：假设输出格式为 [N, 6] (x1, y1, x2, y2, confidence, class_id)
        
        detections = []
        
        if len(output.shape) == 2 and output.shape[1] >= 6:
            for detection in output:
                confidence = detection[4]
                if confidence >= confidence_threshold:
                    class_id = int(detection[5])
                    class_name = class_names[class_id] if class_names and class_id < len(class_names) else f"class_{class_id}"
                    
                    detections.append({
                        "bbox": {
                            "x1": float(detection[0]),
                            "y1": float(detection[1]),
                            "x2": float(detection[2]),
                            "y2": float(detection[3])
                        },
                        "confidence": float(confidence),
                        "class": class_name,
                        "class_id": class_id
                    })
        
        return detections
        
    except Exception as e:
        logger.error(f"检测结果后处理失败: {e}")
        raise ValueError(f"检测结果后处理失败: {str(e)}")


# ==================== 文件操作 ====================

async def save_file_async(file_path: str, data: bytes):
    """异步保存文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(data)
            
    except Exception as e:
        logger.error(f"保存文件失败 {file_path}: {e}")
        raise


async def load_file_async(file_path: str) -> bytes:
    """异步加载文件"""
    try:
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
            
    except Exception as e:
        logger.error(f"加载文件失败 {file_path}: {e}")
        raise


def get_file_hash(file_path: str) -> str:
    """计算文件MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_info(file_path: str) -> Dict[str, Any]:
    """获取文件信息"""
    try:
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "mime_type": mimetypes.guess_type(file_path)[0],
            "hash": get_file_hash(file_path)
        }
    except Exception as e:
        logger.error(f"获取文件信息失败 {file_path}: {e}")
        return {}


# ==================== 数据验证 ====================

def validate_image_format(data: Union[str, bytes]) -> bool:
    """验证图像格式"""
    try:
        if isinstance(data, str):
            # base64数据
            if data.startswith('data:image'):
                data = data.split(',')[1]
            image_bytes = decode_base64(data)
        else:
            image_bytes = data
        
        # 尝试打开图像
        Image.open(io.BytesIO(image_bytes))
        return True
        
    except Exception:
        return False


def validate_model_file(file_path: str) -> Dict[str, Any]:
    """验证模型文件"""
    result = {
        "valid": False,
        "format": None,
        "size": 0,
        "error": None
    }
    
    try:
        if not os.path.exists(file_path):
            result["error"] = "文件不存在"
            return result
        
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        result["size"] = file_size
        
        if file_size == 0:
            result["error"] = "文件为空"
            return result
        
        # 检查文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        supported_formats = ['.hef', '.onnx', '.pb', '.tflite']
        
        if ext in supported_formats:
            result["format"] = ext[1:]  # 移除点号
            result["valid"] = True
        else:
            result["error"] = f"不支持的模型格式: {ext}"
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        return result


# ==================== 性能监控 ====================

class PerformanceTimer:
    """性能计时器"""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = (self.end_time - self.start_time) * 1000  # 转换为毫秒
        logger.info(f"{self.name} 耗时: {duration:.2f}ms")
    
    @property
    def duration_ms(self) -> float:
        """获取持续时间（毫秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


def measure_memory_usage():
    """测量内存使用情况"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            "rss": memory_info.rss,  # 物理内存
            "vms": memory_info.vms,  # 虚拟内存
            "percent": process.memory_percent()
        }
    except ImportError:
        logger.warning("psutil未安装，无法获取内存使用情况")
        return {"rss": 0, "vms": 0, "percent": 0.0}


def measure_cpu_usage():
    """测量CPU使用率"""
    try:
        import psutil
        return psutil.cpu_percent(interval=1)
    except ImportError:
        logger.warning("psutil未安装，无法获取CPU使用率")
        return 0.0


# ==================== 配置管理 ====================

def load_json_config(config_path: str) -> Dict[str, Any]:
    """加载JSON配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败 {config_path}: {e}")
        return {}


def save_json_config(config: Dict[str, Any], config_path: str):
    """保存JSON配置文件"""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存配置文件失败 {config_path}: {e}")
        raise


# ==================== 日志工具 ====================

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """设置日志配置"""
    import logging.config
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False
            }
        }
    }
    
    # 添加文件日志处理器
    if log_file:
        config["handlers"]["file"] = {
            "level": log_level,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        config["loggers"][""]["handlers"].append("file")
    
    logging.config.dictConfig(config)


# ==================== 异步工具 ====================

async def run_in_thread(func, *args, **kwargs):
    """在线程池中运行同步函数"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)


class AsyncLock:
    """异步锁包装器"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self._lock.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()


# ==================== 错误处理 ====================

class Hailo8Error(Exception):
    """Hailo8相关错误基类"""
    pass


class DeviceError(Hailo8Error):
    """设备错误"""
    pass


class ModelError(Hailo8Error):
    """模型错误"""
    pass


class InferenceError(Hailo8Error):
    """推理错误"""
    pass


def handle_exception(func):
    """异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}")
            raise
    return wrapper


async def handle_async_exception(func):
    """异步异常处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"异步函数 {func.__name__} 执行失败: {e}")
            raise
    return wrapper