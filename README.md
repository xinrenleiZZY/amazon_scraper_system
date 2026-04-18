# 目录amazon_scraper_system
amazon_scraper_system/

│

├── backend/                    # 后端服务（FastAPI）

│   ├── app/

│   │   ├── __init__.py        # 包初始化

│   │   │

│   │   ├── main.py            # FastAPI入口，注册路由，启动服务

│   │   │

│   │   ├── config.py          # 配置管理（读取.env环境变量）

│   │   │

│   │   ├── database.py        # PostgreSQL连接池、会话管理

│   │   │

│   │   ├── models.py          # SQLAlchemy数据表定义（ORM映射）

│   │   │

│   │   ├── schemas.py         # Pydantic模型（API请求/响应格式）

│   │   │

│   │   ├── crud.py            # 数据库操作函数（增删改查）

│   │   │

│   │   ├── scraper/           # 爬虫模块

│   │   │   ├── scraper_config.json    原始爬虫代码配置文件，包含关键词列表

│   │   │   ├── anti_scraping_config.py    原始爬虫代码配置文件

│   │   │   ├── auto_amazon_scraper.py    原始爬虫代码

│   │   │   ├── headers_manager.py    原始爬虫代码，管理请求头

│   │   │   ├── scraper.py     # 项目爬虫代码（curl_cffi + BeautifulSoup）

│   │   │   ├── dataprocess.py  原始爬虫数据预处理（处理后存入源数据库）

│   │   │   └── pipeline.py    # 完整流程编排（爬取→处理→存储）

│   │   │

│   │   └── api/               # API路由

│   │       ├── keywords.py    # 关键词管理API（增删改查config.json）

│   │       ├── scraping.py    # 爬取任务API（启动爬取、查看任务状态）

│   │       └── data.py        # 数据查询API（产品列表、分析报告、仪表盘）

│   │

│   ├── requirements.txt        # Python依赖列表

│   └── Dockerfile             # 后端容器构建文件

│

├── frontend/                   # 前端界面（静态HTML/JS）

│   ├── index.html             # 主页面（仪表盘、关键词管理、数据查询）

│   ├── style.css              # 样式（Bootstrap + 自定义）

│   ├── app.js                 # 前端逻辑（调用后端API，渲染图表）

│   └── Dockerfile             # 前端容器构建文件（nginx托管静态文件）

│

├── docker-compose.yml         # 编排所有服务（backend + frontend + postgres）

├── .env.example               # 环境变量模板（数据库密码等）

├── .env                       # 环境变量模板（数据库密码等）

├── config.json                # 爬虫配置文件（关键词列表）

└── README.md                  # 项目说明文档

# Navicat 连接参数
连接名:        amazon_postgres
主机:          localhost
端口:          5200
初始数据库:    amazon_scraper
用户名:        admin
密码:          123456
# 数据库连接配置
┌─────────────────────────────────────────┐
│ PostgreSQL - 新建连接                    │
├─────────────────────────────────────────┤
│ 连接名:  amazon_postgres                 │
│ 主机名:  localhost                       │
│ 端口:    5200                            │
│ 初始数据库: amazon_scraper               │
│ 用户名:  admin                           │
│ 密码:    123456                          │
│                                         │
│ [✓] 保存密码                            │
│                                         │
│ [测试连接]                              │
└─────────────────────────────────────────┘

# 数据库功能介绍
scraping_tasks (任务表)                    raw_search_results (数据表)
┌─────────────────────┐                   ┌─────────────────────────┐
│ id (PK)             │ ←────── 关联 ──── │ task_id (FK)            │
│ keyword             │                   │ asin                    │
│ status (running)    │                   │ title                   │
│ started_at          │                   │ price                   │
│ completed_at        │                   │ ...                     │
│ total_items         │                   └─────────────────────────┘
└─────────────────────┘

# 获取数据流程
───────────────────────────────────────────────────────────────
前端界面                API 接口                后台任务
    ──────────────────────────────────────────────
    │                    │                       │
    │  POST /scrape      │                       │
    ├───────────────────>│                       │
    │                    │  background_tasks     │
    │  {"message": "任务已启动"}                 │
    │<───────────────────┤                       │
    │                    │                       │
    │                    │  run_now(keyword)     │
    │                    ├──────────────────────>│
    │                    │                       │ 爬取数据
    │                    │                       │ 处理数据
    │                    │                       │ 存入数据库
    │                    │                       │
    │  查询状态          │                       │
    ├───────────────────>│                       │
    │                    │  查数据库              │
    │  {"status": "running"}                     │
    │<───────────────────┤                       │
    ──────────────────────────────────────────────


    使用场景
场景1：前端按钮触发
javascript
// 前端点击"开始爬取"按钮
fetch('/api/scrape?keyword=pool party decorations', {
    method: 'POST'
})
.then(res => res.json())
.then(data => console.log(data));
场景2：定时任务自动触发
python
# 使用 APScheduler 每天早上9点执行
from apscheduler.schedulers.background import BackgroundScheduler
import requests

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=9)
def daily_job():
    requests.post('http://localhost:8000/scrape/daily')
场景3：命令行触发
bash
# 用 curl 命令触发
curl -X POST "http://localhost:8000/scrape?keyword=beach%20towels&pages=3"