let currentUserId = null;

async function loadUsers() {
    try {
        const users = await apiFetch('/users');
        const tbody = document.getElementById('usersTableBody');
        if (!users.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">暂无人员，请添加</td></tr>';
            return;
        }
        tbody.innerHTML = users.map((u, idx) => `
            <tr>
                <td>${idx + 1}</td>
                <td>${u.name}</td>
                <td><span class="badge bg-secondary">${u.keywords.length}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditUser(${u.id},'${u.name}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="openKeywords(${u.id},'${u.name}')">
                        <i class="bi bi-tags"></i> 关键词
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${u.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch {
        document.getElementById('usersTableBody').innerHTML = '<tr><td colspan="5" class="text-center text-danger">加载失败</td></tr>';
    }
}

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
        loadUsers();
    } catch { alert('保存失败'); }
}

window.deleteUser = async function(id) {
    if (!confirm('确定删除该人员及其所有关键词？')) return;
    try {
        await apiFetch(`/users/${id}`, { method: 'DELETE' });
        loadUsers();
    } catch { alert('删除失败'); }
};

window.openKeywords = async function(userId, userName) {
    currentUserId = userId;
    document.getElementById('keywordsModalTitle').textContent = `${userName} 的关键词`;
    await renderKeywords();
    new bootstrap.Modal(document.getElementById('keywordsModal')).show();
};

async function renderKeywords() {
    const users = await apiFetch('/users');
    const user = users.find(u => u.id === currentUserId);
    const list = document.getElementById('keywordsList');
    if (!user || !user.keywords.length) {
        list.innerHTML = '<li class="list-group-item text-center text-muted">暂无关键词</li>';
        return;
    }
    list.innerHTML = user.keywords.map(kw => `
        <li class="list-group-item d-flex justify-content-between align-items-center">
            ${kw}
            <button class="btn btn-sm btn-outline-danger" onclick="removeKeyword('${kw}')">
                <i class="bi bi-x"></i>
            </button>
        </li>
    `).join('');
}

window.addKeyword = async function() {
    const kw = document.getElementById('newKeyword').value.trim();
    if (!kw) return;
    try {
        await apiFetch(`/users/${currentUserId}/keywords`, { method: 'POST', body: JSON.stringify({ keyword: kw }) });
        document.getElementById('newKeyword').value = '';
        await renderKeywords();
        loadUsers();
    } catch { alert('添加失败'); }
};

window.removeKeyword = async function(kw) {
    try {
        await apiFetch(`/users/${currentUserId}/keywords?keyword=${encodeURIComponent(kw)}`, { method: 'DELETE' });
        await renderKeywords();
        loadUsers();
    } catch { alert('删除失败'); }
};

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    document.getElementById('saveUser').addEventListener('click', saveUser);
});
