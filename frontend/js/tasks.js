let currentTaskPage = 1;
let totalTaskPages = 1;
let currentStatus = '';
let currentKeyword = '';

// 获取运行中的任务
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

// 加载任务列表
async function loadTasks(page = 1) {
    currentTaskPage = page;
    const params = new URLSearchParams({ 
        page: currentTaskPage, 
        limit: 20,
        status: currentStatus,
        keyword: currentKeyword
    });
    
    try {
        const result = await apiFetch(`/tasks?${params}`);
        const tbody = document.getElementById('tasksTableBody');
        
        if (result.data && result.data.length > 0) {
            tbody.innerHTML = result.data.map(task => {
                const duration = task.completed_at ? 
                    Math.round((new Date(task.completed_at) - new Date(task.started_at)) / 1000) : '-';
                return `
                    <tr>
                        <td>${task.id}</td>
                        <td>${task.keyword}</td>
                        <td><span class="status-badge status-${task.status}">${task.status}</span></td>
                        <td>${task.pages || '自动'}</td>
                        <td>${task.total_items || 0}</td>
                        <td>${new Date(task.started_at).toLocaleString()}</td>
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
            totalTaskPages = result.total_pages || 1;
            renderTaskPagination();
        } else {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">暂无任务</td></tr>';
        }
        // 同时刷新运行中的任务
        await loadRunningTasks();
    } catch (error) {
        document.getElementById('tasksTableBody').innerHTML = '<tr><td colspan="9" class="text-center text-danger">加载失败</td></tr>';
    }
}

// 渲染分页
function renderTaskPagination() {
    const pagination = document.getElementById('taskPagination');
    let html = '';
    
    html += `<li class="page-item ${currentTaskPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadTasks(${currentTaskPage - 1}); return false;">«</a>
    </li>`;
    
    for (let i = 1; i <= totalTaskPages && i <= 10; i++) {
        html += `<li class="page-item ${currentTaskPage === i ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadTasks(${i}); return false;">${i}</a>
        </li>`;
    }
    
    html += `<li class="page-item ${currentTaskPage === totalTaskPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadTasks(${currentTaskPage + 1}); return false;">»</a>
    </li>`;
    
    pagination.innerHTML = html;
}

// 刷新任务
window.refreshTasks = function() {
    loadTasks(currentTaskPage);
};

// 筛选任务
window.filterTasks = function() {
    currentStatus = document.getElementById('taskStatusFilter').value;
    currentKeyword = document.getElementById('taskKeywordFilter').value;
    loadTasks(1);
};

// 查看任务详情
window.viewTaskDetail = async function(taskId) {
    try {
        const task = await apiFetch(`/tasks/${taskId}`);
        const modalBody = document.getElementById('taskDetailBody');
        modalBody.innerHTML = `
            <table class="table">
                <tr><th style="width:150px">任务ID</th><td>${task.id}</td></tr>
                <tr><th>关键词</th><td>${task.keyword}</td></tr>
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

document.addEventListener('DOMContentLoaded', () => {
    loadTasks(1);
    // 每30秒自动刷新
    setInterval(() => loadTasks(currentTaskPage), 30000);
});

// 添加 CSS 动画
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spin {
        display: inline-block;
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);

// 每5秒刷新运行中的任务
setInterval(() => {
    if (document.getElementById('running-tasks-list')) {
        loadRunningTasks();
    }
}, 5000);