#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Hailo8 Integration Demo

A clean demonstration of how to integrate Hailo8 TPU support into other projects
"""

import os
import sys
from pathlib import Path

# Add hailo8_installer to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project, quick_integrate

def demo_quick_integration():
    """Demonstrate quick integration"""
    print("=== Quick Integration Demo ===")
    
    project_path = "/tmp/quick_demo_project"
    os.makedirs(project_path, exist_ok=True)
    
    try:
        # Quick integration
        result = quick_integrate(
            project_path=project_path,
            project_name="Quick Demo Project"
        )
        
        print("✓ Quick integration successful!")
        print(f"Project created at: {project_path}")
        print(f"Integration files: {project_path}/hailo8/")
        
        return True
        
    except Exception as e:
        print(f"✗ Quick integration failed: {e}")
        return False

def demo_detailed_integration():
    """Demonstrate detailed integration"""
    print("\n=== Detailed Integration Demo ===")
    
    project_path = "/tmp/detailed_demo_project"
    os.makedirs(project_path, exist_ok=True)
    
    # Create a sample project structure
    create_sample_project(project_path)
    
    try:
        # Detailed integration
        result = integrate_with_existing_project(
            project_path=project_path,
            project_name="Detailed Demo Project",
            integration_type="detailed",
            config={
                "hailo8_features": [
                    "inference_acceleration",
                    "performance_monitoring"
                ],
                "target_platforms": ["linux"],
                "api_integration": True,
                "monitoring": True
            }
        )
        
        print("✓ Detailed integration successful!")
        print(f"Project created at: {project_path}")
        print("Integration includes:")
        print("  - Hailo8 installer scripts")
        print("  - Configuration files")
        print("  - API integration")
        print("  - Monitoring setup")
        
        return True
        
    except Exception as e:
        print(f"✗ Detailed integration failed: {e}")
        return False

def create_sample_project(project_path):
    """Create a sample project structure"""
    
    # Create directories
    os.makedirs(f"{project_path}/src", exist_ok=True)
    os.makedirs(f"{project_path}/config", exist_ok=True)
    os.makedirs(f"{project_path}/tests", exist_ok=True)
    
    # Create main.py
    with open(f"{project_path}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Sample application main file
\"\"\"

def main():
    print("Sample application running...")
    
    # This is where Hailo8 integration will be added
    try:
        # Import Hailo8 functionality (will be added by integration)
        from hailo8_integration import hailo8_manager
        
        if hailo8_manager.is_available():
            print("Hailo8 TPU is available and ready!")
        else:
            print("Hailo8 TPU not available, using CPU fallback")
            
    except ImportError:
        print("Hailo8 integration not yet installed")
    
    print("Application completed")

if __name__ == "__main__":
    main()
""")
    
    # Create requirements.txt
    with open(f"{project_path}/requirements.txt", "w") as f:
        f.write("""numpy>=1.21.0
pillow>=8.0.0
requests>=2.25.0
""")
    
    # Create README.md
    with open(f"{project_path}/README.md", "w") as f:
        f.write("""# Sample Project

This is a sample project for demonstrating Hailo8 integration.

## Setup

```bash
pip install -r requirements.txt
python src/main.py
```

## Features

- Basic application structure
- Ready for Hailo8 integration
- Modular design
""")

def demo_project_integration():
    """Demonstrate integration with existing project"""
    print("\n=== Project Integration Demo ===")
    
    project_path = "/tmp/project_demo"
    os.makedirs(project_path, exist_ok=True)
    
    # Create a more complex project structure
    create_complex_project(project_path)
    
    try:
        # Integrate with existing project
        result = integrate_with_existing_project(
            project_path=project_path,
            project_name="Complex Demo Project",
            integration_type="detailed",
            config={
                "hailo8_features": [
                    "inference_acceleration",
                    "model_optimization",
                    "performance_monitoring"
                ],
                "target_platforms": ["linux", "docker"],
                "api_integration": True,
                "monitoring": True,
                "auto_setup": True
            }
        )
        
        print("✓ Project integration successful!")
        print(f"Enhanced project at: {project_path}")
        print("Added features:")
        print("  - Hailo8 TPU support")
        print("  - Model optimization")
        print("  - Performance monitoring")
        print("  - Docker integration")
        
        return True
        
    except Exception as e:
        print(f"✗ Project integration failed: {e}")
        return False

def create_complex_project(project_path):
    """Create a more complex project structure"""
    
    # Create directories
    directories = [
        "src/models",
        "src/utils",
        "src/api",
        "config",
        "tests/unit",
        "tests/integration",
        "docs",
        "scripts"
    ]
    
    for directory in directories:
        os.makedirs(f"{project_path}/{directory}", exist_ok=True)
    
    # Create API server
    with open(f"{project_path}/src/api/server.py", "w") as f:
        f.write("""#!/usr/bin/env python3
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'hailo8_available': False  # Will be updated by integration
    })

@app.route('/api/inference', methods=['POST'])
def inference():
    data = request.get_json()
    
    # This is where Hailo8 inference will be integrated
    result = {
        'model': data.get('model', 'unknown'),
        'result': 'placeholder_result',
        'device': 'cpu'  # Will be 'hailo8' after integration
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""")
    
    # Create model handler
    with open(f"{project_path}/src/models/handler.py", "w") as f:
        f.write("""#!/usr/bin/env python3
class ModelHandler:
    def __init__(self):
        self.models = {}
        self.device = 'cpu'  # Will be updated to 'hailo8' by integration
    
    def load_model(self, model_path):
        # Model loading logic
        # Hailo8 optimization will be added here
        pass
    
    def predict(self, input_data):
        # Prediction logic
        # Hailo8 acceleration will be added here
        return {'prediction': 'placeholder'}
""")

def run_all_demos():
    """Run all integration demos"""
    print("Hailo8 Integration Demonstration")
    print("=" * 50)
    
    demos = [
        ("Quick Integration", demo_quick_integration),
        ("Detailed Integration", demo_detailed_integration),
        ("Project Integration", demo_project_integration)
    ]
    
    results = []
    
    for name, demo_func in demos:
        try:
            success = demo_func()
            results.append((name, success))
        except Exception as e:
            print(f"✗ {name} demo failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Demo Results Summary:")
    print("=" * 50)
    
    success_count = 0
    for name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{name:25} {status}")
        if success:
            success_count += 1
    
    print(f"\nTotal: {success_count}/{len(results)} demos successful")
    
    if success_count > 0:
        print("\nDemo projects created in /tmp/:")
        print("- /tmp/quick_demo_project")
        print("- /tmp/detailed_demo_project") 
        print("- /tmp/project_demo")
        print("\nYou can explore these projects to see the integration results!")

if __name__ == "__main__":
    run_all_demos()