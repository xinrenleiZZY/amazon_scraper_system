// frontend/js/mascot.js
(function() {
    // 等待 DOM 加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMascot);
    } else {
        initMascot();
    }
    
    function initMascot() {
        // 检查是否已存在
        if (document.getElementById('mascot-helper')) return;
        
        // 创建精灵容器
        const mascot = document.createElement('div');
        mascot.id = 'mascot-helper';
        mascot.innerHTML = `
            <style>
                #mascot-helper {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 9999;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                .mascot-container {
                    position: relative;
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
                    transition: all 0.3s ease;
                    animation: mascotFloat 3s ease-in-out infinite;
                }
                .mascot-container:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
                }
                .mascot-icon {
                    font-size: 30px;
                    color: white;
                }
                .mascot-tooltip {
                    position: absolute;
                    bottom: 70px;
                    right: 0;
                    background: #1f2937;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-size: 12px;
                    white-space: nowrap;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    opacity: 0;
                    visibility: hidden;
                    transition: all 0.3s ease;
                    pointer-events: none;
                }
                .mascot-tooltip:after {
                    content: '';
                    position: absolute;
                    bottom: -6px;
                    right: 20px;
                    width: 0;
                    height: 0;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 6px solid #1f2937;
                }
                #mascot-helper:hover .mascot-tooltip {
                    opacity: 1;
                    visibility: visible;
                    bottom: 80px;
                }
                @keyframes mascotFloat {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-8px); }
                }
                .mascot-message {
                    position: fixed;
                    bottom: 90px;
                    right: 90px;
                    background: #1f2937;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 20px;
                    font-size: 12px;
                    max-width: 180px;
                    white-space: normal;
                    opacity: 0;
                    transition: opacity 0.3s;
                    pointer-events: none;
                    z-index: 10000;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }
                .mascot-message.show {
                    opacity: 1;
                }
                .quick-menu {
                    position: fixed;
                    bottom: 90px;
                    right: 90px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    overflow: hidden;
                    z-index: 10001;
                    animation: menuSlideIn 0.2s ease-out;
                    min-width: 150px;
                }
                @keyframes menuSlideIn {
                    from {
                        opacity: 0;
                        transform: scale(0.8);
                        transform-origin: bottom right;
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }
                .quick-menu-item {
                    padding: 10px 16px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    cursor: pointer;
                    transition: background 0.2s;
                    border-bottom: 1px solid #f0f0f0;
                    font-size: 13px;
                }
                .quick-menu-item:hover {
                    background: #f0f7ff;
                }
                .quick-menu-item:last-child {
                    border-bottom: none;
                }
                .quick-menu-item i {
                    font-size: 16px;
                    color: #3b82f6;
                    width: 20px;
                }
            </style>
            <div class="mascot-container">
                <i class="bi bi-robot mascot-icon"></i>
                <div class="mascot-tooltip">
                    🤖 需要帮助？<br>点击打开快捷菜单
                </div>
            </div>
        `;
        
        document.body.appendChild(mascot);
        
        // 点击精灵显示快捷菜单
        mascot.addEventListener('click', function(e) {
            e.stopPropagation();
            showQuickMenu();
        });
        
        // 随机提示消息
        const messages = [
            '👋 需要帮助吗？',
            '📊 去数据查询页面看看',
            '🔍 试试关键词筛选功能',
            '📅 可以用日期筛选数据',
            '⚙️ 点击列设置自定义显示',
            '🚀 去爬取控制触发任务',
            '👥 人员管理可以分配关键词'
        ];
        
        let currentMessage = null;
        
        function showRandomMessage() {
            if (currentMessage) return;
            
            const randomMsg = messages[Math.floor(Math.random() * messages.length)];
            const msgDiv = document.createElement('div');
            msgDiv.className = 'mascot-message';
            msgDiv.textContent = randomMsg;
            document.body.appendChild(msgDiv);
            currentMessage = msgDiv;
            
            setTimeout(() => {
                msgDiv.classList.add('show');
            }, 100);
            
            setTimeout(() => {
                msgDiv.classList.remove('show');
                setTimeout(() => {
                    if (msgDiv.parentNode) msgDiv.parentNode.removeChild(msgDiv);
                    currentMessage = null;
                }, 300);
            }, 5000);
        }
        
        function showQuickMenu() {
            // 移除已存在的菜单
            const existingMenu = document.querySelector('.quick-menu');
            if (existingMenu) {
                existingMenu.remove();
                return;
            }
            
            const menu = document.createElement('div');
            menu.className = 'quick-menu';
            menu.innerHTML = `
                <div class="quick-menu-item" onclick="window.location.href='index.html'">
                    <i class="bi bi-speedometer2"></i> 仪表盘
                </div>
                <div class="quick-menu-item" onclick="window.location.href='keywords.html'">
                    <i class="bi bi-tags"></i> 关键词管理
                </div>
                <div class="quick-menu-item" onclick="window.location.href='scrape.html'">
                    <i class="bi bi-cloud-upload"></i> 爬取控制
                </div>
                <div class="quick-menu-item" onclick="window.location.href='data.html'">
                    <i class="bi bi-database"></i> 数据查询
                </div>
                <div class="quick-menu-item" onclick="window.location.href='tasks.html'">
                    <i class="bi bi-list-check"></i> 任务监控
                </div>
                <div class="quick-menu-item" onclick="window.location.href='users.html'">
                    <i class="bi bi-people"></i> 人员管理
                </div>
            `;
            
            document.body.appendChild(menu);
            
            // 点击其他地方关闭菜单
            const closeMenu = function(e) {
                if (!menu.contains(e.target) && e.target !== mascot) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            };
            
            setTimeout(() => {
                document.addEventListener('click', closeMenu);
            }, 100);
        }
        
        // 启动随机消息
        setTimeout(showRandomMessage, 3000);
        setInterval(showRandomMessage, 45000);
    }
})();
// ============================================
// 鼠标拖尾特效
// ============================================
// (function() {
//     // 配置参数
//     const config = {
//         particleCount: 12,      // 拖尾粒子数量
//         particleSize: 6,        // 粒子大小
//         particleColor: ['#3b82f6', '#8b5cf6', '#60a5fa', '#a78bfa', '#c084fc'], // 多彩色
//         fadeDelay: 0.5,         // 淡出延迟(秒)
//         maxTrailLength: 15      // 最大拖尾长度
//     };
    
//     let particles = [];
//     let mouseX = 0, mouseY = 0;
//     let lastX = 0, lastY = 0;
//     let animationId = null;
//     let canvas = null;
//     let ctx = null;
    
//     function initMouseTrail() {
//         // 创建 canvas
//         canvas = document.createElement('canvas');
//         canvas.id = 'mouse-trail-canvas';
//         canvas.style.position = 'fixed';
//         canvas.style.top = '0';
//         canvas.style.left = '0';
//         canvas.style.width = '100%';
//         canvas.style.height = '100%';
//         canvas.style.pointerEvents = 'none';
//         canvas.style.zIndex = '9998';
//         document.body.appendChild(canvas);
        
//         ctx = canvas.getContext('2d');
        
//         // 调整画布大小
//         function resizeCanvas() {
//             canvas.width = window.innerWidth;
//             canvas.height = window.innerHeight;
//         }
//         resizeCanvas();
//         window.addEventListener('resize', resizeCanvas);
        
//         // 监听鼠标移动
//         document.addEventListener('mousemove', function(e) {
//             mouseX = e.clientX;
//             mouseY = e.clientY;
            
//             // 添加新粒子
//             addParticle(mouseX, mouseY);
//         });
        
//         // 监听触摸屏（移动端）
//         document.addEventListener('touchmove', function(e) {
//             if (e.touches.length) {
//                 mouseX = e.touches[0].clientX;
//                 mouseY = e.touches[0].clientY;
//                 addParticle(mouseX, mouseY);
//             }
//         });
        
//         // 开始动画循环
//         animate();
//     }
    
//     function addParticle(x, y) {
//         // 限制拖尾长度
//         if (particles.length > config.maxTrailLength) {
//             particles.shift();
//         }
        
//         const color = config.particleColor[Math.floor(Math.random() * config.particleColor.length)];
        
//         particles.push({
//             x: x,
//             y: y,
//             size: Math.random() * config.particleSize + 2,
//             alpha: 1,
//             color: color,
//             life: 1
//         });
//     }
    
//     function animate() {
//         if (!ctx) return;
        
//         // 清空画布（使用透明度实现渐变消失效果）
//         ctx.clearRect(0, 0, canvas.width, canvas.height);
        
//         // 更新并绘制所有粒子
//         for (let i = particles.length - 1; i >= 0; i--) {
//             const p = particles[i];
            
//             // 减少生命值
//             p.life -= 0.03;
//             p.alpha = p.life;
            
//             if (p.life <= 0) {
//                 particles.splice(i, 1);
//                 continue;
//             }
            
//             // 绘制粒子
//             ctx.beginPath();
//             ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
            
//             // 渐变色填充
//             const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * p.life);
//             gradient.addColorStop(0, p.color);
//             gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
//             ctx.fillStyle = gradient;
            
//             ctx.fill();
//         }
        
//         animationId = requestAnimationFrame(animate);
//     }
    
//     // 页面加载完成后启动
//     if (document.readyState === 'loading') {
//         document.addEventListener('DOMContentLoaded', initMouseTrail);
//     } else {
//         initMouseTrail();
//     }
// })();