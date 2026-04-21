// 加载关键词列表
async function loadKeywords() {
    try {
        const res = await apiFetch('/keywords');
        const keywords = Array.isArray(res) ? res : (res.keywords || []);
        const tbody = document.getElementById('keywordsTableBody');

        if (keywords.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">暂无关键词，请添加</td></tr>';
            return;
        }
        
        tbody.innerHTML = keywords.map((kw, idx) => `
            <tr>
                <td>${idx + 1}</td>
                <td>${kw}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteKeyword('${kw}')">
                        <i class="bi bi-trash"></i> 删除
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        document.getElementById('keywordsTableBody').innerHTML = '<tr><td colspan="3" class="text-center text-danger">加载失败</td></tr>';
    }
}

// 添加关键词
async function addKeyword() {
    const keyword = document.getElementById('newKeyword').value.trim();
    if (!keyword) {
        alert('请输入关键词');
        return;
    }
    
    try {
        await apiFetch(`/keywords?keyword=${encodeURIComponent(keyword)}`, {
            method: 'POST'
        });
        
        bootstrap.Modal.getInstance(document.getElementById('keywordModal')).hide();
        document.getElementById('newKeyword').value = '';
        loadKeywords();
    } catch (error) {
        alert('添加失败: ' + error.message);
    }
}

// 删除关键词
window.deleteKeyword = async function(keyword) {
    if (!confirm(`确定删除关键词 "${keyword}" 吗？`)) return;
    
    try {
        await apiFetch(`/keywords?keyword=${encodeURIComponent(keyword)}`, { method: 'DELETE' });
        loadKeywords();
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
};

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
    document.getElementById('saveKeyword').addEventListener('click', addKeyword);
});