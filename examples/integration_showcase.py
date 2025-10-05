#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hailo8 Integration Showcase

Demonstrates various integration scenarios and capabilities
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Add hailo8_installer to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project

def create_web_app_project(project_path):
    """Create a sample web application project"""
    
    # Create directories
    os.makedirs(project_path + "/app", exist_ok=True)
    os.makedirs(project_path + "/static/css", exist_ok=True)
    os.makedirs(project_path + "/static/js", exist_ok=True)
    os.makedirs(project_path + "/templates", exist_ok=True)
    os.makedirs(project_path + "/models", exist_ok=True)
    
    # Create Flask app
    with open(project_path + "/app.py", "w") as f:
        f.write("""#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/inference', methods=['POST'])
def inference():
    # This will be enhanced with Hailo8 integration
    data = request.get_json()
    
    result = {
        'status': 'success',
        'model': data.get('model', 'default'),
        'device': 'cpu',  # Will be 'hailo8' after integration
        'inference_time': 0.1,
        'result': 'placeholder_result'
    }
    
    return jsonify(result)

@app.route('/api/status')
def status():
    return jsonify({
        'app': 'running',
        'hailo8_available': False,  # Will be updated by integration
        'models_loaded': 0
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
""")
    
    # Create HTML template
    with open(project_path + "/templates/index.html", "w") as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Inference Web App</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1>AI Inference Web Application</h1>
        <div class="status-panel">
            <h2>System Status</h2>
            <div id="status-info">Loading...</div>
        </div>
        
        <div class="inference-panel">
            <h2>Run Inference</h2>
            <form id="inference-form">
                <div class="form-group">
                    <label for="model">Model:</label>
                    <select id="model" name="model">
                        <option value="yolo">YOLO Detection</option>
                        <option value="resnet">ResNet Classification</option>
                        <option value="mobilenet">MobileNet</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="input-data">Input Data:</label>
                    <textarea id="input-data" name="input_data" placeholder="Enter input data..."></textarea>
                </div>
                <button type="submit">Run Inference</button>
            </form>
            <div id="results"></div>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
""")
    
    # Create CSS
    with open(project_path + "/static/css/style.css", "w") as f:
        f.write("""
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    text-align: center;
    margin-bottom: 30px;
}

.status-panel, .inference-panel {
    margin: 20px 0;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 5px;
}

.form-group {
    margin: 15px 0;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

select, textarea {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

button {
    background-color: #007bff;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background-color: #0056b3;
}

#results {
    margin-top: 20px;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 4px;
    display: none;
}
""")
    
    # Create JavaScript
    with open(project_path + "/static/js/app.js", "w") as f:
        f.write("""
// Load status on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStatus();
    
    // Setup form submission
    document.getElementById('inference-form').addEventListener('submit', function(e) {
        e.preventDefault();
        runInference();
    });
});

function loadStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById('status-info');
            statusDiv.innerHTML = `
                <p><strong>App Status:</strong> ${data.app}</p>
                <p><strong>Hailo8 Available:</strong> ${data.hailo8_available ? 'Yes' : 'No'}</p>
                <p><strong>Models Loaded:</strong> ${data.models_loaded}</p>
            `;
        })
        .catch(error => {
            console.error('Error loading status:', error);
        });
}

function runInference() {
    const model = document.getElementById('model').value;
    const inputData = document.getElementById('input-data').value;
    
    const data = {
        model: model,
        input_data: inputData
    };
    
    fetch('/api/inference', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <h3>Inference Results</h3>
            <p><strong>Status:</strong> ${result.status}</p>
            <p><strong>Model:</strong> ${result.model}</p>
            <p><strong>Device:</strong> ${result.device}</p>
            <p><strong>Inference Time:</strong> ${result.inference_time}s</p>
            <p><strong>Result:</strong> ${result.result}</p>
        `;
        resultsDiv.style.display = 'block';
    })
    .catch(error => {
        console.error('Error running inference:', error);
    });
}
""")
    
    # Create requirements.txt
    with open(project_path + "/requirements.txt", "w") as f:
        f.write("""Flask>=2.0.0
numpy>=1.21.0
pillow>=8.0.0
requests>=2.25.0
""")

def create_ml_pipeline_project(project_path):
    """Create a sample ML pipeline project"""
    
    # Create directories
    os.makedirs(project_path + "/src/data", exist_ok=True)
    os.makedirs(project_path + "/src/models", exist_ok=True)
    os.makedirs(project_path + "/src/training", exist_ok=True)
    os.makedirs(project_path + "/src/inference", exist_ok=True)
    os.makedirs(project_path + "/config", exist_ok=True)
    os.makedirs(project_path + "/notebooks", exist_ok=True)
    
    # Create main pipeline script
    with open(project_path + "/src/pipeline.py", "w") as f:
        f.write("""#!/usr/bin/env python3
import os
import json
import numpy as np
from pathlib import Path

class MLPipeline:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()
        self.device = 'cpu'  # Will be 'hailo8' after integration
    
    def load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def preprocess_data(self, data_path):
        print(f"Preprocessing data from {data_path}")
        # Data preprocessing logic
        # Hailo8 optimization will be added here
        return "preprocessed_data"
    
    def train_model(self, data):
        print("Training model...")
        # Model training logic
        # Hailo8 acceleration will be added here
        return "trained_model"
    
    def optimize_model(self, model):
        print("Optimizing model...")
        # Model optimization logic
        # Hailo8 compilation will be added here
        return "optimized_model"
    
    def run_inference(self, model, input_data):
        print("Running inference...")
        # Inference logic
        # Hailo8 acceleration will be added here
        return {"prediction": "sample_result"}
    
    def evaluate_model(self, model, test_data):
        print("Evaluating model...")
        # Model evaluation logic
        return {"accuracy": 0.95, "f1_score": 0.93}

def main():
    pipeline = MLPipeline("config/pipeline_config.json")
    
    # Run pipeline steps
    data = pipeline.preprocess_data("data/raw/")
    model = pipeline.train_model(data)
    optimized_model = pipeline.optimize_model(model)
    
    # Test inference
    test_input = np.random.rand(1, 224, 224, 3)
    result = pipeline.run_inference(optimized_model, test_input)
    print(f"Inference result: {result}")

if __name__ == "__main__":
    main()
""")
    
    # Create config file
    with open(project_path + "/config/pipeline_config.json", "w") as f:
        f.write("""{
    "model": {
        "type": "resnet50",
        "input_shape": [224, 224, 3],
        "num_classes": 1000
    },
    "training": {
        "batch_size": 32,
        "epochs": 100,
        "learning_rate": 0.001,
        "optimizer": "adam"
    },
    "data": {
        "train_path": "data/train/",
        "val_path": "data/val/",
        "test_path": "data/test/"
    },
    "hailo8": {
        "enabled": false,
        "optimization_level": "high",
        "quantization": "int8"
    }
}""")

def create_api_service_project(project_path):
    """Create a sample API service project"""
    
    # Create directories
    os.makedirs(project_path + "/src/api", exist_ok=True)
    os.makedirs(project_path + "/src/models", exist_ok=True)
    os.makedirs(project_path + "/src/utils", exist_ok=True)
    os.makedirs(project_path + "/tests", exist_ok=True)
    
    # Create FastAPI service
    with open(project_path + "/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import numpy as np
from typing import List, Dict, Any

app = FastAPI(title="AI Inference API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InferenceRequest(BaseModel):
    model_name: str
    input_data: List[float]
    parameters: Dict[str, Any] = {}

class InferenceResponse(BaseModel):
    status: str
    model_name: str
    device: str
    inference_time: float
    result: Dict[str, Any]

# Global variables (will be enhanced by Hailo8 integration)
loaded_models = {}
device_info = {"type": "cpu", "hailo8_available": False}

@app.get("/")
async def root():
    return {"message": "AI Inference API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "device": device_info,
        "models_loaded": len(loaded_models)
    }

@app.get("/models")
async def list_models():
    return {
        "available_models": list(loaded_models.keys()),
        "supported_models": ["yolo", "resnet", "mobilenet"]
    }

@app.post("/models/{model_name}/load")
async def load_model(model_name: str):
    # Model loading logic (will be enhanced with Hailo8)
    loaded_models[model_name] = {
        "name": model_name,
        "device": device_info["type"],
        "loaded_at": "2023-01-01T00:00:00Z"
    }
    return {"status": "success", "message": f"Model {model_name} loaded"}

@app.post("/inference", response_model=InferenceResponse)
async def run_inference(request: InferenceRequest):
    if request.model_name not in loaded_models:
        raise HTTPException(status_code=404, detail="Model not loaded")
    
    # Inference logic (will be enhanced with Hailo8 acceleration)
    import time
    start_time = time.time()
    
    # Simulate inference
    result = {
        "prediction": "sample_prediction",
        "confidence": 0.95,
        "classes": ["class1", "class2", "class3"]
    }
    
    inference_time = time.time() - start_time
    
    return InferenceResponse(
        status="success",
        model_name=request.model_name,
        device=device_info["type"],
        inference_time=inference_time,
        result=result
    )

@app.post("/inference/batch")
async def batch_inference(requests: List[InferenceRequest]):
    results = []
    for req in requests:
        try:
            result = await run_inference(req)
            results.append(result)
        except Exception as e:
            results.append({
                "status": "error",
                "model_name": req.model_name,
                "error": str(e)
            })
    return {"results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""")
    
    # Create requirements.txt
    with open(project_path + "/requirements.txt", "w") as f:
        f.write("""fastapi>=0.68.0
uvicorn>=0.15.0
pydantic>=1.8.0
numpy>=1.21.0
pillow>=8.0.0
python-multipart>=0.0.5
""")

def showcase_integrations():
    """Showcase different integration scenarios"""
    
    print("Hailo8 Integration Showcase")
    print("=" * 50)
    
    showcases = [
        {
            "name": "Web Application",
            "description": "Flask web app with AI inference endpoints",
            "path": "/tmp/showcase_webapp",
            "creator": create_web_app_project
        },
        {
            "name": "ML Pipeline",
            "description": "Complete ML training and inference pipeline",
            "path": "/tmp/showcase_mlpipeline",
            "creator": create_ml_pipeline_project
        },
        {
            "name": "API Service",
            "description": "FastAPI microservice for AI inference",
            "path": "/tmp/showcase_apiservice",
            "creator": create_api_service_project
        }
    ]
    
    results = []
    
    for showcase in showcases:
        print(f"\n=== {showcase['name']} Integration ===")
        print(f"Description: {showcase['description']}")
        
        try:
            # Create project
            os.makedirs(showcase['path'], exist_ok=True)
            showcase['creator'](showcase['path'])
            
            # Integrate with Hailo8
            success = integrate_with_existing_project(
                project_path=showcase['path'],
                project_name=showcase['name'],
                hailo8_enabled=True,
                docker_enabled=True,
                auto_install=False,
                log_level="INFO"
            )
            
            if success:
                print(f"SUCCESS: {showcase['name']} integration completed!")
                print(f"Project location: {showcase['path']}")
                print(f"Hailo8 integration: {showcase['path']}/hailo8/")
                results.append((showcase['name'], True))
            else:
                print(f"FAILED: {showcase['name']} integration failed")
                results.append((showcase['name'], False))
                
        except Exception as e:
            print(f"FAILED: {showcase['name']} integration failed: {e}")
            results.append((showcase['name'], False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Integration Showcase Summary:")
    print("=" * 50)
    
    success_count = 0
    for name, success in results:
        status = "SUCCESS" if success else "FAILED"
        print(f"{name.ljust(20)} {status}")
        if success:
            success_count += 1
    
    print(f"\nTotal: {success_count}/{len(results)} integrations successful")
    
    if success_count > 0:
        print("\nShowcase projects created in /tmp/:")
        for showcase in showcases:
            if os.path.exists(showcase['path']):
                print(f"- {showcase['path']}")
        
        print("\nEach project includes:")
        print("- Original project structure and code")
        print("- Hailo8 integration in hailo8/ directory")
        print("- Installation and setup scripts")
        print("- Docker configuration")
        print("- API documentation")
        print("- Testing utilities")

if __name__ == "__main__":
    showcase_integrations()