let currentTaskPage = 1;
let totalTaskPages = 1;
let totalTaskCount = 0;
let currentStatus = '';
let currentKeyword = '';
let currentPageSize = 15;  // 默认每页15条
let tasksRefreshInterval = null;
let runningTasksInterval = null;

// 获取运行中的任务
async function loadRunningTasks() {
    try {
        const response = await fetch('/api/tasks?status=running&limit=50');
        const result = await response.json();
        const runningTasks = result.data || [];
        
        const container = document.getElementById('running-tasks-list');
        if (!container) return;
        
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
                                <i class="bi bi-arrow-repeat spin"></i> ${escapeHtml(task.keyword)}
                            </h6>
                            <span class="badge bg-warning text-dark">运行中</span>
                        </div>
                        <p class="card-text small">
                            <strong>任务ID:</strong> ${task.id}<br>
                            <strong>开始时间:</strong> ${new Date(task.started_at).toLocaleString()}<br>
                            <strong>已抓取:</strong> ${task.total_items || 0} 条
                        </p>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-outline-primary flex-grow-1" onclick="viewTaskDetail(${task.id})">
                                <i class="bi bi-eye"></i> 查看详情
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="showStopPasswordModal(${task.id})" title="终止任务">
                                <i class="bi bi-stop-circle"></i> 终止
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载运行中任务失败:', error);
    }
}

// 显示密码输入模态框
function showStopPasswordModal(taskId) {
    const modalHtml = `
        <div class="modal fade" id="stopTaskPasswordModal" tabindex="-1">
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title"><i class="bi bi-shield-lock"></i> 任务终止验证</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted">正在终止任务 ID: <strong>${taskId}</strong></p>
                        <div class="mb-3">
                            <label class="form-label">请输入操作密码</label>
                            <input type="password" class="form-control" id="stopTaskPassword" placeholder="密码">
                        </div>
                        <div id="stopTaskError" class="text-danger small d-none"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-danger" onclick="confirmStopTask(${taskId})">
                            <i class="bi bi-stop-circle"></i> 确认终止
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('stopTaskPasswordModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('stopTaskPasswordModal'));
    modal.show();
    document.getElementById('stopTaskPassword').focus();
}

// 确认终止任务
window.confirmStopTask = async function(taskId) {
    const password = document.getElementById('stopTaskPassword').value;
    const errorDiv = document.getElementById('stopTaskError');
    
    if (!password) {
        errorDiv.textContent = '请输入密码';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Password': password
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '终止失败');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('stopTaskPasswordModal')).hide();
        showToast('✅ 任务已终止', 'success');
        loadTasks(currentTaskPage);
        loadRunningTasks();
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.classList.remove('d-none');
    }
};

// 添加动画样式
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

// HTML 转义
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 查看商品详情的小窗口
function showProductsDetail() {
    const products = window.currentProducts || [];
    const taskId = window.currentTaskId;
    const keyword = window.currentKeyword || '';
    
    const totalItems = window.currentTaskTotalItems || products.length;

    if (products.length === 0) {
        showToast('暂无商品数据', 'error');
        return;
    }
    
    const modalHtml = `
        <div class="modal fade" id="productsDetailModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-boxes"></i> 关键词详情: ${escapeHtml(keyword)}
                            <span class="badge bg-light text-dark ms-2">任务ID: ${taskId}</span>
                            <span class="badge bg-info ms-2">共 ${products.length} 条商品</span>
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" style="max-height: 500px; overflow-y: auto;">
                        <div class="alert alert-info small mb-2">
                            <i class="bi bi-info-circle"></i> 
                            当前任务共 ${totalItems} 条商品，此处显示 ${products.length} 条（最多显示500条）
                        </div>
                        <div class="table-responsive">
                            <table class="table table-sm table-striped">
                                <thead class="table-dark">
                                    <tr>
                                        <th>#</th>
                                        <th>ASIN</th>
                                        <th>标题</th>
                                        <th>价格</th>
                                        <th>评分</th>
                                        <th>评论数</th>
                                        <th>类型</th>
                                        <th>排名</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${products.map((p, idx) => `
                                        <tr>
                                            <td>${idx + 1} </span></td>
                                            <td><code>${p.asin || '-'}</code> 
                                                ${p.asin ? `<a href="https://www.amazon.com/dp/${p.asin}" target="_blank" class="text-muted"><i class="bi bi-box-arrow-up-right"></i></a>` : ''}
                                            </span>
                                            <td title="${escapeHtml(p.title || '')}" style="max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                                ${escapeHtml((p.title || '-').substring(0, 60))}${(p.title || '').length > 60 ? '...' : ''}
                                            </span>
                                            <td><span class="price-current">${p.price_current || '-'}</span></td>
                                            <td>${p.rating_stars ? p.rating_stars + ' ★' : '-'}</span></td>
                                            <td>${p.rating_count ? p.rating_count.toLocaleString() : '-'}</span></td>
                                            <td><span class="badge ${p.ad_type === 'Organic' ? 'bg-success' : 'bg-primary'}">${p.ad_type || 'Organic'}</span></span>
                                            <td>${p.ad_rank || p.organic_rank || '-'}</span></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                        <button class="btn btn-primary" id="exportProductsBtn">
                            <i class="bi bi-download"></i> 导出CSV
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('productsDetailModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const exportBtn = document.getElementById('exportProductsBtn');
    if (exportBtn) {
        exportBtn.onclick = function() {
            window.open(`/api/results/export?task_id=${taskId}&keyword=${encodeURIComponent(keyword)}`, '_blank');
        };
    }
    
    const modal = new bootstrap.Modal(document.getElementById('productsDetailModal'));
    modal.show();
}

// 导出任务商品数据
window.exportTaskProducts = function(taskId, keyword) {
    window.open(`/api/results/export?task_id=${taskId}&keyword=${encodeURIComponent(keyword)}`, '_blank');
};

// 查看任务详情（完整版）
window.viewTaskDetail = async function(taskId) {
    try {
        const task = await apiFetch(`/tasks/${taskId}`);
        // 获取该任务的实际商品数量
        const taskTotalItems = task.total_items || 0;
        // 获取商品数据 - 使用实际数量或最大限制
        const fetchLimit = Math.min(taskTotalItems, 500); // 最多500条
        const productsRes = await fetch(`/api/results?task_id=${taskId}&limit=${fetchLimit}`);

        const productsData = await productsRes.json();
        const products = productsData.data || [];
        
        window.currentProducts = products;
        window.currentTaskId = task.id;
        window.currentKeyword = task.keyword;
        window.currentTaskTotalItems = taskTotalItems;
        
        const organicCount = products.filter(p => p.ad_type === 'Organic').length;
        const spCount = products.filter(p => p.ad_type === 'SP').length;
        const sbCount = products.filter(p => p.ad_type === 'SB').length;
        const sbVideoCount = products.filter(p => p.ad_type === 'SB_Video').length;
        
        const canStop = task.status === 'running' || task.status === 'pending';
        
        const modalBody = document.getElementById('taskDetailBody');
        modalBody.innerHTML = `
            <div class="mb-3">
                <h6><i class="bi bi-info-circle"></i> 任务信息</h6>
                <table class="table table-sm table-bordered">
                    <tr><th style="width:140px">任务ID</th><td>${task.id}</span></td></tr>
                    <tr>
                        <th>关键词</th>
                        <td>
                            <strong>${escapeHtml(task.keyword)}</strong>
                            <button class="btn btn-sm btn-outline-info ms-2" id="viewAllProductsBtn">
                                <i class="bi bi-eye"></i> 查看全部商品 (${products.length}条)
                            </button>
                         </span>
                     </tr>
                    <tr><th>状态</th><td><span class="status-badge status-${task.status}">${task.status}</span> ${canStop ? '<span class="badge bg-danger ms-2">⚠️ 可终止</span>' : ''}</span> </tr>
                    <tr><th>抓取页数</th><td>${task.pages || '自动'}</span> </tr>
                    <tr>
                        <th>商品数量</th>
                        <td>
                            <strong>${task.total_items || 0}</strong> 条
                            <span class="text-muted ms-2">
                                (有机:${organicCount} | SP:${spCount} | SB:${sbCount} | 视频:${sbVideoCount})
                            </span>
                         </span>
                     </tr>
                    <tr><th>开始时间</th><td>${new Date(task.started_at).toLocaleString()}</span> </tr>
                    <tr><th>完成时间</th><td>${task.completed_at ? new Date(task.completed_at).toLocaleString() : '-'}</span> </tr>
                    <tr><th>运行时长</th><td>${task.completed_at ? Math.round((new Date(task.completed_at) - new Date(task.started_at)) / 1000) + '秒' : '运行中...'}</span> </tr>
                    <tr><th>错误信息</th><td class="text-danger">${task.error_message || '-'}</span> </tr>
                </table>
            </div>
            ${canStop ? `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> 
                <strong>警告：</strong> 终止任务将停止爬取，已抓取的数据会保留。
                <button class="btn btn-danger btn-sm ms-3" id="stopTaskBtn">
                    <i class="bi bi-stop-circle"></i> 终止任务
                </button>
            </div>
            ` : ''}
            <div>
                <h6><i class="bi bi-box"></i> 最新商品 (前20条)</h6>
                <div class="table-responsive" style="max-height: 300px;">
                    <table class="table table-sm table-striped">
                        <thead>
                            <tr><th>ASIN</th><th>标题</th><th>价格</th><th>类型</th><th>排名</th></tr>
                        </thead>
                        <tbody>
                            ${products.slice(0, 20).map(p => `
                                <tr>
                                    <td><code>${p.asin || '-'}</code>
                                        <a href="https://www.amazon.com/dp/${p.asin}" target="_blank" class="text-muted"><i class="bi bi-box-arrow-up-right"></i></a>
                                     </span>
                                    <td title="${p.title || ''}" style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                        ${(p.title || '-').substring(0, 40)}${(p.title || '').length > 40 ? '...' : ''}
                                     </span>
                                    <td><span class="price-current">${p.price_current || '-'}</span><td>
                                    <td><span class="badge ${p.ad_type === 'Organic' ? 'bg-success' : 'bg-primary'}">${p.ad_type || 'Organic'}</span></td>
                                    <td>${p.ad_rank || p.organic_rank || '-'}</td>
                                </tr>
                            `).join('')}
                            ${products.length === 0 ? '<tr><td colspan="5" class="text-center">暂无商品数据</span></td>' : ''}
                        </tbody>
                    </table>
                </div>
                ${products.length > 20 ? `<div class="text-center mt-2"><button class="btn btn-sm btn-outline-primary" id="viewMoreProductsBtn">查看全部 ${products.length} 条商品 <i class="bi bi-arrow-right"></i></button></div>` : ''}
            </div>
        `;
        
        const modalElement = document.getElementById('taskDetailModal');
        const modal = new bootstrap.Modal(modalElement);
        
        setTimeout(() => {
            const viewAllBtn = document.getElementById('viewAllProductsBtn');
            if (viewAllBtn) {
                viewAllBtn.onclick = function() {
                    showProductsDetail();
                };
            }
            
            const viewMoreBtn = document.getElementById('viewMoreProductsBtn');
            if (viewMoreBtn) {
                viewMoreBtn.onclick = function() {
                    showProductsDetail();
                };
            }
            
            const stopBtn = document.getElementById('stopTaskBtn');
            if (stopBtn) {
                stopBtn.onclick = function() {
                    showStopPasswordModal(task.id);
                };
            }
        }, 100);
        
        modal.show();
        
    } catch (error) {
        console.error('加载详情失败:', error);
        alert('加载详情失败: ' + error.message);
    }
};

// 显示提示消息
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.bottom = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.style.marginTop = '10px';
    toast.style.minWidth = '250px';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function renderTaskPagination() {
    const pagination = document.getElementById('taskPagination');
    const totalCountSpan = document.getElementById('taskTotalCount');
    
    if (!pagination) return;
    
    if (totalCountSpan && totalTaskCount > 0) {
        const start = (currentTaskPage - 1) * currentPageSize + 1;
        const end = Math.min(currentTaskPage * currentPageSize, totalTaskCount);
        totalCountSpan.innerHTML = `共 ${totalTaskCount} 条，显示 ${start}-${end}`;
    }
    
    if (totalTaskPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // 上一页
    html += `<li class="page-item ${currentTaskPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadTasks(${currentTaskPage - 1}); return false;">«</a>
    </li>`;
    
    // 页码
    let startPage = Math.max(1, currentTaskPage - 2);
    let endPage = Math.min(totalTaskPages, startPage + 4);
    startPage = Math.max(1, endPage - 4);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${currentTaskPage === i ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadTasks(${i}); return false;">${i}</a>
        </li>`;
    }
    
    // 下一页
    html += `<li class="page-item ${currentTaskPage === totalTaskPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadTasks(${currentTaskPage + 1}); return false;">»</a>
    </li>`;
    
    pagination.innerHTML = html;
}

// 加载任务列表
async function loadTasks(page = 1) {
    currentTaskPage = page;
    const params = new URLSearchParams({ 
        page: currentTaskPage, 
        limit: currentPageSize,
        status: currentStatus,
        keyword: currentKeyword
    });
    
    const tbody = document.getElementById('tasksTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center"><div class="spinner-border spinner-border-sm me-2"></div>加载中...</td></tr>';
    }
    
    try {
        const result = await apiFetch(`/tasks?${params}`);
        
        if (!tbody) {
            console.error('找不到 tasksTableBody 元素');
            return;
        }
        
        let tasks = [];
        let totalPages = 1;
        
        if (result.data && Array.isArray(result.data)) {
            tasks = result.data;
            totalPages = result.total_pages || result.totalPages || 1;
            totalTaskCount = result.total || 0;
        } else if (Array.isArray(result)) {
            tasks = result;
            totalPages = 1;
            totalTaskCount = tasks.length;
        } else {
            tasks = [];
            totalTaskCount = 0;
        }
        
        if (tasks.length > 0) {
            tbody.innerHTML = tasks.map(task => {
                const duration = task.completed_at ? 
                    Math.round((new Date(task.completed_at) - new Date(task.started_at)) / 1000) : '-';
                const rowClass = task.status === 'running' ? 'table-warning' : '';
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
                            ${task.status === 'running' || task.status === 'pending' ? `
                            <button class="btn btn-sm btn-danger ms-1" onclick="showStopPasswordModal(${task.id})" title="终止任务">
                                <i class="bi bi-stop-circle"></i>
                            </button>
                            ` : ''}
                         </td>
                    </tr>
                `;
            }).join('');
            totalTaskPages = totalPages;
            renderTaskPagination();
        } else {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">暂无任务</td></tr>';
            renderTaskPagination();
        }
        
        await loadRunningTasks();
        
        const statusEl = document.getElementById('api-status');
        if (statusEl) {
            statusEl.className = 'badge bg-success';
            statusEl.textContent = 'API 在线';
        }
        
    } catch (error) {
        console.error('loadTasks 执行失败:', error);
        
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">加载失败: ${error.message}</td></tr>`;
        }
        
        const statusEl = document.getElementById('api-status');
        if (statusEl) {
            statusEl.className = 'badge bg-danger';
            statusEl.textContent = 'API 离线';
        }
    }
}

// 切换每页显示数量
function changePageSize() {
    const select = document.getElementById('taskPageSize');
    if (select) {
        currentPageSize = parseInt(select.value);
        currentTaskPage = 1;  // 重置到第一页
        loadTasks(1);
    }
}

// 启动自动刷新
function startAutoRefresh() {
    if (tasksRefreshInterval) clearInterval(tasksRefreshInterval);
    if (runningTasksInterval) clearInterval(runningTasksInterval);
    
    tasksRefreshInterval = setInterval(() => {
        loadTasks(currentTaskPage);
    }, 10000);
    
    runningTasksInterval = setInterval(() => {
        loadRunningTasks();
    }, 3000);
}

// 停止自动刷新
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

// 刷新任务
window.refreshTasks = function() {
    loadTasks(currentTaskPage);
};

// 筛选任务
window.filterTasks = function() {
    currentStatus = document.getElementById('taskStatusFilter').value;
    currentKeyword = document.getElementById('taskKeywordFilter').value;
    currentTaskPage = 1;
    loadTasks(1);
};

// 页面可见性变化
function handleVisibilityChange() {
    if (document.hidden) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
        loadTasks(currentTaskPage);
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    addTaskStyles();
    
    // 绑定分页大小变化事件
    const pageSizeSelect = document.getElementById('taskPageSize');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', changePageSize);
    }
    
    loadTasks(1);
    startAutoRefresh();
    document.addEventListener('visibilitychange', handleVisibilityChange);
});

// 页面关闭时清理
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});

// ========== 终止全部任务 ==========

// 显示终止全部任务的密码输入框
function showStopAllModal() {
    const modalHtml = `
        <div class="modal fade" id="stopAllTasksModal" tabindex="-1">
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title"><i class="bi bi-shield-lock"></i> 批量终止验证</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted"><i class="bi bi-exclamation-triangle text-warning"></i> 
                            此操作将终止所有正在运行的任务</p>
                        <div class="mb-3">
                            <label class="form-label">请输入操作密码</label>
                            <input type="password" class="form-control" id="stopAllPassword" placeholder="密码">
                        </div>
                        <div id="stopAllError" class="text-danger small d-none"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-danger" onclick="confirmStopAllTasks()">
                            <i class="bi bi-stop-circle"></i> 确认终止全部
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('stopAllTasksModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('stopAllTasksModal'));
    modal.show();
    document.getElementById('stopAllPassword').focus();
}

// 确认终止全部任务
window.confirmStopAllTasks = async function() {
    const password = document.getElementById('stopAllPassword').value;
    const errorDiv = document.getElementById('stopAllError');
    
    if (!password) {
        errorDiv.textContent = '请输入密码';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const response = await fetch('/api/tasks/stop-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Password': password
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '终止失败');
        }
        
        const result = await response.json();
        bootstrap.Modal.getInstance(document.getElementById('stopAllTasksModal')).hide();
        showToast(`✅ ${result.message}`, 'success');
        
        // 刷新任务列表
        loadTasks(currentTaskPage);
        loadRunningTasks();
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.classList.remove('d-none');
    }
};

// 修改单个终止函数，使用密码头
window.confirmStopTask = async function(taskId) {
    const password = document.getElementById('stopTaskPassword').value;
    const errorDiv = document.getElementById('stopTaskError');
    
    if (!password) {
        errorDiv.textContent = '请输入密码';
        errorDiv.classList.remove('d-none');
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Password': password
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '终止失败');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('stopTaskPasswordModal')).hide();
        showToast('✅ 任务已终止', 'success');
        loadTasks(currentTaskPage);
        loadRunningTasks();
        
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.classList.remove('d-none');
    }
};