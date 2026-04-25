let currentPage = 1;
let totalPages = 1;
let usersData = []; // #YU 421

// ========== zy 0423 列配置 ==========
// 所有可用字段 (包括默认显示和可选显示)，以及它们的标签和默认显示状态 
const ALL_COLUMNS = [
    // 基础信息
    { key: 'id', label: 'ID', width: '60px', default: true, group: '基础信息' },
    { key: 'keyword', label: '关键词', width: '120px', default: true, group: '基础信息' },
    { key: 'asin', label: 'ASIN', width: '110px', default: true, group: '基础信息' },
    { key: 'title', label: '标题', width: '300px', default: true, group: '基础信息' },
    { key: 'url', label: '商品链接', width: '200px', default: false, group: '基础信息' },
    
    // 价格信息
    { key: 'price_current', label: '当前价格', width: '90px', default: true, group: '价格信息' },
    { key: 'price_list', label: '原价/划线价', width: '90px', default: false, group: '价格信息' },
    
    // 评分信息
    { key: 'rating_stars', label: '评分', width: '80px', default: true, group: '评分信息' },
    { key: 'rating_count', label: '评论数', width: '100px', default: true, group: '评分信息' },
    
    // 排名位置
    { key: 'page', label: '页码', width: '60px', default: false, group: '排名位置' },
    { key: 'data_index', label: '数据索引', width: '80px', default: false, group: '排名位置' },
    { key: 'index_position', label: '页面位置', width: '90px', default: false, group: '排名位置' },
    { key: 'ad_type', label: '广告类型', width: '100px', default: true, group: '排名位置' },
    { key: 'ad_rank', label: '广告排名', width: '90px', default: false, group: '排名位置' },
    { key: 'organic_rank', label: '自然排名', width: '90px', default: true, group: '排名位置' },
    
    // 商品属性
    { key: 'brand_name', label: '品牌', width: '120px', default: false, group: '商品属性' },
    { key: 'is_prime', label: 'Prime', width: '60px', default: false, group: '商品属性' },
    
    // 图片
    { key: 'image_small', label: '小图', width: '80px', default: false, group: '图片' },
    { key: 'image_large', label: '大图', width: '80px', default: false, group: '图片' },
    
    // 内嵌商品（SB广告特有）
    { key: 'inner_products', label: '内嵌商品', width: '200px', default: false, group: '内嵌商品' },
    { key: 'inner_products_count', label: '内嵌商品数', width: '100px', default: false, group: '内嵌商品' },
    
    // 地理位置
    { key: 'postal_code', label: '邮编', width: '80px', default: false, group: '地理位置' },
    
    // 时间戳
    { key: 'date', label: '日期', width: '100px', default: false, group: '时间戳' },
    { key: 'scraped_at', label: '抓取时间', width: '150px', default: true, group: '时间戳' },
    { key: 'created_at', label: '创建时间', width: '150px', default: false, group: '时间戳' },
    { key: 'updated_at', label: '更新时间', width: '150px', default: false, group: '时间戳' }
];

// 默认显示的列（常用的）zy0423
const DEFAULT_COLUMNS = [
    'keyword', 'asin', 'title', 
    'price_current', 'rating_stars', 'rating_count',
    'ad_type','ad_rank','organic_rank', 'page',
    'index_position','organic_rank', 'inner_products',
    'scraped_at'
];

// 存储当前显示的列
let visibleColumns = [];

// 从 localStorage 加载列配置
function loadColumnSettings() {
    const saved = localStorage.getItem('data_visible_columns');
    if (saved) {
        visibleColumns = JSON.parse(saved);
    } else {
        // 默认只显示 default: true 的列
        visibleColumns = ALL_COLUMNS.filter(col => col.default).map(col => col.key);
    }
    
    // 渲染设置面板
    renderColumnSettingsPanel();
}

// 渲染列设置面板
function renderColumnSettingsPanel() {
    const container = document.getElementById('columnSettingsList');
    if (!container) return;
    
    container.innerHTML = ALL_COLUMNS.map(col => `
        <div class="col-md-4 mb-2">
            <div class="form-check">
                <input class="form-check-input" type="checkbox" 
                       value="${col.key}" 
                       id="col_${col.key}"
                       ${visibleColumns.includes(col.key) ? 'checked' : ''}>
                <label class="form-check-label" for="col_${col.key}">
                    <span class="badge bg-secondary" style="background: #6c757d;">${col.label}</span>
                    <span class="text-muted small ms-1">(${col.key})</span>
                </label>
            </div>
        </div>
    `).join('');
}

// 全选
function selectAllColumns() {
    ALL_COLUMNS.forEach(col => {
        const cb = document.getElementById(`col_${col.key}`);
        if (cb) cb.checked = true;
    });
}

// 全不选
function deselectAllColumns() {
    ALL_COLUMNS.forEach(col => {
        const cb = document.getElementById(`col_${col.key}`);
        if (cb) cb.checked = false;
    });
}

// 恢复默认
function resetToDefaultColumns() {
    const defaultKeys = ALL_COLUMNS.filter(col => col.default).map(col => col.key);
    ALL_COLUMNS.forEach(col => {
        const cb = document.getElementById(`col_${col.key}`);
        if (cb) cb.checked = defaultKeys.includes(col.key);
    });
}

// 保存列设置
function saveColumnSettings() {
    visibleColumns = [];
    ALL_COLUMNS.forEach(col => {
        const cb = document.getElementById(`col_${col.key}`);
        if (cb && cb.checked) {
            visibleColumns.push(col.key);
        }
    });
    localStorage.setItem('data_visible_columns', JSON.stringify(visibleColumns));
    
    // 关闭模态框
    bootstrap.Modal.getInstance(document.getElementById('columnSettingsModal')).hide();
    
    // 重新加载数据
    searchData(currentPage);
}

// 渲染表头（领星风格）
function renderTableHeader() {
    const columns = visibleColumns.map(key => {
        const col = ALL_COLUMNS.find(c => c.key === key);
        const label = col?.label || key;
        return `<th>${label}</th>`;
    }).join('');
    
    return `<tr>${columns}</tr>`;
}

// 渲染数据行
function renderTableRow(item) {
    const cells = visibleColumns.map(key => {
        let value = item[key];
        
        // 特殊格式化
        if (key === 'rating_stars' && value) {   // 1. 评分显示星号
            value = `${value} ★`;
        } else if (key === 'rating_count' && value) {  // 2. 评论数格式化
            value = value.toLocaleString();
        } else if (key === 'ad_type' && value) { // 3. 广告类型徽章 
            let badgeClass = 'bg-secondary';
            if (value === 'Organic') badgeClass = 'bg-success';
            else if (value === 'SP') badgeClass = 'bg-primary';
            else if (value === 'SB') badgeClass = 'bg-info text-dark';
            else if (value === 'SB_Video') badgeClass = 'bg-warning text-dark';
            else if (value === 'Title') badgeClass = 'bg-secondary';
            return `<td><span class="badge ${badgeClass}">${value}</span></td>`;
        }  else if (key === 'is_prime' && value === true) { // 4. Prime 标识
             return `<td><i class="bi bi-check-lg text-primary"></i> Prime</td>`;
        }  else if (key === 'is_prime') { // 4. Prime 标识
             return `<td>-</td>`;
        } else if (key === 'title' && value) {// 5. 标题（带 tooltip 和截断）
            // 标题截断并添加 tooltip
            const truncated = value.length > 50 ? value.substring(0, 50) + '...' : value;
            return `<td title="${escapeHtml(value)}" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(truncated)}</td>`;
        } 
        // 6. 商品链接（SB广告特有，链接很长）
        else if (key === 'url' && value && value !== 'N/A') {
            // 缩短显示
            return `<td><a href="${value}" target="_blank" rel="noopener noreferrer"><i class="bi bi-box-arrow-up-right"></i> 查看</a></td>`;
        }
        else if (key === 'url') {
            return `<td>-</td>`;
        }
        // 7. ASIN（可能多个，用逗号分隔）
        else if (key === 'asin' && value) {
            if (value.includes(',')) {
                // 多个 ASIN 的情况（SB广告）
                const asins = value.split(',');
                const asinBadges = asins.map(a => `<code class="me-1">${a}</code>`).join('');
                return `<td>${asinBadges} <a href="https://www.amazon.com/dp/${asins[0]}" target="_blank" class="text-muted"><i class="bi bi-box-arrow-up-right small"></i></a></td>`;
            }
            return `<td><code>${value}</code> <a href="https://www.amazon.com/dp/${value}" target="_blank" class="text-muted"><i class="bi bi-box-arrow-up-right small"></i></a></td>`;
        } 
        // 8. 关键词加粗
        else if (key === 'keyword' && value) {
            return `<td><strong>${escapeHtml(value)}</strong></td>`;
        }
        // 9. 内嵌商品数量
        else if (key === 'inner_products_count' && value) {
            if (value > 0) {
                return `<td><span class="badge bg-secondary" title="包含 ${value} 个内嵌商品">${value}个商品</span></td>`;
            }
            return `<td>-</td>`;
        }
        // 10. 内嵌商品详情（完整显示）
        else if (key === 'inner_products' && value) {
            try {
                const products = Array.isArray(value) ? value : JSON.parse(value);
                if (products && products.length > 0) {
                    const productList = products.map(p => 
                        `<div class="small">${p.position}. ${escapeHtml(p.title || '').substring(0, 30)}... <span class="text-primary">${p.price || '-'}</span></div>`
                    ).join('');
                    return `<td><span class="badge bg-secondary" style="cursor: pointer;" onclick="showInnerProductsModal(${JSON.stringify(products).replace(/"/g, '&quot;')})">查看详情 (${products.length})</span></td>`;
                }
                return `<td>-</td>`;
            } catch(e) {
                return `<td>-</td>`;
            }
        }
        // 11. 小图预览
        else if (key === 'image_small' && value) {
            return `<td><img src="${value}" style="width: 40px; height: auto; max-height: 40px; object-fit: contain;" onerror="this.style.display='none'"></td>`;
        }
        // 12. 大图链接
        else if (key === 'image_large' && value) {
            return `<td><a href="${value}" target="_blank">查看大图</a></td>`;
        }
        // 13. 品牌名
        else if (key === 'brand_name' && value) {
            return `<td><span class="text-muted">${escapeHtml(value)}</span></td>`;
        }
        // 14. 页面位置组合（index_position）
        else if (key === 'index_position' && value) {
            return `<td><code>${value}</code></td>`;
        }
        // 15. 时间戳格式化
        else if ((key === 'created_at' || key === 'updated_at') && value) {
            value = new Date(value).toLocaleString();
        }
        else if (key === 'scraped_at' && value) {
            value = new Date(value).toLocaleString();
        } 
        else if (key === 'date' && value) {
            value = new Date(value).toLocaleDateString();
        } 
        // 16. 空值处理
        else if (value === undefined || value === null || value === '') {
            value = '-';
        }
        
        // 普通文本，需要转义
        if (typeof value === 'string') {
            return `<td>${escapeHtml(value)}</td>`;
        }
        return `<td>${value}</td>`;
    }).join('');
    
    return `<tr>${cells}</tr>`;
}

// 内嵌商品详情弹窗
function showInnerProductsModal(products) {
    const modalHtml = `
        <div class="modal fade" id="innerProductsModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="bi bi-box"></i> 内嵌商品详情</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-striped">
                                <thead>
                                    <tr><th>位置</th><th>ASIN</th><th>标题</th><th>价格</th></tr>
                                </thead>
                                <tbody>
                                    ${products.map(p => `
                                        <tr>
                                            <td>${p.position}</td>
                                            <td><code>${p.asin || '-'}</code> <a href="https://www.amazon.com/dp/${p.asin}" target="_blank"><i class="bi bi-box-arrow-up-right"></i></a></td>
                                            <td style="max-width: 400px;">${escapeHtml(p.title || '-')}</td>
                                            <td>${p.price || '-'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 移除已存在的模态框
    const existingModal = document.getElementById('innerProductsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 添加并显示
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('innerProductsModal'));
    modal.show();
    
    // 关闭时移除DOM
    document.getElementById('innerProductsModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}
// HTML 转义函数
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
// ========== zy 0423 列配置 ==========
// #YU 421
async function loadUsers() {
    try {
        usersData = await apiFetch('/users');
        const select = document.getElementById('filterUser');
        select.innerHTML = '<option value="">全部人员</option>' +
            usersData.map(u => `<option value="${u.id}">${u.name}</option>`).join('');
    } catch (e) {
        console.error('加载人员失败:', e);
    }
}

// #YU 421
window.onUserChange = function() {
    const userId = document.getElementById('filterUser').value;
    const kwSelect = document.getElementById('filterKeyword');
    if (!userId) { loadKeywords(); return; }
    const user = usersData.find(u => u.id == userId);
    const keywords = user ? user.keywords : [];
    kwSelect.innerHTML = '<option value="">全部关键词</option>' +
        keywords.map(kw => `<option value="${kw}">${kw}</option>`).join('');
    searchData(1); // #YU 421 不强制选第一个，"全部关键词"触发多关键词查询
};

// #zy 加载关键词列表
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
// #zy 加载ASIN列表（用于筛选）
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

// #zy 搜索数据
window.searchData = async function(page = 1) {
    currentPage = page;
    const userId = document.getElementById('filterUser').value; // #YU 421
    const keyword = document.getElementById('filterKeyword').value;
    
    const asin = document.getElementById('filterAsin').value;
    const adType = document.getElementById('filterAdType').value;
    const dateFrom = document.getElementById('filterDateFrom').value;  // 开始日期
    const dateTo = document.getElementById('filterDateTo').value;      // 结束日期
    
    const params = new URLSearchParams({ page: currentPage, limit: 50 });
    if (keyword) params.append('keyword', keyword);
    
    // #YU 421 选了人员但没选具体关键词，查该人所有关键词
    if (userId && !keyword) {
        const user = usersData.find(u => u.id == userId);
        if (user?.keywords?.length) {
            user.keywords.forEach(kw => params.append('keywords', kw));
        }
    }

    if (asin) params.append('asin', asin);
    if (adType) params.append('ad_type', adType);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    
    try {
        const result = await apiFetch(`/results?${params}`);
        const tbody = document.getElementById('dataTableBody');

        const thead = document.querySelector('#dataTable thead'); // #zy0423 渲染表头

        // 加载列配置（如果还没加载）zy0423
        if (visibleColumns.length === 0) {
            loadColumnSettings();
        }
        
        // 渲染表头zy0423
        if (thead) {
            thead.innerHTML = renderTableHeader();
        }

        // #zy0423 原有的静态列渲染逻辑，改为动态列渲染
        // if (result.data && result.data.length > 0) {
        //     tbody.innerHTML = result.data.map(item => {
        //         // 计算页面位置描述
        //         let placement = '';
        //         if (item.ad_type === 'Organic' && item.organic_rank) {
        //             placement = `第${item.page}页第${item.organic_rank}位`;
        //         } else if (item.ad_type !== 'Organic' && item.ad_rank) {
        //             placement = `第${item.page}页第${item.ad_rank}位`;
        //         }
                
        //         return `
        //             <tr>
        //                 <td>${item.id || '-'}</td>
        //                 <td><strong>${item.keyword || '-'}</strong></td>
        //                 <td><code>${item.asin || '-'}</code></td>
        //                 <td title="${item.title || ''}" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
        //                     ${(item.title || '').substring(0, 50)}${(item.title || '').length > 50 ? '...' : ''}
        //                 </td>
        //                 <td>${item.price_current || '-'}</td>
        //                 <td>${item.rating_stars ? item.rating_stars + ' ★' : '-'}</td>
        //                 <td>${item.rating_count ? item.rating_count.toLocaleString() : '-'}</td>
        //                 <td>
        //                     <span class="badge ${item.ad_type === 'Organic' ? 'bg-success' : 'bg-primary'}">
        //                         ${item.ad_type || 'Organic'}
        //                     </span>
        //                 </td>
        //                 <td>${item.ad_rank || '-'}</td>
        //                 <td>${item.organic_rank || '-'}</td>
        //                 <td>${item.page || '-'}</td>
        //                 <td><small>${placement || '-'}</small></td>
        //                 <td><small>${new Date(item.scraped_at).toLocaleString()}</small></td>
        //             </tr>
        //         `;
        //     }).join('');
        //     totalPages = result.total_pages || 1;
        //     renderPagination();
        // } else {
        //     tbody.innerHTML = '<tr><td colspan="10" class="text-center">暂无数据</td></tr>';
        // }

        // #zy0423 使用动态列渲染
        if (result.data && result.data.length > 0) {
            // 使用动态列渲染
            tbody.innerHTML = result.data.map(item => renderTableRow(item)).join('');
            totalPages = result.total_pages || 1;
            renderPagination();
        } else {
            const colSpan = visibleColumns.length || 10;
            tbody.innerHTML = `<tr><td colspan="${colSpan}" class="text-center">暂无数据</td></tr>`;
        }
    } catch (error) {
        console.error('加载数据失败:', error);
        document.getElementById('dataTableBody').innerHTML = '<tr><td colspan="13" class="text-center text-danger">加载失败</td></tr>';
    }
};

// #zy 渲染分页
// 渲染分页（领星风格 - 分页和跳转同一行）
function renderPagination() {
    const container = document.getElementById('paginationContainer');
    if (!container) return;
    
    // 左侧分页按钮
    let buttonsHtml = `
        <button class="page-btn" onclick="searchData(1)" ${currentPage === 1 ? 'disabled' : ''}>
            <i class="bi bi-chevron-double-left"></i>
        </button>
        <button class="page-btn" onclick="searchData(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            <i class="bi bi-chevron-left"></i>
        </button>
    `;
    
    // 显示页码范围
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    startPage = Math.max(1, endPage - 4);
    
    for (let i = startPage; i <= endPage; i++) {
        buttonsHtml += `<button class="page-btn ${currentPage === i ? 'active' : ''}" onclick="searchData(${i})">${i}</button>`;
    }
    
    buttonsHtml += `
        <button class="page-btn" onclick="searchData(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="bi bi-chevron-right"></i>
        </button>
        <button class="page-btn" onclick="searchData(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>
            <i class="bi bi-chevron-double-right"></i>
        </button>
    `;
    
    // 完整布局：左侧分页按钮 + 中间页码信息 + 右侧跳转
    container.innerHTML = `
        <div class="pagination-buttons">${buttonsHtml}</div>
        <div class="page-info">第 ${currentPage} / ${totalPages} 页</div>
        <div class="pagination-jump">
            <span class="text-muted small">跳转到</span>
            <input type="number" id="jumpPage" min="1" max="${totalPages}" placeholder="${currentPage}">
            <button onclick="jumpToPage()">跳转</button>
        </div>
    `;
    
    // 绑定跳转输入框的回车事件
    const jumpInput = document.getElementById('jumpPage');
    if (jumpInput) {
        jumpInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                jumpToPage();
            }
        });
    }
}

// 跳转函数
window.jumpToPage = function() {
    const input = document.getElementById('jumpPage');
    if (!input) return;
    let targetPage = parseInt(input.value);
    if (isNaN(targetPage)) targetPage = 1;
    targetPage = Math.max(1, Math.min(targetPage, totalPages));
    searchData(targetPage);
};

// #YU 421
window.jumpToPage = function() {
    const val = parseInt(document.getElementById('jumpPage').value);
    if (val >= 1 && val <= totalPages) searchData(val);
};

// #zy 重置筛选
window.resetFilters = function() {
    document.getElementById('filterUser').value = ''; // #YU 421
    document.getElementById('filterKeyword').value = '';
    loadKeywords(); // #YU 421 重置关键词列表
    document.getElementById('filterAsin').value = '';
    document.getElementById('filterAdType').value = '';
    document.getElementById('filterDate').value = '';
    searchData(1);
};

// #zy 导出数据
window.exportData = function() {
    const keyword = document.getElementById('filterKeyword').value;
    
    const asin = document.getElementById('filterAsin').value;
    const adType = document.getElementById('filterAdType').value;
    const date = document.getElementById('filterDate').value;
    
    let url = `${API_BASE}/results/export`;
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    if (asin) params.append('asin', asin);
    if (adType) params.append('ad_type', adType);
    if (date) params.append('date', date);
    if (params.toString()) url += '?' + params.toString();

    const a = document.createElement('a');
    a.href = url;
    a.download = 'results.csv';
    a.click();
};

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();           // 添加这一行 - 加载人员列表
    loadKeywords();        // 加载关键词列表
    loadAsinOptions();     // 加载ASIN列表
    loadColumnSettings();  // 加载列配置
    searchData(1);         // 加载数据
});