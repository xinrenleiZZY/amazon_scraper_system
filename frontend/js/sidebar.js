// 侧边栏配置
const sidebarItems = [
    { href: 'index.html', icon: 'bi-speedometer2', text: '仪表盘' },
    { href: 'keywords.html', icon: 'bi-tags', text: '关键词管理' },
    { href: 'keywords_overview.html', icon: 'bi-list-ul', text: '关键词总览' },
    { href: 'scrape.html', icon: 'bi-cloud-upload', text: '爬取控制' },
    { href: 'data.html', icon: 'bi-database', text: '数据查询' },
    { href: 'tasks.html', icon: 'bi-list-check', text: '任务监控' },
    { href: 'users.html', icon: 'bi-people', text: '人员管理' }
];

function renderSidebar() {
    const currentPage = window.location.pathname.split('/').pop();
    const nav = document.querySelector('.sidebar .nav');
    if (!nav) return;

    nav.innerHTML = sidebarItems.map(item => {
        const active = item.href === currentPage ? 'active' : '';
        return `<li class="nav-item"><a class="nav-link ${active}" href="${item.href}"><i class="bi ${item.icon}"></i> ${item.text}</a></li>`;
    }).join('');
}

document.addEventListener('DOMContentLoaded', renderSidebar);
