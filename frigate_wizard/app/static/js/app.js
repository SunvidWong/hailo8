// Frigate Setup Wizard 主要JavaScript文件

// 全局配置
window.wizardConfig = {
    refreshInterval: 30000, // 30秒刷新一次状态
    toastDuration: 5000,    // Toast显示5秒
    apiTimeout: 30000,      // API超时30秒
    logMaxLines: 1000       // 日志最大行数
};

// 全局变量
let statusCheckInterval;
let toastContainer;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    // 创建Toast容器
    createToastContainer();
    
    // 初始化工具提示
    initializeTooltips();
    
    // 开始状态检查
    startStatusCheck();
    
    // 绑定全局事件
    bindGlobalEvents();
    
    // 检查系统状态
    checkSystemStatus();
    
    console.log('Frigate Setup Wizard initialized');
}

// 创建Toast容器
function createToastContainer() {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
    toastContainer.style.zIndex = '9999';
    document.body.appendChild(toastContainer);
}

// 显示Toast通知
function showToast(message, type = 'info', duration = null) {
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${getToastColor(type)} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${getToastIcon(type)}"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: duration || window.wizardConfig.toastDuration
    });
    
    toast.show();
    
    // 自动移除Toast元素
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// 获取Toast颜色
function getToastColor(type) {
    const colors = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'primary'
    };
    return colors[type] || 'primary';
}

// 获取Toast图标
function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 初始化工具提示
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 开始状态检查
function startStatusCheck() {
    // 立即检查一次
    checkSystemStatus();
    
    // 设置定期检查
    statusCheckInterval = setInterval(() => {
        checkSystemStatus();
    }, window.wizardConfig.refreshInterval);
}

// 检查系统状态
function checkSystemStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicators(data);
        })
        .catch(error => {
            console.error('Error checking system status:', error);
        });
}

// 更新状态指示器
function updateStatusIndicators(statusData) {
    // 更新Docker状态
    updateIndicator('docker', statusData.system?.docker);
    updateIndicator('docker_compose', statusData.system?.docker_compose);
    updateIndicator('python', statusData.system?.python);
    updateIndicator('git', statusData.system?.git);
    
    // 更新Frigate状态
    updateIndicator('frigate_installed', statusData.frigate?.installed);
    updateIndicator('frigate_running', statusData.frigate?.running);
    updateIndicator('frigate_config', statusData.frigate?.config_exists);
    updateIndicator('frigate_web', statusData.frigate?.web_accessible);
    
    // 更新Hailo8状态
    updateIndicator('hailo8_hardware', statusData.hailo8?.hardware_detected);
    updateIndicator('hailo8_driver', statusData.hailo8?.driver_installed);
    updateIndicator('hailo8_runtime', statusData.hailo8?.runtime_available);
    updateIndicator('hailo8_models', statusData.hailo8?.models_available);
}

// 更新单个状态指示器
function updateIndicator(service, status) {
    const indicator = document.querySelector(`[data-service="${service}"]`);
    if (indicator) {
        indicator.className = 'status-indicator ' + (status ? 'status-online' : 'status-offline');
    }
}

// 绑定全局事件
function bindGlobalEvents() {
    // 处理表单提交
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.classList.contains('ajax-form')) {
            e.preventDefault();
            handleAjaxForm(form);
        }
    });
    
    // 处理AJAX链接
    document.addEventListener('click', function(e) {
        const link = e.target.closest('.ajax-link');
        if (link) {
            e.preventDefault();
            handleAjaxLink(link);
        }
    });
    
    // 处理确认对话框
    document.addEventListener('click', function(e) {
        const button = e.target.closest('[data-confirm]');
        if (button) {
            const message = button.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        }
    });
}

// 处理AJAX表单
function handleAjaxForm(form) {
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    const method = form.method || 'POST';
    
    showToast('正在处理请求...', 'info');
    
    fetch(url, {
        method: method,
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || '操作成功', 'success');
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else if (data.reload) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showToast(data.error || '操作失败', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('网络错误', 'error');
    });
}

// 处理AJAX链接
function handleAjaxLink(link) {
    const url = link.href;
    const method = link.getAttribute('data-method') || 'GET';
    const confirm = link.getAttribute('data-confirm');
    
    if (confirm && !window.confirm(confirm)) {
        return;
    }
    
    showToast('正在处理请求...', 'info');
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || '操作成功', 'success');
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            } else if (data.reload) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showToast(data.error || '操作失败', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('网络错误', 'error');
    });
}

// API请求封装
function apiRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        timeout: window.wizardConfig.apiTimeout
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        });
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化时间
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 复制到剪贴板
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('已复制到剪贴板', 'success');
        }).catch(err => {
            console.error('复制失败:', err);
            showToast('复制失败', 'error');
        });
    } else {
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('已复制到剪贴板', 'success');
        } catch (err) {
            console.error('复制失败:', err);
            showToast('复制失败', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// 下载文件
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 防抖函数
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 显示加载状态
function showLoading(element, text = '加载中...') {
    const originalContent = element.innerHTML;
    element.setAttribute('data-original-content', originalContent);
    element.innerHTML = `
        <div class="d-flex align-items-center justify-content-center">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            ${text}
        </div>
    `;
    element.disabled = true;
}

// 隐藏加载状态
function hideLoading(element) {
    const originalContent = element.getAttribute('data-original-content');
    if (originalContent) {
        element.innerHTML = originalContent;
        element.removeAttribute('data-original-content');
    }
    element.disabled = false;
}

// 验证表单
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// 清理资源
function cleanup() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
}

// 页面卸载时清理资源
window.addEventListener('beforeunload', cleanup);

// 导出全局函数
window.wizardApp = {
    showToast,
    apiRequest,
    formatFileSize,
    formatTime,
    formatDate,
    copyToClipboard,
    downloadFile,
    debounce,
    throttle,
    showLoading,
    hideLoading,
    validateForm,
    checkSystemStatus,
    updateStatusIndicators
};

// 控制台欢迎信息
console.log(`
╔══════════════════════════════════════╗
║        Frigate Setup Wizard          ║
║     集成Hailo8 TPU的智能安装向导        ║
╚══════════════════════════════════════╝
版本: 1.0.0
作者: Frigate Setup Wizard Team
`);