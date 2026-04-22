let logPollingInterval = null;
let lastRunningTasks = [];
let logRefreshInterval = null; // ZY0422-xia

// 加载关键词列表
async function loadKeywords() {
    try {
        const res = await apiFetch('/keywords');
        const keywords = Array.isArray(res) ? res : (res.keywords || []);
        const select = document.getElementById('scrapeKeyword');
        select.innerHTML = '<option value="">-- 所有关键词 --</option>' +
            keywords.map(kw => `<option value="${kw}">${kw}</option>`).join('');
    } catch (error) {
        console.error('加载关键词失败:', error);
    }
}

// 添加日志到控制台
function addLog(message, type = 'info') {
    const container = document.getElementById('log-container');
    if (!container) {
        console.log(`[${type}] ${message}`);
        return;
    }
    
    const time = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    
    let color = '#d4d4d4';
    if (message.includes('✅')) color = '#4ec9b0';
    if (message.includes('❌')) color = '#f48771';
    if (message.includes('🚀')) color = '#569cd6';
    if (message.includes('📅')) color = '#ce9178';
    if (message.includes('⚠️')) color = '#f0ad4e';
    if (message.includes('INFO')) color = '#9cdcfe';
    if (message.includes('ERROR')) color = '#f48771';
    if (message.includes('WARNING')) color = '#f0ad4e';
    
    logEntry.style.color = color;
    logEntry.style.fontFamily = 'monospace';
    logEntry.style.fontSize = '12px';
    logEntry.style.margin = '2px 0';
    logEntry.innerHTML = `<span style="color: #858585;">[${time}]</span> ${escapeHtml(message)}`; // zy0422
    
    container.appendChild(logEntry);
    container.scrollTop = container.scrollHeight;
    
    // 限制日志条数
    while (container.children.length > 500) {  // 200 to 500 zy0422
        container.removeChild(container.firstChild);
    }
}

// HTML 转义 zy 0422
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// 从 API 获取日志 zy 0422
async function fetchLogsFromAPI() {
    try {
        const response = await apiFetch('/logs?lines=50');
        if (response && response.logs && response.logs.length > 0) {
            // 清空并重新显示最新日志
            const container = document.getElementById('log-container');
            if (container) {
                container.innerHTML = '';
                response.logs.forEach(line => {
                    if (line.trim()) {
                        addLogFromAPI(line.trim());
                    }
                });
            }
        }
    } catch (error) {
        console.error('获取日志失败:', error);
    }
}

// 从 API 添加日志（不带时间戳，因为日志已有） zy 0422
function addLogFromAPI(message) {
    const container = document.getElementById('log-container');
    if (!container) return;
    
    const logEntry = document.createElement('div');
    
    let color = '#d4d4d4';
    if (message.includes('✅')) color = '#4ec9b0';
    if (message.includes('❌')) color = '#f48771';
    if (message.includes('🚀')) color = '#569cd6';
    if (message.includes('📅')) color = '#ce9178';
    if (message.includes('⚠️')) color = '#f0ad4e';
    if (message.includes('INFO')) color = '#9cdcfe';
    if (message.includes('ERROR')) color = '#f48771';
    if (message.includes('WARNING')) color = '#f0ad4e';
    
    logEntry.style.color = color;
    logEntry.style.fontFamily = 'monospace';
    logEntry.style.fontSize = '12px';
    logEntry.style.margin = '2px 0';
    logEntry.innerHTML = escapeHtml(message);
    
    container.appendChild(logEntry);
    container.scrollTop = container.scrollHeight;
    
    // 限制日志条数
    while (container.children.length > 500) {
        container.removeChild(container.firstChild);
    }
}
// 启动日志轮询 zy 0422
function startLogPolling() {
    if (logRefreshInterval) clearInterval(logRefreshInterval);
    // 每3秒获取一次最新日志
    logRefreshInterval = setInterval(fetchLogsFromAPI, 3000);
    // 立即执行一次
    fetchLogsFromAPI();
}

// 停止日志轮询 zy 0422
function stopLogPolling() {
    if (logRefreshInterval) {
        clearInterval(logRefreshInterval);
        logRefreshInterval = null;
    }
}

// 检查任务状态（轮询）zy 0422
async function checkTasksStatus() {
    try {
        const response = await fetch('/api/tasks?limit=20');
        const result = await response.json();
        const tasks = result.data || [];
        
        // 获取运行中的任务
        const runningTasks = tasks.filter(t => t.status === 'running');
        
        // 检查是否有新任务开始
        const currentRunningIds = runningTasks.map(t => t.id);
        const previousRunningIds = lastRunningTasks.map(t => t.id);
        
        // 新任务开始
        const newTasks = runningTasks.filter(t => !previousRunningIds.includes(t.id));
        for (const task of newTasks) {
            addLog(`🚀 新任务开始: ${task.keyword} (ID: ${task.id})`, 'info');
        }
        
        // 任务完成
        const completedTasks = lastRunningTasks.filter(t => !currentRunningIds.includes(t.id));
        for (const task of completedTasks) {
            const updatedTask = tasks.find(t => t.id === task.id);
            if (updatedTask && updatedTask.status === 'completed') {
                addLog(`✅ 任务完成: ${task.keyword} - 共 ${updatedTask.total_items || 0} 条数据`, 'success');
            } else if (updatedTask && updatedTask.status === 'failed') {
                addLog(`❌ 任务失败: ${task.keyword} - ${updatedTask.error_message || '未知错误'}`, 'error');
            }
        }
        
        lastRunningTasks = runningTasks;
        
        // 更新状态显示
        const statusDiv = document.getElementById('scrapeStatus');
        if (statusDiv) {
            if (runningTasks.length > 0) {
                statusDiv.innerHTML = `
                    <div class="alert alert-info">
                        <i class="bi bi-arrow-repeat spin"></i> 
                        正在运行 ${runningTasks.length} 个任务: ${runningTasks.map(t => t.keyword).join(', ')}
                    </div>
                `;
            } else {
                statusDiv.innerHTML = '<div class="text-center text-muted">暂无运行中的任务</div>';
            }
        }
        
    } catch (error) {
        console.error('检查任务状态失败:', error);
    }
}
// 开始爬取
window.startScrape = async function() {
    const keyword = document.getElementById('scrapeKeyword').value;
    const pages = document.getElementById('scrapePages').value;
    
    let url = '/scrape';
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    if (pages) params.append('pages', pages);
    if (params.toString()) url += '?' + params.toString();
    
    const statusDiv = document.getElementById('scrapeStatus');
    statusDiv.innerHTML = '<div class="alert alert-info"><i class="bi bi-hourglass-split"></i> 任务已提交，正在执行...</div>';
    
    try {
        const result = await apiFetch(url, { method: 'POST' });
        statusDiv.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> ${result.message}</div>`;
     } catch (error) { // zy 0422-xia 添加错误处理
        statusDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 启动失败: ${error.message}</div>`;
        addLog(`❌ 启动失败: ${error.message}`, 'error');
    }
};

// 触发每日任务
window.triggerDaily = async function() {
    try {
        await apiFetch('/scrape/daily', { method: 'POST' });
        alert('每日任务已触发');
    } catch (error) {
        alert('触发失败: ' + error.message);
    }
};

// 触发每周任务
window.triggerWeekly = async function() {
    try {
        await apiFetch('/scrape/weekly', { method: 'POST' });
        alert('每周任务已触发');
    } catch (error) {
        alert('触发失败: ' + error.message);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
});

// 启动轮询
function startPolling() {
    if (logPollingInterval) clearInterval(logPollingInterval);
    // 每3秒检查一次
    logPollingInterval = setInterval(checkTasksStatus, 3000);
    // 立即执行一次
    checkTasksStatus();
    // 启动日志轮询 zy0422
    startLogPolling(); 
}

// 停止轮询
function stopPolling() {
    if (logPollingInterval) {
        clearInterval(logPollingInterval);
        logPollingInterval = null;
    }
    stopLogPolling(); // zyzy0422
}

// 页面加载
document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
    startPolling();
});

// 页面关闭时清理
window.addEventListener('beforeunload', () => {
    stopPolling();
});