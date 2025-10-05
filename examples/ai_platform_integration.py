#!/usr/bin/env python3
"""
AI 平台集成示例

展示如何将 Hailo8 TPU 支持集成到完整的 AI 平台中
包括模型训练、部署、推理、监控等完整流程
"""

import os
import sys
from pathlib import Path

# 添加 hailo8_installer 到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from hailo8_installer.integration import integrate_with_existing_project

def create_ai_platform():
    """创建 AI 平台示例"""
    project_path = "/tmp/ai_platform_hailo8"
    os.makedirs(project_path, exist_ok=True)
    
    # 创建平台目录结构
    directories = [
        "frontend",
        "backend",
        "ml_pipeline",
        "model_registry",
        "inference_engine",
        "data_management",
        "monitoring",
        "deployment",
        "docs",
        "scripts",
        "tests"
    ]
    
    for directory in directories:
        os.makedirs(f"{project_path}/{directory}", exist_ok=True)
        os.makedirs(f"{project_path}/{directory}/src", exist_ok=True)
        os.makedirs(f"{project_path}/{directory}/config", exist_ok=True)
    
    # 创建各个组件
    create_frontend(f"{project_path}/frontend")
    create_backend(f"{project_path}/backend")
    create_ml_pipeline(f"{project_path}/ml_pipeline")
    create_model_registry(f"{project_path}/model_registry")
    create_inference_engine(f"{project_path}/inference_engine")
    create_data_management(f"{project_path}/data_management")
    create_monitoring(f"{project_path}/monitoring")
    create_deployment_configs(f"{project_path}/deployment")
    create_platform_docs(f"{project_path}/docs")
    create_platform_scripts(f"{project_path}/scripts")
    create_root_config(project_path)
    
    return project_path

def create_frontend(frontend_path):
    """创建前端应用"""
    # React 应用主文件
    with open(f"{frontend_path}/src/App.js", "w") as f:
        f.write("""import React, { useState, useEffect } from 'react';
import './App.css';

// 组件导入
import Dashboard from './components/Dashboard';
import ModelManagement from './components/ModelManagement';
import InferenceConsole from './components/InferenceConsole';
import DataManagement from './components/DataManagement';
import Monitoring from './components/Monitoring';
import Settings from './components/Settings';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [systemStatus, setSystemStatus] = useState({});
  const [user, setUser] = useState(null);

  useEffect(() => {
    // 获取系统状态
    fetchSystemStatus();
    // 检查用户登录状态
    checkAuthStatus();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/v1/system/status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('获取系统状态失败:', error);
    }
  };

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (token) {
        const response = await fetch('/api/v1/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        }
      }
    } catch (error) {
      console.error('检查认证状态失败:', error);
    }
  };

  const handleLogin = async (credentials) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
        setUser(data.user);
        return true;
      }
      return false;
    } catch (error) {
      console.error('登录失败:', error);
      return false;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
    setCurrentView('dashboard');
  };

  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>🧠 AI Platform with Hailo8</h1>
          <div className="system-status">
            <span className={`status-indicator ${systemStatus.hailo8_available ? 'online' : 'offline'}`}>
              Hailo8 TPU: {systemStatus.hailo8_available ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
        <div className="header-right">
          <span>欢迎, {user.username}</span>
          <button onClick={handleLogout} className="logout-btn">退出</button>
        </div>
      </header>

      <div className="app-body">
        <nav className="sidebar">
          <ul>
            <li className={currentView === 'dashboard' ? 'active' : ''}>
              <button onClick={() => setCurrentView('dashboard')}>
                📊 仪表板
              </button>
            </li>
            <li className={currentView === 'models' ? 'active' : ''}>
              <button onClick={() => setCurrentView('models')}>
                🤖 模型管理
              </button>
            </li>
            <li className={currentView === 'inference' ? 'active' : ''}>
              <button onClick={() => setCurrentView('inference')}>
                ⚡ 推理控制台
              </button>
            </li>
            <li className={currentView === 'data' ? 'active' : ''}>
              <button onClick={() => setCurrentView('data')}>
                📁 数据管理
              </button>
            </li>
            <li className={currentView === 'monitoring' ? 'active' : ''}>
              <button onClick={() => setCurrentView('monitoring')}>
                📈 监控中心
              </button>
            </li>
            <li className={currentView === 'settings' ? 'active' : ''}>
              <button onClick={() => setCurrentView('settings')}>
                ⚙️ 系统设置
              </button>
            </li>
          </ul>
        </nav>

        <main className="main-content">
          {currentView === 'dashboard' && <Dashboard systemStatus={systemStatus} />}
          {currentView === 'models' && <ModelManagement />}
          {currentView === 'inference' && <InferenceConsole />}
          {currentView === 'data' && <DataManagement />}
          {currentView === 'monitoring' && <Monitoring />}
          {currentView === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
}

// 登录表单组件
function LoginForm({ onLogin }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const success = await onLogin(credentials);
    setLoading(false);
    if (!success) {
      alert('登录失败，请检查用户名和密码');
    }
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h2>🧠 AI Platform 登录</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>用户名:</label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>密码:</label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
        <div className="demo-accounts">
          <p>演示账户:</p>
          <p>管理员: admin / admin123</p>
          <p>用户: user / user123</p>
        </div>
      </div>
    </div>
  );
}

export default App;
""")
    
    # 仪表板组件
    os.makedirs(f"{frontend_path}/src/components", exist_ok=True)
    with open(f"{frontend_path}/src/components/Dashboard.js", "w") as f:
        f.write("""import React, { useState, useEffect } from 'react';

function Dashboard({ systemStatus }) {
  const [metrics, setMetrics] = useState({});
  const [recentActivities, setRecentActivities] = useState([]);

  useEffect(() => {
    fetchMetrics();
    fetchRecentActivities();
    
    // 定期更新数据
    const interval = setInterval(() => {
      fetchMetrics();
      fetchRecentActivities();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/v1/metrics/dashboard');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('获取指标失败:', error);
    }
  };

  const fetchRecentActivities = async () => {
    try {
      const response = await fetch('/api/v1/activities/recent');
      const data = await response.json();
      setRecentActivities(data.activities || []);
    } catch (error) {
      console.error('获取活动记录失败:', error);
    }
  };

  return (
    <div className="dashboard">
      <h2>系统仪表板</h2>
      
      {/* 系统状态卡片 */}
      <div className="status-cards">
        <div className="status-card">
          <h3>🔥 Hailo8 TPU</h3>
          <div className={`status ${systemStatus.hailo8_available ? 'online' : 'offline'}`}>
            {systemStatus.hailo8_available ? '在线' : '离线'}
          </div>
          <p>设备温度: {systemStatus.temperature || 'N/A'}°C</p>
        </div>
        
        <div className="status-card">
          <h3>🤖 活跃模型</h3>
          <div className="metric-value">{metrics.active_models || 0}</div>
          <p>总模型数: {metrics.total_models || 0}</p>
        </div>
        
        <div className="status-card">
          <h3>⚡ 推理请求</h3>
          <div className="metric-value">{metrics.inference_requests_today || 0}</div>
          <p>今日请求数</p>
        </div>
        
        <div className="status-card">
          <h3>📊 系统负载</h3>
          <div className="metric-value">{metrics.cpu_usage || 0}%</div>
          <p>CPU 使用率</p>
        </div>
      </div>

      {/* 性能图表 */}
      <div className="charts-section">
        <div className="chart-container">
          <h3>推理性能趋势</h3>
          <div className="chart-placeholder">
            <p>推理延迟: {metrics.avg_inference_time || 0}ms</p>
            <p>吞吐量: {metrics.throughput || 0} req/s</p>
            <div className="performance-bar">
              <div 
                className="performance-fill" 
                style={{width: `${Math.min(100, (metrics.throughput || 0) * 10)}%`}}
              ></div>
            </div>
          </div>
        </div>
        
        <div className="chart-container">
          <h3>资源使用情况</h3>
          <div className="resource-usage">
            <div className="resource-item">
              <span>CPU:</span>
              <div className="usage-bar">
                <div 
                  className="usage-fill cpu" 
                  style={{width: `${metrics.cpu_usage || 0}%`}}
                ></div>
              </div>
              <span>{metrics.cpu_usage || 0}%</span>
            </div>
            <div className="resource-item">
              <span>内存:</span>
              <div className="usage-bar">
                <div 
                  className="usage-fill memory" 
                  style={{width: `${metrics.memory_usage || 0}%`}}
                ></div>
              </div>
              <span>{metrics.memory_usage || 0}%</span>
            </div>
            <div className="resource-item">
              <span>磁盘:</span>
              <div className="usage-bar">
                <div 
                  className="usage-fill disk" 
                  style={{width: `${metrics.disk_usage || 0}%`}}
                ></div>
              </div>
              <span>{metrics.disk_usage || 0}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* 最近活动 */}
      <div className="recent-activities">
        <h3>最近活动</h3>
        <div className="activities-list">
          {recentActivities.length > 0 ? (
            recentActivities.map((activity, index) => (
              <div key={index} className="activity-item">
                <span className="activity-time">
                  {new Date(activity.timestamp).toLocaleString()}
                </span>
                <span className="activity-type">{activity.type}</span>
                <span className="activity-description">{activity.description}</span>
              </div>
            ))
          ) : (
            <p>暂无活动记录</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
""")
    
    # 推理控制台组件
    with open(f"{frontend_path}/src/components/InferenceConsole.js", "w") as f:
        f.write("""import React, { useState, useEffect } from 'react';

function InferenceConsole() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [inputData, setInputData] = useState('');
  const [inferenceResult, setInferenceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [inferenceHistory, setInferenceHistory] = useState([]);

  useEffect(() => {
    fetchModels();
    fetchInferenceHistory();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/v1/models');
      const data = await response.json();
      setModels(data);
      if (data.length > 0) {
        setSelectedModel(data[0].model_id);
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
    }
  };

  const fetchInferenceHistory = async () => {
    try {
      const response = await fetch('/api/v1/inference/history');
      const data = await response.json();
      setInferenceHistory(data.history || []);
    } catch (error) {
      console.error('获取推理历史失败:', error);
    }
  };

  const handleInference = async () => {
    if (!selectedModel || !inputData) {
      alert('请选择模型并输入数据');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/inference', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          model_id: selectedModel,
          input_data: inputData,
          input_shape: [1, 224, 224, 3]
        })
      });

      const result = await response.json();
      setInferenceResult(result);
      
      // 刷新历史记录
      fetchInferenceHistory();
      
    } catch (error) {
      console.error('推理失败:', error);
      alert('推理失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setInputData(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="inference-console">
      <h2>推理控制台</h2>
      
      <div className="inference-form">
        <div className="form-section">
          <h3>模型选择</h3>
          <select 
            value={selectedModel} 
            onChange={(e) => setSelectedModel(e.target.value)}
            className="model-select"
          >
            {models.map(model => (
              <option key={model.model_id} value={model.model_id}>
                {model.name} ({model.model_type})
              </option>
            ))}
          </select>
          
          {selectedModel && (
            <div className="model-info">
              {models.find(m => m.model_id === selectedModel) && (
                <div>
                  <p><strong>描述:</strong> {models.find(m => m.model_id === selectedModel).description}</p>
                  <p><strong>输入尺寸:</strong> {models.find(m => m.model_id === selectedModel).input_shape.join(' × ')}</p>
                  <p><strong>框架:</strong> {models.find(m => m.model_id === selectedModel).framework}</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="form-section">
          <h3>输入数据</h3>
          <div className="input-options">
            <div className="input-option">
              <label>文件上传:</label>
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileUpload}
                className="file-input"
              />
            </div>
            <div className="input-option">
              <label>或直接输入数据:</label>
              <textarea
                value={inputData}
                onChange={(e) => setInputData(e.target.value)}
                placeholder="输入 base64 编码的图像数据或其他格式数据"
                className="data-input"
                rows={4}
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <button 
            onClick={handleInference}
            disabled={loading || !selectedModel || !inputData}
            className="inference-btn"
          >
            {loading ? '推理中...' : '开始推理'}
          </button>
        </div>
      </div>

      {/* 推理结果 */}
      {inferenceResult && (
        <div className="inference-result">
          <h3>推理结果</h3>
          <div className="result-info">
            <p><strong>任务ID:</strong> {inferenceResult.task_id}</p>
            <p><strong>设备:</strong> {inferenceResult.device}</p>
            <p><strong>推理时间:</strong> {inferenceResult.inference_time}</p>
            <p><strong>置信度:</strong> {inferenceResult.confidence}</p>
          </div>
          
          {inferenceResult.predictions && (
            <div className="predictions">
              <h4>预测结果:</h4>
              <ul>
                {inferenceResult.predictions.map((pred, index) => (
                  <li key={index}>
                    <span className="class-name">{pred.class}</span>
                    <span className="confidence">{(pred.confidence * 100).toFixed(2)}%</span>
                    <div className="confidence-bar">
                      <div 
                        className="confidence-fill" 
                        style={{width: `${pred.confidence * 100}%`}}
                      ></div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 推理历史 */}
      <div className="inference-history">
        <h3>推理历史</h3>
        <div className="history-list">
          {inferenceHistory.length > 0 ? (
            inferenceHistory.slice(0, 10).map((item, index) => (
              <div key={index} className="history-item">
                <span className="history-time">
                  {new Date(item.timestamp).toLocaleString()}
                </span>
                <span className="history-model">{item.model_id}</span>
                <span className="history-device">{item.device}</span>
                <span className="history-time-taken">{item.inference_time}</span>
                <span className={`history-status ${item.status}`}>{item.status}</span>
              </div>
            ))
          ) : (
            <p>暂无推理历史</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default InferenceConsole;
""")
    
    # CSS 样式
    with open(f"{frontend_path}/src/App.css", "w") as f:
        f.write("""/* AI Platform 样式 */
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-left h1 {
  margin: 0;
  font-size: 1.5rem;
}

.system-status {
  margin-top: 0.5rem;
}

.status-indicator {
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-indicator.online {
  background: rgba(76, 175, 80, 0.2);
  color: #4CAF50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.status-indicator.offline {
  background: rgba(244, 67, 54, 0.2);
  color: #F44336;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.logout-btn:hover {
  background: rgba(255,255,255,0.3);
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 250px;
  background: #f8f9fa;
  border-right: 1px solid #e9ecef;
  padding: 1rem 0;
}

.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar li {
  margin: 0.25rem 0;
}

.sidebar button {
  width: 100%;
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.9rem;
}

.sidebar li.active button {
  background: #e3f2fd;
  color: #1976d2;
  border-right: 3px solid #1976d2;
}

.sidebar button:hover {
  background: #f5f5f5;
}

.main-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  background: #fafafa;
}

/* 仪表板样式 */
.dashboard h2 {
  margin-bottom: 2rem;
  color: #333;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.status-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  border: 1px solid #e9ecef;
}

.status-card h3 {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 0.9rem;
  font-weight: 500;
}

.status-card .status {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.status-card .status.online {
  color: #4CAF50;
}

.status-card .status.offline {
  color: #F44336;
}

.status-card .metric-value {
  font-size: 2rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 0.5rem;
}

.status-card p {
  margin: 0;
  color: #666;
  font-size: 0.85rem;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-container {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  border: 1px solid #e9ecef;
}

.chart-container h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
}

.performance-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 1rem;
}

.performance-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s ease;
}

.resource-usage {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.resource-item span:first-child {
  width: 60px;
  font-weight: 500;
  color: #666;
}

.usage-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.usage-fill.cpu {
  background: linear-gradient(90deg, #2196F3, #03A9F4);
}

.usage-fill.memory {
  background: linear-gradient(90deg, #FF9800, #FFC107);
}

.usage-fill.disk {
  background: linear-gradient(90deg, #9C27B0, #E91E63);
}

.resource-item span:last-child {
  width: 50px;
  text-align: right;
  font-weight: 500;
  color: #333;
}

/* 推理控制台样式 */
.inference-console h2 {
  margin-bottom: 2rem;
  color: #333;
}

.inference-form {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.1rem;
}

.model-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.model-info {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.model-info p {
  margin: 0.5rem 0;
  color: #666;
}

.input-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.input-option label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.file-input, .data-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.data-input {
  resize: vertical;
  font-family: monospace;
}

.inference-btn {
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.inference-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.inference-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.inference-result {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.inference-result h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.result-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.result-info p {
  margin: 0;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.predictions ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.predictions li {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.class-name {
  font-weight: 500;
  color: #333;
  min-width: 100px;
}

.confidence {
  font-weight: 600;
  color: #666;
  min-width: 60px;
}

.confidence-bar {
  flex: 1;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s ease;
}

/* 登录表单样式 */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-form {
  background: white;
  padding: 3rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  width: 100%;
  max-width: 400px;
}

.login-form h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #333;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.login-form button {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s;
}

.login-form button:hover:not(:disabled) {
  transform: translateY(-2px);
}

.login-form button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.demo-accounts {
  margin-top: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  font-size: 0.85rem;
  color: #666;
}

.demo-accounts p {
  margin: 0.25rem 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-body {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    order: 2;
  }
  
  .main-content {
    order: 1;
  }
  
  .status-cards {
    grid-template-columns: 1fr;
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
}
""")
    
    # package.json
    with open(f"{frontend_path}/package.json", "w") as f:
        f.write("""{
  "name": "ai-platform-frontend",
  "version": "1.0.0",
  "description": "AI Platform with Hailo8 TPU Support - Frontend",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "axios": "^1.6.0",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",
    "react-router-dom": "^6.8.0",
    "web-vitals": "^3.3.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
""")

def create_backend(backend_path):
    """创建后端 API 服务"""
    # 主应用文件
    with open(f"{backend_path}/src/main.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
AI Platform 后端 API 服务
\"\"\"

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import asyncio
import sys
from pathlib import Path

# 添加 Hailo8 支持
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "hailo8"))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Platform API",
    description="基于 Hailo8 TPU 的 AI 平台后端服务",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 认证
security = HTTPBearer()

# 数据模型
class InferenceRequest(BaseModel):
    model_id: str
    input_data: Any
    input_shape: Optional[List[int]] = [1, 224, 224, 3]
    parameters: Optional[Dict[str, Any]] = {}

class UserLogin(BaseModel):
    username: str
    password: str

# 全局状态
system_status = {
    "hailo8_available": False,
    "temperature": 45,
    "initialized": False
}

inference_history = []
activities = []

# Hailo8 集成
class Hailo8Manager:
    \"\"\"Hailo8 管理器\"\"\"
    
    def __init__(self):
        self.initialized = False
        self.available = False
    
    async def initialize(self):
        \"\"\"初始化 Hailo8\"\"\"
        if self.initialized:
            return self.available
        
        try:
            # 导入 Hailo8 支持
            from hailo8_installer import test_hailo8
            
            # 测试 Hailo8 可用性
            self.available = await asyncio.get_event_loop().run_in_executor(
                None, test_hailo8
            )
            
            system_status["hailo8_available"] = self.available
            system_status["initialized"] = True
            
            if self.available:
                logger.info("Hailo8 TPU 初始化成功")
                activities.append({
                    "timestamp": "2024-01-01T00:00:00Z",
                    "type": "system",
                    "description": "Hailo8 TPU 初始化成功"
                })
            else:
                logger.warning("Hailo8 TPU 不可用")
                activities.append({
                    "timestamp": "2024-01-01T00:00:00Z",
                    "type": "warning",
                    "description": "Hailo8 TPU 不可用，使用 CPU 模式"
                })
            
            self.initialized = True
            return self.available
            
        except Exception as e:
            logger.error(f"Hailo8 初始化失败: {e}")
            system_status["hailo8_available"] = False
            system_status["initialized"] = True
            self.initialized = True
            return False

# 全局 Hailo8 管理器
hailo8_manager = Hailo8Manager()

@app.on_event("startup")
async def startup_event():
    \"\"\"启动事件\"\"\"
    logger.info("启动 AI Platform 后端服务")
    await hailo8_manager.initialize()

# 认证相关
USERS_DB = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    \"\"\"验证令牌\"\"\"
    # 简化的令牌验证
    token = credentials.credentials
    if token in ["admin_token", "user_token"]:
        return {"username": "admin" if token == "admin_token" else "user"}
    raise HTTPException(status_code=401, detail="无效的认证令牌")

# API 路由
@app.get("/")
async def root():
    \"\"\"根路径\"\"\"
    return {
        "service": "AI Platform API",
        "version": "1.0.0",
        "hailo8_available": system_status["hailo8_available"]
    }

@app.get("/api/v1/system/status")
async def get_system_status():
    \"\"\"获取系统状态\"\"\"
    return system_status

@app.post("/api/v1/auth/login")
async def login(request: UserLogin):
    \"\"\"用户登录\"\"\"
    username = request.username
    password = request.password
    
    if username in USERS_DB and USERS_DB[username]["password"] == password:
        # 简化的令牌生成
        token = f"{username}_token"
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": username,
                "role": USERS_DB[username]["role"]
            }
        }
    
    raise HTTPException(status_code=401, detail="用户名或密码错误")

@app.get("/api/v1/auth/me")
async def get_current_user(user: dict = Depends(verify_token)):
    \"\"\"获取当前用户\"\"\"
    return user

@app.get("/api/v1/models")
async def get_models():
    \"\"\"获取模型列表\"\"\"
    return [
        {
            "model_id": "resnet50",
            "name": "ResNet-50",
            "description": "深度残差网络，用于图像分类",
            "model_type": "classification",
            "framework": "pytorch",
            "input_shape": [1, 224, 224, 3],
            "output_shape": [1, 1000]
        },
        {
            "model_id": "mobilenet_v2",
            "name": "MobileNet V2",
            "description": "轻量级卷积神经网络",
            "model_type": "classification",
            "framework": "tensorflow",
            "input_shape": [1, 224, 224, 3],
            "output_shape": [1, 1000]
        },
        {
            "model_id": "yolo_v5",
            "name": "YOLO v5",
            "description": "实时目标检测模型",
            "model_type": "detection",
            "framework": "pytorch",
            "input_shape": [1, 640, 640, 3],
            "output_shape": [1, 25200, 85]
        }
    ]

@app.post("/api/v1/inference")
async def run_inference(
    request: InferenceRequest,
    user: dict = Depends(verify_token)
):
    \"\"\"运行推理\"\"\"
    try:
        # 模拟推理过程
        await asyncio.sleep(0.1)  # 模拟推理时间
        
        result = {
            "task_id": f"task_{len(inference_history) + 1}",
            "status": "completed",
            "model_id": request.model_id,
            "device": "Hailo8 TPU" if system_status["hailo8_available"] else "CPU",
            "inference_time": "0.025s" if system_status["hailo8_available"] else "0.150s",
            "confidence": 0.95,
            "predictions": [
                {"class": "cat", "confidence": 0.95},
                {"class": "dog", "confidence": 0.03},
                {"class": "bird", "confidence": 0.02}
            ]
        }
        
        # 记录推理历史
        inference_history.append({
            "timestamp": "2024-01-01T00:00:00Z",
            "model_id": request.model_id,
            "device": result["device"],
            "inference_time": result["inference_time"],
            "status": "completed",
            "user": user["username"]
        })
        
        # 记录活动
        activities.append({
            "timestamp": "2024-01-01T00:00:00Z",
            "type": "inference",
            "description": f"用户 {user['username']} 使用模型 {request.model_id} 进行推理"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"推理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/inference/history")
async def get_inference_history(user: dict = Depends(verify_token)):
    \"\"\"获取推理历史\"\"\"
    return {"history": inference_history[-20:]}  # 返回最近20条

@app.get("/api/v1/metrics/dashboard")
async def get_dashboard_metrics():
    \"\"\"获取仪表板指标\"\"\"
    return {
        "active_models": 3,
        "total_models": 3,
        "inference_requests_today": len(inference_history),
        "cpu_usage": 45,
        "memory_usage": 60,
        "disk_usage": 35,
        "avg_inference_time": 25 if system_status["hailo8_available"] else 150,
        "throughput": 40 if system_status["hailo8_available"] else 6
    }

@app.get("/api/v1/activities/recent")
async def get_recent_activities():
    \"\"\"获取最近活动\"\"\"
    return {"activities": activities[-10:]}  # 返回最近10条

@app.get("/health")
async def health_check():
    \"\"\"健康检查\"\"\"
    return {
        "status": "healthy",
        "hailo8_available": system_status["hailo8_available"],
        "initialized": system_status["initialized"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""")
    
    # requirements.txt
    with open(f"{backend_path}/requirements.txt", "w") as f:
        f.write("""fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
aiofiles>=23.0.0
""")
    
    # Dockerfile
    with open(f"{backend_path}/Dockerfile", "w") as f:
        f.write("""FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY static/ ./static/
COPY hailo8/ ./hailo8/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
""")

def create_ml_pipeline(pipeline_path):
    """创建机器学习流水线"""
    # 流水线管理器
    with open(f"{pipeline_path}/src/pipeline_manager.py", "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
机器学习流水线管理器
\"\"\"

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml

logger = logging.getLogger(__name__)

class MLPipeline:
    \"\"\"机器学习流水线\"\"\"
    
    def __init__(self, pipeline_id: str, config: Dict[str, Any]):
        self.pipeline_id = pipeline_id
        self.config = config
        self.status = "created"
        self.steps = []
        self.results = {}
    
    async def add_step(self, step_name: str, step_config: Dict[str, Any]):
        \"\"\"添加流水线步骤\"\"\"
        step = {
            "name": step_name,
            "config": step_config,
            "status": "pending",
            "start_time": None,
            "end_time": None,
            "result": None,
            "error": None
        }
        self.steps.append(step)
        logger.info(f"添加步骤 {step_name} 到流水线 {self.pipeline_id}")
    
    async def run(self):
        \"\"\"运行流水线\"\"\"
        logger.info(f"开始运行流水线 {self.pipeline_id}")
        self.status = "running"
        
        try:
            for i, step in enumerate(self.steps):
                await self._run_step(i, step)
                
                if step["status"] == "failed":
                    self.status = "failed"
                    logger.error(f"流水线 {self.pipeline_id} 在步骤 {step['name']} 失败")
                    return
            
            self.status = "completed"
            logger.info(f"流水线 {self.pipeline_id} 运行完成")
            
        except Exception as e:
            self.status = "failed"
            logger.error(f"流水线 {self.pipeline_id} 运行失败: {e}")
""")
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import yaml

logger = logging.getLogger(__name__)

class MLPipeline:
    \"\"\"机器学习流水线\"\"\"
    
    def __init__(self, pipeline_id: str, config: Dict[str, Any]):
        self.pipeline_id = pipeline_id
        self.config = config
        self.status = "created"
        self.steps = []
        self.results = {}
    
    async def add_step(self, step_name: str, step_config: Dict[str, Any]):
        \"\"\"添加流水线步骤\"\"\"
        step = {
            "name": step_name,
            "config": step_config,
            "status": "pending",
            "start_time": None,
            "end_time": None,
            "result": None,
            "error": None
        }
        self.steps.append(step)
        logger.info(f"添加步骤 {step_name} 到流水线 {self.pipeline_id}")
    
    async def run(self):
        \"\"\"运行流水线\"\"\"
        logger.info(f"开始运行流水线 {self.pipeline_id}")
        self.status = "running"
        
        try:
            for i, step in enumerate(self.steps):
                await self._run_step(i, step)
                
                if step["status"] == "failed":
                    self.status = "failed"
                    logger.error(f"流水线 {self.pipeline_id} 在步骤 {step['name']} 失败")
                    return
            
            self.status = "completed"
            logger.info(f"流水线 {self.pipeline_id} 运行完成")
            
        except Exception as e:
            self.status = "failed"
            logger.error(f"流水线 {self.pipeline_id} 运行失败: {e}")
    
    async def _run_step(self, step_index: int, step: Dict[str, Any]):
        \"\"\"运行单个步骤\"\"\"
        step_name = step["name"]
        logger.info(f"运行步骤 {step_name}")
        
        step["status"] = "running"
        step["start_time"] = "2024-01-01T00:00:00Z"
        
        try:
            # 根据步骤类型执行不同操作
            if step_name == "data_preprocessing":
                result = await self._preprocess_data(step["config"])
            elif step_name == "model_training":
                result = await self._train_model(step["config"])
            elif step_name == "model_evaluation":
                result = await self._evaluate_model(step["config"])
            elif step_name == "model_optimization":
                result = await self._optimize_model(step["config"])
            elif step_name == "hailo_compilation":
                result = await self._compile_for_hailo(step["config"])
            elif step_name == "deployment":
                result = await self._deploy_model(step["config"])
            else:
                result = {"message": f"未知步骤类型: {step_name}"}
            
            step["result"] = result
            step["status"] = "completed"
            step["end_time"] = "2024-01-01T00:00:00Z"
            
            logger.info(f"步骤 {step_name} 完成")
            
        except Exception as e:
            step["error"] = str(e)
            step["status"] = "failed"
            step["end_time"] = "2024-01-01T00:00:00Z"
            logger.error(f"步骤 {step_name} 失败: {e}")
    
    async def _preprocess_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"数据预处理\"\"\"
        await asyncio.sleep(2)  # 模拟处理时间
        return {
            "processed_samples": 10000,
            "train_samples": 8000,
            "val_samples": 1000,
            "test_samples": 1000,
            "data_format": "normalized",
            "augmentation_applied": True
        }
    
    async def _train_model(self, config: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"模型训练\"\"\"
        await asyncio.sleep(5)  # 模拟训练时间
        return {
            "epochs": config.get("epochs", 100),
            "final_accuracy": 0.95,
            "final_loss": 0.05,
            "training_time": "2h 30m",
            "model_size": "98.5MB",
            "best_epoch": 85
        }
    
    async def _evaluate_model(self, config: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"模型评估\"\"\"
        await asyncio.sleep(1)  # 模拟评估时间
        return {
            "test_accuracy": 0.94,
            "test_loss": 0.06,
            "precision": 0.93,
            "recall": 0.95,
            "f1_score": 0.94,
            "inference_time_cpu": "150ms",
            "inference_time_gpu": "15ms"
        }
    
    async def _optimize_model(self, config: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"模型优化\"\"\"
        await asyncio.sleep(3)  # 模拟优化时间
        return {
            "optimization_method": config.get("method", "quantization"),
            "original_size": "98.5MB",
            "optimized_size": "24.6MB",
            "compression_ratio": "4:1",
            "accuracy_drop": 0.01,
            "speed_improvement": "3.2x"
        }
    
    async def _compile_for_hailo(self, config: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Hailo 编译\"\"\"
        await asyncio.sleep(4)  # 模拟编译时间
        return {
            "hailo_model_size": "12.3MB",
            "compilation_time": "4m 15s",
            "target_device": "Hailo-8",
            "expected_fps": 120,
            "expected_latency": "8.3ms",
            "power_consumption": "2.5W",
            "compilation_success": True
        }
    
    async def _deploy_model(self, config: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"模型部署\"\"\"
        await asyncio.sleep(2)  # 模拟部署时间
        return {
            "deployment_target": config.get("target", "production"),
            "endpoint_url": "https://api.example.com/v1/inference",
            "model_version": "1.0.0",
            "deployment_time": "2m 30s",
            "health_check": "passed",
            "auto_scaling": True
        }

class PipelineManager:
    \"\"\"流水线管理器\"\"\"
    
    def __init__(self):
        self.pipelines: Dict[str, MLPipeline] = {}
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        \"\"\"加载流水线模板\"\"\"
        return {
            "image_classification": {
                "name": "图像分类流水线",
                "description": "完整的图像分类模型训练和部署流水线",
                "steps": [
                    {"name": "data_preprocessing", "config": {"augmentation": True}},
                    {"name": "model_training", "config": {"epochs": 100, "batch_size": 32}},
                    {"name": "model_evaluation", "config": {"test_split": 0.1}},
                    {"name": "model_optimization", "config": {"method": "quantization"}},
                    {"name": "hailo_compilation", "config": {"target": "hailo8"}},
                    {"name": "deployment", "config": {"target": "production"}}
                ]
            },
            "object_detection": {
                "name": "目标检测流水线",
                "description": "YOLO 目标检测模型训练和部署流水线",
                "steps": [
                    {"name": "data_preprocessing", "config": {"format": "yolo"}},
                    {"name": "model_training", "config": {"epochs": 200, "model": "yolov5"}},
                    {"name": "model_evaluation", "config": {"metrics": ["mAP", "precision", "recall"]}},
                    {"name": "model_optimization", "config": {"method": "pruning"}},
                    {"name": "hailo_compilation", "config": {"target": "hailo8"}},
                    {"name": "deployment", "config": {"target": "edge"}}
                ]
            }
        }
    
    async def create_pipeline(self, pipeline_id: str, template_name: str, custom_config: Optional[Dict[str, Any]] = None) -> MLPipeline:
        \"\"\"创建流水线\"\"\"
        if template_name not in self.templates:
            raise ValueError(f"未知的模板: {template_name}")
        
        template = self.templates[template_name]
        config = template.copy()
        
        if custom_config:
            config.update(custom_config)
        
        pipeline = MLPipeline(pipeline_id, config)
        
        # 添加步骤
        for step_config in template["steps"]:
            await pipeline.add_step(step_config["name"], step_config["config"])
        
        self.pipelines[pipeline_id] = pipeline
        logger.info(f"创建流水线 {pipeline_id} (模板: {template_name})")
        
        return pipeline
    
    async def run_pipeline(self, pipeline_id: str):
        """运行流水线"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"流水线不存在: {pipeline_id}")
        
        pipeline = self.pipelines[pipeline_id]
        await pipeline.run()
        
        return pipeline
    
    def get_pipeline(self, pipeline_id: str) -> Optional[MLPipeline]:
        """获取流水线"""
        return self.pipelines.get(pipeline_id)
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """列出所有流水线"""
        return [
            {
                "pipeline_id": pid,
                "status": pipeline.status,
                "config": pipeline.config,
                "steps_count": len(pipeline.steps)
            }
            for pid, pipeline in self.pipelines.items()
        ]
    
    def get_templates(self) -> Dict[str, Any]:
        """获取模板列表"""
        return self.templates

# 全局流水线管理器实例
pipeline_manager = PipelineManager()
"""