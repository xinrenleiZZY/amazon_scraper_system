// #YU 421
let kwTagsMap = {};

// #YU 422 批量导入关键词（关键词总览页面）
window.importKeywords = async function() {
    const file = document.getElementById('importFile').files[0];
    if (!file) { alert('请选择文件'); return; }
    const formData = new FormData();
    formData.append('file', file);
    try {
        // #YU 422 使用 apiFetch 替代直接 fetch，确保请求头正确
        const res = await apiFetch('/keywords/import', { 
            method: 'POST', 
            body: formData,
            headers: {} // #YU 422 FormData 不需要 Content-Type，让浏览器自动设置
        });
        document.getElementById('importResult').innerHTML = `<div class="alert alert-success">导入成功：新增 ${res.imported} 个，共 ${res.total} 个</div>`;
        loadKeywords();
    } catch (e) {
        document.getElementById('importResult').innerHTML = `<div class="alert alert-danger">导入失败: ${e.message}</div>`;
    }
};
// #YU 422 已注释：原使用 fetch 的代码
// const response = await fetch(`${API_BASE}/keywords/import`, { method: 'POST', body: formData });
// if (!response.ok) throw new Error(`HTTP ${response.status}`);
// const res = await response.json();

// #YU 421 加载所有标签
async function loadAllTags(keywords) {
    kwTagsMap = {};
    await Promise.all(keywords.map(async kw => {
        try { kwTagsMap[kw] = await apiFetch(`/keywords/${encodeURIComponent(kw)}/tags`); }
        catch(e) { kwTagsMap[kw] = []; }
    }));
}

//  YU 421
async function loadKeywords() {
    try {
        const res = await apiFetch('/keywords');
        const keywords = Array.isArray(res) ? res : (res.keywords || []);
        await loadAllTags(keywords); // #YU 421
        const tbody = document.getElementById('keywordsTableBody');
        if (keywords.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">暂无关键词，请添加</td></tr>';
            return;
        }
        tbody.innerHTML = keywords.map((kw, idx) => {
            const tags = kwTagsMap[kw] || []; // #YU 421
            const tagBadges = tags.length
                ? tags.map(t => `<span class="badge bg-info text-dark me-1">${t}</span>`).join('')
                : '<span class="text-muted">-</span>';
            return `
            <tr>
                <td>${idx + 1}</td>
                <td>${kw}</td>
                <td>${tagBadges}</td> <!-- #YU 422 只展示标签 -->
                <td>
                    <button class="btn btn-sm btn-success me-1" onclick="editKeyword('${kw}')"> <!-- #YU 421 -->
                        <i class="bi bi-pencil"></i> 修改
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteKeyword('${kw}')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </td>
            </tr>`;
        }).join('');
    } catch (error) {
        document.getElementById('keywordsTableBody').innerHTML = '<tr><td colspan="4" class="text-center text-danger">加载失败</td></tr>';
    }
}

async function addKeyword() {
    const keyword = document.getElementById('newKeyword').value.trim();
    if (!keyword) { alert('请输入关键词'); return; }
    try {
        await apiFetch(`/keywords?keyword=${encodeURIComponent(keyword)}`, { method: 'POST' });
        bootstrap.Modal.getInstance(document.getElementById('keywordModal')).hide();
        document.getElementById('newKeyword').value = '';
        loadKeywords();
    } catch (error) {
        alert('添加失败: ' + error.message);
    }
}

// #YU 421 修改关键词
window.editKeyword = function(keyword) {
    document.getElementById('editOldKeyword').value = keyword;
    document.getElementById('editNewKeyword').value = keyword;
    renderEditTagsList(keyword); // #YU 422
    new bootstrap.Modal(document.getElementById('editKeywordModal')).show();
};

window.deleteKeyword = async function(keyword) {
    if (!confirm(`确定删除关键词 "${keyword}" 吗？`)) return;
    try {
        await apiFetch(`/keywords?keyword=${encodeURIComponent(keyword)}`, { method: 'DELETE' });
        loadKeywords();
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
};

// #YU 422 修改modal中的标签渲染
function renderEditTagsList(keyword) {
    const tags = kwTagsMap[keyword] || [];
    document.getElementById('editTagsList').innerHTML = tags.length
        ? tags.map((t, i) => `<span class="badge bg-info text-dark me-1 mb-1">${t} <span style="cursor:pointer" onclick="removeEditTag(${i})">×</span></span>`).join('')
        : '<span class="text-muted small">暂无标签</span>';
}

window.addEditTag = function() {
    const kw = document.getElementById('editOldKeyword').value;
    const tag = document.getElementById('editNewTag').value.trim();
    if (!tag) return;
    if (!kwTagsMap[kw]) kwTagsMap[kw] = [];
    kwTagsMap[kw].push(tag);
    document.getElementById('editNewTag').value = '';
    renderEditTagsList(kw);
};

window.removeEditTag = function(idx) {
    const kw = document.getElementById('editOldKeyword').value;
    kwTagsMap[kw] = (kwTagsMap[kw] || []).filter((_, i) => i !== idx);
    renderEditTagsList(kw);
};

// #YU 421 标签管理
window.openTags = function(keyword) {
    document.getElementById('tagsModalKw').textContent = keyword;
    renderTagsList(keyword);
    new bootstrap.Modal(document.getElementById('tagsModal')).show();
};

function renderTagsList(keyword) {
    const tags = kwTagsMap[keyword] || [];
    document.getElementById('tagsList').innerHTML = tags.length
        ? tags.map((t, i) => `<div class="d-flex align-items-center mb-1"><span class="flex-grow-1">${t}</span><button class="btn btn-sm btn-outline-danger py-0" onclick="removeTag('${keyword}',${i})"><i class="bi bi-x"></i></button></div>`).join('')
        : '<div class="text-muted">暂无标签</div>';
}

window.addTag = async function() {
    const kw = document.getElementById('tagsModalKw').textContent;
    const tag = document.getElementById('newTag').value.trim();
    if (!tag) return;
    const tags = [...(kwTagsMap[kw] || []), tag];
    await apiFetch(`/keywords/${encodeURIComponent(kw)}/tags`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags) });
    kwTagsMap[kw] = tags;
    document.getElementById('newTag').value = '';
    renderTagsList(kw);
    loadKeywords();
};

window.removeTag = async function(kw, idx) {
    const tags = (kwTagsMap[kw] || []).filter((_, i) => i !== idx);
    await apiFetch(`/keywords/${encodeURIComponent(kw)}/tags`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags) });
    kwTagsMap[kw] = tags;
    renderTagsList(kw);
    loadKeywords();
};

document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
    document.getElementById('saveKeyword').addEventListener('click', addKeyword);
    // #YU 421 确认修改关键词
    document.getElementById('confirmEditKeyword').addEventListener('click', async () => {
        const oldKw = document.getElementById('editOldKeyword').value;
        const newKw = document.getElementById('editNewKeyword').value.trim();
        if (!newKw) return;
        try {
            // 保存标签 #YU 422
            const tags = kwTagsMap[oldKw] || [];
            await apiFetch(`/keywords/${encodeURIComponent(oldKw)}/tags`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags) });
            if (newKw !== oldKw) {
                const res = await apiFetch('/keywords');
                const keywords = Array.isArray(res) ? res : (res.keywords || []);
                const updated = keywords.map(k => k === oldKw ? newKw : k);
                await apiFetch('/keywords', { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(updated) });
            }
            bootstrap.Modal.getInstance(document.getElementById('editKeywordModal')).hide();
            loadKeywords();
        } catch (error) {
            alert('修改失败: ' + error.message);
        }
    });
});
