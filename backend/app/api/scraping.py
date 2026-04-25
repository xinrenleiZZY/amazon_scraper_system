# backend/app/api/scraping.py
from fastapi import APIRouter, BackgroundTasks, Query, WebSocket, WebSocketDisconnect, Depends, HTTPException,Header
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
import asyncio
from datetime import datetime


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


# 在文件末尾添加
@router.post("/tasks/{task_id}/stop")
def stop_task(
    task_id: int, 
    password: str = Header(..., alias="X-Password"),
    db: Session = Depends(get_db)
):
    """终止正在运行的任务（需要密码验证）"""
    from app.models import ScrapingTask
    
    # 密码验证
    if password != "He123456":
        raise HTTPException(status_code=403, detail="密码错误，无权终止任务")
    
    task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status not in ['running', 'pending']:
        raise HTTPException(status_code=400, detail="只能终止运行中或等待中的任务")
    
    # 更新任务状态为失败
    task.status = 'failed'
    task.error_message = '用户手动终止'
    task.completed_at = datetime.now()
    db.commit()
    
    return {"message": "任务已终止", "task_id": task_id}