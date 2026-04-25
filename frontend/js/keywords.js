let usersData = []; // #YU 421
let kwOwnersMap = {}; // #YU 421 keyword → [name, ...]
let kwTagsMap = {}; // #YU 421 keyword → [tag, ...]

let kwFestivalMap = {}; // #zy 424 keyword → festival (节日)
let kwFestivalTypeMap = {}; // keyword → festival_type (大/小节日)
let kwHotSeasonMap = {}; // keyword → hot_season (热卖期)
// #YU 421
async function loadUsersForKeywords() {
    try {
        usersData = await apiFetch('/users');
        // 构建 n:n 映射
        kwOwnersMap = {};
        usersData.forEach(u => u.keywords.forEach(kw => {
            if (!kwOwnersMap[kw]) kwOwnersMap[kw] = [];
            kwOwnersMap[kw].push(u.name);
        }));
        // 填充人员下拉
        const select = document.getElementById('filterUser');
        select.innerHTML = '<option value="">全部人员</option>' +
            usersData.map(u => `<option value="${u.id}">${u.name}</option>`).join('');
    } catch (e) {
        console.error('加载人员失败:', e);
    }
}

// YU 421 加载关键词列表
async function loadKeywords(filterKeywords = null) {
    try {
        const res = await apiFetch('/keywords');
        let keywords = Array.isArray(res) ? res : (res.keywords || []);
        if (filterKeywords !== null) {
            keywords = keywords.filter(kw => filterKeywords.includes(kw));
        }
        await loadAllTags(keywords); // #YU 421
        await loadAllFestivals(keywords);      // 加载节日
        await loadAllFestivalTypes(keywords);  // 加载大/小节日
        await loadAllHotSeasons(keywords);     // 加载热卖期

        const tbody = document.getElementById('keywordsTableBody');
        if (keywords.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">暂无关键词</td></tr>';
            return;
        }
        tbody.innerHTML = keywords.map((kw, idx) => {
            const owners = kwOwnersMap[kw] || [];
            const ownerBadges = owners.length
                ? owners.map(n => `<span class="badge bg-secondary me-1">${n}</span>`).join('')
                : '<span class="text-muted">-</span>';
            
            // #YU 421
            const tags = kwTagsMap[kw] || []; 
            const tagBadges = tags.length
                ? tags.map(t => `<span class="badge bg-info text-dark me-1">${t}</span>`).join('')
                : '<span class="text-muted">-</span>';
            
             // ===== zy0424 新增字段 =====
            const festival = kwFestivalMap[kw] || '';
            const festivalBadge = festival ? `<span class="badge bg-primary me-1">${festival}</span>` : '<span class="text-muted">-</span>';
            
            const festivalType = kwFestivalTypeMap[kw] || '';
            let festivalTypeBadge = '';
            if (festivalType === '大节日') {
                festivalTypeBadge = `<span class="badge bg-danger me-1">${festivalType}</span>`;
            } else if (festivalType === '小节日') {
                festivalTypeBadge = `<span class="badge bg-warning text-dark me-1">${festivalType}</span>`;
            } else {
                festivalTypeBadge = '<span class="text-muted">-</span>';
            }
            
            const hotSeason = kwHotSeasonMap[kw] || '';
            let hotSeasonBadge = '';
            if (hotSeason) {
                hotSeasonBadge = `<span class="badge bg-info me-1">${hotSeason}</span>`;
            } else {
                hotSeasonBadge = '<span class="text-muted">-</span>';
            }
            // =====zy0424 新增字段结束 =====
            
            return `
            <tr>
                <td>${idx + 1}</td>
                <td>${kw}</td>
               
                <!-- #YU 421 -->
                <td>${tagBadges}</td> <!-- #YU 422 只展示标签 -->
               
                <td>${festivalBadge}</td> <!-- #zy0424 展示节日 -->
                <td>${festivalTypeBadge}</td>   <!-- #zy0424 展示节日类型 -->
                <td>${hotSeasonBadge}</td><!-- #zy0424 展示热卖期 -->

                <td>${ownerBadges}</td>
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
        document.getElementById('keywordsTableBody').innerHTML = '<tr><td colspan="8" class="text-center text-danger">加载失败</td></tr>';
    }  
}

// ===== 新增：加载节日 =====
async function loadAllFestivals(keywords) {
    kwFestivalMap = {};
    await Promise.all(keywords.map(async kw => {
        try { 
            const data = await apiFetch(`/keywords/festival?keyword=${encodeURIComponent(kw)}`);
            kwFestivalMap[kw] = data || '';
        } catch(e) { 
            kwFestivalMap[kw] = ''; 
        }
    }));
}

// 加载大/小节日
async function loadAllFestivalTypes(keywords) {
    kwFestivalTypeMap = {};
    await Promise.all(keywords.map(async kw => {
        try { 
            const data = await apiFetch(`/keywords/festival-type?keyword=${encodeURIComponent(kw)}`);
            kwFestivalTypeMap[kw] = data || '';
        } catch(e) { 
            kwFestivalTypeMap[kw] = ''; 
        }
    }));
}

// 加载热卖期
async function loadAllHotSeasons(keywords) {
    kwHotSeasonMap = {};
    await Promise.all(keywords.map(async kw => {
        try { 
            const data = await apiFetch(`/keywords/hot-season?keyword=${encodeURIComponent(kw)}`);
            kwHotSeasonMap[kw] = data || '';
        } catch(e) { 
            kwHotSeasonMap[kw] = ''; 
        }
    }));
}

// #ZY 加载关键词列表
async function loadKeywords_old_旧版本列表() {
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

// #YU 421
window.onUserFilter = function() {
    const userId = document.getElementById('filterUser').value;
    if (!userId) { loadKeywords(); return; }
    const user = usersData.find(u => u.id == userId);
    loadKeywords(user ? user.keywords : []);
};

// #ZY 添加关键词
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

// #ZY 删除关键词
window.deleteKeyword = async function(keyword) {
    if (!confirm(`确定删除关键词 "${keyword}" 吗？`)) return;
    
    try {
        await apiFetch(`/keywords?keyword=${encodeURIComponent(keyword)}`, { method: 'DELETE' });
        loadKeywords();
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
};

// #YU 422 按人员批量导入关键词（关键词管理页面）
window.importKeywordsWithUser = async function() {
    const file = document.getElementById('importUserFile').files[0];
    if (!file) { alert('请选择文件'); return; }
    const formData = new FormData();
    formData.append('file', file);
    try {
        // #YU 422 使用 apiFetch 替代直接 fetch，确保请求头正确
        const res = await apiFetch('/keywords/import-with-user', { 
            method: 'POST', 
            body: formData,
            headers: {} // #YU 422 FormData 不需要 Content-Type，让浏览器自动设置
        });
        document.getElementById('importUserResult').innerHTML = `<div class="alert alert-success">导入成功：新增关键词 ${res.imported_keywords} 个，新增关联 ${res.imported_relations} 条</div>`;
        await loadUsersForKeywords();
        loadKeywords();
    } catch (e) {
        document.getElementById('importUserResult').innerHTML = `<div class="alert alert-danger">导入失败: ${e.message}</div>`;
    }
};
// #ZY 下载导入模版文件
window.downloadTemplate = function() {
    try {
        // 创建工作簿
        const workbook = XLSX.utils.book_new();
        
        // 准备数据 - 新格式：关键词 | 负责人 | 标签 | 节日 | 大/小节日 | 热卖期
        const data = [
            ['关键词', '负责人', '标签', '节日', '大/小节日', '热卖期'],
            ['pool+party+decorations', '张三', '夏季,泳池派对', '夏季', '小节日', '高峰期'],
            ['summer+decorations', '', '装饰,夏季', '夏季', '', '预热期'],
            ['beach+towels', '李四', '沙滩,毛巾', '', '', ''],
            ['Christmas', '王五', '圣诞,礼物', '圣诞节', '大节日', '高峰期'],
            ['示例：请输入关键词(必填)', '示例：选填', '示例：多个用逗号分隔', '示例：选填', '示例：大节日/小节日', '示例：高峰期/预热期/平淡期/7-8月']
        ];

        // 创建工作表
        const worksheet = XLSX.utils.aoa_to_sheet(data);
        
        // 设置列宽
        worksheet['!cols'] = [
            {wch: 40},  // 关键词列宽
            {wch: 15},  // 负责人列宽
            {wch: 25},  // 标签列宽
            {wch: 20},  // 节日列宽
            {wch: 15},  // 大/小节日列宽
            {wch: 15}   // 热卖期列宽
        ];
        
        // 添加工作表到工作簿
        XLSX.utils.book_append_sheet(workbook, worksheet, '关键词导入模版');
        
        // 添加说明页
        const helpData = [
            ['📋 导入说明'],
            [''],
            ['1. 第一列是关键词（必填）'],
            ['2. 第二列是人员姓名（选填，多个用逗号分隔）'],
            ['3. 第三列是标签（选填，多个用逗号分隔）'],
            ['4. 第四列是节日（选填）'],
            ['5. 第五列是大/小节日（选填，可选值：大节日/小节日）'],
            ['6. 第六列是热卖期（选填，可选值：高峰期/预热期/平淡期）'],
            ['7. 空行会被自动跳过'],
            ['8. 支持的文件格式：.xlsx, .xls'],
            ['9. 已存在的关键词不会重复添加']
        ];
        const helpWorksheet = XLSX.utils.aoa_to_sheet(helpData);
        helpWorksheet['!cols'] = [{wch: 50}];
        XLSX.utils.book_append_sheet(workbook, helpWorksheet, '使用说明');
        
        // 生成文件名
        const today = new Date();
        const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        const fileName = `关键词导入模版_${dateStr}.xlsx`;
        
        // 下载文件
        XLSX.writeFile(workbook, fileName);
    } catch (error) {
        console.error('生成模版失败:', error);
        alert('生成模版失败: ' + error.message);
    }
};
// #YU 421 加载所有标签
async function loadAllTags(keywords) {
    kwTagsMap = {};
    await Promise.all(keywords.map(async kw => {
        try { kwTagsMap[kw] = await apiFetch(`/keywords/tags?keyword=${encodeURIComponent(kw)}`); }
        catch(e) { kwTagsMap[kw] = []; }
    }));
}

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
    await apiFetch(`/keywords/tags?keyword=${encodeURIComponent(kw)}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags) });
    kwTagsMap[kw] = tags;
    document.getElementById('newTag').value = '';
    renderTagsList(kw);
    loadKeywords();
};

window.removeTag = async function(kw, idx) {
    const tags = (kwTagsMap[kw] || []).filter((_, i) => i !== idx);
    await apiFetch(`/keywords/tags?keyword=${encodeURIComponent(kw)}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags) });
    kwTagsMap[kw] = tags;
    renderTagsList(kw);
    loadKeywords();
};

// #YU 422 修改modal中的标签渲染
function renderEditTagsList(keyword) {
    const tags = kwTagsMap[keyword] || [];
    document.getElementById('editTagsList').innerHTML = tags.length
        ? tags.map((t, i) => `<span class="badge bg-info text-dark me-1 mb-1">${t} <span style="cursor:pointer" onclick="removeEditTag(${i})">×</span></span>`).join('')
        : '<span class="text-muted small">暂无标签</span>';
}
// 渲染编辑模态框中的节日选项1
function renderEditFestivalOptions(keyword) {
    const festival = kwFestivalMap[keyword] || '';
    const festivalType = kwFestivalTypeMap[keyword] || '';
    const hotSeason = kwHotSeasonMap[keyword] || '';
    
    // 节日输入框
    document.getElementById('editFestival').value = festival;
    
    // 大/小节日下拉
    const festivalTypeSelect = document.getElementById('editFestivalType');
    festivalTypeSelect.innerHTML = `
        <option value="">请选择</option>
        <option value="大节日" ${festivalType === '大节日' ? 'selected' : ''}>大节日</option>
        <option value="小节日" ${festivalType === '小节日' ? 'selected' : ''}>小节日</option>
    `;
    
    // 热卖期下拉
    const hotSeasonSelect = document.getElementById('editHotSeason');
    hotSeasonSelect.innerHTML = `
        <option value="">请选择</option>
        <option value="高峰期" ${hotSeason === '高峰期' ? 'selected' : ''}>🔥 高峰期</option>
        <option value="预热期" ${hotSeason === '预热期' ? 'selected' : ''}>⏰ 预热期</option>
        <option value="平淡期" ${hotSeason === '平淡期' ? 'selected' : ''}>平淡期</option>
    `;
}
// 渲染编辑模态框中的节日等选项2
function renderEditExtraFields(keyword) {
    const festival = kwFestivalMap[keyword] || '';
    const festivalType = kwFestivalTypeMap[keyword] || '';
    const hotSeason = kwHotSeasonMap[keyword] || '';
    
    // 节日输入框
    document.getElementById('editFestival').value = festival;
    
    // 大/小节日下拉
    const festivalTypeSelect = document.getElementById('editFestivalType');
    festivalTypeSelect.innerHTML = `
        <option value="">请选择</option>
        <option value="大节日" ${festivalType === '大节日' ? 'selected' : ''}>大节日</option>
        <option value="小节日" ${festivalType === '小节日' ? 'selected' : ''}>小节日</option>
    `;
    
    // 热卖期输入框（直接设置值）
    document.getElementById('editHotSeason').value = hotSeason;
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

// #YU 421 修改关键词
window.editKeyword = function(keyword) {
    document.getElementById('editOldKeyword').value = keyword;
    document.getElementById('editNewKeyword').value = keyword;
    renderEditTagsList(keyword); // #YU 422
    // renderEditFestivalOptions(keyword);  // 新增
    renderEditExtraFields(keyword);  // 调用新函数名
    new bootstrap.Modal(document.getElementById('editKeywordModal')).show();
};

// #YU 页面初始化
document.addEventListener('DOMContentLoaded', async () => {
    await loadUsersForKeywords(); // #YU 421 先加载人员建立映射
    loadKeywords();
    document.getElementById('saveKeyword').addEventListener('click', addKeyword);
    // #YU 421 确认修改关键词
    document.getElementById('confirmEditKeyword').addEventListener('click', async () => {
        const oldKw = document.getElementById('editOldKeyword').value;
        const newKw = document.getElementById('editNewKeyword').value.trim();
        const festival = document.getElementById('editFestival').value.trim();
        const festivalType = document.getElementById('editFestivalType').value;
        const hotSeason = document.getElementById('editHotSeason').value;
        if (!newKw) return;
        try {
            // 保存标签 #YU 422
            const tags = kwTagsMap[oldKw] || [];
            await apiFetch(`/keywords/tags?keyword=${encodeURIComponent(oldKw)}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(tags) });
            // 保存新字段
            await apiFetch(`/keywords/festival?keyword=${encodeURIComponent(oldKw)}`, { 
                method: 'PUT', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(festival) 
            });
            await apiFetch(`/keywords/festival-type?keyword=${encodeURIComponent(oldKw)}`, { 
                method: 'PUT', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(festivalType) 
            });
            await apiFetch(`/keywords/hot-season?keyword=${encodeURIComponent(oldKw)}`, { 
                method: 'PUT', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(hotSeason) 
            });
            
            // 修改关键词名称
            if (newKw !== oldKw) {
                const res = await apiFetch('/keywords');
                const keywords = Array.isArray(res) ? res : (res.keywords || []);
                const updated = keywords.map(k => k === oldKw ? newKw : k);
                await apiFetch('/keywords', { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(updated) });
            }
            bootstrap.Modal.getInstance(document.getElementById('editKeywordModal')).hide();
            await loadUsersForKeywords();
            loadKeywords();
        } catch (error) {
            alert('修改失败: ' + error.message);
        }
    });
});

// #ZY 页面初始化
// document.addEventListener('DOMContentLoaded', () => {
//     loadKeywords();
//     document.getElementById('saveKeyword').addEventListener('click', addKeyword);
// });