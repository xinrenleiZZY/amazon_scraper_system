# 目录amazon_scraper_system

## 🏗️ 系统架构

```
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
```

# Navicat 连接参数
```
连接名:        amazon_postgres
主机:          localhost
端口:          5200
初始数据库:    amazon_scraper
用户名:        admin
密码:          123456
```
# 数据库连接配置
```
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
```
# 数据库功能介绍
```
scraping_tasks (任务表)                    raw_search_results (数据表)
┌─────────────────────┐                   ┌─────────────────────────┐
│ id (PK)             │ ←────── 关联 ──── │ task_id (FK)            │
│ keyword             │                   │ asin                    │
│ status (running)    │                   │ title                   │
│ started_at          │                   │ price                   │
│ completed_at        │                   │ ...                     │
│ total_items         │                   └─────────────────────────┘
└─────────────────────┘
```
# 获取数据流程
```
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
```
```
┌─────────────────────────────────────────────────────────────────┐
│                        后端数据存储                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  scraper_config.json              PostgreSQL                   │
│  ├── keywords[]                   ├── users (id, name)          │
│  └── keyword_tags{}               └── user_keywords (user_id, keyword)
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
        │  关键词管理    │   │  关键词总览    │   │   人员管理    │
        │  (完整版)      │   │  (精简版)     │   │              │
        ├───────────────┤   ├───────────────┤   ├───────────────┤
        │ 显示:         │   │ 显示:         │   │ 显示:         │
        │ - 关键词      │   │ - 关键词      │   │ - 人员列表    │
        │ - 标签        │   │ - 标签        │   │ - 关键词数量  │
        │ - 负责人      │   │               │   │ - 关键词列表  │
        ├───────────────┤   ├───────────────┤   ├───────────────┤
        │ 操作:         │   │ 操作:          │   │ 操作:         │
        │ - 增删改关键词│   │ - 增删改关键词  │   │ - 增删改人员  │
        │ - 管理标签    │   │ - 管理标签     │   │ - 分配关键词  │
        │ - 按人员筛选  │   │ - 批量导入     │   │              │
        │ - 批量导入    │   │   (纯关键词)   │   │              │
        │   (含人员)    │   │               │   │              │
        └───────────────┘   └───────────────┘   └───────────────┘

                    ┌─────────────────────────────────────┐
                    │          后端统一数据源              │
                    ├─────────────────────────────────────┤
                    │  • scraper_config.json (关键词+标签) │
                    │  • PostgreSQL (人员+关联关系)        │
                    └─────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
    ┌───────────────┐         ┌───────────────┐         ┌───────────────┐
    │  关键词管理    │         │  关键词总览    │         │   人员管理    │
    │ (keywords.js) │         │(overview.js)  │         │  (users.js)   │
    └───────────────┘         └───────────────┘         └───────────────┘
```
# 重启服务
docker-compose up -d --build
docker-compose down
docker-compose up -d
# 手动重启前端
docker restart amazon_frontend
# 查看日志

docker-compose logs -f
docker logs amazon_backend --tail 30
# 访问所有页面
http://localhost:8880/index.html     # 仪表盘
http://localhost:8880/keywords.html  # 关键词管理
http://localhost:8880/scrape.html    # 爬取控制
http://localhost:8880/data.html      # 数据查询
http://localhost:8880/tasks.html     # 任务监控

# 容器内结构
```
/app
├── Dockerfile
├── main.py
├── requirements.txt
├── amazon_scraper.log
├── __pycache__/
└── app/
    ├── __init__.py
    ├── __pycache__/
    ├── api/
    ├── scraper/
    ├── config.py
    ├── crud.py
    ├── database.py
    ├── main.py
    ├── models.py
    └── schemas.py
```
# Amazon Scraper System

亚马逊商品数据爬取系统 - 支持关键词搜索、数据采集、可视化展示的全栈解决方案。

## 📋 目录

- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [数据库设计](#数据库设计)
- [API接口](#api接口)
- [使用场景](#使用场景)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 🏗️ 系统架构

```
amazon_scraper_system/
│
├── backend/                    # 后端服务（FastAPI）
│   ├── app/
│   │   ├── __init__.py        # 包初始化
│   │   ├── main.py            # FastAPI入口，注册路由，启动服务
│   │   ├── config.py          # 配置管理（读取.env环境变量）
│   │   ├── database.py        # PostgreSQL连接池、会话管理
│   │   ├── models.py          # SQLAlchemy数据表定义（ORM映射）
│   │   ├── schemas.py         # Pydantic模型（API请求/响应格式）
│   │   ├── crud.py            # 数据库操作函数（增删改查）
│   │   ├── scraper/           # 爬虫模块
│   │   │   ├── scraper_config.json      # 爬虫配置文件
│   │   │   ├── anti_scraping_config.py  # 反爬配置
│   │   │   ├── auto_amazon_scraper.py   # 核心爬虫
│   │   │   ├── headers_manager.py       # 请求头管理
│   │   │   ├── scraper.py               # curl_cffi + BeautifulSoup实现
│   │   │   ├── dataprocess.py           # 数据预处理
│   │   │   └── pipeline.py              # 完整流程编排
│   │   └── api/               # API路由
│   │       ├── keywords.py    # 关键词管理
│   │       ├── scraping.py    # 爬取任务管理
│   │       └── data.py        # 数据查询
│   ├── requirements.txt        # Python依赖
│   └── Dockerfile             # 后端容器配置
│
├── frontend/                  # 前端界面
│   ├── index.html              # 主页面
│   ├── keywords.html
│   ├── scrape.html
│   ├── data.html
│   ├── tasks.html
│   ├── nginx.conf   
│   ├── Dockerfile             # Nginx容器配置     
│   ├── css/
│   │   └── style.css         # 样式文件
│   └── js/                   # 前端逻辑
│       ├── common.js
│       ├── dashboard.js
│       ├── keywords.js
│       ├── scrape.js
│       ├── data.js
│       └── tasks.js
│
├── docker-compose.yml         # 服务编排
├── .env.example               # 环境变量模板
├── config.json                # 关键词配置
└── README.md                  # 项目文档
```

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- Python 3.12+（本地开发）
- PostgreSQL 15+（本地开发）

### 使用 Docker Compose 启动

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd amazon_scraper_system

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库密码等

# 3. 启动所有服务
docker-compose up -d

# 4. 查看服务状态
docker-compose ps
```

### 本地开发

```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端开发（使用任意静态服务器）
cd frontend
python -m http.server 3000
```

### 数据库连接（Navicat）

| 配置项 | 值 |
|--------|-----|
| 连接名 | `amazon_postgres` |
| 主机名 | `localhost` |
| 端口 | `5200` |
| 初始数据库 | `amazon_scraper` |
| 用户名 | `admin` |
| 密码 | `123456` |

## 💾 数据库设计

### 核心表结构

```sql
-- 任务表（scraping_tasks）
-- 记录每次爬取任务的执行情况
CREATE TABLE scraping_tasks (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending/running/completed/failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_items INTEGER DEFAULT 0
);

-- 搜索结果表（raw_search_results）
-- 存储爬取的商品数据
CREATE TABLE raw_search_results (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES scraping_tasks(id),
    asin VARCHAR(50) NOT NULL,
    title TEXT,
    price VARCHAR(50),
    rating DECIMAL(3,2),
    review_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 表关系

```
┌─────────────────────┐       ┌─────────────────────────┐
│  scraping_tasks     │       │  raw_search_results     │
├─────────────────────┤       ├─────────────────────────┤
│ id (PK)             │───┐   │ id (PK)                 │
│ keyword             │   │   │ task_id (FK) ───────────┘
│ status              │   └──>│ asin                    │
│ started_at          │       │ title                   │
│ completed_at        │       │ price                   │
│ total_items         │       │ rating                  │
└─────────────────────┘       └─────────────────────────┘
```

## 🔌 API接口

### 爬取任务

```bash
# 启动爬取任务
POST /api/scrape?keyword={keyword}&pages={pages}

# 示例
curl -X POST "http://localhost:8000/api/scrape?keyword=pool%20party%20decorations&pages=3"

# 响应
{
    "message": "任务已启动",
    "task_id": 1,
    "keyword": "pool party decorations"
}
```

### 任务状态

```bash
# 查询任务状态
GET /api/task/{task_id}/status

# 响应
{
    "task_id": 1,
    "keyword": "pool party decorations",
    "status": "running",
    "started_at": "2026-04-18T09:00:00",
    "total_items": 45
}
```

### 数据查询

```bash
# 获取搜索结果
GET /api/results?keyword={keyword}&limit={limit}&offset={offset}

# 获取仪表盘数据
GET /api/dashboard
```

## 📖 使用场景

### 场景1：前端按钮触发

```javascript
// 点击"开始爬取"按钮
async function startScraping(keyword) {
    const response = await fetch(`/api/scrape?keyword=${keyword}`, {
        method: 'POST'
    });
    const data = await response.json();
    console.log('任务已启动:', data);
    
    // 轮询任务状态
    const taskId = data.task_id;
    const interval = setInterval(async () => {
        const status = await fetch(`/api/task/${taskId}/status`);
        const result = await status.json();
        if (result.status === 'completed') {
            clearInterval(interval);
            loadResults(keyword);
        }
    }, 3000);
}
```

### 场景2：定时任务自动触发

```python
# 使用 APScheduler 每天早上9点执行
from apscheduler.schedulers.background import BackgroundScheduler
import requests

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=9, minute=0)
def daily_scraping_job():
    """每日定时爬取任务"""
    keywords = ['pool party decorations', 'summer decor', 'beach towels']
    for keyword in keywords:
        response = requests.post(
            f'http://localhost:8000/api/scrape',
            params={'keyword': keyword, 'pages': 3}
        )
        print(f"Started task for {keyword}: {response.json()}")

scheduler.start()
```

### 场景3：命令行触发

```bash
# 使用 curl 命令触发爬取
curl -X POST "http://localhost:8000/api/scrape?keyword=beach%20towels&pages=5"

# 使用 Python requests
python -c "
import requests
response = requests.post('http://localhost:8000/api/scrape', 
                        params={'keyword': 'summer decor', 'pages': 2})
print(response.json())
"
```

### 场景4：批量关键词爬取

```bash
# 批量爬取配置文件中的关键词
curl -X POST "http://localhost:8000/api/scrape/batch"
```

## ⚙️ 配置说明

### 环境变量（.env）

```bash
# 数据库配置
DB_HOST=postgres
DB_PORT=5432
DB_NAME=amazon_scraper
DB_USER=admin
DB_PASSWORD=123456

# 后端服务配置
BACKEND_PORT=8000
SECRET_KEY=your-secret-key-here

# 爬虫配置
REQUEST_DELAY=2
MAX_RETRIES=3
USER_AGENT_ROTATION=true
```

### 关键词配置（config.json）

```json
{
    "keywords": [
        "pool party decorations",
        "summer decor",
        "beach towels",
        "summer party decorations"
    ],
    "settings": {
        "pages_per_keyword": 3,
        "request_delay": 2,
        "output_format": "json"
    }
}
```

## ❓ 常见问题

### 1. 数据库连接失败

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### 2. 爬虫被反爬

- 调整请求延迟：增加 `REQUEST_DELAY` 值
- 更换代理IP：配置代理池
- 更新请求头：使用真实的浏览器 User-Agent

### 3. 查看爬取日志

```bash
# 查看后端日志
docker-compose logs backend

# 实时查看
docker-compose logs -f backend

# 查看爬虫专用日志
tail -f backend/app/scraper/amazon_scraper.log
```

### 4. 清空数据重新开始

```bash
# 重置数据库
docker-compose down -v
docker-compose up -d

# 或仅清空表数据
docker-compose exec postgres psql -U admin -d amazon_scraper -c "TRUNCATE scraping_tasks, raw_search_results;"
```

## 📝 数据流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端界面   │ ──> │  API 接口   │ ──> │  后台任务   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │
      │  POST /scrape      │                    │
      ├───────────────────>│                    │
      │                    │  background_tasks  │
      │  {"message": "任务已启动"}              │
      │<───────────────────┤                    │
      │                    │                    │
      │                    │  run_now(keyword)  │
      │                    ├───────────────────>│
      │                    │                    │
      │                    │                    ├─ 爬取数据
      │                    │                    ├─ 处理数据
      │                    │                    ├─ 存入数据库
      │                    │                    │
      │  查询状态           │                    │
      ├───────────────────>│                    │
      │                    │  查询数据库         │
      │  {"status": "running"}                  │
      │<───────────────────┤                    │
```
根据你提供的所有文件，我来总结一下当前系统的完整功能：

## 🏗️ 系统概述

---

## 📋 核心功能模块

### 1. 关键词管理 (`keywords.html` + `keywords.js`)
| 功能 | 说明 |
|------|------|
| 关键词列表 | 展示所有关键词，显示标签和负责人 |
| 添加关键词 | 手动添加单个关键词 |
| 修改关键词 | 修改关键词名称 |
| 删除关键词 | 删除关键词 |
| 标签管理 | 为关键词添加/删除标签 |
| 人员筛选 | 按负责人筛选关键词 |
| 批量导入 | Excel导入（关键词+人员姓名） |
| 下载模板 | 下载导入模板文件 |

### 2. 关键词总览 (`keywords_overview.html` + `keywords_overview.js`)
| 功能 | 说明 |
|------|------|
| 关键词列表 | 只显示关键词和标签（不显示负责人） |
| 批量导入 | 纯关键词导入（只有关键词列） |
| 下载模板 | 下载导入模板 |

### 3. 人员管理 (`users.html` + `users.js`)
| 功能 | 说明 |
|------|------|
| 人员列表 | 查看所有人员及其负责的关键词数量 |
| 添加人员 | 添加新人员 |
| 编辑人员 | 修改人员姓名 |
| 删除人员 | 删除人员及其关键词关联 |
| 分配关键词 | 为人员添加/移除关键词 |

### 4. 爬取控制 (`scrape.html` + `scrape.js`)
| 功能 | 说明 |
|------|------|
| 手动爬取 | 选择关键词和页数，立即执行爬取 |
| 每日任务 | 每天早上9点自动爬取所有关键词 |
| 每周任务 | 每周一早上9点自动爬取所有关键词 |
| 实时状态 | 显示正在运行的任务 |
| 实时日志 | 显示爬取过程的日志输出 |

### 5. 数据查询 (`data.html` + `data.js`)
| 功能 | 说明 |
|------|------|
| 产品列表 | 查看爬取到的商品数据 |
| 关键词筛选 | 按关键词筛选数据 |
| ASIN筛选 | 按ASIN筛选商品 |
| 分页浏览 | 分页查看数据 |

### 6. 任务监控 (`tasks.html` + `tasks.js`)
| 功能 | 说明 |
|------|------|
| 运行中任务 | 实时显示正在执行的任务 |
| 任务列表 | 所有历史任务记录 |
| 状态筛选 | 按状态筛选（运行中/已完成/失败） |
| 关键词筛选 | 按关键词筛选任务 |
| 任务详情 | 查看任务详情和抓取的商品列表 |
| 自动刷新 | 每10秒自动刷新任务列表 |

### 7. 仪表盘 (`index.html` + `dashboard.js`)
| 功能 | 说明 |
|------|------|
| 统计概览 | 总关键词数、总商品数、任务数等 |
| 图表展示 | 数据可视化图表 |

---

## 🔄 数据流转流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户操作                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────┬───────────┼───────────┬───────────────┐
        ▼               ▼           ▼           ▼               ▼
   ┌─────────┐    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │关键词管理│    │人员管理 │   │爬取控制 │   │数据查询 │   │任务监控 │
   └─────────┘    └─────────┘   └─────────┘   └─────────┘   └─────────┘
        │               │           │               │               │
        ▼               ▼           ▼               ▼               ▼
   ┌─────────────────────────────────────────────────────────────────┐
   │                        后端 API (FastAPI)                        │
   │  /keywords  /users  /scrape  /tasks  /results  /logs           │
   └─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
   ┌─────────┐                ┌─────────┐                ┌─────────┐
   │config.json│                │PostgreSQL│                │日志文件 │
   │ - 关键词  │                │ - 商品数据│                │.log     │
   │ - 标签    │                │ - 任务记录│                │         │
   └─────────┘                │ - 人员    │                └─────────┘
                              │ - 关联关系│
                              └─────────┘
```

---

## 📊 数据库表结构

| 表名 | 用途 |
|------|------|
| `raw_search_results` | 存储爬取的商品数据（ASIN、标题、价格、评分等） |
| `scraping_tasks` | 存储爬取任务记录（状态、开始时间、完成时间等） |
| `users` | 存储人员信息 |
| `user_keywords` | 人员与关键词的关联关系 |

---

## 🔌 API 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/keywords` | 获取关键词列表 |
| POST | `/api/keywords` | 添加关键词 |
| DELETE | `/api/keywords` | 删除关键词 |
| PUT | `/api/keywords` | 批量更新关键词 |
| GET | `/api/keywords/{kw}/tags` | 获取关键词标签 |
| PUT | `/api/keywords/{kw}/tags` | 更新关键词标签 |
| POST | `/api/keywords/import` | 批量导入关键词 |
| POST | `/api/keywords/import-with-user` | 按人员批量导入 |
| GET | `/api/users` | 获取人员列表 |
| POST | `/api/users` | 添加人员 |
| PUT | `/api/users/{id}` | 更新人员 |
| DELETE | `/api/users/{id}` | 删除人员 |
| POST | `/api/users/{id}/keywords` | 为用户添加关键词 |
| DELETE | `/api/users/{id}/keywords` | 移除用户的关键词 |
| POST | `/api/scrape` | 启动爬取任务 |
| POST | `/api/scrape/daily` | 触发每日任务 |
| POST | `/api/scrape/weekly` | 触发每周任务 |
| GET | `/api/tasks` | 获取任务列表 |
| GET | `/api/tasks/{id}` | 获取任务详情 |
| GET | `/api/results` | 获取商品数据 |
| GET | `/api/logs` | 获取爬取日志 |

---

## 🐳 容器服务

| 容器名 | 端口 | 说明 |
|--------|------|------|
| `amazon_postgres` | 5200 | PostgreSQL 数据库 |
| `amazon_backend` | 8888 | FastAPI 后端服务 |
| `amazon_frontend` | 8880 | Nginx 前端服务 |

---

## ✅ 总结

这是一个**功能完整的亚马逊爬虫管理系统**，支持：
- 关键词和人员的**灵活管理**
- **自动/手动**爬取亚马逊数据
- **实时监控**任务状态
- **数据查询**和**可视化**
- **Docker 一键部署**

当前的主要问题是 **502 错误**（前端连不上后端），重启容器即可解决。
## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request

## 📧 联系方式

- 作者: xinrenleiZZY
- 邮箱: xinrenlei_zy@gmail.com
```

主要改进点：

1. **添加了目录** - 方便快速导航
2. **使用标准Markdown语法** - 代码块指定语言、表格对齐
3. **添加图标** - 增强视觉识别度
4. **结构化分层** - 使用多级标题组织内容
5. **完善代码示例** - 所有代码都有语言标识
6. **添加配置说明** - 环境变量和配置文件示例
7. **常见问题** - 方便排错
8. **数据流程图** - 使用ASCII艺术图展示流程
9. **表格格式化** - 数据库连接参数使用表格展示
10. **添加许可证和贡献指南**
