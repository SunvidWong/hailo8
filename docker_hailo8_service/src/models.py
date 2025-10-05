"""
Hailo8服务API数据模型定义
使用Pydantic进行数据验证和序列化
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


# ==================== 枚举类型 ====================

class DeviceStatus(str, Enum):
    """设备状态枚举"""
    AVAILABLE = "available"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InputFormat(str, Enum):
    """输入数据格式枚举"""
    BASE64 = "base64"
    NUMPY = "numpy"
    IMAGE_URL = "image_url"
    RAW_BYTES = "raw_bytes"


class OutputFormat(str, Enum):
    """输出数据格式枚举"""
    JSON = "json"
    NUMPY = "numpy"
    BASE64 = "base64"


# ==================== 基础响应模型 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field("", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


# ==================== 健康检查和状态模型 ====================

class HealthResponse(BaseResponse):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class DeviceInfo(BaseModel):
    """设备信息模型"""
    device_id: str = Field(..., description="设备ID")
    device_name: str = Field(..., description="设备名称")
    status: DeviceStatus = Field(..., description="设备状态")
    temperature: Optional[float] = Field(None, description="设备温度(°C)")
    utilization: Optional[float] = Field(None, description="设备利用率(%)")
    memory_used: Optional[int] = Field(None, description="已使用内存(MB)")
    memory_total: Optional[int] = Field(None, description="总内存(MB)")
    firmware_version: Optional[str] = Field(None, description="固件版本")
    driver_version: Optional[str] = Field(None, description="驱动版本")
    last_update: datetime = Field(default_factory=datetime.now, description="最后更新时间")


class ServiceStatus(BaseModel):
    """服务状态模型"""
    service_name: str = Field("hailo8-service", description="服务名称")
    version: str = Field("1.0.0", description="服务版本")
    uptime: float = Field(..., description="运行时间(秒)")
    total_requests: int = Field(0, description="总请求数")
    active_tasks: int = Field(0, description="活跃任务数")
    loaded_models: int = Field(0, description="已加载模型数")
    available_devices: int = Field(0, description="可用设备数")
    system_info: Dict[str, Any] = Field(default_factory=dict, description="系统信息")


# ==================== 模型管理模型 ====================

class ModelLoadRequest(BaseModel):
    """模型加载请求"""
    model_path: str = Field(..., description="模型文件路径")
    model_id: str = Field(..., description="模型唯一标识")
    device_id: Optional[str] = Field(None, description="指定设备ID，为空则自动选择")
    
    @validator('model_path')
    def validate_model_path(cls, v):
        if not v or not v.strip():
            raise ValueError('模型路径不能为空')
        return v.strip()
    
    @validator('model_id')
    def validate_model_id(cls, v):
        if not v or not v.strip():
            raise ValueError('模型ID不能为空')
        return v.strip()


class ModelLoadResponse(BaseResponse):
    """模型加载响应"""
    model_id: str = Field(..., description="模型ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="加载详情")


class ModelInfo(BaseModel):
    """模型信息"""
    model_id: str = Field(..., description="模型ID")
    model_path: str = Field(..., description="模型路径")
    device_id: str = Field(..., description="所在设备ID")
    load_time: datetime = Field(..., description="加载时间")
    input_shape: Optional[List[int]] = Field(None, description="输入形状")
    output_shape: Optional[List[int]] = Field(None, description="输出形状")
    model_size: Optional[int] = Field(None, description="模型大小(bytes)")
    inference_count: int = Field(0, description="推理次数")
    avg_inference_time: Optional[float] = Field(None, description="平均推理时间(ms)")


# ==================== 推理服务模型 ====================

class InferenceRequest(BaseModel):
    """推理请求"""
    model_id: str = Field(..., description="模型ID")
    input_data: Union[str, List, Dict] = Field(..., description="输入数据")
    input_format: InputFormat = Field(InputFormat.BASE64, description="输入格式")
    output_format: OutputFormat = Field(OutputFormat.JSON, description="输出格式")
    
    @validator('model_id')
    def validate_model_id(cls, v):
        if not v or not v.strip():
            raise ValueError('模型ID不能为空')
        return v.strip()


class InferenceResponse(BaseResponse):
    """推理响应"""
    task_id: Optional[str] = Field(None, description="任务ID（异步推理时使用）")
    output_data: Optional[Union[Dict, List, str]] = Field(None, description="输出数据")
    inference_time: Optional[float] = Field(None, description="推理时间(ms)")
    details: Dict[str, Any] = Field(default_factory=dict, description="推理详情")


class BatchInferenceRequest(BaseModel):
    """批量推理请求"""
    model_id: str = Field(..., description="模型ID")
    input_batch: List[Union[str, List, Dict]] = Field(..., description="批量输入数据")
    input_format: InputFormat = Field(InputFormat.BASE64, description="输入格式")
    output_format: OutputFormat = Field(OutputFormat.JSON, description="输出格式")
    batch_size: Optional[int] = Field(None, description="批处理大小，为空则使用全部")
    
    @validator('input_batch')
    def validate_input_batch(cls, v):
        if not v or len(v) == 0:
            raise ValueError('批量输入数据不能为空')
        return v


class BatchInferenceResponse(BaseResponse):
    """批量推理响应"""
    task_id: Optional[str] = Field(None, description="任务ID")
    batch_results: List[Dict[str, Any]] = Field(default_factory=list, description="批量结果")
    total_time: Optional[float] = Field(None, description="总处理时间(ms)")
    details: Dict[str, Any] = Field(default_factory=dict, description="处理详情")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: Optional[float] = Field(None, description="进度百分比(0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


# ==================== 监控和统计模型 ====================

class ServiceStats(BaseModel):
    """服务统计信息"""
    total_requests: int = Field(0, description="总请求数")
    successful_requests: int = Field(0, description="成功请求数")
    failed_requests: int = Field(0, description="失败请求数")
    avg_response_time: float = Field(0.0, description="平均响应时间(ms)")
    total_inference_time: float = Field(0.0, description="总推理时间(ms)")
    total_inferences: int = Field(0, description="总推理次数")
    active_models: int = Field(0, description="活跃模型数")
    device_stats: List[Dict[str, Any]] = Field(default_factory=list, description="设备统计")
    memory_usage: Dict[str, float] = Field(default_factory=dict, description="内存使用情况")
    cpu_usage: float = Field(0.0, description="CPU使用率")
    uptime: float = Field(0.0, description="运行时间(秒)")


# ==================== 配置模型 ====================

class ServiceConfig(BaseModel):
    """服务配置模型"""
    max_concurrent_inferences: int = Field(10, description="最大并发推理数")
    model_cache_size: int = Field(5, description="模型缓存大小")
    inference_timeout: float = Field(30.0, description="推理超时时间(秒)")
    enable_metrics: bool = Field(True, description="启用监控指标")
    log_level: str = Field("INFO", description="日志级别")
    debug_mode: bool = Field(False, description="调试模式")


# ==================== 错误模型 ====================

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    status_code: int = Field(..., description="HTTP状态码")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


# ==================== 工具函数 ====================

def create_error_response(
    error_message: str,
    status_code: int = 500,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        error=error_message,
        error_code=error_code,
        status_code=status_code,
        details=details or {}
    )


def create_success_response(
    message: str = "操作成功",
    data: Optional[Dict[str, Any]] = None
) -> BaseResponse:
    """创建成功响应"""
    response = BaseResponse(success=True, message=message)
    if data:
        for key, value in data.items():
            setattr(response, key, value)
    return response