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
// 加载ASIN列表（用于筛选）
async function loadAsinOptions() {
    try {
        const result = await apiFetch('/results?limit=500');
        const asins = [...new Set((result.data || []).map(item => item.asin).filter(a => a))];
        const select = document.getElementById('filterAsin');
        select.innerHTML = '<option value="">全部ASIN</option>' + 
            asins.slice(0, 100).map(asin => `<option value="${asin}">${asin}</option>`).join('');
    } catch (error) {
        console.error('加载ASIN列表失败:', error);
    }
}

// 搜索数据
window.searchData = async function(page = 1) {
    currentPage = page;
    const keyword = document.getElementById('filterKeyword').value;
    
    const asin = document.getElementById('filterAsin').value;
    const adType = document.getElementById('filterAdType').value;
    const date = document.getElementById('filterDate').value;
    
    const params = new URLSearchParams({ page: currentPage, limit: 20 });
    if (keyword) params.append('keyword', keyword);
    
    if (asin) params.append('asin', asin);
    if (adType) params.append('ad_type', adType);
    if (date) params.append('date', date);
    
    try {
        const result = await apiFetch(`/results?${params}`);
        const tbody = document.getElementById('dataTableBody');
        if (result.data && result.data.length > 0) {
            tbody.innerHTML = result.data.map(item => {
                // 计算页面位置描述
                let placement = '';
                if (item.ad_type === 'Organic' && item.organic_rank) {
                    placement = `第${item.page}页第${item.organic_rank}位`;
                } else if (item.ad_type !== 'Organic' && item.ad_rank) {
                    placement = `第${item.page}页第${item.ad_rank}位`;
                }
                
                return `
                    <tr>
                        <td>${item.id || '-'}</td>
                        <td><strong>${item.keyword || '-'}</strong></td>
                        <td><code>${item.asin || '-'}</code></td>
                        <td title="${item.title || ''}" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${(item.title || '').substring(0, 50)}${(item.title || '').length > 50 ? '...' : ''}
                        </td>
                        <td>${item.price_current || '-'}</td>
                        <td>${item.rating_stars ? item.rating_stars + ' ★' : '-'}</td>
                        <td>${item.rating_count ? item.rating_count.toLocaleString() : '-'}</td>
                        <td>
                            <span class="badge ${item.ad_type === 'Organic' ? 'bg-success' : 'bg-primary'}">
                                ${item.ad_type || 'Organic'}
                            </span>
                        </td>
                        <td>${item.ad_rank || '-'}</td>
                        <td>${item.organic_rank || '-'}</td>
                        <td>${item.page || '-'}</td>
                        <td><small>${placement || '-'}</small></td>
                        <td><small>${new Date(item.scraped_at).toLocaleString()}</small></td>
                    </tr>
                `;
            }).join('');
            totalPages = result.total_pages || 1;
            renderPagination();
        } else {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center">暂无数据</td></tr>';
        }
    } catch (error) {
        console.error('加载数据失败:', error);
        document.getElementById('dataTableBody').innerHTML = '<tr><td colspan="13" class="text-center text-danger">加载失败</td></tr>';
    }
};

// 渲染分页
function renderPagination() {
    const pagination = document.getElementById('pagination');
    let html = '';
    
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="searchData(${currentPage - 1}); return false;">«</a>
    </li>`;
    
    let startPage = Math.max(1, currentPage - 4);
    let endPage = Math.min(totalPages, startPage + 9);
    startPage = Math.max(1, endPage - 9);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${currentPage === i ? 'active' : ''}">
            <a class="page-link" href="#" onclick="searchData(${i}); return false;">${i}</a>
        </li>`;
    }
    
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="searchData(${currentPage + 1}); return false;">»</a>
    </li>`;
    
    pagination.innerHTML = html;
}


// 重置筛选
window.resetFilters = function() {
    document.getElementById('filterKeyword').value = '';
    
    document.getElementById('filterAsin').value = '';
    document.getElementById('filterAdType').value = '';
    document.getElementById('filterDate').value = '';
    searchData(1);
};

// 导出数据
window.exportData = function() {
    const keyword = document.getElementById('filterKeyword').value;
    
    const asin = document.getElementById('filterAsin').value;
    const adType = document.getElementById('filterAdType').value;
    const date = document.getElementById('filterDate').value;
    
    let url = '/results/export';
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    
    if (asin) params.append('asin', asin);
    if (adType) params.append('ad_type', adType);
    if (date) params.append('date', date);
    if (params.toString()) url += '?' + params.toString();
    
    window.open(url);
};

document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
    loadAsinOptions();
    searchData(1);
});