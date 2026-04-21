// 自动检测：本地直接访问后端，Docker 通过 nginx 代理
const API_BASE = (location.port === '8000' || location.hostname === 'localhost' && location.port !== '8880')
    ? 'http://localhost:8000/api'
    : '/api';

const HEALTH_URL = API_BASE.startsWith('http') ? 'http://localhost:8000/health' : '/health';

async function checkApiStatus() {
    try {
        // 使用相对路径，通过 nginx 代理
        const response = await fetch(HEALTH_URL);
        const statusEl = document.getElementById('api-status');
        if (response.ok) {
            statusEl.textContent = 'API 在线';
            statusEl.className = 'badge bg-success';
        } else {
            throw new Error();
        }
    } catch (error) {
        const statusEl = document.getElementById('api-status');
        statusEl.textContent = 'API 离线';
        statusEl.className = 'badge bg-danger';
    }
}

async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${url}`, {
            ...options,
            headers: { 'Content-Type': 'application/json', ...options.headers }
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`API Error: ${url}`, error);
        throw error;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    checkApiStatus();
});