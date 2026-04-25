// 侧边栏配置
const sidebarItems = [
    { href: 'index.html', icon: 'bi-speedometer2', text: '仪表盘' },
    { href: 'keywords.html', icon: 'bi-tags', text: '关键词管理' },
    { href: 'keywords_overview.html', icon: 'bi-list-ul', text: '关键词总览' },
    { href: 'scrape.html', icon: 'bi-cloud-upload', text: '爬取控制' },
    { href: 'data.html', icon: 'bi bi-cloud-download', text: '数据查询' },
    { href: 'tasks.html', icon: 'bi-list-check', text: '任务监控' },
    { href: 'users.html', icon: 'bi-people', text: '人员管理' }
    
];
// 获取标题元素
function getTitleElement() {
    return document.querySelector('.sidebar .position-sticky h5');
}

// 更新标题显示（根据折叠状态）
function updateTitle(isCollapsed) {
    const titleEl = getTitleElement();
    if (!titleEl) return;
    
    if (isCollapsed) {
        // 折叠时显示简写
        titleEl.innerHTML = 'HZX<br><span style="font-size: 12px;">service</span>';
        titleEl.style.fontSize = '14px';
        titleEl.style.lineHeight = '1.3';
        titleEl.style.textAlign = 'center';
    } else {
        // 展开时显示完整标题
        titleEl.innerHTML = '汇挚鑫-亚马逊商品排名监控系统';
        titleEl.style.fontSize = '';
        titleEl.style.lineHeight = '';
        titleEl.style.textAlign = '';
    }
}
// 设置初始标题（不管折叠状态，先设置完整标题，后续根据状态调整）
function initTitle() {
    const titleEl = getTitleElement();
    if (titleEl && titleEl.innerHTML === '汇挚鑫-亚马逊商品排名监控系统') {
        // 标题已经是完整的，不需要修改
        return;
    }
    if (titleEl) {
        titleEl.innerHTML = '汇挚鑫-亚马逊商品排名监控系统';
    }
}

function renderSidebar() {
    const currentPage = window.location.pathname.split('/').pop();
    const nav = document.querySelector('.sidebar .nav');
    if (!nav) return;

    // 设置 nav 为 flex 列布局，让折叠按钮在底部
    nav.style.display = 'flex';
    nav.style.flexDirection = 'column';
    nav.style.height = 'calc(100vh - 80px)';

    // 渲染菜单项
    const menuItems = sidebarItems.map(item => {
        const active = item.href === currentPage ? 'active' : '';
        return `
            <li class="nav-item" style="list-style: none;">
                <a class="nav-link ${active}" href="${item.href}" data-tooltip="${item.text}">
                    <i class="bi ${item.icon}"></i>
                    <span>${item.text}</span>
                </a>
            </li>
        `;
    }).join('');
    
    // 菜单项 + 底部间距
    nav.innerHTML = `
        <div style="flex: 1;">
            ${menuItems}
        </div>
    `;
    
    // 添加折叠按钮到底部
    addCollapseButton();
    
    // 确保标题被正确初始化
    initTitle();
    // 初始化标题（根据当前折叠状态）
    const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    updateTitle(isCollapsed);
    // 添加底部版本信息
    addSidebarFooter();
}

document.addEventListener('DOMContentLoaded', renderSidebar);
// 添加底部版本信息
function addSidebarFooter() {
    const sidebar = document.querySelector('.sidebar .position-sticky');
    if (!sidebar) return;
    
    // 检查是否已存在 footer
    if (document.querySelector('.sidebar-footer')) return;
    
    const footer = document.createElement('div');
    footer.className = 'sidebar-footer';
    footer.innerHTML = `
        <i class="bi bi-database"></i> v2.0<br>
        <span style="font-size: 10px;">© 汇挚鑫科技</span>
    `;
    sidebar.appendChild(footer);
}

// 添加侧边栏折叠功能（可选）
function addSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    const toggleBtn = document.createElement('div');
    toggleBtn.className = 'sidebar-toggle';
    toggleBtn.innerHTML = '<i class="bi bi-chevron-left"></i>';
    toggleBtn.onclick = function() {
        sidebar.classList.toggle('collapsed');
        const icon = this.querySelector('i');
        if (sidebar.classList.contains('collapsed')) {
            icon.classList.remove('bi-chevron-left');
            icon.classList.add('bi-chevron-right');
            sidebar.style.width = '70px';
            document.querySelector('.col-md-10').classList.remove('col-md-10');
            document.querySelector('.col-md-10').classList.add('col-md-11');
        } else {
            icon.classList.remove('bi-chevron-right');
            icon.classList.add('bi-chevron-left');
            sidebar.style.width = '';
            document.querySelector('.col-md-11').classList.remove('col-md-11');
            document.querySelector('.col-md-11').classList.add('col-md-10');
        }
    };
    sidebar.appendChild(toggleBtn);
}

// 添加折叠按钮
function addCollapseButton() {
    const nav = document.querySelector('.sidebar .nav');
    if (!nav) return;
    
    // 检查是否已存在折叠项
    if (document.querySelector('.nav-collapse-item')) return;
    
    const collapseWrapper = document.querySelector('.sidebar .nav > div');
    if (!collapseWrapper) return;
    
    const collapseItem = document.createElement('li');
    collapseItem.className = 'nav-item nav-collapse-item';
    collapseItem.style.listStyle = 'none';
    collapseItem.style.marginTop = 'auto';
    collapseItem.style.borderTop = '1px solid rgba(255, 255, 255, 0.08)';
    collapseItem.style.paddingTop = '12px';
    
    collapseItem.innerHTML = `
        <a class="nav-link" href="#" onclick="toggleSidebar(); return false;">
            <i class="bi bi-chevron-left" id="sidebarCollapseIcon"></i>
            <span>收起菜单</span>
        </a>
    `;
    
    collapseWrapper.appendChild(collapseItem);
}

// 切换侧边栏折叠状态
window.toggleSidebar = function() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.col-md-10');
    const collapseIcon = document.getElementById('sidebarCollapseIcon');
    const collapseText = document.querySelector('.nav-collapse-item span');
    
    if (!sidebar) return;
    
    sidebar.classList.toggle('collapsed');
    
    if (sidebar.classList.contains('collapsed')) {
        sidebar.style.width = '80px';
        if (mainContent) {
            mainContent.classList.remove('col-md-10');
            mainContent.classList.add('col-md-11');
        }
        if (collapseIcon) {
            collapseIcon.classList.remove('bi-chevron-left');
            collapseIcon.classList.add('bi-chevron-right');
        }
        if (collapseText) collapseText.textContent = '展开';
        
        document.querySelectorAll('.sidebar .nav-link span').forEach(span => {
            const parentItem = span.closest('.nav-item');
            // 跳过折叠按钮本身的文字
            if (parentItem && !parentItem.classList.contains('nav-collapse-item')) {
                span.style.display = 'none';
            }
        });
        updateTitle(true);
        localStorage.setItem('sidebar_collapsed', 'true');
    } else {
        sidebar.style.width = '';
        if (mainContent) {
            mainContent.classList.remove('col-md-11');
            mainContent.classList.add('col-md-10');
        }
        if (collapseIcon) {
            collapseIcon.classList.remove('bi-chevron-right');
            collapseIcon.classList.add('bi-chevron-left');
        }
        if (collapseText) collapseText.textContent = '收起菜单';
        
        document.querySelectorAll('.sidebar .nav-link span').forEach(span => {
            span.style.display = '';
        });
        updateTitle(false);
        localStorage.setItem('sidebar_collapsed', 'false');
    }
};

// 加载保存的折叠状态
function loadSidebarState() {
    const isCollapsed = localStorage.getItem('sidebar_collapsed') === 'true';
    if (isCollapsed) {
        setTimeout(() => {
            window.toggleSidebar();
        }, 100);
    }
}

// 加载右下角精灵
function loadMascot() {
    // 检查是否已经存在
    if (document.querySelector('#mascot-helper')) return;
    
    const script = document.createElement('script');
    script.src = 'js/mascot.js';
    document.body.appendChild(script);
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    
    renderSidebar();
    loadSidebarState();
    loadMascot();
});