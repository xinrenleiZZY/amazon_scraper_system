let currentUserId = null;
let allAvailableKeywords = [];      // 所有可用关键词
let currentUserKeywords = [];       // 当前用户的关键词
let keywordPage = 1;
let keywordPageSize = 10;
let keywordTotalPages = 1;

// ========== 人员分页变量 ==========
let usersData = [];                  // 所有人员数据
let userPage = 1;
let userPageSize = 10;
let userTotalPages = 1;

async function loadUsers() {
    try {
        usersData = await apiFetch('/users');
        userTotalPages = Math.ceil(usersData.length / userPageSize);
        renderUsersList();
        renderUserPagination();
    } catch {
        document.getElementById('usersTableBody').innerHTML = '<table><td colspan="4" class="text-center text-danger">加载失败</td></tr>';
    }
}

function renderUsersList() {
    const tbody = document.getElementById('usersTableBody');
    const start = (userPage - 1) * userPageSize;
    const end = start + userPageSize;
    const pageUsers = usersData.slice(start, end);
    
    if (!pageUsers.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">暂无人员，请添加</td></tr>';
        return;
    }
    
    tbody.innerHTML = pageUsers.map((u, idx) => `
        <tr>
            <td>${start + idx + 1}</td>
            <td><i class="bi bi-person-circle text-primary me-2"></i>${escapeHtml(u.name)}</td>
            <td><span class="badge bg-secondary rounded-pill">${u.keywords.length}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditUser(${u.id},'${escapeHtml(u.name)}')" title="编辑">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-success me-1" onclick="openKeywords(${u.id},'${escapeHtml(u.name)}')" title="管理关键词">
                    <i class="bi bi-tags"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${u.id})" title="删除">
                    <i class="bi bi-trash"></i>
                </button>
             </td>
         </tr>
    `).join('');
}

function renderUserPagination() {
    const paginationContainer = document.getElementById('userPaginationContainer');
    if (!paginationContainer) {
        // 动态创建分页容器（如果不存在）
        const cardBody = document.querySelector('#usersTable').closest('.card-body');
        if (!cardBody.querySelector('#userPaginationContainer')) {
            const paginationDiv = document.createElement('div');
            paginationDiv.id = 'userPaginationContainer';
            paginationDiv.className = 'mt-3';
            cardBody.appendChild(paginationDiv);
        }
    }
    
    const container = document.getElementById('userPaginationContainer');
    if (!container) return;
    
    if (userTotalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<nav><ul class="pagination pagination-sm justify-content-center mb-0">';
    
    // 上一页
    html += `<li class="page-item ${userPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="changeUserPage(${userPage - 1}); return false;">«</a>
    </li>`;
    
    // 页码
    let startPage = Math.max(1, userPage - 2);
    let endPage = Math.min(userTotalPages, startPage + 4);
    startPage = Math.max(1, endPage - 4);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${userPage === i ? 'active' : ''}">
            <a class="page-link" href="#" onclick="changeUserPage(${i}); return false;">${i}</a>
        </li>`;
    }
    
    // 下一页
    html += `<li class="page-item ${userPage === userTotalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="changeUserPage(${userPage + 1}); return false;">»</a>
    </li>`;
    
    html += `</ul></nav>`;
    html += `<div class="text-center text-muted small mt-2">共 ${usersData.length} 人，第 ${userPage}/${userTotalPages} 页</div>`;
    
    container.innerHTML = html;
}

window.changeUserPage = function(page) {
    if (page < 1 || page > userTotalPages) return;
    userPage = page;
    renderUsersList();
    renderUserPagination();
};

function openAddUser() {
    document.getElementById('userModalTitle').textContent = '添加人员';
    document.getElementById('editUserId').value = '';
    document.getElementById('userName').value = '';
}

window.openEditUser = function(id, name) {
    document.getElementById('userModalTitle').textContent = '编辑人员';
    document.getElementById('editUserId').value = id;
    document.getElementById('userName').value = name;
    new bootstrap.Modal(document.getElementById('userModal')).show();
};

async function saveUser() {
    const id = document.getElementById('editUserId').value;
    const name = document.getElementById('userName').value.trim();
    if (!name) { alert('请输入姓名'); return; }

    try {
        if (id) {
            await apiFetch(`/users/${id}`, { method: 'PUT', body: JSON.stringify({ name }) });
        } else {
            await apiFetch('/users', { method: 'POST', body: JSON.stringify({ name }) });
        }
        bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
        // 重新加载数据并回到第一页
        userPage = 1;
        await loadUsers();
    } catch { alert('保存失败'); }
}

window.deleteUser = async function(id) {
    if (!confirm('确定删除该人员及其所有关键词？')) return;
    try {
        await apiFetch(`/users/${id}`, { method: 'DELETE' });
        // 重新计算总页数
        usersData = await apiFetch('/users');
        userTotalPages = Math.ceil(usersData.length / userPageSize);
        if (userPage > userTotalPages && userPage > 1) {
            userPage = userTotalPages;
        }
        if (userPage < 1) userPage = 1;
        renderUsersList();
        renderUserPagination();
    } catch { alert('删除失败'); }
};

// 打开关键词管理
window.openKeywords = async function(userId, userName) {
    currentUserId = userId;
    document.getElementById('keywordsModalTitle').innerHTML = `<i class="bi bi-person-badge"></i> ${escapeHtml(userName)} 的关键词管理`;
    
    await loadAvailableKeywords();
    await loadUserKeywords();
    renderAvailableKeywords();
    keywordPage = 1;
    renderCurrentKeywords();
    
    new bootstrap.Modal(document.getElementById('keywordsModal')).show();
};

// 加载所有可用关键词
async function loadAvailableKeywords() {
    try {
        const res = await apiFetch('/keywords');
        allAvailableKeywords = Array.isArray(res) ? res : (res.keywords || []);
    } catch (error) {
        console.error('加载可用关键词失败:', error);
        allAvailableKeywords = [];
    }
}

// 加载当前用户的关键词
async function loadUserKeywords() {
    try {
        const users = await apiFetch('/users');
        const user = users.find(u => u.id === currentUserId);
        currentUserKeywords = user ? user.keywords : [];
        document.getElementById('keywordCount').textContent = currentUserKeywords.length;
    } catch (error) {
        console.error('加载用户关键词失败:', error);
        currentUserKeywords = [];
    }
}

// 渲染可用关键词列表
function renderAvailableKeywords() {
    const container = document.getElementById('availableKeywordsList');
    if (!allAvailableKeywords.length) {
        container.innerHTML = '<div class="text-center text-muted py-2">暂无关键词，请先在关键词管理页面添加</div>';
        return;
    }
    
    const available = allAvailableKeywords.filter(kw => !currentUserKeywords.includes(kw));
    
    if (!available.length) {
        container.innerHTML = '<div class="text-center text-muted py-2">所有关键词都已添加</div>';
        return;
    }
    
    container.innerHTML = `
        <select multiple class="form-select" id="availableKeywordsSelect" size="8" style="border: none;">
            ${available.map(kw => `<option value="${escapeHtml(kw)}">${escapeHtml(kw)}</option>`).join('')}
        </select>
    `;
}

// 批量添加选中的关键词
window.batchAddKeywords = async function() {
    const select = document.getElementById('availableKeywordsSelect');
    if (!select) return;
    
    const selected = Array.from(select.selectedOptions).map(opt => opt.value);
    if (!selected.length) {
        alert('请先选择要添加的关键词（按住 Ctrl 多选）');
        return;
    }
    
    let successCount = 0;
    for (const kw of selected) {
        try {
            await apiFetch(`/users/${currentUserId}/keywords`, { 
                method: 'POST', 
                body: JSON.stringify({ keyword: kw }) 
            });
            successCount++;
        } catch(e) {
            console.error(`添加 ${kw} 失败:`, e);
        }
    }
    
    if (successCount > 0) {
        await loadUserKeywords();
        await loadAvailableKeywords();
        renderAvailableKeywords();
        keywordPage = 1;
        renderCurrentKeywords();
        // 刷新人员列表（不改变页码）
        usersData = await apiFetch('/users');
        renderUsersList();
        renderUserPagination();
        alert(`成功添加 ${successCount} 个关键词`);
    }
};

// 渲染当前用户的关键词（带分页）
function renderCurrentKeywords() {
    const container = document.getElementById('currentKeywordsContainer');
    const paginationDiv = document.getElementById('keywordPagination');
    
    keywordTotalPages = Math.ceil(currentUserKeywords.length / keywordPageSize);
    
    if (currentUserKeywords.length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-4"><i class="bi bi-inbox"></i> 暂无关键词，请从上方添加</div>';
        paginationDiv.style.display = 'none';
        return;
    }
    
    const start = (keywordPage - 1) * keywordPageSize;
    const end = start + keywordPageSize;
    const pageKeywords = currentUserKeywords.slice(start, end);
    
    container.innerHTML = `
        <div class="list-group list-group-flush">
            ${pageKeywords.map(kw => `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span><i class="bi bi-tag text-primary me-2"></i>${escapeHtml(kw)}</span>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeKeyword('${escapeHtml(kw)}')" title="删除">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>
            `).join('')}
        </div>
    `;
    
    if (keywordTotalPages > 1) {
        paginationDiv.style.display = 'block';
        renderKeywordPagination();
    } else {
        paginationDiv.style.display = 'none';
    }
}

// 渲染关键词分页控件
function renderKeywordPagination() {
    const nav = document.getElementById('keywordPageNav');
    let html = '';
    
    html += `<li class="page-item ${keywordPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="changeKeywordPage(${keywordPage - 1}); return false;">«</a>
    </li>`;
    
    let startPage = Math.max(1, keywordPage - 2);
    let endPage = Math.min(keywordTotalPages, startPage + 4);
    startPage = Math.max(1, endPage - 4);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${keywordPage === i ? 'active' : ''}">
            <a class="page-link" href="#" onclick="changeKeywordPage(${i}); return false;">${i}</a>
        </li>`;
    }
    
    html += `<li class="page-item ${keywordPage === keywordTotalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="changeKeywordPage(${keywordPage + 1}); return false;">»</a>
    </li>`;
    
    nav.innerHTML = html;
}

// 切换关键词分页
window.changeKeywordPage = function(page) {
    if (page < 1 || page > keywordTotalPages) return;
    keywordPage = page;
    renderCurrentKeywords();
};

// 添加单个关键词
window.addKeyword = async function() {
    const input = document.getElementById('newKeyword');
    const kw = input.value.trim();
    if (!kw) {
        alert('请输入关键词');
        return;
    }
    
    if (currentUserKeywords.includes(kw)) {
        alert('该关键词已存在');
        input.value = '';
        return;
    }
    
    try {
        await apiFetch(`/users/${currentUserId}/keywords`, { 
            method: 'POST', 
            body: JSON.stringify({ keyword: kw }) 
        });
        input.value = '';
        await loadUserKeywords();
        await loadAvailableKeywords();
        renderAvailableKeywords();
        keywordPage = 1;
        renderCurrentKeywords();
        // 刷新人员列表
        usersData = await apiFetch('/users');
        renderUsersList();
        renderUserPagination();
    } catch (error) {
        alert('添加失败: ' + error.message);
    }
};

// 删除单个关键词
window.removeKeyword = async function(kw) {
    if (!confirm(`确定删除关键词 "${kw}" 吗？`)) return;
    
    try {
        await apiFetch(`/users/${currentUserId}/keywords?keyword=${encodeURIComponent(kw)}`, { method: 'DELETE' });
        await loadUserKeywords();
        await loadAvailableKeywords();
        renderAvailableKeywords();
        
        if (currentUserKeywords.length === 0) {
            keywordPage = 1;
        } else {
            const start = (keywordPage - 1) * keywordPageSize;
            if (start >= currentUserKeywords.length && keywordPage > 1) {
                keywordPage--;
            }
        }
        renderCurrentKeywords();
        // 刷新人员列表
        usersData = await apiFetch('/users');
        renderUsersList();
        renderUserPagination();
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
};

// 工具函数
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    document.getElementById('saveUser').addEventListener('click', saveUser);
});