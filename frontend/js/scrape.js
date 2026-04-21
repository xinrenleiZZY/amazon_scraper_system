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
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger"><i class="bi bi-exclamation-circle"></i> 启动失败: ${error.message}</div>`;
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

document.addEventListener('DOMContentLoaded', () => {
    loadKeywords();
});