const API = '/api';
let allResults = [];

function showTab(name, el) {
    document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    el.classList.add('active');
    if (name === 'tasks') loadTasks();
    if (name === 'keywords') loadKeywords();
}

async function searchData() {
    const keyword = document.getElementById('search-keyword').value.trim();
    const asin = document.getElementById('search-asin').value.trim();
    const adtype = document.getElementById('search-adtype').value;

    let url = `${API}/results?limit=500`;
    if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;

    const res = await fetch(url);
    let data = await res.json();

    if (asin) data = data.filter(r => r.asin && r.asin.toUpperCase().includes(asin.toUpperCase()));
    if (adtype) data = data.filter(r => r.ad_type === adtype);

    allResults = data;
    renderResults(data);
}

function renderResults(data) {
    document.getElementById('results-count').textContent = `共 ${data.length} 条记录`;
    const tbody = document.getElementById('results-body');
    if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="11" class="empty">暂无数据</td></tr>';
        return;
    }
    tbody.innerHTML = data.map(r => `
        <tr>
            <td>${r.date || ''}</td>
            <td>${r.keyword || ''}</td>
            <td><code>${r.asin || ''}</code></td>
            <td><span class="badge badge-${r.ad_type}">${r.ad_type || ''}</span></td>
            <td>${r.ad_rank || ''}</td>
            <td>${r.organic_rank || ''}</td>
            <td>${r.page || ''}</td>
            <td title="${(r.title || '').replace(/"/g, '&quot;')}">${r.title || ''}</td>
            <td>${r.price_current || ''}</td>
            <td>${r.rating_stars ? r.rating_stars + ' ★' : ''}</td>
            <td>${r.rating_count ? r.rating_count.toLocaleString() : ''}</td>
        </tr>`).join('');
}

function exportCSV() {
    if (!allResults.length) return alert('请先查询数据');
    const headers = ['date','keyword','asin','ad_type','ad_rank','organic_rank','page','title','price_current','rating_stars','rating_count'];
    const rows = [headers, ...allResults.map(r => headers.map(h => JSON.stringify(r[h] ?? '')))];
    const csv = '\uFEFF' + rows.map(r => r.join(',')).join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], {type: 'text/csv'}));
    a.download = `results_${Date.now()}.csv`;
    a.click();
}

function setStatus(msg, isError = false) {
    const el = document.getElementById('scrape-status');
    el.textContent = msg;
    el.className = 'status-box' + (isError ? ' error' : '');
    el.classList.remove('hidden');
}

async function triggerScrape() {
    const keyword = document.getElementById('scrape-keyword').value.trim();
    const pages = document.getElementById('scrape-pages').value.trim();
    let url = `${API}/scrape`;
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    if (pages) params.append('pages', pages);
    if (params.toString()) url += '?' + params.toString();
    try {
        const res = await fetch(url, {method: 'POST'});
        const data = await res.json();
        setStatus(data.message || JSON.stringify(data));
    } catch(e) { setStatus('请求失败: ' + e.message, true); }
}

async function triggerDaily() {
    try {
        const res = await fetch(`${API}/scrape/daily`, {method: 'POST'});
        const data = await res.json();
        setStatus(data.message || JSON.stringify(data));
    } catch(e) { setStatus('请求失败: ' + e.message, true); }
}

async function triggerWeekly() {
    try {
        const res = await fetch(`${API}/scrape/weekly`, {method: 'POST'});
        const data = await res.json();
        setStatus(data.message || JSON.stringify(data));
    } catch(e) { setStatus('请求失败: ' + e.message, true); }
}

async function loadTasks() {
    const res = await fetch(`${API}/tasks?limit=50`);
    const data = await res.json();
    const tbody = document.getElementById('tasks-body');
    if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty">暂无任务</td></tr>';
        return;
    }
    tbody.innerHTML = data.map(t => `
        <tr>
            <td>${t.id}</td>
            <td>${t.keyword}</td>
            <td><span class="badge badge-${t.status}">${t.status}</span></td>
            <td>${t.total_items ?? ''}</td>
            <td>${t.started_at ? t.started_at.slice(0,19).replace('T',' ') : ''}</td>
            <td>${t.completed_at ? t.completed_at.slice(0,19).replace('T',' ') : ''}</td>
            <td title="${(t.error_message||'').replace(/"/g,'&quot;')}">${t.error_message || ''}</td>
        </tr>`).join('');
}

async function loadKeywords() {
    const res = await fetch(`${API}/keywords`);
    const data = await res.json();
    renderKeywords(data.keywords || []);
}

function renderKeywords(keywords) {
    const el = document.getElementById('keywords-list');
    if (!keywords.length) { el.innerHTML = '<span style="color:#aaa;font-size:13px">暂无关键词</span>'; return; }
    el.innerHTML = keywords.map(k => `
        <span class="keyword-tag">
            ${k}
            <button onclick="removeKeyword('${k.replace(/'/g,"\\'")}')">×</button>
        </span>`).join('');
}

async function addKeyword() {
    const input = document.getElementById('new-keyword');
    const kw = input.value.trim();
    if (!kw) return;
    const res = await fetch(`${API}/keywords?keyword=${encodeURIComponent(kw)}`, {method: 'POST'});
    const data = await res.json();
    input.value = '';
    renderKeywords(data.keywords || []);
}

async function removeKeyword(kw) {
    const res = await fetch(`${API}/keywords?keyword=${encodeURIComponent(kw)}`, {method: 'DELETE'});
    const data = await res.json();
    renderKeywords(data.keywords || []);
}

searchData();
