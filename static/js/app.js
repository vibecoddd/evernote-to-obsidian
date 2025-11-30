// 全局应用JavaScript

// 全局变量
let currentTheme = 'light';
let notifications = [];

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    // 初始化主题
    initializeTheme();

    // 初始化工具提示
    initializeTooltips();

    // 初始化通知系统
    initializeNotifications();

    // 设置全局错误处理
    setupGlobalErrorHandling();

    // 初始化页面特定功能
    initializePageSpecific();
}

// 主题系统
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
    applyTheme(currentTheme);

    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            currentTheme = e.matches ? 'dark' : 'light';
            applyTheme(currentTheme);
        }
    });
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    // 更新主题按钮状态（如果存在）
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark' ?
            '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', currentTheme);
    applyTheme(currentTheme);
}

// 工具提示初始化
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// 通知系统
function initializeNotifications() {
    // 创建通知容器
    if (!document.getElementById('notificationContainer')) {
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1060';
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const id = 'notification-' + Date.now();
    const typeColors = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };

    const typeIcons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };

    const notification = document.createElement('div');
    notification.id = id;
    notification.className = `toast align-items-center ${typeColors[type]} text-white border-0`;
    notification.setAttribute('role', 'alert');
    notification.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas ${typeIcons[type]} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"
                    data-bs-dismiss="toast"></button>
        </div>
    `;

    document.getElementById('notificationContainer').appendChild(notification);

    // 使用Bootstrap Toast
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(notification, { delay: duration });
        toast.show();

        // 自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration + 500);
    }

    notifications.push(id);
    return id;
}

// 全局错误处理
function setupGlobalErrorHandling() {
    window.addEventListener('error', function(event) {
        console.error('全局错误:', event.error);
        showNotification('发生了一个错误，请刷新页面重试', 'error');
    });

    window.addEventListener('unhandledrejection', function(event) {
        console.error('未处理的Promise拒绝:', event.reason);
        showNotification('网络或服务器错误，请检查连接', 'error');
    });
}

// 页面特定初始化
function initializePageSpecific() {
    const currentPage = getCurrentPage();

    switch(currentPage) {
        case 'index':
            initializeIndexPage();
            break;
        case 'config':
            initializeConfigPage();
            break;
        case 'migrate':
            initializeMigratePage();
            break;
        case 'results':
            initializeResultsPage();
            break;
    }
}

function getCurrentPage() {
    const path = window.location.pathname;
    if (path === '/' || path === '/index') return 'index';
    if (path === '/config') return 'config';
    if (path === '/migrate') return 'migrate';
    if (path === '/results') return 'results';
    return 'unknown';
}

// 首页初始化
function initializeIndexPage() {
    // 添加动画效果
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('animate__animated', 'animate__fadeInUp');
    });
}

// 配置页面初始化
function initializeConfigPage() {
    // 自动保存功能
    const form = document.getElementById('configForm');
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('change', debounce(saveFormData, 1000));
        });
    }

    // 加载保存的表单数据
    loadFormData();
}

// 迁移页面初始化
function initializeMigratePage() {
    // 页面离开确认
    let migrationInProgress = false;

    window.addEventListener('beforeunload', function(e) {
        if (migrationInProgress) {
            const confirmationMessage = '迁移正在进行中，确定要离开吗？';
            e.returnValue = confirmationMessage;
            return confirmationMessage;
        }
    });

    // 全局变量更新
    window.setMigrationStatus = function(status) {
        migrationInProgress = status;
    };
}

// 结果页面初始化
function initializeResultsPage() {
    // 自动刷新结果
    const refreshInterval = 30000; // 30秒
    setInterval(function() {
        const migrationHistory = document.getElementById('migrationHistory');
        if (migrationHistory && !migrationHistory.querySelector('.spinner-border')) {
            // 只在没有加载状态时刷新
            loadMigrationHistory();
        }
    }, refreshInterval);
}

// 工具函数

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 表单数据保存和加载
function saveFormData() {
    const form = document.getElementById('configForm');
    if (form) {
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        // 保存复选框状态
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            data[checkbox.id] = checkbox.checked;
        });

        localStorage.setItem('tempFormData', JSON.stringify(data));
    }
}

function loadFormData() {
    const savedData = localStorage.getItem('tempFormData');
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            const form = document.getElementById('configForm');

            if (form) {
                // 填充表单字段
                Object.keys(data).forEach(key => {
                    const element = form.querySelector(`[name="${key}"], #${key}`);
                    if (element) {
                        if (element.type === 'checkbox') {
                            element.checked = data[key];
                        } else if (element.type === 'radio') {
                            if (element.value === data[key]) {
                                element.checked = true;
                            }
                        } else {
                            element.value = data[key];
                        }
                    }
                });
            }
        } catch (e) {
            console.warn('加载表单数据失败:', e);
        }
    }
}

// API请求封装
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, finalOptions);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API请求失败:', error);
        showNotification(`请求失败: ${error.message}`, 'error');
        throw error;
    }
}

// 文件大小格式化
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 时间格式化
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}小时${minutes}分${remainingSeconds}秒`;
    } else if (minutes > 0) {
        return `${minutes}分${remainingSeconds}秒`;
    } else {
        return `${remainingSeconds}秒`;
    }
}

// 复制到剪贴板
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('已复制到剪贴板', 'success', 2000);
    } catch (err) {
        console.error('复制失败:', err);

        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();

        try {
            document.execCommand('copy');
            showNotification('已复制到剪贴板', 'success', 2000);
        } catch (fallbackErr) {
            showNotification('复制失败，请手动复制', 'error');
        }

        document.body.removeChild(textArea);
    }
}

// 下载文件
function downloadFile(content, filename, contentType = 'text/plain') {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    window.URL.revokeObjectURL(url);
}

// 加载状态管理
function showLoading(element, text = '加载中...') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }

    if (element) {
        element.innerHTML = `
            <div class="text-center py-4">
                <div class="loading-spinner"></div>
                <div class="mt-2">${text}</div>
            </div>
        `;
    }
}

function hideLoading(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }

    if (element) {
        const loadingElement = element.querySelector('.loading-spinner');
        if (loadingElement) {
            loadingElement.parentElement.remove();
        }
    }
}

// 确认对话框
function confirmAction(message, callback, cancelCallback = null) {
    if (confirm(message)) {
        callback();
    } else if (cancelCallback) {
        cancelCallback();
    }
}

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K: 全局搜索
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }

    // Esc: 关闭模态框
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            if (typeof bootstrap !== 'undefined') {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
        });
    }
});

// 导出全局函数到window对象
window.appFunctions = {
    toggleTheme,
    showNotification,
    apiRequest,
    formatFileSize,
    formatDuration,
    copyToClipboard,
    downloadFile,
    showLoading,
    hideLoading,
    confirmAction
};