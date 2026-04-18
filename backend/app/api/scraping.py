from fastapi import APIRouter, BackgroundTasks
from typing import Optional
from app.scraper.pipeline import run_now, run_daily, run_weekly

router = APIRouter()

@router.post("/scrape")
def start_scraping(background_tasks: BackgroundTasks, keyword: Optional[str] = None, pages: Optional[int] = None):
    background_tasks.add_task(run_now, keyword, pages)
    return {"message": "任务已启动", "keyword": keyword or "all"}

@router.post("/scrape/daily")
def trigger_daily(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_daily)
    return {"message": "每日任务已启动"}

@router.post("/scrape/weekly")
def trigger_weekly(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_weekly)
    return {"message": "每周任务已启动"}