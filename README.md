```markdown
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
├── frontend/                   # 前端界面
│   ├── index.html             # 主页面
│   ├── style.css              # 样式文件
│   ├── app.js                 # 前端逻辑
│   └── Dockerfile             # Nginx容器配置
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