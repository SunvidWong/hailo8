#!/usr/bin/env python3
"""
Hailo8 AI Service
示例AI服务，展示如何使用Hailo8 Runtime API进行图像处理和分析
"""

import asyncio
import io
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from PIL import Image

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask应用配置
app = Flask(__name__)
CORS(app)

# 配置
HAILO_API_URL = os.getenv('HAILO_API_URL', 'http://hailo-runtime:8000')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8080))
UPLOAD_FOLDER = Path('/app/uploads')
OUTPUT_FOLDER = Path('/app/outputs')

# 创建必要的目录
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)


class HailoAIClient:
    """Hailo Runtime API客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def health_check(self) -> bool:
        """检查Hailo服务健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    def ready_check(self) -> Dict:
        """检查服务就绪状态"""
        try:
            response = self.session.get(f"{self.base_url}/ready", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "not_ready"}
        except Exception as e:
            logger.error(f"就绪检查失败: {e}")
            return {"status": "error", "error": str(e)}

    def run_inference(self, image_data: bytes, model_name: str = None,
                     confidence_threshold: float = 0.5) -> Dict:
        """执行图像推理"""
        try:
            # 准备请求
            files = {'file': ('image.jpg', image_data, 'image/jpeg')}
            data = {
                'model_name': model_name,
                'confidence_threshold': confidence_threshold
            }

            # 发送推理请求
            response = self.session.post(
                f"{self.base_url}/api/v1/inference/image",
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"推理请求失败: {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    error_msg += f" - {error_detail}"
                except:
                    pass
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"推理失败: {e}")
            return {"success": False, "error": str(e)}

    def get_device_status(self) -> Dict:
        """获取设备状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/device/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"请求失败: {response.status_code}"}
        except Exception as e:
            logger.error(f"获取设备状态失败: {e}")
            return {"error": str(e)}


# 全局客户端实例
hailo_client = HailoAIClient(HAILO_API_URL)


def process_image(image_data: bytes, inference_results: Dict) -> bytes:
    """处理图像，添加推理结果可视化"""
    try:
        # 将字节数据转换为numpy数组
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("无法解码图像")

        # 如果有推理结果，在图像上绘制边界框
        if inference_results.get('success') and 'results' in inference_results:
            results = inference_results['results']
            if 'predictions' in results:
                for prediction in results['predictions']:
                    bbox = prediction.get('bbox', [])
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = map(int, bbox)
                        label = prediction.get('class', 'unknown')
                        confidence = prediction.get('confidence', 0.0)

                        # 绘制边界框
                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # 绘制标签
                        label_text = f"{label}: {confidence:.2f}"
                        cv2.putText(image, label_text, (x1, y1-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 将处理后的图像编码回字节数据
        success, encoded_image = cv2.imencode('.jpg', image)
        if not success:
            raise ValueError("无法编码处理后的图像")

        return encoded_image.tobytes()

    except Exception as e:
        logger.error(f"图像处理失败: {e}")
        return image_data  # 返回原始图像


# API路由
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "Hailo8 AI Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/status', methods=['GET'])
def status_check():
    """服务状态检查"""
    # 检查Hailo Runtime服务
    hailo_ready = hailo_client.health_check()
    hailo_status = hailo_client.ready_check()

    return jsonify({
        "service_status": "running",
        "hailo_runtime_connected": hailo_ready,
        "hailo_runtime_status": hailo_status,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/inference', methods=['POST'])
def inference():
    """图像推理端点"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400

        # 获取参数
        model_name = request.form.get('model_name')
        confidence_threshold = float(request.form.get('confidence_threshold', 0.5))
        process_image_flag = request.form.get('process_image', 'true').lower() == 'true'

        # 读取图像数据
        image_data = file.read()

        # 执行推理
        inference_results = hailo_client.run_inference(
            image_data, model_name, confidence_threshold
        )

        # 处理图像（如果需要）
        processed_image = None
        if process_image_flag and inference_results.get('success'):
            processed_image = process_image(image_data, inference_results)

            # 保存处理后的图像
            timestamp = int(time.time())
            output_path = OUTPUT_FOLDER / f"processed_{timestamp}.jpg"
            with open(output_path, 'wb') as f:
                f.write(processed_image)

            inference_results['processed_image_path'] = str(output_path)

        # 添加服务信息
        inference_results['service_info'] = {
            "service": "Hailo8 AI Service",
            "timestamp": datetime.now().isoformat(),
            "processing_time": inference_results.get('processing_time', 0)
        }

        return jsonify(inference_results)

    except Exception as e:
        logger.error(f"推理请求失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/batch_inference', methods=['POST'])
def batch_inference():
    """批量推理端点"""
    try:
        # 检查是否有文件上传
        if 'files' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400

        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "文件列表为空"}), 400

        # 获取参数
        model_name = request.form.get('model_name')
        confidence_threshold = float(request.form.get('confidence_threshold', 0.5))

        results = []
        total_start_time = time.time()

        for i, file in enumerate(files):
            if file.filename == '':
                continue

            start_time = time.time()
            image_data = file.read()

            # 执行推理
            inference_result = hailo_client.run_inference(
                image_data, model_name, confidence_threshold
            )

            # 添加文件信息
            inference_result['file_info'] = {
                "filename": file.filename,
                "file_index": i,
                "file_size": len(image_data)
            }

            # 添加处理时间
            processing_time = time.time() - start_time
            inference_result['service_processing_time'] = processing_time

            results.append(inference_result)

        # 计算总体统计
        total_time = time.time() - total_start_time
        successful_inferences = sum(1 for r in results if r.get('success', False))

        return jsonify({
            "batch_results": results,
            "batch_stats": {
                "total_files": len(files),
                "successful_inferences": successful_inferences,
                "failed_inferences": len(files) - successful_inferences,
                "total_processing_time": total_time,
                "average_processing_time": total_time / len(files) if files else 0
            },
            "service_info": {
                "service": "Hailo8 AI Service",
                "timestamp": datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"批量推理失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/device_info', methods=['GET'])
def device_info():
    """获取设备信息"""
    device_status = hailo_client.get_device_status()

    return jsonify({
        "device_status": device_status,
        "service_info": {
            "service": "Hailo8 AI Service",
            "hailo_api_url": HAILO_API_URL,
            "timestamp": datetime.now().isoformat()
        }
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    """获取服务统计信息"""
    # 这里可以实现实际的统计信息收集
    stats = {
        "service_uptime": "unknown",  # 需要实际计算
        "total_inferences": 0,       # 需要实际计数
        "successful_inferences": 0,  # 需要实际计数
        "average_processing_time": 0.0,
        "device_status": hailo_client.get_device_status()
    }

    return jsonify(stats)


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "端点未找到"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"内部服务器错误: {error}")
    return jsonify({"error": "内部服务器错误"}), 500


def main():
    """主函数"""
    logger.info("🚀 启动Hailo8 AI Service")
    logger.info(f"📡 Hailo Runtime API: {HAILO_API_URL}")
    logger.info(f"🌐 服务端口: {SERVICE_PORT}")

    # 测试连接
    if hailo_client.health_check():
        logger.info("✅ 成功连接到Hailo Runtime服务")
    else:
        logger.warning("⚠️ 无法连接到Hailo Runtime服务，服务将在模拟模式下运行")

    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=SERVICE_PORT,
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    main()