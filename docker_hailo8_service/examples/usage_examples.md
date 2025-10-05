# Hailo8 Docker服务使用示例

本文档提供了如何使用Hailo8 Docker服务的详细示例，包括不同的部署方式和客户端调用方法。

## 目录
- [快速开始](#快速开始)
- [部署方式](#部署方式)
- [客户端调用示例](#客户端调用示例)
- [API使用示例](#api使用示例)
- [容器间通信](#容器间通信)
- [监控和调试](#监控和调试)

## 快速开始

### 1. 构建服务镜像

```bash
# 克隆项目
git clone <repository-url>
cd docker_hailo8_service

# 构建Hailo8服务镜像
docker build -t hailo8-service:latest .
```

### 2. 简单部署

```bash
# 使用简化的docker-compose配置
docker-compose -f docker-compose.simple.yml up -d

# 检查服务状态
curl http://localhost:8080/health
```

### 3. 完整部署（包含监控）

```bash
# 使用完整的docker-compose配置
docker-compose up -d

# 访问服务
curl http://localhost:8080/health

# 访问监控面板
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus
```

## 部署方式

### 方式1: 单容器部署

```bash
# 直接运行容器
docker run -d \
  --name hailo8-service \
  --device=/dev/hailo0 \
  -p 8080:8080 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  -e HAILO8_MOCK_MODE=false \
  -e HAILO8_DEVICE_COUNT=1 \
  hailo8-service:latest
```

### 方式2: Docker Compose部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  hailo8-service:
    build: .
    container_name: hailo8-service
    restart: unless-stopped
    ports:
      - "8080:8080"
    devices:
      - "/dev/hailo0:/dev/hailo0"
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - HAILO8_MOCK_MODE=false
      - HAILO8_DEVICE_COUNT=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 方式3: Kubernetes部署

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hailo8-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hailo8-service
  template:
    metadata:
      labels:
        app: hailo8-service
    spec:
      containers:
      - name: hailo8-service
        image: hailo8-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: HAILO8_MOCK_MODE
          value: "false"
        - name: HAILO8_DEVICE_COUNT
          value: "1"
        volumeMounts:
        - name: models-volume
          mountPath: /app/models
        - name: hailo-device
          mountPath: /dev/hailo0
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
          requests:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: models-volume
        hostPath:
          path: /path/to/models
      - name: hailo-device
        hostPath:
          path: /dev/hailo0
---
apiVersion: v1
kind: Service
metadata:
  name: hailo8-service
spec:
  selector:
    app: hailo8-service
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

## 客户端调用示例

### Python客户端

```python
import asyncio
from hailo8_client import Hailo8Client, load_image_as_base64

async def main():
    async with Hailo8Client('http://hailo8-service:8080') as client:
        # 1. 健康检查
        health = await client.health_check()
        print(f"服务状态: {health}")
        
        # 2. 加载模型
        load_result = await client.load_model(
            model_path="/app/models/yolov5s.hef",
            model_id="yolov5s"
        )
        print(f"模型加载: {load_result}")
        
        # 3. 执行推理
        image_base64 = await load_image_as_base64("input.jpg")
        result = await client.run_inference(
            model_id="yolov5s",
            input_data=image_base64
        )
        print(f"推理结果: {result}")
        
        # 4. 批量推理
        batch_images = [
            await load_image_as_base64("img1.jpg"),
            await load_image_as_base64("img2.jpg"),
            await load_image_as_base64("img3.jpg")
        ]
        batch_result = await client.run_batch_inference(
            model_id="yolov5s",
            input_batch=batch_images
        )
        print(f"批量推理结果: {batch_result}")
        
        # 5. 异步推理
        task_id = await client.submit_async_inference(
            model_id="yolov5s",
            input_data=image_base64
        )
        async_result = await client.wait_for_async_result(task_id)
        print(f"异步推理结果: {async_result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript客户端

```javascript
// hailo8-client.js
class Hailo8Client {
    constructor(baseUrl) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }
    
    async request(method, endpoint, data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        return await response.json();
    }
    
    async healthCheck() {
        return await this.request('GET', '/health');
    }
    
    async loadModel(modelPath, modelId, config = null) {
        return await this.request('POST', '/models/load', {
            model_path: modelPath,
            model_id: modelId,
            config
        });
    }
    
    async runInference(modelId, inputData, inputFormat = 'base64', outputFormat = 'json') {
        return await this.request('POST', '/inference', {
            model_id: modelId,
            input_data: inputData,
            input_format: inputFormat,
            output_format: outputFormat
        });
    }
}

// 使用示例
async function main() {
    const client = new Hailo8Client('http://hailo8-service:8080');
    
    // 健康检查
    const health = await client.healthCheck();
    console.log('服务状态:', health);
    
    // 加载模型
    const loadResult = await client.loadModel('/app/models/model.hef', 'my_model');
    console.log('模型加载:', loadResult);
    
    // 执行推理
    const imageBase64 = await fileToBase64('input.jpg');
    const result = await client.runInference('my_model', imageBase64);
    console.log('推理结果:', result);
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = error => reject(error);
    });
}
```

### Go客户端

```go
// hailo8_client.go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

type Hailo8Client struct {
    BaseURL string
    Client  *http.Client
}

func NewHailo8Client(baseURL string) *Hailo8Client {
    return &Hailo8Client{
        BaseURL: baseURL,
        Client: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *Hailo8Client) request(method, endpoint string, data interface{}) (map[string]interface{}, error) {
    url := c.BaseURL + endpoint
    
    var body io.Reader
    if data != nil {
        jsonData, err := json.Marshal(data)
        if err != nil {
            return nil, err
        }
        body = bytes.NewBuffer(jsonData)
    }
    
    req, err := http.NewRequest(method, url, body)
    if err != nil {
        return nil, err
    }
    
    if data != nil {
        req.Header.Set("Content-Type", "application/json")
    }
    
    resp, err := c.Client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return result, nil
}

func (c *Hailo8Client) HealthCheck() (map[string]interface{}, error) {
    return c.request("GET", "/health", nil)
}

func (c *Hailo8Client) LoadModel(modelPath, modelID string) (map[string]interface{}, error) {
    data := map[string]interface{}{
        "model_path": modelPath,
        "model_id":   modelID,
    }
    return c.request("POST", "/models/load", data)
}

func (c *Hailo8Client) RunInference(modelID, inputData string) (map[string]interface{}, error) {
    data := map[string]interface{}{
        "model_id":      modelID,
        "input_data":    inputData,
        "input_format":  "base64",
        "output_format": "json",
    }
    return c.request("POST", "/inference", data)
}

func main() {
    client := NewHailo8Client("http://hailo8-service:8080")
    
    // 健康检查
    health, err := client.HealthCheck()
    if err != nil {
        panic(err)
    }
    fmt.Printf("服务状态: %+v\n", health)
    
    // 加载模型
    loadResult, err := client.LoadModel("/app/models/model.hef", "my_model")
    if err != nil {
        panic(err)
    }
    fmt.Printf("模型加载: %+v\n", loadResult)
    
    // 执行推理（需要先将图片转换为base64）
    // imageBase64 := ... // 图片的base64编码
    // result, err := client.RunInference("my_model", imageBase64)
    // fmt.Printf("推理结果: %+v\n", result)
}
```

## API使用示例

### 1. 健康检查

```bash
curl -X GET http://localhost:8080/health
```

响应:
```json
{
  "healthy": true,
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "uptime": 3600.5
}
```

### 2. 获取设备信息

```bash
curl -X GET http://localhost:8080/devices
```

响应:
```json
{
  "devices": [
    {
      "device_id": "hailo0",
      "status": "available",
      "temperature": 45.2,
      "utilization": 0.0,
      "memory_used": 0,
      "memory_total": 1073741824
    }
  ]
}
```

### 3. 加载模型

```bash
curl -X POST http://localhost:8080/models/load \
  -H "Content-Type: application/json" \
  -d '{
    "model_path": "/app/models/yolov5s.hef",
    "model_id": "yolov5s",
    "config": {
      "batch_size": 1,
      "input_format": "NHWC"
    }
  }'
```

### 4. 执行推理

```bash
# 将图片转换为base64
IMAGE_BASE64=$(base64 -i input.jpg)

curl -X POST http://localhost:8080/inference \
  -H "Content-Type: application/json" \
  -d "{
    \"model_id\": \"yolov5s\",
    \"input_data\": \"$IMAGE_BASE64\",
    \"input_format\": \"base64\",
    \"output_format\": \"json\"
  }"
```

### 5. 批量推理

```bash
curl -X POST http://localhost:8080/inference/batch \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "yolov5s",
    "input_batch": ["'$IMAGE1_BASE64'", "'$IMAGE2_BASE64'", "'$IMAGE3_BASE64'"],
    "input_format": "base64",
    "output_format": "json"
  }'
```

## 容器间通信

### 示例1: Web应用调用Hailo8服务

```yaml
# docker-compose.yml
version: '3.8'

services:
  hailo8-service:
    build: .
    container_name: hailo8-service
    devices:
      - "/dev/hailo0:/dev/hailo0"
    volumes:
      - ./models:/app/models
    networks:
      - ai-network
    
  web-app:
    image: my-web-app:latest
    container_name: web-app
    ports:
      - "3000:3000"
    environment:
      - HAILO8_SERVICE_URL=http://hailo8-service:8080
    depends_on:
      - hailo8-service
    networks:
      - ai-network

networks:
  ai-network:
    driver: bridge
```

### 示例2: 多个客户端服务

```yaml
version: '3.8'

services:
  hailo8-service:
    build: .
    container_name: hailo8-service
    devices:
      - "/dev/hailo0:/dev/hailo0"
    volumes:
      - ./models:/app/models
    networks:
      - ai-network
    
  image-processor:
    image: image-processor:latest
    container_name: image-processor
    environment:
      - HAILO8_SERVICE_URL=http://hailo8-service:8080
    volumes:
      - ./input:/app/input
      - ./output:/app/output
    depends_on:
      - hailo8-service
    networks:
      - ai-network
    
  video-analyzer:
    image: video-analyzer:latest
    container_name: video-analyzer
    environment:
      - HAILO8_SERVICE_URL=http://hailo8-service:8080
    volumes:
      - ./videos:/app/videos
      - ./results:/app/results
    depends_on:
      - hailo8-service
    networks:
      - ai-network

networks:
  ai-network:
    driver: bridge
```

## 监控和调试

### 1. 查看服务日志

```bash
# 查看Hailo8服务日志
docker logs hailo8-service -f

# 查看特定时间段的日志
docker logs hailo8-service --since="2024-01-01T12:00:00" --until="2024-01-01T13:00:00"
```

### 2. 监控服务状态

```bash
# 获取服务状态
curl http://localhost:8080/status

# 获取服务统计
curl http://localhost:8080/stats

# 获取Prometheus指标
curl http://localhost:8080/metrics
```

### 3. 性能测试

```python
# performance_test.py
import asyncio
import time
from hailo8_client import Hailo8Client, load_image_as_base64

async def performance_test():
    async with Hailo8Client('http://localhost:8080') as client:
        # 加载模型
        await client.load_model("/app/models/model.hef", "test_model")
        
        # 准备测试数据
        image_base64 = await load_image_as_base64("test_image.jpg")
        
        # 单次推理性能测试
        start_time = time.time()
        for i in range(100):
            result = await client.run_inference("test_model", image_base64)
        single_time = time.time() - start_time
        
        print(f"单次推理 100次耗时: {single_time:.2f}秒")
        print(f"平均每次推理: {single_time/100*1000:.2f}毫秒")
        
        # 批量推理性能测试
        batch_data = [image_base64] * 10
        start_time = time.time()
        for i in range(10):
            result = await client.run_batch_inference("test_model", batch_data)
        batch_time = time.time() - start_time
        
        print(f"批量推理 10批次(每批10张)耗时: {batch_time:.2f}秒")
        print(f"平均每张图片: {batch_time/100*1000:.2f}毫秒")

if __name__ == "__main__":
    asyncio.run(performance_test())
```

### 4. 故障排除

```bash
# 检查容器状态
docker ps -a

# 检查容器资源使用
docker stats hailo8-service

# 进入容器调试
docker exec -it hailo8-service /bin/bash

# 检查Hailo设备
ls -la /dev/hailo*

# 检查模型文件
ls -la /app/models/

# 测试API连通性
curl -v http://localhost:8080/health
```

## 最佳实践

### 1. 资源管理

- 为容器设置合适的内存和CPU限制
- 使用健康检查确保服务可用性
- 定期清理临时文件和日志

### 2. 安全考虑

- 使用非root用户运行容器
- 限制容器的网络访问
- 定期更新基础镜像和依赖

### 3. 性能优化

- 使用批量推理提高吞吐量
- 合理设置并发限制
- 监控设备温度和利用率

### 4. 部署建议

- 使用Docker Compose管理多服务部署
- 配置日志轮转避免磁盘空间不足
- 设置合适的重启策略

这些示例涵盖了Hailo8 Docker服务的主要使用场景，可以根据具体需求进行调整和扩展。