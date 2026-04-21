let currentPage = 1;
let totalPages = 1;

// 加载关键词列表
async function loadKeywords() {
    try {
        const res = await apiFetch('/keywords');
        const keywords = Array.isArray(res) ? res : (res.keywords || []);
        const select = document.getElementById('filterKeyword');
        select.innerHTML = '<option value="">全部关键词</option>' +
            keywords.map(kw => `<option value="${kw}">${kw}</option>`).join('');
    } catch (error) {
        console.error('加载关键词失败:', error);
    }
}

// 搜索数据
window.searchData = async function(page = 1) {
    currentPage = page;
    const keyword = document.getElementById('filterKeyword').value;
    const adType = document.getElementById('filterAdType').value;
    const date = document.getElementById('filterDate').value;
    
    const params = new URLSearchParams({ page: currentPage, limit: 20 });
    if (keyword) params.append('keyword', keyword);
    if (adType) params.append('ad_type', adType);
    if (date) params.append('date', date);
    
    try {
        const result = await apiFetch(`/results?${params}`);
        const tbody = document.getElementById('dataTableBody');
        
        if (result.data && result.data.length > 0) {
            tbody.innerHTML = result.data.map(item => `
                <tr>
                    <td>${item.id || '-'}</td>
                    <td>${item.keyword || '-'}</td>
                    <td><code>${item.asin || '-'}</code></td>
                    <td title="${item.title || ''}">${(item.title || '').substring(0, 50)}${(item.title || '').length > 50 ? '...' : ''}</td>
                    <td>${item.price_current || '-'}</td>
                    <td>${item.rating_stars || '-'}</td>
                    <td>${item.rating_count || '-'}</td>
                    <td><span class="badge bg-secondary">${item.ad_type || '-'}</span></td>
                    <td>${item.organic_rank || item.ad_rank || '-'}</td>
                    <td>${new Date(item.scraped_at).toLocaleString()}</td>
                </tr>
            `).join('');
            totalPages = result.total_pages || 1;
            renderPagination();
        } else {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center">暂无数据</td></tr>';
        }
    } catch (error) {
        document.getElementById('dataTableBody').innerHTML = '<tr><td colspan="10" class="text-center text-danger">加载失败</td></tr>';
    }
};

// 渲染分页
function renderPagination() {
    const pagination = document.getElementById('pagination');
    let html = '';
    
    // 上一页
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="searchData(${currentPage - 1}); return false;">«</a>
    </li>`;
    
    // 页码
    for (let i = 1; i <= totalPages && i <= 10; i++) {
        html += `<li class="page-item ${currentPage === i ? 'active' : ''}">
            <a class="page-link" href="#" onclick="searchData(${i}); return false;">${i}</a>
        </li>`;
    }
    
    // 下一页
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="searchData(${currentPage + 1}); return false;">»</a>
    </li>`;
    
    pagination.innerHTML = html;
}

// 重置筛选
window.resetFilters = function() {
    document.getElementById('filterKeyword').value = '';
    document.getElementById('filterAdType').value = '';
    document.getElementById('filterDate').value = '';
    searchData(1);
};

// 导出数据
window.exportData = function() {
    const keyword = document.getElementById('filterKeyword').value;
    const adType = document.getElementById('filterAdType').value;
    const date = document.getElementById('filterDate').value;
    
    let url = '/results/export';
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    if (adType) params.append('ad_type', adType);
    if (date) params.append('date', date);
    if (params.toString()) url += '?' + params.toString();
    
    window.open(url);
};

document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
    searchData(1);
});