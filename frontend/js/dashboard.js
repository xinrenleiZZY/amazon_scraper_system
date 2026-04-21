async function loadDashboard() {
    const contentDiv = document.getElementById('content');
    try {
        const stats = await fetch('/api/stats').then(r => r.json());
        const tasksRes = await fetch('/api/tasks?limit=5').then(r => r.json());
        const productsRes = await fetch('/api/results?limit=10').then(r => r.json());
        
        const recentTasks = tasksRes.data || [];
        const recentData = productsRes.data || [];
        
        contentDiv.innerHTML = `
            <div class="row mb-4">
                <div class="col-md-3 mb-3"><div class="card card-stats"><div class="card-body"><div class="d-flex justify-content-between"><div><p class="text-muted mb-0">总关键词</p><p class="h2">${stats.total_keywords || 0}</p></div><i class="bi bi-tags fs-1 text-primary"></i></div></div></div></div>
                <div class="col-md-3 mb-3"><div class="card card-stats"><div class="card-body"><div class="d-flex justify-content-between"><div><p class="text-muted mb-0">总任务数</p><p class="h2">${stats.total_tasks || 0}</p></div><i class="bi bi-list-check fs-1 text-success"></i></div></div></div></div>
                <div class="col-md-3 mb-3"><div class="card card-stats"><div class="card-body"><div class="d-flex justify-content-between"><div><p class="text-muted mb-0">总商品数</p><p class="h2">${(stats.total_products || 0).toLocaleString()}</p></div><i class="bi bi-box fs-1 text-warning"></i></div></div></div></div>
                <div class="col-md-3 mb-3"><div class="card card-stats"><div class="card-body"><div class="d-flex justify-content-between"><div><p class="text-muted mb-0">今日抓取</p><p class="h2">${(stats.today_count || 0).toLocaleString()}</p></div><i class="bi bi-calendar-day fs-1 text-info"></i></div></div></div></div>
            </div>
            <div class="row">
                <div class="col-md-6 mb-4"><div class="card"><div class="card-header"><h5>最近任务</h5></div><div class="card-body"><table class="table table-sm"><thead><tr><th>关键词</th><th>状态</th><th>数量</th></tr></thead><tbody>${recentTasks.map(t => `<tr><td>${t.keyword}</td><td><span class="badge bg-${t.status === 'completed' ? 'success' : 'warning'}">${t.status}</span></td><td>${t.total_items || 0}</td></tr>`).join('') || '<tr><td colspan="3">暂无数据</td></tr>'}</tbody></table></div></div></div>
                <div class="col-md-6 mb-4"><div class="card"><div class="card-header"><h5>最新商品</h5></div><div class="card-body"><table class="table table-sm"><thead><tr><th>ASIN</th><th>标题</th><th>价格</th></tr></thead><tbody>${recentData.map(p => `<tr><td><code>${p.asin || '-'}</code></td><td>${(p.title || '').substring(0, 30)}...</td><td>${p.price_current || '-'}</td></tr>`).join('') || '<tr><td colspan="3">暂无数据</td></tr>'}</tbody></table></div></div></div>
            </div>
        `;
    } catch(e) {
        contentDiv.innerHTML = '<div class="alert alert-danger">加载失败</div>';
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadDashboard);
} else {
    loadDashboard();
}
