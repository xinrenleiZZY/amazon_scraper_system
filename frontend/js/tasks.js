let currentTaskPage = 1;
let totalTaskPages = 1;
let currentStatus = '';
let currentKeyword = '';
let tasksRefreshInterval = null;  // 任务列表刷新定时器 ZY0422-xia
let runningTasksInterval = null;   // 运行中任务刷新定时器 ZY0422-xia

// 获取运行中的任务ZY0422-xia
async function loadRunningTasks() {
    try {
        const response = await fetch('/api/tasks?status=running&limit=50');
        const result = await response.json();
        const runningTasks = result.data || [];
        
        const container = document.getElementById('running-tasks-list');
        if (runningTasks.length === 0) {
            container.innerHTML = '<div class="col-12 text-center text-muted">暂无运行中的任务</div>';
            return;
        }
        
        container.innerHTML = runningTasks.map(task => `
            <div class="col-md-4 mb-3">
                <div class="card border-warning h-100">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <h6 class="card-title text-warning">
                                <i class="bi bi-arrow-repeat spin"></i> ${task.keyword}
                            </h6>
                            <span class="badge bg-warning text-dark">运行中</span>
                        </div>
                        <p class="card-text small">
                            <strong>任务ID:</strong> ${task.id}<br>
                            <strong>开始时间:</strong> ${new Date(task.started_at).toLocaleString()}<br>
                            <strong>已抓取:</strong> ${task.total_items || 0} 条
                        </p>
                        <button class="btn btn-sm btn-outline-primary w-100" onclick="viewTaskDetail(${task.id})">
                            <i class="bi bi-eye"></i> 查看详情
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载运行中任务失败:', error);
    }
}
// 添加动画样式ZY0422-xia
function addTaskStyles() {
    if (document.getElementById('task-animation-style')) return;
    
    const style = document.createElement('style');
    style.id = 'task-animation-style';
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .spin {
            display: inline-block;
            animation: spin 1s linear infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .animate-pulse {
            animation: pulse 1.5s ease-in-out infinite;
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 500;
        }
        .status-running {
            background-color: #ffc107;
            color: #000;
            animation: pulse 1.5s ease-in-out infinite;
        }
        .status-completed {
            background-color: #28a745;
            color: #fff;
        }
        .status-failed {
            background-color: #dc3545;
            color: #fff;
        }
        .status-pending {
            background-color: #6c757d;
            color: #fff;
        }
        table tbody tr.table-warning {
            background-color: #fff3cd !important;
        }
    `;
    document.head.appendChild(style);
}

// HTML 转义ZY0422-xia
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 查看任务详情（增加商品列表）
async function viewTaskDetail(taskId) {
    try {
        const taskRes = await fetch(`/api/tasks/${taskId}`);
        const task = await taskRes.json();
        
        // 获取该任务抓取的商品
        const productsRes = await fetch(`/api/results?task_id=${taskId}&limit=100`);
        const productsData = await productsRes.json();
        const products = productsData.data || [];
        
        const modalBody = document.getElementById('taskDetailBody');
        modalBody.innerHTML = `
            <div class="mb-3">
                <h6>任务信息</h6>
                <table class="table table-sm">
                    <tr><th style="width:120px">任务ID</th><td>${task.id}</td></tr>
                    <tr><th>关键词</th><td><strong>${task.keyword}</strong></td></tr>
                    <tr><th>状态</th><td><span class="badge bg-${task.status === 'completed' ? 'success' : task.status === 'running' ? 'warning' : 'secondary'}">${task.status}</span></td></tr>
                    <tr><th>抓取页数</th><td>${task.pages || '自动'}</td></tr>
                    <tr><th>商品数量</th><td>${task.total_items || 0}</td></tr>
                    <tr><th>开始时间</th><td>${new Date(task.started_at).toLocaleString()}</td></tr>
                    <tr><th>完成时间</th><td>${task.completed_at ? new Date(task.completed_at).toLocaleString() : '-'}</td></tr>
                    <tr><th>错误信息</th><td class="text-danger">${task.error_message || '-'}</td></tr>
                </table>
            </div>
            <div>
                <h6>抓取的商品 (${products.length}条)</h6>
                <div class="table-responsive" style="max-height: 300px;">
                    <table class="table table-sm table-striped">
                        <thead>
                            <tr><th>ASIN</th><th>标题</th><th>价格</th><th>类型</th><th>排名</th></tr>
                        </thead>
                        <tbody>
                            ${products.map(p => `
                                <tr>
                                    <td><code>${p.asin || '-'}</code></td>
                                    <td title="${p.title || ''}">${(p.title || '').substring(0, 40)}${(p.title || '').length > 40 ? '...' : ''}</td>
                                    <td>${p.price_current || '-'}</td>
                                    <td><span class="badge bg-secondary">${p.ad_type || 'Organic'}</span></td>
                                    <td>${p.ad_rank || p.organic_rank || '-'}</td>
                                </tr>
                            `).join('')}
                            ${products.length === 0 ? '<tr><td colspan="5" class="text-center">暂无商品数据</td></tr>' : ''}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        new bootstrap.Modal(document.getElementById('taskDetailModal')).show();
    } catch (error) {
        alert('加载详情失败: ' + error.message);
    }
}
function renderTaskPagination() {
    const pagination = document.getElementById('taskPagination');
    if (!pagination) return;
    
    if (totalTaskPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    for (let i = 1; i <= totalTaskPages; i++) {
        html += `<li class="page-item ${i === currentTaskPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="loadTasks(${i}); return false;">${i}</a>
                </li>`;
    }
    pagination.innerHTML = html;
}
// 加载任务列表 zy0422
async function loadTasks(page = 1) {
    console.log('loadTasks 被调用, page:', page);  // 添加日志
    currentTaskPage = page;
    const params = new URLSearchParams({ 
        page: currentTaskPage, 
        limit: 20,
        status: currentStatus,
        keyword: currentKeyword
    });
    
    // 显示加载状态
    const tbody = document.getElementById('tasksTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center"><div class="spinner-border spinner-border-sm me-2"></div>加载中...</td></tr>';
    }
    
    try {
        console.log('请求URL:', `/tasks?${params}`);  // 打印请求URL
        const result = await apiFetch(`/tasks?${params}`);
        console.log('API返回数据:', result);  // 打印返回数据
        
        if (!tbody) {
            console.error('找不到 tasksTableBody 元素');
            return;
        }
        
        // 适配不同的返回数据格式
        let tasks = [];
        let totalPages = 1;
        
        if (result.data && Array.isArray(result.data)) {
            // 格式: { data: [...], total_pages: 5 }
            tasks = result.data;
            totalPages = result.total_pages || result.totalPages || 1;
        } else if (Array.isArray(result)) {
            // 格式: 直接返回数组
            tasks = result;
            totalPages = 1;
        } else if (result.code === 0 && result.data) {
            // 格式: { code: 0, data: { list: [...], total: 100 } }
            tasks = result.data.list || result.data.data || [];
            totalPages = result.data.total_pages || result.data.totalPages || 1;
        } else {
            console.warn('未知的数据格式:', result);
            tasks = [];
        }
        
        console.log('解析后的任务数量:', tasks.length);  // 打印任务数量
        
        if (tasks.length > 0) {
            tbody.innerHTML = tasks.map(task => {
                const duration = task.completed_at ? 
                    Math.round((new Date(task.completed_at) - new Date(task.started_at)) / 1000) : '-';
                const rowClass = task.status === 'running' ? 'table-warning' : '';
                // 使用 escapeHtml 防止XSS攻击
                const keyword = escapeHtml(task.keyword || '');
                return `
                    <tr class="${rowClass}">
                        <td>${task.id}</td>
                        <td><strong>${keyword}</strong></td>
                        <td><span class="status-badge status-${task.status}">${task.status}</span></td>
                        <td>${task.pages || '自动'}</td>
                        <td>${task.total_items || 0}</td>
                        <td>${task.started_at ? new Date(task.started_at).toLocaleString() : '-'}</td>
                        <td>${task.completed_at ? new Date(task.completed_at).toLocaleString() : '-'}</td>
                        <td>${duration !== '-' ? duration + '秒' : '-'}</td>
                        <td>
                            <button class="btn btn-sm btn-info" onclick="viewTaskDetail(${task.id})">
                                <i class="bi bi-eye"></i>
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
            totalTaskPages = totalPages;
            
            // 检查分页函数是否存在
            if (typeof renderTaskPagination === 'function') {
                renderTaskPagination();
            } else {
                console.warn('renderTaskPagination 函数未定义');
            }
        } else {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">暂无任务</td></tr>';
        }
        
        // 同时刷新运行中的任务
        if (typeof loadRunningTasks === 'function') {
            await loadRunningTasks();
        }
        
        // 更新API状态为在线
        const statusEl = document.getElementById('api-status');
        if (statusEl) {
            statusEl.className = 'badge bg-success';
            statusEl.textContent = 'API 在线';
        }
        
    } catch (error) {
        console.error('loadTasks 执行失败:', error);
        console.error('错误详情:', error.stack);
        
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">加载失败: ${error.message}</td></tr>`;
        }
        
        // 更新API状态为离线
        const statusEl = document.getElementById('api-status');
        if (statusEl) {
            statusEl.className = 'badge bg-danger';
            statusEl.textContent = 'API 离线';
        }
    }
}

// 启动自动刷新ZY0422-xia
function startAutoRefresh() {
    // 清除已有定时器
    if (tasksRefreshInterval) clearInterval(tasksRefreshInterval);
    if (runningTasksInterval) clearInterval(runningTasksInterval);
    
    // 任务列表每10秒刷新一次（保持当前页）
    tasksRefreshInterval = setInterval(() => {
        loadTasks(currentTaskPage);
    }, 10000);
    
    // 运行中任务每3秒刷新一次（更实时）
    runningTasksInterval = setInterval(() => {
        loadRunningTasks();
    }, 3000);
}

// 停止自动刷新ZY0422-xia
function stopAutoRefresh() {
    if (tasksRefreshInterval) {
        clearInterval(tasksRefreshInterval);
        tasksRefreshInterval = null;
    }
    if (runningTasksInterval) {
        clearInterval(runningTasksInterval);
        runningTasksInterval = null;
    }
}

// 刷新任务（手动）ZY0422-xia
window.refreshTasks = function() {
    loadTasks(currentTaskPage);
};

// 筛选任务ZY0422-xia
window.filterTasks = function() {
    currentStatus = document.getElementById('taskStatusFilter').value;
    currentKeyword = document.getElementById('taskKeywordFilter').value;
    loadTasks(1);
};

// 查看任务详情ZY0422-xia
window.viewTaskDetail = async function(taskId) {
    try {
        const task = await apiFetch(`/tasks/${taskId}`);
        const modalBody = document.getElementById('taskDetailBody');
        modalBody.innerHTML = `
            <table class="table">
                <tr><th style="width:150px">任务ID</th><td>${task.id}</td></tr>
                <tr><th>关键词</th><td><strong>${escapeHtml(task.keyword)}</strong></td></tr>
                <tr><th>状态</th><td><span class="status-badge status-${task.status}">${task.status}</span></td></tr>
                <tr><th>抓取页数</th><td>${task.pages || '自动'}</td></tr>
                <tr><th>商品数量</th><td>${task.total_items || 0}</td></tr>
                <tr><th>开始时间</th><td>${new Date(task.started_at).toLocaleString()}</td></tr>
                <tr><th>完成时间</th><td>${task.completed_at ? new Date(task.completed_at).toLocaleString() : '-'}</td></tr>
                <tr><th>源文件</th><td>${task.source_file || '-'}</td></tr>
                <tr><th>错误信息</th><td class="text-danger">${task.error_message || '-'}</td></tr>
            </table>
        `;
        new bootstrap.Modal(document.getElementById('taskDetailModal')).show();
    } catch (error) {
        alert('加载详情失败: ' + error.message);
    }
};


// 页面可见性变化时优化刷新（页面不可见时停止刷新，节省资源）
function handleVisibilityChange() {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
        loadTasks(currentTaskPage);  // 立即刷新
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    addTaskStyles();
    loadTasks(1);
    startAutoRefresh();
    
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', handleVisibilityChange);
});

// 页面关闭时清理
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});