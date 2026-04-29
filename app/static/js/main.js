/**
 * 主要 JavaScript 模組 — 賽特選房系統
 */

// ============ 工具函式 ============

/**
 * 安全地發送 AJAX 請求
 */
async function makeRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        const data = await response.json();
        return { success: response.ok, data, status: response.status };
    } catch (error) {
        console.error('請求失敗:', error);
        return { success: false, error: error.message, status: 0 };
    }
}

/**
 * 顯示通知
 */
function showNotification(message, type = 'info', duration = 3000) {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show fade-in`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, duration);
}

/**
 * 格式化貨幣 (台幣)
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('zh-TW', {
        style: 'currency',
        currency: 'TWD',
        minimumFractionDigits: 0
    }).format(amount);
}

/**
 * 格式化日期時間
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// ============ 實時監控 ============

/**
 * 定期輪詢監控 API
 */
let monitorInterval = null;

function startMonitoring() {
    // 首次立即查詢
    updateMonitorStatus();
    
    // 之後每 5 秒更新一次
    monitorInterval = setInterval(updateMonitorStatus, 5000);
}

async function updateMonitorStatus() {
    // 僅在主控台頁面執行
    if (!window.location.pathname.includes('dashboard') && window.location.pathname !== '/') {
        return;
    }
    
    const result = await makeRequest('/api/monitor/status');
    
    if (result.success && result.data.data) {
        const status = result.data.data;
        
        // 更新 DOM 中的監控數據
        updateDashboardUI(status);
    } else if (result.status === 401) {
        // 會話過期，導向登入
        window.location.href = '/login';
    }
}

function updateDashboardUI(status) {
    // 更新房間表格（如果存在）
    const roomsTable = document.getElementById('roomsTable');
    if (roomsTable && status.room_status) {
        roomsTable.innerHTML = status.room_status.map(room => `
            <tr>
                <td><strong>${room.room_code}</strong></td>
                <td>${room.room_name}</td>
                <td>
                    <span class="badge" style="background-color: ${room.win_rate >= 55 ? '#28a745' : room.win_rate >= 50 ? '#007bff' : '#ffc107'};">
                        ${room.win_rate.toFixed(1)}%
                    </span>
                </td>
                <td>${room.current_odds.toFixed(2)}</td>
                <td><small>${new Date(room.last_updated).toLocaleTimeString('zh-TW')}</small></td>
            </tr>
        `).join('');
    }
    
    // 更新警告容器（如果存在）
    const alertsContainer = document.getElementById('alertsContainer');
    if (alertsContainer && status.recent_alerts) {
        if (status.recent_alerts.length === 0) {
            alertsContainer.innerHTML = '<p class="text-muted">目前無警告</p>';
        } else {
            alertsContainer.innerHTML = status.recent_alerts.map(alert => `
                <div class="alert alert-warning alert-dismissible fade show" role="alert">
                    <strong>${alert.type}：</strong> ${alert.message}
                    <br>
                    <small class="text-muted">${alert.created_at}</small>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `).join('');
        }
    }
}

function stopMonitoring() {
    if (monitorInterval) {
        clearInterval(monitorInterval);
        monitorInterval = null;
    }
}

// ============ 設定表單 ============

/**
 * 初始化設定表單提交處理
 */
function initSettingsForm() {
    const settingsForm = document.getElementById('settingsForm');
    if (!settingsForm) return;
    
    settingsForm.addEventListener('submit', handleSettingsSubmit);
}

async function handleSettingsSubmit(e) {
    e.preventDefault();
    
    const formData = {
        daily_target: parseFloat(document.getElementById('dailyTarget').value),
        target_type: 'amount',
        stop_loss_amount: parseFloat(document.getElementById('stopLoss').value) || null,
        auto_play_enabled: document.getElementById('autoPlay')?.checked || false
    };
    
    // 驗證
    if (!formData.daily_target || formData.daily_target <= 0) {
        showNotification('每日出金目標必須大於 0', 'error');
        return;
    }
    
    const result = await makeRequest('/api/settings', {
        method: 'POST',
        body: JSON.stringify(formData)
    });
    
    if (result.success) {
        showNotification('✅ 設定保存成功！', 'success', 2000);
        // 2 秒後重新載入以更新頁面
        setTimeout(() => location.reload(), 2000);
    } else {
        const errorMsg = result.data?.error || result.error || '設定保存失敗';
        showNotification(`❌ ${errorMsg}`, 'error', 3000);
    }
}

// ============ 頁面初始化 ============

document.addEventListener('DOMContentLoaded', () => {
    // 初始化設定表單
    initSettingsForm();
    
    // 主控台頁面啟動即時監控
    if (window.location.pathname.includes('dashboard') || window.location.pathname === '/') {
        startMonitoring();
    }
});

// 頁面卸載時停止監控
window.addEventListener('beforeunload', () => {
    stopMonitoring();
});

// ============ 調試工具 ============

window.debug = {
    formatCurrency,
    formatDateTime,
    makeRequest,
    showNotification
};
