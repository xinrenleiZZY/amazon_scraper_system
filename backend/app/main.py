# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime

# 导入 API 路由
# 直接导入 router
from app.api.data import router as data_router
from app.api.scraping import router as scraping_router
from app.api.keywords import router as keywords_router
from app.api.distributed import router as distributed_router# ZY0422
from app.api.users import router as users_router #YU 421
from app.api.asin_monitor import router as asin_monitor_router
# zy 0422 添加日志路由
from app.api import logs


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Amazon Scraper API", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(data_router, prefix="/api", tags=["数据查询"])
app.include_router(scraping_router, prefix="/api", tags=["爬取控制"])
app.include_router(keywords_router, prefix="/api", tags=["关键词管理"])
app.include_router(distributed_router, prefix="/api", tags=["分布式爬取"])# ZY 0422
app.include_router(users_router, prefix="/api", tags=["人员管理"]) #YU 421
app.include_router(asin_monitor_router, prefix="/api", tags=["ASIN监控"])
app.include_router(logs.router, prefix="/api", tags=["logs"])# zy 0422 添加日志路由


# ========== Cron 定时任务调度器 ==========

scheduler = BackgroundScheduler()
scheduled_jobs = {}


def setup_cron_jobs():
    """设置定时任务"""
    global scheduled_jobs
    
    from app.scraper.schedule_config import load_schedule_config
    from app.scraper.pipeline import run_batch, run_now
    
    # 清除现有任务
    for job_id, job in scheduled_jobs.items():
        try:
            scheduler.remove_job(job_id)
            logger.info(f"移除旧任务: {job_id}")
        except Exception as e:
            logger.warning(f"移除任务失败 {job_id}: {e}")
    scheduled_jobs.clear()
    
    # 加载配置
    try:
        config = load_schedule_config()
    except Exception as e:
        logger.error(f"加载定时任务配置失败: {e}")
        return
    
    for job_config in config.get('jobs', []):
        if not job_config.get('enabled', True):
            logger.info(f"跳过已禁用的任务: {job_config.get('name')}")
            continue
        
        job_id = job_config['id']
        cron = job_config.get('cron', '')
        
        if not cron:
            logger.warning(f"任务 {job_id} 缺少 Cron 表达式，跳过")
            continue
        
        try:
            # 解析 Cron 表达式 (分 时 日 月 周)
            parts = cron.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                trigger = CronTrigger(
                    minute=minute, hour=hour, day=day,
                    month=month, day_of_week=day_of_week
                )
            else:
                logger.warning(f"无效的 Cron 表达式: {cron}，跳过任务 {job_id}")
                continue
            
            # 获取任务参数
            keywords = job_config.get('keywords', [])
            pages = job_config.get('pages')
            
            # 创建任务函数（闭包捕获参数）
            def create_job_func(job_cfg, kw_list, page_num):
                def job_func():
                    logger.info(f"📅 执行定时任务 [{job_cfg.get('name')}] - {datetime.now()}")
                    try:
                        if kw_list and '__ALL__' not in kw_list and len(kw_list) > 0:
                            # 爬取指定关键词
                            for keyword in kw_list:
                                logger.info(f"  → 爬取关键词: {keyword}")
                                run_now(keyword, page_num)
                        else:
                            # 爬取全部关键词
                            logger.info(f"  → 爬取全部关键词")
                            run_batch(page_num)
                        logger.info(f"✅ 定时任务 [{job_cfg.get('name')}] 执行完成")
                    except Exception as e:
                        logger.error(f"❌ 定时任务 [{job_cfg.get('name')}] 执行失败: {e}")
                return job_func
            
            job = scheduler.add_job(
                create_job_func(job_config, keywords, pages),
                trigger=trigger,
                id=job_id,
                replace_existing=True
            )
            scheduled_jobs[job_id] = job
            logger.info(f"✅ 已添加定时任务: {job_config['name']} - Cron: {cron}（{'全部关键词' if not keywords or '__ALL__' in keywords else f'{len(keywords)}个关键词'}）")
            
        except Exception as e:
            logger.error(f"添加定时任务失败 {job_config.get('name', job_id)}: {e}")


def reload_cron_jobs():
    """重新加载定时任务（供API调用）"""
    logger.info("重新加载定时任务...")
    setup_cron_jobs()


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    logger.info("启动 Cron 定时任务调度器...")
    scheduler.start()
    setup_cron_jobs()
    # 每30分钟检查一次 ASIN 监控任务
    from app.api.asin_monitor import run_due_monitor_tasks
    from app.database import get_db as db_factory
    scheduler.add_job(
        lambda: run_due_monitor_tasks(db_factory),
        "interval", minutes=30, id="asin_monitor_checker", replace_existing=True
    )
    logger.info("✅ Cron 定时任务调度器已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止调度器"""
    logger.info("停止 Cron 定时任务调度器...")
    scheduler.shutdown()
    logger.info("✅ Cron 定时任务调度器已停止")


@app.get("/")
def root():
    return {"message": "Amazon Scraper API is running", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}