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


// ========== 定时任务管理 0428 ==========

// 加载定时任务列表
async function loadScheduleJobs() {
    try {
        const jobs = await apiFetch('/schedule/jobs');
        const container = document.getElementById('scheduleJobsList');
        
        if (!jobs.length) {
            container.innerHTML = '<div class="text-center text-muted py-3">暂无定时任务，点击上方按钮添加</div>';
            return;
        }
        
        container.innerHTML = jobs.map(job => `
            <div class="card mb-2 job-card">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">
                                ${job.enabled ? '<i class="bi bi-play-circle text-success"></i>' : '<i class="bi bi-pause-circle text-secondary"></i>'}
                                ${escapeHtml(job.name)}
                                <span class="badge ${job.enabled ? 'bg-success' : 'bg-secondary'} ms-2">${job.enabled ? '启用' : '禁用'}</span>
                            </h6>
                            <div class="small text-muted mb-2">
                                <code class="cron-badge">${escapeHtml(job.cron)}</code>
                                <span class="mx-2">|</span>
                                <i class="bi bi-tag"></i> 
                                ${job.keywords && job.keywords.length > 0 
                                    ? (job.keywords.includes('__ALL__') || job.keywords.length === 0
                                        ? '<span class="badge bg-primary">所有关键词</span>'
                                        : job.keywords.map(k => `<span class="badge bg-secondary me-1">${escapeHtml(k)}</span>`).join(''))
                                    : '<span class="badge bg-primary">所有关键词</span>'}
                            </div>
                            ${job.description ? `<div class="small text-muted"><i class="bi bi-file-text"></i> ${escapeHtml(job.description)}</div>` : ''}
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-secondary" onclick="viewJobRunHistory('${job.id}','${escapeHtml(job.name)}')" title="运行记录">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-primary" onclick="editScheduleJob('${job.id}')" title="编辑">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteScheduleJob('${job.id}')" title="删除">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载定时任务失败:', error);
        document.getElementById('scheduleJobsList').innerHTML = '<div class="text-center text-danger py-3">加载失败</div>';
    }
}

// 显示添加任务模态框
function showAddScheduleModal() {
    document.getElementById('scheduleJobModalTitle').textContent = '添加定时任务';
    document.getElementById('editJobId').value = '';
    document.getElementById('jobName').value = '';
    document.getElementById('jobCron').value = '';
    document.getElementById('jobPages').value = '';
    document.getElementById('jobEnabled').checked = true;
    document.getElementById('jobDescription').value = '';
    jobKwPickerSelected.clear();
    document.getElementById('jobKeywordCount').textContent = '所有关键词';
    new bootstrap.Modal(document.getElementById('scheduleJobModal')).show();
}

// 编辑定时任务
window.editScheduleJob = async function(jobId) {
    try {
        const jobs = await apiFetch('/schedule/jobs');
        const job = jobs.find(j => j.id === jobId);
        if (!job) return;

        document.getElementById('scheduleJobModalTitle').textContent = '编辑定时任务';
        document.getElementById('editJobId').value = job.id;
        document.getElementById('jobName').value = job.name;
        document.getElementById('jobCron').value = job.cron;
        document.getElementById('jobPages').value = job.pages || '';
        document.getElementById('jobEnabled').checked = job.enabled;
        document.getElementById('jobDescription').value = job.description || '';

        jobKwPickerSelected.clear();
        if (job.keywords && job.keywords.length > 0 && !job.keywords.includes('__ALL__')) {
            job.keywords.forEach(k => jobKwPickerSelected.add(k));
        }
        document.getElementById('jobKeywordCount').textContent =
            jobKwPickerSelected.size ? `已选 ${jobKwPickerSelected.size} 个关键词` : '所有关键词';

        new bootstrap.Modal(document.getElementById('scheduleJobModal')).show();
    } catch (error) {
        alert('加载失败: ' + error.message);
    }
};

// 定时任务关键词弹窗
let jobKwPickerSelected = new Set();

window.toggleJobKwPanel = function() {
    const panel = document.getElementById('jobKwInlinePanel');
    const hidden = panel.style.display === 'none';
    if (hidden) renderJobKwPickerList(document.getElementById('jobKwPickerSearch').value || '');
    panel.style.display = hidden ? '' : 'none';
};

function renderJobKwPickerList(filter) {
    const list = document.getElementById('jobKwPickerList');
    const filtered = allCustomKeywords.filter(kw => kw.toLowerCase().includes(filter.toLowerCase()));
    list.innerHTML = `<div class="d-flex flex-wrap gap-2 p-2">${
        filtered.map(kw => {
            const sel = jobKwPickerSelected.has(kw);
            return `<span class="badge rounded-pill px-3 py-2" style="cursor:pointer;font-size:13px;font-weight:normal;
                background:${sel ? '#0d6efd' : '#e9ecef'};color:${sel ? '#fff' : '#495057'};border:1px solid ${sel ? '#0d6efd' : '#ced4da'}"
                onclick="jobKwPickerToggle(this,'${escapeHtml(kw)}')">${escapeHtml(kw)}</span>`;
        }).join('')
    }</div>`;
    document.getElementById('jobKwPickerSelectedCount').textContent = jobKwPickerSelected.size;
}

window.jobKwPickerFilter = function(val) { renderJobKwPickerList(val); };

window.jobKwPickerToggle = function(el, kw) {
    if (jobKwPickerSelected.has(kw)) {
        jobKwPickerSelected.delete(kw);
        el.style.background = '#e9ecef'; el.style.color = '#495057'; el.style.borderColor = '#ced4da';
    } else {
        jobKwPickerSelected.add(kw);
        el.style.background = '#0d6efd'; el.style.color = '#fff'; el.style.borderColor = '#0d6efd';
    }
    document.getElementById('jobKwPickerSelectedCount').textContent = jobKwPickerSelected.size;
};

window.jobKwPickerSelectAll = function() {
    const filter = document.getElementById('jobKwPickerSearch').value || '';
    allCustomKeywords.filter(kw => kw.toLowerCase().includes(filter.toLowerCase())).forEach(kw => jobKwPickerSelected.add(kw));
    renderJobKwPickerList(filter);
};

window.jobKwPickerClearAll = function() {
    jobKwPickerSelected.clear();
    renderJobKwPickerList(document.getElementById('jobKwPickerSearch').value || '');
};

window.confirmJobKwPicker = function() {
    document.getElementById('jobKeywordCount').textContent =
        jobKwPickerSelected.size ? `已选 ${jobKwPickerSelected.size} 个关键词` : '所有关键词';
    document.getElementById('jobKwInlinePanel').style.display = 'none';
};

// 加载关键词到选择框（保留兼容）
async function loadKeywordsForSelect() {
    if (!allCustomKeywords.length) {
        const res = await apiFetch('/keywords');
        allCustomKeywords = Array.isArray(res) ? res : (res.keywords || []);
    }
}

// 保存定时任务
window.saveScheduleJob = async function() {
    const jobId = document.getElementById('editJobId').value;
    const name = document.getElementById('jobName').value.trim();
    const cron = document.getElementById('jobCron').value.trim();
    const pages = document.getElementById('jobPages').value;
    const enabled = document.getElementById('jobEnabled').checked;
    const description = document.getElementById('jobDescription').value;
    const selectedKeywords = jobKwPickerSelected.size ? [...jobKwPickerSelected] : ['__ALL__'];

    if (!name) { alert('请输入任务名称'); return; }
    if (!cron) { alert('请输入Cron表达式'); return; }

    const jobData = { name, cron, keywords: selectedKeywords, pages: pages ? parseInt(pages) : null, enabled, description };

    try {
        if (jobId) {
            await apiFetch(`/schedule/jobs/${jobId}`, { method: 'PUT', body: JSON.stringify(jobData) });
        } else {
            await apiFetch('/schedule/jobs', { method: 'POST', body: JSON.stringify(jobData) });
        }
        bootstrap.Modal.getInstance(document.getElementById('scheduleJobModal')).hide();
        loadScheduleJobs();
        addLog('📅 定时任务已更新，将在下次执行时生效', 'info');
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
};

// 删除定时任务
window.deleteScheduleJob = async function(jobId) {
    if (!confirm('确定删除该定时任务吗？')) return;
    try {
        await apiFetch(`/schedule/jobs/${jobId}`, { method: 'DELETE' });
        loadScheduleJobs();
        addLog('📅 定时任务已删除', 'info');
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
};

window.viewJobRunHistory = async function(jobId, jobName) {
    document.getElementById('jobRunHistoryName').textContent = jobName;
    const content = document.getElementById('jobRunHistoryContent');
    content.innerHTML = '<div class="text-center text-muted p-3">加载中...</div>';
    new bootstrap.Modal(document.getElementById('jobRunHistoryModal')).show();
    try {
        const runs = await apiFetch(`/schedule/jobs/${jobId}/runs`);
        if (!runs.length) {
            content.innerHTML = '<div class="text-center text-muted p-3">暂无运行记录</div>';
            return;
        }
        content.innerHTML = runs.map(r => {
            const t = new Date(r.time).toLocaleString('zh-CN');
            const ok = r.status === 'success';
            return `<div class="d-flex align-items-center px-3 py-2 border-bottom">
                <i class="bi ${ok ? 'bi-check-circle text-success' : 'bi-x-circle text-danger'} me-2"></i>
                <span class="small">${t}</span>
                ${r.note ? `<span class="small text-muted ms-2">${escapeHtml(r.note)}</span>` : ''}
            </div>`;
        }).join('');
    } catch (e) {
        content.innerHTML = '<div class="text-center text-danger p-3">加载失败</div>';
    }
};

// 在页面初始化时加载定时任务 0428
// 修改原有的 DOMContentLoaded 事件，添加 loadScheduleJobs 0428



// 自定义爬取
let customUsersData = [];
let allCustomKeywords = [];
let selectedCustomKeywords = new Set();

async function loadCustomPanel() {
    const res = await apiFetch('/keywords');
    allCustomKeywords = Array.isArray(res) ? res : (res.keywords || []);

    const usersRes = await apiFetch('/users');
    customUsersData = Array.isArray(usersRes) ? usersRes : (usersRes.users || []);
    const ownerSelect = document.getElementById('customOwner');
    ownerSelect.innerHTML = '<option value="">-- 选择负责人 --</option>' +
        customUsersData.map(u => `<option value="${u.id}">${escapeHtml(u.name)}</option>`).join('');
}

document.querySelectorAll('input[name="customMode"]').forEach(radio => {
    radio.addEventListener('change', () => {
        const isKeyword = radio.value === 'keyword';
        document.getElementById('customKeywordPanel').style.display = isKeyword ? '' : 'none';
        document.getElementById('customOwnerPanel').style.display = isKeyword ? 'none' : '';
    });
});

// 关键词选择器 modal
window.openKeywordPickerModal = function() {
    renderKwPickerList(document.getElementById('kwPickerSearch').value || '');
    new bootstrap.Modal(document.getElementById('keywordPickerModal')).show();
};

function renderKwPickerList(filter) {
    const list = document.getElementById('kwPickerList');
    const filtered = allCustomKeywords.filter(kw => kw.toLowerCase().includes(filter.toLowerCase()));
    list.innerHTML = `<div class="d-flex flex-wrap gap-2 p-2">${
        filtered.map(kw => {
            const sel = selectedCustomKeywords.has(kw);
            return `<span class="badge rounded-pill px-3 py-2" style="cursor:pointer;font-size:13px;font-weight:normal;
                background:${sel ? '#0d6efd' : '#e9ecef'};color:${sel ? '#fff' : '#495057'};border:1px solid ${sel ? '#0d6efd' : '#ced4da'}"
                onclick="kwPickerToggleTag(this,'${escapeHtml(kw)}')">${escapeHtml(kw)}</span>`;
        }).join('')
    }</div>`;
    document.getElementById('kwPickerSelectedCount').textContent = selectedCustomKeywords.size;
}

window.kwPickerFilter = function(val) { renderKwPickerList(val); };

window.kwPickerToggleTag = function(el, kw) {
    if (selectedCustomKeywords.has(kw)) {
        selectedCustomKeywords.delete(kw);
        el.style.background = '#e9ecef'; el.style.color = '#495057'; el.style.borderColor = '#ced4da';
    } else {
        selectedCustomKeywords.add(kw);
        el.style.background = '#0d6efd'; el.style.color = '#fff'; el.style.borderColor = '#0d6efd';
    }
    document.getElementById('kwPickerSelectedCount').textContent = selectedCustomKeywords.size;
};

window.kwPickerSelectAll = function() {
    const filter = document.getElementById('kwPickerSearch').value || '';
    allCustomKeywords.filter(kw => kw.toLowerCase().includes(filter.toLowerCase()))
        .forEach(kw => selectedCustomKeywords.add(kw));
    renderKwPickerList(filter);
};

window.kwPickerClearAll = function() {
    selectedCustomKeywords.clear();
    renderKwPickerList(document.getElementById('kwPickerSearch').value || '');
};

window.confirmKeywordPicker = function() {
    const count = selectedCustomKeywords.size;
    const eyeBtn = document.getElementById('customKeywordEyeBtn');
    document.getElementById('customKeywordCount').textContent = count ? `已选 ${count} 个关键词` : '未选择';
    eyeBtn.style.display = count ? '' : 'none';
    bootstrap.Modal.getInstance(document.getElementById('keywordPickerModal')).hide();
};

// 负责人关键词查看 modal
window.onCustomOwnerChange = function() {
    const userId = document.getElementById('customOwner').value;
    const user = customUsersData.find(u => String(u.id) === String(userId));
    const preview = document.getElementById('customOwnerKwPreview');
    if (user && user.keywords && user.keywords.length) {
        preview.innerHTML = `共 <strong>${user.keywords.length}</strong> 个关键词
            <button type="button" class="btn btn-sm btn-outline-secondary py-0 px-1" onclick="openOwnerKwDetail()" title="查看关键词"><i class="bi bi-eye"></i></button>`;
    } else {
        preview.innerHTML = userId ? '该负责人暂无关键词' : '';
    }
};

window.openOwnerKwDetail = function() {
    const userId = document.getElementById('customOwner').value;
    const user = customUsersData.find(u => String(u.id) === String(userId));
    if (!user) return;
    document.getElementById('ownerKwDetailContent').innerHTML =
        user.keywords.map(kw => `<span class="badge bg-secondary me-1 mb-1">${escapeHtml(kw)}</span>`).join('');
    new bootstrap.Modal(document.getElementById('ownerKwDetailModal')).show();
};

window.startCustomScrape = async function() {
    const mode = document.querySelector('input[name="customMode"]:checked').value;
    const pages = document.getElementById('customPages').value;
    const statusDiv = document.getElementById('scrapeStatus');

    let keywords = [];
    if (mode === 'keyword') {
        keywords = [...selectedCustomKeywords];
        if (!keywords.length) { alert('请至少选择一个关键词'); return; }
    } else {
        const userId = document.getElementById('customOwner').value;
        if (!userId) { alert('请选择负责人'); return; }
        const user = customUsersData.find(u => String(u.id) === String(userId));
        keywords = user && user.keywords ? user.keywords : [];
        if (!keywords.length) { alert('该负责人暂无关键词'); return; }
    }

    statusDiv.innerHTML = '<div class="alert alert-info"><i class="bi bi-hourglass-split"></i> 自定义任务已提交...</div>';
    try {
        for (const kw of keywords) {
            const params = new URLSearchParams({ keyword: kw });
            if (pages) params.append('pages', pages);
            await apiFetch(`/scrape?${params}`, { method: 'POST' });
        }
        statusDiv.innerHTML = `<div class="alert alert-success"><i class="bi bi-check-circle"></i> 已提交 ${keywords.length} 个关键词爬取任务</div>`;
        addLog(`🚀 自定义爬取已提交：${keywords.join(', ')}`, 'info');
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 提交失败: ${error.message}</div>`;
    }
};

// 页面加载 文件底部：0428更新
document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
    loadCustomPanel();
    startPolling();
    loadScheduleJobs().catch(err => console.error('加载定时任务失败:', err));
});

// 页面关闭时清理
window.addEventListener('beforeunload', () => {
    stopPolling();
});