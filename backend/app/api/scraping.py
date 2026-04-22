# backend/app/api/scraping.py
from fastapi import APIRouter, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from typing import Optional
import asyncio

router = APIRouter()

@router.get("/tasks/running") # ZY 0422
def get_running_tasks():
    """获取正在运行的任务"""
    from app.models import ScrapingTask
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # 查找状态为 running 或 pending 的任务
        running = db.query(ScrapingTask).filter(
            ScrapingTask.status.in_(['running', 'pending'])
        ).all()
        return running
    finally:
        db.close()

@router.post("/scrape") # ZY 0422 使用使用 asyncio.to_thread 异步
async def start_scraping(
    background_tasks: BackgroundTasks,
    keyword: Optional[str] = Query(None),
    pages: Optional[int] = Query(None)
):
    """启动爬取任务"""
    # 使用 asyncio.to_thread 避免阻塞主线程
    async def run_in_thread():
        from app.scraper.pipeline import run_now
        # 在线程池中执行同步代码
        result = await asyncio.to_thread(run_now, keyword, pages)
        return result
        # background_tasks.add_task(run_now, keyword, pages)

    # 创建后台任务
    task = asyncio.create_task(run_in_thread())
    return {
        "message": "任务已启动",
        "keyword": keyword or "所有关键词",
        "pages": pages or "自动"
    }


@router.post("/scrape/daily")
def trigger_daily(background_tasks: BackgroundTasks):
    """触发每日任务"""
    from app.scraper.pipeline import run_daily
    
    background_tasks.add_task(run_daily)
    return {"message": "每日任务已启动"}


@router.post("/scrape/weekly")
def trigger_weekly(background_tasks: BackgroundTasks):
    """触发每周任务"""
    from app.scraper.pipeline import run_weekly
    
    background_tasks.add_task(run_weekly)
    return {"message": "每周任务已启动"}